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

from . import api, cache_key, force_refresh
from .misc import History
from .custom import Resource
from .client import node_fields
from .clients import RunningBackup, ClientsReport, RunningClients
from ..engines.server import BUIServer  # noqa
from ..ext.cache import cache
from ..config import config
from ..decorators import browser_cache
from ..tasks import perform_restore, load_all_tree

from time import time
from zlib import adler32
from flask import url_for, Response, current_app, after_this_request, \
    send_file, request
from flask_login import current_user
from datetime import timedelta
from werkzeug.datastructures import Headers
try:
    from .ext.ws import socketio  # noqa
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

if config.get('WITH_SQL'):
    from ..ext.sql import db
    from ..models import Task
else:
    db = None

bui = current_app  # type: BUIServer
ns = api.namespace('async', 'Asynchronous methods')

task_types = {
    'restore': (perform_restore, '.async_get_file'),
    'browse': (load_all_tree, '.async_do_browse_all'),
}


@ns.route('/status/<task_type>/<task_id>',
          '/<server>/status/<task_type>/<task_id>',
          endpoint='async_status')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
        'task_id': 'The task ID to process',
        'task_type': 'The task type (either "restore" or "browse")',
    }
)
class AsyncStatus(Resource):
    """The :class:`burpui.api.async.AsyncStatus` resource allows you to
    follow a restore task.

    This resource is part of the :mod:`burpui.api.async` module.
    """
    if config['WITH_LIMIT']:
        try:
            from ..ext.limit import limiter
            decorators = [limiter.exempt]
        except ImportError:
            pass

    @ns.doc(
        responses={
            200: 'Success',
            500: 'Task failed',
        },
    )
    def get(self, task_type, task_id, server=None):
        """Returns the state of the given task"""
        if task_type not in task_types:
            return {'state': 'FAILURE'}
        task_obj, callback = task_types[task_type]
        task = task_obj.AsyncResult(task_id)
        if task.state == 'FAILURE':
            if db:
                rec = Task.query.filter_by(uuid=task_id).first()
                if rec:
                    try:
                        db.session.delete(rec)
                        db.session.commit()
                    except:
                        db.session.rollback()
            task.revoke()
            err = str(task.result)
            self.abort(502, err)
        if task.state == 'SUCCESS':
            if not task.result:
                self.abort(500, 'The task did not return anything')
            server = task.result.get('server')
            return {
                'state': task.state,
                'location': url_for(
                    callback,
                    task_id=task_id,
                    server=server
                )
            }
        return {'state': task.state}

    @ns.doc(
        responses={
            201: 'Success',
            400: 'Wrong request',
            403: 'Permission denied',
        },
    )
    def delete(self, task_type, task_id, server=None):
        """Cancel a given task"""
        if task_type not in task_types:
            return '', 400
        task_obj, _ = task_types[task_type]
        task = task_obj.AsyncResult(task_id)
        user = task.result.get('user')
        dst_server = task.result.get('server')

        if (current_user.name != user or (dst_server and dst_server != server)) and \
                not current_user.acl.is_admin():
            self.abort(403, 'Unauthorized access')

        # do not remove the task from db yet since we may need to remove
        # some temporary files afterward. The "cleanup_restore" task will take
        # care of this
        task.revoke()
        return '', 201


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
                err = task.result.get('error')
                if err != 'encrypted' and not task.result.get('admin'):
                    err = 'An error occurred while performing the ' \
                          'restoration. Please contact your administrator ' \
                          'for further details'
                self.abort(
                    500,
                    'Unsuccessful task:\n{}'.format(err)
                )
            self.abort(400, 'Task not processed yet: {}'.format(task.state))

        path = task.result.get('path')
        user = task.result.get('user')
        dst_server = task.result.get('server')
        filename = task.result.get('filename')

        if (current_user.name != user or (dst_server and dst_server != server)) and \
                not current_user.acl.is_admin():
            self.abort(403, 'Unauthorized access')

        if db:
            rec = Task.query.filter_by(uuid=task_id).first()
            if rec:
                try:
                    db.session.delete(rec)
                    db.session.commit()
                except:
                    db.session.rollback()
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
            fh = open(path, 'rb')

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
            bui.client.logger.error(str(e))
            self.abort(500, str(e))

        return resp

    def stream_file(self, path, filename, server):
        socket = bui.client.get_file(path, server)
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
        server_log = f' on {server}' if server else ''
        args_log = args.copy()
        # don't leak secrets in logs
        del args_log['pass']
        bui.audit.logger.info(f'{current_user} requested restoration of backup n°{backup} for {name}{server_log}: {args_log}')
        room = None
        if WS_AVAILABLE:
            room = request.sid
        if not files or not name or not backup:
            self.abort(400, 'missing arguments')
        # Manage ACL
        if not current_user.is_anonymous and \
                not current_user.acl.is_admin() and \
                not current_user.acl.is_client_rw(name, server):
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
                current_user.name,
                not current_user.is_anonymous and current_user.acl.is_admin(),
                room
            ]
        )
        if db:
            db_task = Task(
                task.id,
                'perform_restore',
                current_user.name,
                timedelta(minutes=60)
            )
            try:
                db.session.add(db_task)
                db.session.commit()
            except:
                db.session.rollback()
        return {'id': task.id, 'name': 'perform_restore'}, 202


@ns.route('/running',
          '/<server>/running',
          '/running/<client>',
          '/<server>/running/<client>',
          endpoint='async_running_clients')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
        'client': 'Client name',
    },
)
class AsyncRunningClients(RunningClients):
    """The :class:`burpui.api.async.AsyncRunningClients` resource allows you
    to retrieve a list of clients that are currently running a backup.

    This resource is part of the :mod:`burpui.api.async` module.

    This resource is backed by a periodic task. If the periodic task fail or is
    not running, we fallback to the "synchronous" API call.

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.

    .. seealso:: :class:`burpui.api.clients.RunningClients`
    """

    def get(self, client=None, server=None):
        """Returns a list of clients currently running a backup

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            [ 'client1', 'client2' ]


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to see.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param client: Ask a specific client in order to know if it is running a backup
        :type client: str

        :returns: The *JSON* described above.
        """
        server = server or self.parser.parse_args()['serverName']
        res = cache.cache.get('backup_running_result')
        if res is None:
            res = bui.client.is_one_backup_running(server)
        return self._running_clients(res, client, server)


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
    not running, we fallback to the "synchronous" API call.

    This resource is part of the :mod:`burpui.api.async` module.
    """

    @ns.marshal_with(
        RunningBackup.running_fields,
        code=200,
        description='Success',
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
            res = bui.client.is_one_backup_running(server)
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

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_with(
        History.history_fields,
        code=200,
        description='Success',
        as_list=True
    )
    @ns.expect(History.parser)
    @ns.doc(
        responses={
            200: 'Success',
            403: 'Insufficient permissions',
        },
    )
    @browser_cache(1800)
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
        if res is None:
            return self._get_backup_history(client, server)

        return self._get_backup_history(client, server, res)


@ns.route('/report',
          '/<server>/report',
          endpoint='async_clients_report')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
    },
)
class AsyncClientsReport(ClientsReport):
    """The :class:`burpui.api.async.AsyncClientsReport` resource allows you to
    access general reports about your clients.

    This resource is part of the :mod:`burpui.api.clients` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_with(
        ClientsReport.report_fields,
        code=200,
        description='Success',
    )
    @ns.expect(ClientsReport.parser)
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    @browser_cache(1800)
    def get(self, server=None):
        """Returns a global report about all the clients of a given server

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "backups": [
                {
                  "name": "client1",
                  "number": 15
                },
                {
                  "name": "client2",
                  "number": 1
                }
              ],
              "clients": [
                {
                  "name": "client1",
                  "stats": {
                    "total": 296377,
                    "totsize": 57055793698,
                    "windows": "unknown"
                  }
                },
                {
                  "name": "client2",
                  "stats": {
                    "total": 3117,
                    "totsize": 5345361,
                    "windows": "true"
                  }
                }
              ]
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :returns: The *JSON* described above
        """
        server = server or self.parser.parse_args()['serverName']
        self._check_acl(server)
        res = cache.cache.get('all_clients_reports')
        if res is None:
            return self._get_clients_reports(server=server)

        return self._get_clients_reports(res, server)


@ns.route('/browseall/<name>/<int:backup>',
          '/<server>/browsall/<name>/<int:backup>',
          endpoint='async_client_tree_all')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in' +
                  ' multi-agent mode',
        'name': 'Client name',
        'backup': 'Backup number',
    },
)
class AsyncClientTreeAll(Resource):
    """The :class:`burpui.api.async.AsyncClientTreeAll` resource allows you to
    retrieve a list of all the files in a given backup through the celery
    worker.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument(
        'serverName',
        help='Which server to collect data from when in multi-agent mode'
    )

    @ns.expect(parser)
    @ns.doc(
        responses={
            202: 'Accepted',
            405: 'Method not allowed',
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def post(self, server=None, name=None, backup=None):
        """Launch the tasks that will gather all nodes of a given backup

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
        server = server or args.get('serverName')

        if not bui.client.get_attr('batch_list_supported', False, server):
            self.abort(
                405,
                'Sorry, the requested backend does not support this method'
            )

        # Manage ACL
        if not current_user.is_anonymous and \
                not current_user.acl.is_admin() and \
                not current_user.acl.is_client_allowed(name, server):
            self.abort(403, 'Sorry, you are not allowed to view this client')

        task = load_all_tree.apply_async(
            args=[
                name,
                backup,
                server,
                current_user.name
            ]
        )
        return {'id': task.id, 'name': 'load_all_tree'}, 202


@ns.route('/get-browse/<task_id>',
          '/<server>/get-browse/<task_id>',
          endpoint='async_do_browse_all')
@ns.doc(
    params={
        'task_id': 'The task ID to process',
    }
)
class AsyncDoBrowseAll(Resource):
    """The :class:`burpui.api.async.AsyncDoBrowseAll` resource allows you to
    retrieve the tree generated by the given task.

    This resource is part of the :mod:`burpui.api.async` module.
    """

    @ns.marshal_list_with(node_fields, code=200, description='Success')
    @ns.doc(
        responses={
            400: 'Incomplete task',
            403: 'Insufficient permissions',
            500: 'Task failed',
        },
    )
    def get(self, task_id, server=None):
        """Returns the generated archive"""
        task = load_all_tree.AsyncResult(task_id)
        if task.state != 'SUCCESS':
            if task.state == 'FAILURE':
                self.abort(
                    500,
                    'Unsuccessful task: {}'.format(task.result.get('error'))
                )
            self.abort(400, 'Task not processed yet: {}'.format(task.state))

        user = task.result.get('user')
        dst_server = task.result.get('server')
        resp = task.result.get('tree')

        if current_user.name != user or (dst_server and dst_server != server):
            self.abort(403, 'Unauthorized access')

        task.revoke()

        return resp
