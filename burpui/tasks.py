"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui.tasks
    :platform: Unix
    :synopsis: Burp-UI tasks module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import sys
import os

from six import iteritems
from flask import current_app
from datetime import timedelta, datetime
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from time import gmtime, strftime, sleep

# Try to load modules from our current env first
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from burpui._compat import PY3  # noqa
from burpui.config import config  # noqa
from burpui.ext.tasks import celery  # noqa
from burpui.ext.cache import cache  # noqa
from burpui.sessions import session_manager  # noqa
from burpui.server import BUIServer  # noqa
from burpui.exceptions import BUIserverException  # noqa
from burpui.api.client import ClientTreeAll  # noqa

try:
    from .ext.ws import socketio
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

if not PY3:
    from itertools import imap as map

if config.get('WITH_SQL'):
    from burpui.ext.sql import db
else:
    db = None

bui = current_app  # type: BUIServer
logger = get_task_logger(__name__)
ME = __name__

LOCK_EXPIRE = 60 * 30  # Lock expires in 30 minutes

BEAT_SCHEDULE = {
    'ping-backend-hourly': {
        'task': '{}.ping_backend'.format(ME),
        'schedule': crontab(minute='15'),  # run every hour
    },
    'backup-running-4-minutely': {
        'task': '{}.backup_running'.format(ME),
        'schedule': timedelta(seconds=15),  # run every 15 seconds
    },
    'get-all-backups-every-twenty-minutes': {
        'task': '{}.get_all_backups'.format(ME),
        'schedule': crontab(minute='*/20'),  # every 20 minutes
    },
    'get-all-clients-reports-every-twenty-minutes': {
        'task': '{}.get_all_clients_reports'.format(ME),
        'schedule': crontab(minute='*/20'),  # every 20 minutes
    },
    'cleanup-expired-sessions-every-four-hours': {
        'task': '{}.cleanup_expired_sessions'.format(ME),
        'schedule': crontab(hour='*/4'),  # every four hours
    },
}

if db:
    from burpui.models import Task

    BEAT_SCHEDULE.update({
        'cleanup-restore-hourly': {
            'task': '{}.cleanup_restore'.format(ME),
            'schedule': crontab(minute='12'),  # run every hour
        },
    })

if 'CELERYBEAT_SCHEDULE' in celery.conf and \
        isinstance(celery.conf['CELERYBEAT_SCHEDULE'], dict):
    celery.conf['CELERYBEAT_SCHEDULE'].update(BEAT_SCHEDULE)
else:
    celery.conf['CELERYBEAT_SCHEDULE'] = BEAT_SCHEDULE


def acquire_lock(name, value='nyan', timeout=LOCK_EXPIRE):
    """Utility function to acquire a lock before processing the request"""
    lock = cache.cache.get(name)
    if lock:
        acquire_lock.lock = lock
        return False
    return cache.cache.add(name, value, timeout)


acquire_lock.lock = None


def release_lock(name):
    """Utility function to release a lock"""
    return cache.cache.delete(name)


def wait_for(lock_name, value, wait=10, timeout=LOCK_EXPIRE):
    """Utility function to wait until the given lock has been released"""
    old_lock = None
    if not acquire_lock(lock_name, value, timeout):
        logger.warn(
            'A task is already running. Wait for it: {}/{}'.format(
                lock_name,
                acquire_lock.lock
            )
        )
        old_lock = acquire_lock.lock
        # The lock should be released after LOCK_EXPLIRE max
        while not acquire_lock(lock_name, value, timeout):
            sleep(wait)

        # TODO: maybe we should check the status of task referenced by"old_lock"
        # to make sure the lock did not expire and the task is actually over
        logger.debug('lock released by: {}'.format(old_lock))

    return old_lock


@celery.task(ignore_result=True)
def ping_backend():
    if bui.standalone:
        bui.client.status()
    else:
        def __status(server):
            (serv, back) = server
            try:
                return bui.client.status(agent=serv)
            except BUIserverException:
                return False

        list(map(
            __status,
            iteritems(bui.client.servers)
        ))


@celery.task(bind=True, ignore_result=True)
def backup_running(self):
    # run one at the time, if one task was already running, we just discard
    # the new attempt
    if not acquire_lock(self.name):
        return None
    try:
        res = bui.client.is_one_backup_running()
        cache.cache.set(
            'backup_running_result',
            res,
            120
        )
        if WS_AVAILABLE:
            running = False
            if isinstance(res, dict):
                for _, run in iteritems(res):
                    if len(run) > 0:
                        running = True
                        break
            elif len(res) > 0:
                running = True
            socketio.emit('backup_running', running, namespace='/ws')
    finally:
        release_lock(self.name)


@celery.task(bind=True, ignore_result=True)
def get_all_backups(self):
    # run one at the time, if one task was already running, we just discard
    # the new attempt
    if not acquire_lock(self.name):
        return None
    try:
        backups = {}
        if bui.standalone:
            for cli in bui.client.get_all_clients():
                backups[cli['name']] = bui.client.get_client(cli['name'])
        else:
            for serv in bui.client.servers:
                backups[serv] = {}
                for cli in bui.client.get_all_clients(agent=serv):
                    backups[serv][cli['name']] = bui.client.get_client(cli['name'], agent=serv)
        cache.cache.set('all_backups', backups, 3600)
    finally:
        release_lock(self.name)


@celery.task(bind=True, ignore_result=True)
def get_all_clients_reports(self):
    # run one at the time, if one task was already running, we just discard
    # the new attempt
    if not acquire_lock(self.name):
        return None
    try:
        reports = {}
        if bui.standalone:
            reports = bui.client.get_clients_report(bui.client.get_all_clients())
        else:
            for serv in bui.client.servers:
                reports[serv] = bui.client.get_clients_report(bui.client.get_all_clients(agent=serv), serv)
        cache.cache.set('all_clients_reports', reports, 3600)
    finally:
        release_lock(self.name)


@celery.task(ignore_result=True)
def cleanup_expired_sessions():
    def expires(sess):
        ret = session_manager.invalidate_session_by_id(sess.uuid)
        if ret:
            session_manager.delete_session_by_id(sess.uuid)
        return ret
    list(map(expires, session_manager.get_expired_sessions()))


@celery.task(ignore_result=True)
def cleanup_restore():
    tasks = db.session.query(Task).filter(Task.task == 'perform_restore').filter(datetime.utcnow() > Task.expire).all()
    for rec in tasks:
        logger.info('Task expired: {}'.format(rec))
        task = perform_restore.AsyncResult(rec.uuid)
        try:
            if task.state != 'SUCCESS':
                logger.warn(
                    'Task is not done yet or did not end '
                    'successfully: {}'.format(task.state)
                )
                continue
            if not task.result:
                logger.warn('The task did not return anything')
                continue
            server = task.result.get('server')
            path = task.result.get('path')
            if path:
                if server:
                    if not bui.client.del_file(path, agent=server):
                        logger.warn("'{}' already removed".format(path))
                else:
                    if os.path.isfile(path):
                        os.unlink(path)
        finally:
            try:
                db.session.delete(rec)
                db.session.commit()
            except:
                db.session.rollback()
            task.revoke()


@celery.task(bind=True)
def perform_restore(self, client, backup,
                    files, strip, fmt, passwd, server=None, user=None,
                    admin=False, room=None, expire=timedelta(minutes=60)):
    ret = None
    lock_name = '{}-{}'.format(self.name, server)

    # TODO: maybe do something with old_lock someday
    wait_for(lock_name, self.request.id)

    try:
        if server:
            filename = 'restoration_%d_%s_on_%s_at_%s.%s' % (
                backup,
                client,
                server,
                strftime("%Y-%m-%d_%H_%M_%S", gmtime()),
                fmt)
        else:
            filename = 'restoration_%d_%s_at_%s.%s' % (
                backup,
                client,
                strftime("%Y-%m-%d_%H_%M_%S", gmtime()),
                fmt)

        self.update_state(state='STARTED', meta={'step': 'doing'})
        archive, err = bui.client.restore_files(
            client,
            backup,
            files,
            strip,
            fmt,
            passwd,
            server
        )
        if not archive:
            if not err:
                err = 'Something went wrong while restoring'
            self.update_state(state='FAILURE', meta={'error': err})
            logger.error('FAILURE: {}'.format(err))
        else:
            ret = {
                'filename': filename,
                'path': archive,
                'user': user,
                'server': server,
                'admin': admin
            }
            logger.debug(ret)

    finally:
        release_lock(lock_name)

    if db:
        curr = Task.query.filter_by(uuid=self.request.id).first()
        if curr:
            curr.expire = datetime.utcnow() + expire
            try:
                db.session.commit()
            except:
                db.session.rollback()

    if err:
        # make the task crash
        raise Exception(err)

    return ret


@celery.task(bind=True)
def load_all_tree(self, client, backup, server=None, user=None):
    key = 'load_all_tree-{}-{}-{}'.format(client, backup, server)
    ret = cache.cache.get(key)
    if ret:
        return {
            'client': client,
            'backup': backup,
            'server': server,
            'user': user,
            'tree': ret
        }

    lock_name = '{}-{}'.format(self.name, server)

    # TODO: maybe do something with old_lock someday
    wait_for(lock_name, self.request.id)

    try:
        ret = ClientTreeAll._get_tree_all(client, backup, server)
    except BUIserverException as exp:
        raise Exception(str(exp))
    finally:
        release_lock(lock_name)

    cache.cache.set(key, ret, 3600)
    return {
        'client': client,
        'backup': backup,
        'server': server,
        'user': user,
        'tree': ret
    }


def force_scheduling_now():
    """Force scheduling some tasks now"""
    get_all_backups.delay()
    backup_running.delay()
    get_all_clients_reports.delay()
    cleanup_expired_sessions.delay()
    cleanup_restore.delay()
