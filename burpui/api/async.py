# -*- coding: utf8 -*-
"""
.. module:: burpui.api.async
    :platform: Unix
    :synopsis: Burp-UI async api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import os
import select
import struct

from . import api, cache_key
from .clients import RunningBackup
from .misc import History
from ..server import BUIServer  # noqa
from .custom import Resource
from ..ext.async import celery
from ..ext.cache import cache
from ..config import config
from ..exceptions import BUIserverException

from six import iteritems
from zlib import adler32
from flask import url_for, Response, current_app, after_this_request, \
    send_file, redirect
from time import gmtime, strftime, time, sleep
from datetime import timedelta, datetime
from werkzeug.datastructures import Headers
from celery.schedules import crontab
from celery.utils.log import get_task_logger

if config.get('WITH_SQL'):
    from ..ext.sql import db
else:
    db = None

bui = current_app  # type: BUIServer
ns = api.namespace('async', 'Asynchronous methods')
logger = get_task_logger(__name__)
ME = __name__

LOCK_EXPIRE = 60 * 30  # Lock expires in 30 minutes

BEAT_SCHEDULE = {
    'ping-backend-hourly': {
        'task': '{}.ping_backend'.format(ME),
        'schedule': crontab(minute='15'),  # run every hour
    },
    'backup-running-minutely': {
        'task': '{}.backup_running'.format(ME),
        'schedule': crontab(),  # run every minute
    },
    'get-all-backups-bi-hourly': {
        'task': '{}.get_all_backups'.format(ME),
        'schedule': crontab(minute='23,53'),  # every 30 minutes
    },
}

if db:
    from ..models import Task

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
    lock = cache.cache.get(name)
    if lock:
        acquire_lock.lock = lock
        return False
    return cache.cache.add(name, value, timeout)
acquire_lock.lock = None


def release_lock(name):
    return cache.cache.delete(name)


def wait_for(lock_name, value, wait=10, timeout=LOCK_EXPIRE):
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


@celery.task
def ping_backend():
    if bui.standalone:
        logger.debug(bui.cli.status())
    else:
        for server, backend in iteritems(bui.cli.servers):
            logger.debug(bui.cli.status(agent=server))


@celery.task(bind=True)
def backup_running(self):
    # run once at the time, if one task was already running, we just discard
    # the new attempt
    if not acquire_lock(self.name):
        return None
    try:
        cache.cache.set(
            'backup_running_result',
            bui.cli.is_one_backup_running(),
            120
        )
    finally:
        release_lock(self.name)


@celery.task(bind=True)
def get_all_backups(self):
    # run once at the time, if one task was already running, we just discard
    # the new attempt
    if not acquire_lock(self.name):
        return None
    try:
        backups = {}
        if bui.standalone:
            for cli in bui.cli.get_all_clients():
                backups[cli['name']] = bui.cli.get_client(cli['name'])
        else:
            for serv in bui.cli.servers:
                backups[serv] = {}
                for cli in bui.cli.get_all_clients(agent=serv):
                    backups[serv][cli['name']] = bui.cli.get_client(cli['name'], agent=serv)
        cache.cache.set('all_backups', backups, 3600)
    finally:
        release_lock(self.name)


@celery.task
def cleanup_restore():
    tasks = Task.query.filter_by(task='perform_restore').all()
    for rec in tasks:
        if rec.expire and datetime.utcnow() > rec.expire:
            logger.info('Task expired: {}'.format(rec))
            task = perform_restore.AsyncResult(rec.uuid)
            try:
                if task.state != 'SUCCESS':
                    logger.warn(
                        'Task is not done yet or did not end '
                        'successfully: {}'.format(task.state)
                    )
                    task.revoke(terminate=True)
                    continue
                if not task.result:
                    logger.warn('The task did not return anything')
                    continue
                server = task.result.get('server')
                path = task.result.get('path')
                if path:
                    if server:
                        if not bui.cli.del_file(path, agent=server):
                            logger.warn("'{}' already removed".format(path))
                    else:
                        if os.path.isfile(path):
                            os.unlink(path)
            finally:
                db.session.delete(rec)
                db.session.commit()
                task.revoke()


@celery.task(bind=True)
def perform_restore(self, client, backup,
                    files, strip, fmt, passwd, server=None, user=None,
                    expire=timedelta(minutes=60)):
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
        archive, err = bui.cli.restore_files(
            client,
            backup,
            files,
            strip,
            fmt,
            passwd,
            server
        )
        if not archive:
            if err:
                self.update_state(state='FAILURE', meta={'error': err})
            else:
                err = 'Something went wrong while restoring'
                self.update_state(
                    state='FAILURE',
                    meta={'error': err}
                )
            logger.error('FAILURE: {}'.format(err))
        else:
            ret = {
                'filename': filename,
                'path': archive,
                'user': user,
                'server': server
            }
            logger.debug(ret)

    finally:
        release_lock(lock_name)

    if db:
        curr = Task.query.filter_by(uuid=self.request.id).first()
        if curr:
            curr.expire = datetime.utcnow() + expire
            db.session.commit()

    if err:
        # make the task crash
        raise BUIserverException(err)

    return ret


@ns.route('/status/<task_id>', endpoint='async_restore_status')
@ns.doc(
    params={
        'task_id': 'The task ID to process',
    }
)
class AsyncRestoreStatus(Resource):
    """The :class:`burpui.api.async.AsyncRestoreStatus` resource allows you to
    follow a restore task.

    This resource is part of the :mod:`burpui.api.async` module.
    """
    @ns.doc(
        responses={
            200: 'Success',
            500: 'Task failed',
        },
    )
    def get(self, task_id):
        """Returns the state of the given task"""
        task = perform_restore.AsyncResult(task_id)
        if task.state == 'FAILURE':
            if db:
                rec = Task.query.filter_by(uuid=task_id).first()
                if rec:
                    db.session.delete(rec)
                    db.session.commit()
            task.revoke()
            err = str(task.result)
            self.abort(500, err)
        if task.state == 'SUCCESS':
            if not task.result:
                self.abort(500, 'The task did not return anything')
            server = task.result.get('server')
            return {
                'state': task.state,
                'location': url_for(
                    '.async_get_file',
                    task_id=task_id,
                    server=server
                )
            }
        return {'state': task.state}


@ns.route('/get/<task_id>',
          '/<server>/get/<task_id>',
          endpoint='async_get_file')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
        'task_id': 'The task ID to process',
    }
)
class AsyncGetFile(Resource):
    """The :class:`burpui.api.async.AsyncGetFile` resource allows you to
    retrieve the archive generated by the given task.

    This resource is part of the :mod:`burpui.api.async` module.
    """

    @ns.doc(
        responses={
            200: 'Success',
            400: 'Incomplete task',
            403: 'Insufficient permissions',
            500: 'Task failed',
        },
    )
    def get(self, task_id, server=None):
        """Returns the generated archive"""
        task = perform_restore.AsyncResult(task_id)
        if task.state != 'SUCCESS':
            if task.state == 'FAILURE':
                self.abort(
                    500,
                    'Unsuccessful task: {}'.format(task.result.get('error'))
                )
            self.abort(400, 'Task not processed yet: {}'.format(task.state))

        path = task.result.get('path')
        user = task.result.get('user')
        dst_server = task.result.get('server')
        filename = task.result.get('filename')

        if self.username != user or (dst_server and dst_server != server):
            self.abort(403, 'Unauthorized access')

        if db:
            rec = Task.query.filter_by(uuid=task_id).first()
            if rec:
                db.session.delete(rec)
                db.session.commit()
        task.revoke()

        if dst_server:
            return self.stream_file(path, filename, dst_server)

        try:
            # Trick to delete the file while sending it to the client.
            # First, we open the file in reading mode so that a file handler
            # is open on the file. Then we delete it as soon as the request
            # ended. Because the fh is open, the file will be actually removed
            # when the transfer is done and the send_file method has closed
            # the fh. Only tested on Linux systems.
            fh = open(path, 'r')

            @after_this_request
            def remove_file(response):
                """Callback function to run after the client has handled
                the request to remove temporary files.
                """
                os.remove(path)
                return response

            resp = send_file(fh,
                             as_attachment=True,
                             attachment_filename=filename,
                             mimetype='application/zip')
            resp.set_cookie('fileDownload', 'true')
        except Exception as e:
            bui.cli.logger.error(str(e))
            self.abort(500, str(e))

        return resp

    def stream_file(self, path, filename, server):
        socket = bui.cli.get_file(path, server)
        if not socket:
            self.abort(500)
        lengthbuf = socket.recv(8)
        length, = struct.unpack('!Q', lengthbuf)

        def stream(sock, l):
            """The restoration took place on another server so we need
            to stream the file that is not present on the current
            machine.
            """
            bsize = 1024
            received = 0
            if l < bsize:
                bsize = l
            while received < l:
                buf = b''
                r, _, _ = select.select([sock], [], [], 5)
                if not r:
                    self.abort(500, 'Socket timed-out')
                buf += sock.recv(bsize)
                if not buf:
                    continue
                received += len(buf)
                self.logger.debug('{}/{}'.format(received, l))
                yield buf
            sock.sendall(struct.pack('!Q', 2))
            sock.sendall(b'RE')
            sock.close()

        headers = Headers()
        headers.add('Content-Disposition',
                    'attachement',
                    filename=filename)
        headers['Content-Length'] = length

        resp = Response(stream(socket, length),
                        mimetype='application/zip',
                        headers=headers,
                        direct_passthrough=True)
        resp.set_cookie('fileDownload', 'true')
        resp.set_etag('flask-%s-%s-%s' % (
            time(),
            length,
            adler32(filename.encode('utf-8')) & 0xffffffff))

        return resp


@ns.route('/archive/<name>/<int:backup>',
          '/<server>/archive/<name>/<int:backup>',
          endpoint='async_restore')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
        'name': 'Client name',
        'backup': 'Backup number',
    },
)
class AsyncRestore(Resource):
    """The :class:`burpui.api.async.AsyncRestore` resource allows you to
    perform a file restoration.

    This resource is part of the :mod:`burpui.api.async` module.

    The following parameters are supported:
    - ``list``: list of files/directories to restore
    - ``strip``: number of elements to strip in the path
    - ``format``: returning archive format
    - ``pass``: password to use for encrypted backups
    """
    parser = ns.parser()
    parser.add_argument(
        'pass',
        help='Password to use for encrypted backups',
        nullable=True
    )
    parser.add_argument(
        'format',
        required=False,
        help='Returning archive format',
        choices=('zip', 'tar.gz', 'tar.bz2'),
        default='zip',
        nullable=True
    )
    parser.add_argument(
        'strip',
        type=int,
        help='Number of elements to strip in the path',
        default=0,
        nullable=True
    )
    parser.add_argument(
        'list',
        required=True,
        help='List of files/directories to restore',
        nullable=False
    )

    @ns.expect(parser, validate=True)
    @ns.doc(
        responses={
            202: 'Accepted',
            400: 'Missing parameter',
            403: 'Insufficient permissions',
        },
    )
    def post(self, server=None, name=None, backup=None):
        """Performs an online restoration

        **POST** method provided by the webservice.

        This method returns a :mod:`flask.Response` object.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :param backup: The backup we are working on
        :type backup: int
        """
        args = self.parser.parse_args()
        files = args['list']
        strip = args['strip']
        fmt = args['format'] or 'zip'
        passwd = args['pass']
        if not files or not name or not backup:
            self.abort(400, 'missing arguments')
        # Manage ACL
        if (bui.acl and
                (not bui.acl.is_client_allowed(self.username,
                                               name,
                                               server) and not
                 self.is_admin)):
            self.abort(
                403,
                'You are not allowed to perform a restoration for this client'
            )
        task = perform_restore.apply_async(
            args=[
                name,
                backup,
                files,
                strip,
                fmt,
                passwd,
                server,
                self.username
            ]
        )
        if db:
            db_task = Task(
                task.id,
                'perform_restore',
                self.username,
                timedelta(minutes=60)
            )
            db.session.add(db_task)
            db.session.commit()
        return {'id': task.id, 'name': 'perform_restore'}, 202


@ns.route('/backup-running',
          '/<server>/backup-running',
          endpoint='async_running_backup')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
    }
)
class AsyncRunningBackup(RunningBackup):
    """The :class:`burpui.api.async.AsyncRunningBackup` resource allows you to
    access the status of the server in order to know if there is a running
    backup currently.

    This resource is backed by a periodic task. If the periodic task fail or is
    not running, we redirect to the "synchronous" API call.

    This resource is part of the :mod:`burpui.api.async` module.
    """

    @ns.marshal_with(
        RunningBackup.running_fields,
        code=200,
        description='Success',
        strict=False
    )
    def get(self, server=None):
        """Tells if a backup is running right now

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
                "running": false
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :returns: The *JSON* described above.
        """
        res = cache.cache.get('backup_running_result')
        if res is None:
            # redirect to synchronous API call
            # FIXME: Since we subclass the original code, we don't need the
            # redirect anymore if the redirection is problematic
            return redirect(url_for('api.running_backup', server=server))
        return {'running': self._is_one_backup_running(res, server)}


@ns.route('/history',
          '/history/<client>',
          '/<server>/history',
          '/<server>/history/<client>',
          endpoint='async_history')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
        'client': 'Client name',
    },
)
class AsyncHistory(History):
    """The :class:`burpui.api.misc.History` resource allows you to retrieve
    an history of the backups

    This resource is backed by a periodic task. If the periodic task fail or is
    not running, we redirect to the "synchronous" API call.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode and ``clientName`` is also allowed to filter
    by client.

    ::

        $('#calendar').fullCalendar({

            eventSources: [

                // your event source
                {
                    events: [ // put the array in the `events` property
                        {
                            title  : 'event1',
                            start  : '2010-01-01'
                        },
                        {
                            title  : 'event2',
                            start  : '2010-01-05',
                            end    : '2010-01-07'
                        },
                        {
                            title  : 'event3',
                            start  : '2010-01-09T12:30:00',
                        }
                    ],
                    color: 'black',     // an option!
                    textColor: 'yellow' // an option!
                }

                // any other event sources...

            ]

        });

    """

    @cache.cached(timeout=1800, key_prefix=cache_key)
    @ns.marshal_with(
        History.history_fields,
        code=200,
        description='Success',
        strict=False,
        as_list=True
    )
    @ns.expect(History.parser)
    @ns.doc(
        responses={
            200: 'Success',
            403: 'Insufficient permissions',
        },
    )
    def get(self, client=None, server=None):
        """Returns a list of calendars describing the backups that have been
        completed so far

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            [
              {
                "color": "#7C6F44",
                "events": [
                  {
                    "backup": "0000001",
                    "end": "2015-01-25 13:32:04+01:00",
                    "name": "toto-test",
                    "start": "2015-01-25 13:32:00+01:00",
                    "title": "Client: toto-test, Backup n°0000001",
                    "url": "/client/toto-test"
                  }
                ],
                "name": "toto-test",
                "textColor": "white"
              }
            ]


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str
        :param client: Which client to collect data from
        :type client: str

        :returns: The *JSON* described above
        """
        self._check_acl(client, server)
        res = cache.cache.get('all_backups')
        args = self.parser.parse_args()
        if res is None:
            # redirect to synchronous API call
            # FIXME: Since we subclass the original code, we don't need the
            # redirect anymore if the redirection is problematic
            return redirect(url_for('api.history', client=client, server=server, start=args['start'], end=args['end']))

        return self._get_backup_history(client, server, res)
