"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui.tasks
    :platform: Unix
    :synopsis: Burp-UI tasks module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import os
from datetime import datetime, timedelta
from time import gmtime, sleep, strftime

from celery.schedules import crontab
from celery.utils.log import get_task_logger
from flask import current_app

from burpui._compat import to_unicode  # noqa
from burpui.api.client import ClientTreeAll  # noqa
from burpui.config import config  # noqa
from burpui.engines.server import BUIServer  # noqa
from burpui.exceptions import BUIserverException, TooManyRecordsException  # noqa
from burpui.ext.cache import cache  # noqa
from burpui.ext.tasks import celery  # noqa
from burpui.sessions import session_manager  # noqa
from burpui.utils import NOTIF_ERROR

try:
    from burpui.ext.ws import socketio

    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

if config.get("WITH_SQL"):
    from burpui.ext.sql import db
else:
    db = None

bui = current_app  # type: BUIServer
logger = get_task_logger(__name__)
ME = __name__

LOCK_EXPIRE = 60 * 30  # Lock expires in 30 minutes

BEAT_SCHEDULE = {
    "backup-running-4-minutely": {
        "task": "{}.backup_running".format(ME),
        "schedule": timedelta(seconds=15),  # run every 15 seconds
    },
    "get-all-backups-every-twenty-minutes": {
        "task": "{}.get_all_backups".format(ME),
        "schedule": crontab(minute="*/20"),  # every 20 minutes
    },
    "get-all-clients-reports-every-twenty-minutes": {
        "task": "{}.get_all_clients_reports".format(ME),
        "schedule": crontab(minute="*/20"),  # every 20 minutes
    },
    "cleanup-expired-sessions-every-four-hours": {
        "task": "{}.cleanup_expired_sessions".format(ME),
        "schedule": crontab(minute=1, hour="*/4"),  # every four hours
    },
}

if db:
    from burpui.models import Task

    BEAT_SCHEDULE.update(
        {
            "cleanup-restore-hourly": {
                "task": "{}.cleanup_restore".format(ME),
                "schedule": crontab(minute="12"),  # run every hour
            },
        }
    )

if "CELERYBEAT_SCHEDULE" in celery.conf and isinstance(
    celery.conf["CELERYBEAT_SCHEDULE"], dict
):
    celery.conf["CELERYBEAT_SCHEDULE"].update(BEAT_SCHEDULE)
else:
    celery.conf["CELERYBEAT_SCHEDULE"] = BEAT_SCHEDULE


def acquire_lock(name, value="nyan", timeout=LOCK_EXPIRE):
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
            "A task is already running. Wait for it: {}/{}".format(
                lock_name, acquire_lock.lock
            )
        )
        old_lock = acquire_lock.lock
        # The lock should be released after LOCK_EXPIRE max
        while not acquire_lock(lock_name, value, timeout):
            sleep(wait)

        # TODO: maybe we should check the status of task referenced by"old_lock"
        # to make sure the lock did not expire and the task is actually over
        logger.debug("lock released by: {}".format(old_lock))

    return old_lock


@celery.task(bind=True, ignore_result=True)
def backup_running(self):
    # run one at the time, if one task was already running, we just discard
    # the new attempt
    if not acquire_lock(self.name):
        return None
    try:
        res = bui.client.is_one_backup_running()
        cache.cache.set("backup_running_result", res, 120)
        if WS_AVAILABLE:
            running = False
            if isinstance(res, dict):
                for run in res.values():
                    if len(run) > 0:
                        running = True
                        break
            elif len(res) > 0:
                running = True
            socketio.emit("backup_running", running, namespace="/ws")
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
        if bui.config["STANDALONE"]:
            for cli in bui.client.get_all_clients():
                backups[cli["name"]] = bui.client.get_client(cli["name"])
        else:
            for serv in bui.client.servers:
                backups[serv] = {}
                for cli in bui.client.get_all_clients(agent=serv):
                    backups[serv][cli["name"]] = bui.client.get_client(
                        cli["name"], agent=serv
                    )
        cache.cache.set("all_backups", backups, 3600)
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
        if bui.config["STANDALONE"]:
            reports = bui.client.get_clients_report(bui.client.get_all_clients())
        else:
            for serv in bui.client.servers:
                reports[serv] = bui.client.get_clients_report(
                    bui.client.get_all_clients(agent=serv), serv
                )
        cache.cache.set("all_clients_reports", reports, 3600)
    finally:
        release_lock(self.name)


@celery.task(
    ignore_result=True,
    max_retries=5,
    autoretry_for=(TooManyRecordsException,),
    retry_backoff=4,
)
def cleanup_expired_sessions():
    bucket = []

    def expires(sess):
        ret = session_manager.invalidate_session_by_id(sess.uuid)
        if ret:
            bucket.append(sess.uuid)
        return ret

    # remove expired sessions, limit to 10000 per batch
    list(map(expires, session_manager.get_expired_sessions(10000)))
    session_manager.bulk_session_delete_by_id(bucket)

    # if we still have more than 10000 expired session, schedule a new cleanup soon
    # unless we already ran 5 successive cleanups (in which case we will just wait
    # for the next schedule to trigger the task).
    if session_manager.get_expired_sessions_count() >= 10000:
        # we raise an exception so celery knows it has to restart this tasks
        # anytime soon.
        raise TooManyRecordsException


@celery.task(
    ignore_result=True,
    max_retries=3,
    autoretry_for=(TooManyRecordsException,),
    retry_backoff=True,
)
def cleanup_restore():
    bucket = []
    query = Task.query.filter(
        Task.task == "perform_restore", Task.expire <= datetime.utcnow()
    )
    for rec in query.limit(100):
        logger.info("Task expired: {}".format(rec))
        task = perform_restore.AsyncResult(rec.uuid)
        try:
            if task.state != "SUCCESS":
                logger.warn(
                    "Task is not done yet or did not end "
                    "successfully: {}".format(task.state)
                )
                continue
            if not task.result:
                logger.warn("The task did not return anything")
                continue
            server = task.result.get("server")
            path = task.result.get("path")
            if path:
                if server:
                    if not bui.client.del_file(path, agent=server):
                        logger.warn("'{}' already removed".format(path))
                else:
                    if os.path.isfile(path):
                        os.unlink(path)
        finally:
            bucket.append(rec.uuid)
            task.revoke()
    try:
        Task.query.filter(Task.uuid.in_(bucket)).delete(synchronize_session=False)
        db.session.commit()
    except:
        db.session.rollback()
    if query.count() > 100:
        raise TooManyRecordsException


@celery.task(bind=True)
def perform_restore(
    self,
    client,
    backup,
    files,
    strip,
    fmt,
    passwd,
    server=None,
    user=None,
    admin=False,
    room=None,
    expire=timedelta(minutes=60),
):
    ret = None
    # we can have only one restore per server-client at the time
    lock_name = "{}-{}-{}".format(self.name, server, client)

    # TODO: maybe do something with old_lock someday
    wait_for(lock_name, self.request.id)

    try:
        if server:
            filename = "restoration_%d_%s_on_%s_at_%s.%s" % (
                backup,
                client,
                server,
                strftime("%Y-%m-%d_%H_%M_%S", gmtime()),
                fmt,
            )
        else:
            filename = "restoration_%d_%s_at_%s.%s" % (
                backup,
                client,
                strftime("%Y-%m-%d_%H_%M_%S", gmtime()),
                fmt,
            )

        self.update_state(state="STARTED", meta={"step": "doing"})
        archive, err = bui.client.restore_files(
            client, backup, files, strip, fmt, passwd, server
        )
        if not archive:
            if not err:
                err = "Something went wrong while restoring"
            self.update_state(state="FAILURE", meta={"error": to_unicode(err)})
            logger.error("FAILURE: {}".format(err))
        else:
            ret = {
                "filename": filename,
                "path": to_unicode(archive),
                "user": user,
                "server": server,
                "admin": admin,
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
def delete_client(
    self, client, keepconf, delcert, revoke, template, delete, server, user
):
    parser = bui.client.get_parser(agent=server)
    self.update_state(state="STARTED", meta={"step": "doing"})

    res = parser.remove_client(client, keepconf, delcert, revoke, template, delete)
    if any(x == NOTIF_ERROR for x, _ in res):
        self.update_state(state="FAILURE", meta={"error": res})
        raise Exception(res)

    ret = {
        "result": res,
        "client": client,
        "server": server,
        "user": user,
        "kwargs": {
            "keepconf": keepconf,
            "delcert": delcert,
            "revoke": revoke,
            "template": template,
            "delete": delete,
            "template": template,
        },
    }
    logger.debug(ret)
    return ret


@celery.task(bind=True)
def load_all_tree(self, client, backup, server=None, user=None):
    key = "load_all_tree-{}-{}-{}".format(client, backup, server)
    ret = cache.cache.get(key)
    if ret:
        return {
            "client": client,
            "backup": backup,
            "server": server,
            "user": user,
            "tree": ret,
        }

    lock_name = "{}-{}".format(self.name, server)

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
        "client": client,
        "backup": backup,
        "server": server,
        "user": user,
        "tree": ret,
    }


def force_scheduling_now():
    """Force scheduling some tasks now"""
    get_all_backups.delay()
    backup_running.delay()
    get_all_clients_reports.delay()
    cleanup_expired_sessions.delay()
    cleanup_restore.delay()
