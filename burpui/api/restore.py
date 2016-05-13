# -*- coding: utf8 -*-
"""
.. module:: burpui.api.restore
    :platform: Unix
    :synopsis: Burp-UI restore api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import select
import struct

from zlib import adler32
from time import gmtime, strftime, time

# This is a submodule we can also use "from ..api import api"
from . import api
from .custom import fields, Resource
from .custom.inputs import boolean
from ..exceptions import BUIserverException
from flask import Response, send_file, make_response, after_this_request
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException

ns = api.namespace('restore', 'Restore methods')


@ns.route('/archive/<name>/<int:backup>',
          '/<server>/archive/<name>/<int:backup>',
          endpoint='restore')
class Restore(Resource):
    """The :class:`burpui.api.restore.Restore` resource allows you to
    perform a file restoration.

    This resource is part of the :mod:`burpui.api.restore` module.

    The following parameters are supported:
    - ``list``: list of files/directories to restore
    - ``strip``: number of elements to strip in the path
    - ``format``: returning archive format
    - ``pass``: password to use for encrypted backups
    """
    parser = api.parser()
    parser.add_argument('pass', help='Password to use for encrypted backups', location=('form', 'json'), nullable=True)
    parser.add_argument('format', required=False, help='Returning archive format', location=('form', 'json'), choices=('zip', 'tar.gz', 'tar.bz2'), default='zip', nullable=True)
    parser.add_argument('strip', type=int, help='Number of elements to strip in the path', default=0, location=('form', 'json'), nullable=True)
    parser.add_argument('list', required=True, help='List of files/directories to restore', location=('form', 'json'), nullable=False)
    # FIXME: the example json seems interpreted during the raise of the exception
    # parser.add_argument('list', required=True, help='List of files/directories to restore (example: \'{"restore":[{"folder":true,"key":"/etc"}]}\')', location=('form', 'json'), nullable=False)

    @ns.expect(parser, validate=True)
    @ns.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
            'name': 'Client name',
            'backup': 'Backup number',
        },
        responses={
            200: 'Success',
            400: 'Missing parameter',
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def post(self, server=None, name=None, backup=None):
        """Performs an online restoration

        **POST** method provided by the webservice.
        This method returns a :mod:`flask.Response` object.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :param backup: The backup we are working on
        :type backup: int

        :returns: A :mod:`flask.Response` object representing an archive of the restored files
        """
        args = self.parser.parse_args()
        l = args['list']
        s = args['strip']
        f = args['format'] or 'zip'
        p = args['pass']
        resp = None
        # Check params
        if not l or not name or not backup:
            self.abort(400, 'missing arguments')
        # Manage ACL
        if (api.bui.acl and
                (not api.bui.acl.is_client_allowed(self.username,
                                                   name,
                                                   server) and not
                 self.is_admin)):
            self.abort(403, 'You are not allowed to perform a restoration for this client')
        if server:
            filename = 'restoration_%d_%s_on_%s_at_%s.%s' % (
                backup,
                name,
                server,
                strftime("%Y-%m-%d_%H_%M_%S", gmtime()),
                f)
        else:
            filename = 'restoration_%d_%s_at_%s.%s' % (
                backup,
                name,
                strftime("%Y-%m-%d_%H_%M_%S", gmtime()),
                f)
        if not server:
            # Standalone mode, we can just return the file unless there were errors
            archive, err = api.bui.cli.restore_files(name, backup, l, s, f, p)
            if not archive:
                if err:
                    return make_response(err, 500)
                self.abort(500)
            try:
                # Trick to delete the file while sending it to the client.
                # First, we open the file in reading mode so that a file handler
                # is open on the file. Then we delete it as soon as the request
                # ended. Because the fh is open, the file will be actually removed
                # when the transfer is done and the send_file method has closed
                # the fh. Only tested on Linux systems.
                fh = open(archive, 'r')

                @after_this_request
                def remove_file(response):
                    """Callback function to run after the client has handled
                    the request to remove temporary files.
                    """
                    import os
                    os.remove(archive)
                    return response

                resp = send_file(fh,
                                 as_attachment=True,
                                 attachment_filename=filename,
                                 mimetype='application/zip')
                resp.set_cookie('fileDownload', 'true')
            except Exception as e:
                api.bui.cli.logger.error(str(e))
                self.abort(500, str(e))
        else:
            # Multi-agent mode
            socket = None
            try:
                socket, length, err = api.bui.cli.restore_files(name,
                                                                backup,
                                                                l,
                                                                s,
                                                                f,
                                                                p,
                                                                server)
                api.bui.cli.logger.debug('Need to get {} Bytes : {}'.format(length, socket))

                if err:
                    api.bui.cli.logger.debug('Something went wrong: {}'.format(err))
                    socket.sendall(struct.pack('!Q', 2))
                    socket.sendall(b'RE')
                    socket.close()
                    return make_response(err, 500)

                def stream_file(sock, l):
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
                            raise Exception('Socket timed-out')
                        buf += sock.recv(bsize)
                        if not buf:
                            continue
                        received += len(buf)
                        api.bui.cli.logger.debug('{}/{}'.format(received, l))
                        yield buf
                    sock.sendall(struct.pack('!Q', 2))
                    sock.sendall(b'RE')
                    sock.close()

                headers = Headers()
                headers.add('Content-Disposition',
                            'attachment',
                            filename=filename)
                headers['Content-Length'] = length

                resp = Response(stream_file(socket, length),
                                mimetype='application/zip',
                                headers=headers,
                                direct_passthrough=True)
                resp.set_cookie('fileDownload', 'true')
                resp.set_etag('flask-%s-%s-%s' % (
                    time(),
                    length,
                    adler32(filename.encode('utf-8')) & 0xffffffff))
            except HTTPException as e:
                raise e
            except Exception as e:
                api.bui.cli.logger.error(str(e))
                self.abort(500, str(e))
        return resp


@ns.route('/server-restore/<name>',
          '/<server>/server-restore/<name>',
          methods=['GET', 'DELETE'],
          endpoint='is_server_restore')
@ns.route('/server-restore/<name>/<int:backup>',
          '/<server>/server-restore/<name>/<int:backup>',
          methods=['PUT'],
          endpoint='server_restore')
class ServerRestore(Resource):
    """The :class:`burpui.api.restore.ServerRestore` resource allows you to
    prepare a file restoration.

    This resource is part of the :mod:`burpui.api.restore` module.

    The following parameters are supported:
    - ``list-sc``: list of files/directories to restore
    - ``strip-sc``: number of elements to strip in the path
    - ``prefix-sc``: prefix to the restore path
    - ``force-sc``: whether to overwrite existing files
    - ``restoreto-sc``: restore files on an other client
    """
    parser = api.parser()
    parser.add_argument('list-sc', required=True, help='List of files/directories to restore', location='form', nullable=False)
    parser.add_argument('strip-sc', type=int, help='Number of elements to strip in the path', default=0, location='form', nullable=True)
    parser.add_argument('prefix-sc', help='Prefix to the restore path', location='form', nullable=True)
    parser.add_argument('force-sc', type=boolean, help='Whether to overwrite existing files', default=False, location='form', nullable=True)
    parser.add_argument('restoreto-sc', help='Restore files on an other client', location='form', nullable=True)

    list_fields = api.model('ListRestoreFiles', {
        'key': fields.String(
            required=True,
            description='Path to a file/directory to restore'
        ),
        'folder': fields.Boolean(
            required=True,
            description='Is the path pointed to a directory'
        )
    })
    restoration_fields = api.model('EditRestoration', {
        'backup': fields.Integer(
            required=True,
            description='Backup number to restore'
        ),
        'strip': fields.Integer(
            required=False,
            description='Number of leading path to strip while restoring'
        ),
        'prefix': fields.String(
            required=False,
            description='Where to restore files',
            attribute='restoreprefix'
        ),
        'force': fields.Boolean(
            required=False,
            description='Whether to replace files that are already present',
            default=False,
            attribute='overwrite'
        ),
        'to': fields.String(
            required=False,
            description='What client the restoration is intended to',
        ),
        'orig_client': fields.String(
            required=False,
            description='Name of the client to restore from when different' +
                        ' from the current one'
        ),
        'found': fields.Boolean(
            required=False,
            description='Did we found a restore file',
            default=False
        ),
        'list': fields.Nested(
            list_fields,
            as_list=True,
            description='List of path to restore'
        )
    })

    @ns.marshal_with(restoration_fields, code=200, description='Success')
    @ns.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
            'name': 'Client name',
        },
        responses={
            400: 'Missing parameter',
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def get(self, server=None, name=None):
        """Reads the content of the 'restore' file if present

        **GET** method provided by the webservice.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :returns: The content of the restore file
        """
        if not name:
            self.abort(400, 'Missing options')
        # Manage ACL
        if (api.bui.acl and
                (not api.bui.acl.is_client_allowed(self.username,
                                                   name,
                                                   server) and not
                 self.is_admin)):
            self.abort(403, 'You are not allowed to edit a restoration for this client')
        try:
            return api.bui.cli.is_server_restore(name, server)
        except BUIserverException as e:
            self.abort(500, str(e))

    @ns.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
            'name': 'Client name',
        },
        responses={
            200: 'Success',
            400: 'Missing parameter',
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def delete(self, server=None, name=None):
        """Remove the 'restore' file if present

        **DELETE** method provided by the webservice.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :returns: Status message (success or failure)
        """
        if not name:
            self.abort(400, 'Missing options')
        # Manage ACL
        if (api.bui.acl and
                (not api.bui.acl.is_client_allowed(self.username,
                                                   name,
                                                   server) and not
                 self.is_admin)):
            self.abort(403, 'You are not allowed to cancel a restoration for this client')
        try:
            return api.bui.cli.cancel_server_restore(name, server)
        except BUIserverException as e:
            self.abort(500, str(e))

    @ns.expect(parser)
    @ns.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
            'name': 'Client name',
            'backup': 'Backup number',
        },
        responses={
            201: 'Success',
            400: 'Missing parameter',
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def put(self, server=None, name=None, backup=None):
        """Schedule a server-initiated restoration

        **PUT** method provided by the webservice.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :param backup: The backup we are working on
        :type backup: int

        :returns: Status message (success or failure)
        """
        args = self.parser.parse_args()
        files_list = args['list-sc']
        strip = args['strip-sc']
        prefix = args['prefix-sc']
        force = args['force-sc']
        to = args['restoreto-sc']
        json = []
        # Check params
        if not files_list or not name or not backup:
            self.abort(400, 'Missing options')
        # Manage ACL
        if (api.bui.acl and
                (not api.bui.acl.is_client_allowed(self.username,
                                                   name,
                                                   server) and not
                 self.is_admin and
                 (to and not
                  api.bui.acl.is_client_allowed(self.username,
                                                to,
                                                server)))):
            self.abort(
                403,
                'You are not allowed to perform a restoration for this client'
            )
        try:
            json = api.bui.cli.server_restore(
                name,
                backup,
                files_list,
                strip,
                force,
                prefix,
                to,
                server
            )
            return json, 201
        except BUIserverException as e:
            self.abort(500, str(e))
