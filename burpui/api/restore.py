# -*- coding: utf8 -*-
"""
.. module:: restore
    :platform: Unix
    :synopsis: Burp-UI restore api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
import select

from zlib import adler32
from time import gmtime, strftime, time

from burpui.api import api
from flask.ext.restful import reqparse, Resource, abort
from flask.ext.login import current_user, login_required
from flask import Response, send_file, make_response, after_this_request
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException


@api.resource('/api/restore/<name>/<int:backup>',
              '/api/<server>/restore/<name>/<int:backup>',
              endpoint='api.restore')
class Restore(Resource):
    """
    The :class:`burpui.api.restore.Restore` resource allows you to
    perform a file restoration.

    This resource is part of the :mod:`burpui.api.restore` module.

    The following ``GET`` parameters are supported:
    - ``list``: list of files/directories to restore
    - ``strip``: number of elements to strip in the path
    - ``format``: returning archive format
    - ``pass``: password to use for encrypted backups
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('list', type=str)
        self.parser.add_argument('strip', type=str)
        self.parser.add_argument('format', type=str)
        self.parser.add_argument('pass', type=str)

    @login_required
    def post(self, server=None, name=None, backup=None):
        """
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
        f = args['format']
        p = args['pass']
        resp = None
        if not f:
            f = 'zip'
        # Check params
        if not l or not name or not backup:
            abort(500)
        # Manage ACL
        if (api.bui.acl and
                (not api.bui.acl.is_client_allowed(current_user.name,
                                                   name,
                                                   server) and not
                 api.bui.acl.is_admin(current_user.name))):
            abort(403)
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
                abort(500)
            try:
                # Trick to delete the file while sending it to the client.
                # First, we open the file in reading mode so that a file handler
                # is open on the file. Then we delete it as soon as the request
                # ended. Because the fh is open, the file will be actually removed
                # when the transfert is done and the send_file method has closed
                # the fh.
                fh = open(archive, 'r')

                @after_this_request
                def remove_file(response):
                    import os
                    os.remove(archive)
                    return response
                resp = send_file(fh,
                                 as_attachment=True,
                                 attachment_filename=filename,
                                 mimetype='application/zip')
                resp.set_cookie('fileDownload', 'true')
            except Exception as e:
                api.app.logger.error(str(e))
                abort(500)
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
                api.app.logger.debug('Need to get %d Bytes : %s', length, socket)

                if err:
                    api.app.logger.debug('Something went wrong: %s', err)
                    socket.close()
                    return make_response(err, 500)

                # The restoration took place on another server so we need to stream
                # the file that is not present on the current machine.
                def stream_file(sock, l):
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
                        api.app.logger.debug('%d/%d', received, l)
                        yield buf
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
                api.app.logger.error(str(e))
                abort(500)
        return resp
