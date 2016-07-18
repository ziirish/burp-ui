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

from . import api
from .custom import Resource

from zlib import adler32
from flask import url_for, Response, current_app as bui, after_this_request, \
    send_file
from time import gmtime, strftime, time, sleep
from datetime import timedelta, datetime
from werkzeug.datastructures import Headers
from celery.utils.log import get_task_logger

ns = api.namespace('async', 'Asynchronous methods')
cache = api.cache
celery = api.celery
app_cli = api.app_cli
db = api.db
app = api.gapp
logger = get_task_logger(__name__)

if db:
    from ..models import Task
    from celery.schedules import crontab

    celery.conf['CELERYBEAT_SCHEDULE'] = {
        'cleanup-restore-hourly': {
            'task': 'burpui.api.async.cleanup_restore',
            'schedule': crontab(minute='12'),  # run every hour
        },
        'ping-backend-hourly': {
            'task': 'burpui.api.async.ping_backend',
            'schedule': crontab(minute='*/2'),  # run every hour
        },
    }

LOCK_EXPIRE = 60 * 30  # Lock expires in 30 minutes


@celery.task
def ping_backend():
    with app.app_context():
        logger.debug('PING')
        if app.standalone:
            logger.debug(app_cli.status())


@celery.task
def cleanup_restore():
    with app.app_context():
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
                    server = task.result.get('server')
                    path = task.result.get('path')
                    if server:
                        if not app_cli.del_file(path, agent=server):
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
    with app.app_context():
        def acquire_lock(name):
            return cache.cache.add(name, 'true', LOCK_EXPIRE)

        def release_lock(name):
            return cache.cache.delete(name)

        ret = None
        lock_name = '{}-{}'.format(self.name, server)

        if not acquire_lock(lock_name):
            logger.warn(
                'A task is already running. Wait for it: {}'.format(lock_name)
            )
            # The lock should be released after LOCK_EXPLIRE max
            while not acquire_lock(lock_name):
                sleep(10)

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
            archive, err = app_cli.restore_files(
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
                    self.update_state(
                        state='FAILURE',
                        meta={'error': 'Something went wrong while restoring'}
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
                print curr, curr.expire
                curr.expire = datetime.utcnow() + expire
                db.session.commit()
        return ret


@ns.route('/status/<task_id>', endpoint='async_restore_status')
@ns.doc(
    params={
        'task_id': 'The task ID to process',
    }
)
class AsyncRestoreStatus(Resource):
    """The :class:`burpui.api.restore.AsyncRestoreStatus` resource allows you to
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
            self.abort(500, task.result.get('error'))
        if task.state == 'SUCCESS':
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
    """The :class:`burpui.api.restore.AsyncRestoreStatus` resource allows you to
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
    """The :class:`burpui.api.restore.AsyncRestore` resource allows you to
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
