# -*- coding: utf8 -*-
from zlib import adler32
from time import gmtime, strftime, time

from burpui import app, bui, login_manager
from burpui.api import api
from flask.ext.restful import reqparse, Resource, abort
from flask.ext.login import current_user, login_required
from flask import jsonify, send_file, make_response, after_this_request

@api.resource('/api/restore/<name>/<int:backup>', '/api/<server>/restore/<name>/<int:backup>')
class Restore(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('list', type=str)
        self.parser.add_argument('strip', type=str)
        self.parser.add_argument('format', type=str)
        self.parser.add_argument('pass', type=str)

    @login_required
    def post(self, server=None, name=None, backup=None):
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
        if bui.acl_handler and \
                (not bui.acl_handler.get_acl().is_client_allowed(current_user.name, name, server) \
                and not bui.acl_handler.get_acl().is_admin(current_user.name)):
            abort(403)
        if server:
            filename = 'restoration_%d_%s_on_%s_at_%s.%s' % (backup, name, server, strftime("%Y-%m-%d_%H_%M_%S", gmtime()), f)
        else:
            filename = 'restoration_%d_%s_at_%s.%s' % (backup, name, strftime("%Y-%m-%d_%H_%M_%S", gmtime()), f)
        if not server:
            archive, err = bui.cli.restore_files(name, backup, l, s, f, p)
            if not archive:
                if err:
                    return make_response(err, 500)
                abort(500)
            try:
                fh = open(archive, 'r')
                @after_this_request
                def remove_file(response):
                    import os
                    os.remove(archive)
                    return response
                resp = send_file(fh, as_attachment=True, attachment_filename=filename, mimetype='application/zip')
                resp.set_cookie('fileDownload', 'true')
            except Exception, e:
                app.logger.error(str(e))
                abort(500)
        else:
            socket = None
            try:
                socket, length, err = bui.cli.restore_files(name, backup, l, s, f, p, server)
                app.logger.debug('Need to get %d Bytes : %s', length, socket)

                if err:
                    app.logger.debug('Something went wrong: %s', err)
                    socket.close()
                    return make_response(err, 500)

                def stream_file(sock, l):
                    bsize = 1024
                    received = 0
                    if l < bsize:
                        bsize = l
                    while received < l:
                        buf = b''
                        r, _, _ = select.select([sock], [], [], 5)
                        if not r:
                            raise Exception ('Socket timed-out')
                        buf += sock.recv(bsize)
                        if not buf:
                            continue
                        received += len(buf)
                        app.logger.debug('%d/%d', received, l)
                        yield buf
                    sock.close()

                headers = Headers()
                headers.add('Content-Disposition', 'attachment', filename=filename)
                headers['Content-Length'] = length

                resp = Response(stream_file(socket, length), mimetype='application/zip',
                                headers=headers, direct_passthrough=True)
                resp.set_cookie('fileDownload', 'true')
                resp.set_etag('flask-%s-%s-%s' % (
                        time(),
                        length,
                        adler32(filename.encode('utf-8')) & 0xffffffff))
            except HTTPException, e:
                raise e
            except Exception, e:
                app.logger.error(str(e))
                abort(500)
        return resp
