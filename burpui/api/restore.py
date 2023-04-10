# -*- coding: utf8 -*-
"""
.. module:: burpui.api.restore
    :platform: Unix
    :synopsis: Burp-UI restore api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import select
import struct
from time import gmtime, strftime, time
from zlib import adler32

from flask import Response, after_this_request, current_app, make_response, send_file
from flask_login import current_user
from flask_restx import inputs
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException

from ..engines.server import BUIServer  # noqa
from ..exceptions import BUIserverException
from . import api
from .custom import Resource, fields

bui = current_app  # type: BUIServer
ns = api.namespace("restore", "Restore methods")


@ns.route(
    "/archive/<name>/<int:backup>",
    "/<server>/archive/<name>/<int:backup>",
    endpoint="restore",
)
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
        "name": "Client name",
        "backup": "Backup number",
    },
)
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

    parser = ns.parser()
    parser.add_argument(
        "pass", help="Password to use for encrypted backups", nullable=True
    )
    parser.add_argument(
        "format",
        required=False,
        help="Returning archive format",
        choices=("zip", "tar.gz", "tar.bz2"),
        default="zip",
        nullable=True,
    )
    parser.add_argument(
        "strip",
        type=int,
        help="Number of elements to strip in the path",
        default=0,
        nullable=True,
    )
    parser.add_argument(
        "list",
        required=True,
        help="List of files/directories to restore",
        nullable=False,
    )
    # FIXME: the example json seems interpreted during the raise of the exception
    # parser.add_argument('list', required=True, help='List of files/directories to restore (example: \'{"restore":[{"folder":true,"key":"/etc"}]}\')', nullable=False)

    @ns.expect(parser, validate=True)
    @ns.doc(
        responses={
            200: "Success",
            400: "Missing parameter",
            403: "Insufficient permissions",
            500: "Internal failure",
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
        lst = args["list"]
        stp = args["strip"]
        fmt = args["format"] or "zip"
        pwd = args["pass"]
        args_log = args.copy()
        # don't leak secrets in logs
        del args_log["pass"]
        bui.audit.logger.info(
            f"requested restoration of backup n°{backup} for {name} with {args_log}",
            server=server,
        )
        resp = None
        # Check params
        if not lst or not name or not backup:
            self.abort(400, "missing arguments")
        # Manage ACL
        if (
            not current_user.is_anonymous
            and not current_user.acl.is_admin()
            and not current_user.acl.is_client_rw(name, server)
        ):
            self.abort(
                403, "You are not allowed to perform a restoration for this client"
            )
        if server:
            filename = "restoration_%d_%s_on_%s_at_%s.%s" % (
                backup,
                name,
                server,
                strftime("%Y-%m-%d_%H_%M_%S", gmtime()),
                fmt,
            )
        else:
            filename = "restoration_%d_%s_at_%s.%s" % (
                backup,
                name,
                strftime("%Y-%m-%d_%H_%M_%S", gmtime()),
                fmt,
            )

        archive, err = bui.client.restore_files(
            name, backup, lst, stp, fmt, pwd, server
        )
        if not archive:
            bui.audit.logger.error(f"restoration failed: {err}")
            if err:
                if (
                    not current_user.is_anonymous
                    and not current_user.acl.is_admin()
                    or bui.demo
                ) and err != "encrypted":
                    err = (
                        "An error occurred while performing the "
                        "restoration. Please contact your administrator "
                        "for further details"
                    )
                return make_response(err, 500)
            return make_response(err, 500)

        if not server:
            try:
                # Trick to delete the file while sending it to the client.
                # First, we open the file in reading mode so that a file handler
                # is open on the file. Then we delete it as soon as the request
                # ended. Because the fh is open, the file will be actually removed
                # when the transfer is done and the send_file method has closed
                # the fh. Only tested on Linux systems.
                fh = open(archive, "rb")

                @after_this_request
                def remove_file(response):
                    """Callback function to run after the client has handled
                    the request to remove temporary files.
                    """
                    import os

                    os.remove(archive)
                    return response

                resp = send_file(
                    fh,
                    as_attachment=True,
                    download_name=filename,
                    mimetype="application/zip",
                )
                resp.set_cookie("fileDownload", "true")
            except Exception as exp:
                bui.client.logger.error(str(exp))
                self.abort(500, str(exp))
        else:
            # Multi-agent mode
            try:
                socket = bui.client.get_file(archive, server)
                if not socket:
                    self.abort(500)

                lengthbuf = socket.recv(8)
                (length,) = struct.unpack("!Q", lengthbuf)

                bui.client.logger.debug(
                    "Need to get {} Bytes : {}".format(length, socket)
                )

                def stream_file(sock, size):
                    """The restoration took place on another server so we need
                    to stream the file that is not present on the current
                    machine.
                    """
                    bsize = 1024
                    received = 0
                    if size < bsize:
                        bsize = size
                    while received < size:
                        buf = b""
                        read, _, _ = select.select([sock], [], [], 5)
                        if not read:
                            raise Exception("Socket timed-out")
                        buf += sock.recv(bsize)
                        if not buf:
                            continue
                        received += len(buf)
                        self.logger.debug("{}/{}".format(received, size))
                        yield buf
                    sock.sendall(struct.pack("!Q", 2))
                    sock.sendall(b"RE")
                    sock.close()

                headers = Headers()
                headers.add("Content-Disposition", "attachment", filename=filename)
                headers["Content-Length"] = length

                resp = Response(
                    stream_file(socket, length),
                    mimetype="application/zip",
                    headers=headers,
                    direct_passthrough=True,
                )
                resp.set_cookie("fileDownload", "true")
                resp.set_etag(
                    "flask-%s-%s-%s"
                    % (time(), length, adler32(filename.encode("utf-8")) & 0xFFFFFFFF)
                )
            except HTTPException as exp:
                raise exp
            except Exception as exp:
                bui.client.logger.error(str(exp))
                self.abort(500, str(exp))
        bui.audit.logger.info(f"sending file {archive}")
        return resp


@ns.route(
    "/server-restore/<name>",
    "/<server>/server-restore/<name>",
    methods=["GET", "DELETE"],
    endpoint="is_server_restore",
)
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
        "name": "Client name",
    },
)
class ServerRestore(Resource):
    """The :class:`burpui.api.restore.ServerRestore` resource allows you to
    monitor or cancel a server-initiated restoration.

    This resource is part of the :mod:`burpui.api.restore` module.
    """

    list_fields = ns.model(
        "ListRestoreFiles",
        {
            "key": fields.String(
                required=True, description="Path to a file/directory to restore"
            ),
            "folder": fields.Boolean(
                required=True, description="Is the path pointed to a directory"
            ),
        },
    )
    restoration_fields = ns.model(
        "EditRestoration",
        {
            "backup": fields.Integer(
                required=True, description="Backup number to restore"
            ),
            "strip": fields.Integer(
                required=False,
                description="Number of leading path to strip while restoring",
            ),
            "prefix": fields.String(
                required=False,
                description="Where to restore files",
                attribute="restoreprefix",
            ),
            "force": fields.Boolean(
                required=False,
                description="Whether to replace files that are already present",
                default=False,
                attribute="overwrite",
            ),
            "to": fields.String(
                required=False,
                description="What client the restoration is intended to",
            ),
            "orig_client": fields.String(
                required=False,
                description="Name of the client to restore from when different"
                + " from the current one",
            ),
            "found": fields.Boolean(
                required=False, description="Did we found a restore file", default=False
            ),
            "list": fields.Nested(
                list_fields, as_list=True, description="List of path to restore"
            ),
        },
    )

    @ns.marshal_with(restoration_fields, code=200, description="Success")
    @ns.doc(
        responses={
            400: "Missing parameter",
            403: "Insufficient permissions",
            500: "Internal failure",
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
            self.abort(400, "Missing options")
        # Manage ACL
        if (
            not current_user.is_anonymous
            and not current_user.acl.is_admin()
            and not current_user.acl.is_client_rw(name, server)
        ):
            self.abort(403, "You are not allowed to edit a restoration for this client")
        try:
            return bui.client.is_server_restore(name, server)
        except BUIserverException as e:
            self.abort(500, str(e))

    @ns.doc(
        responses={
            200: "Success",
            400: "Missing parameter",
            403: "Insufficient permissions",
            500: "Internal failure",
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
        bui.audit.logger.info(
            f"attempt to remove 'restore' file for {name}", server=server
        )
        if not name:
            self.abort(400, "Missing options")
        # Manage ACL
        if (
            not current_user.is_anonymous
            and not current_user.acl.is_admin()
            and not current_user.acl.is_client_rw(name, server)
        ):
            self.abort(
                403, "You are not allowed to cancel a restoration for this client"
            )
        try:
            return bui.client.cancel_server_restore(name, server)
        except BUIserverException as e:
            self.abort(500, str(e))


@ns.route(
    "/server-restore/<name>/<int:backup>",
    "/<server>/server-restore/<name>/<int:backup>",
    methods=["PUT"],
    endpoint="server_restore",
)
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
        "name": "Client name",
        "backup": "Backup number",
    },
)
class DoServerRestore(Resource):
    """The :class:`burpui.api.restore.DoServerRestore` resource allows you to
    schedule a server-initiated restoration.

    The following parameters are supported:
    - ``list-sc``: list of files/directories to restore
    - ``strip-sc``: number of elements to strip in the path
    - ``prefix-sc``: prefix to the restore path
    - ``force-sc``: whether to overwrite existing files
    - ``restoreto-sc``: restore files on an other client
    """

    parser = ns.parser()
    parser.add_argument(
        "list-sc",
        required=True,
        help="List of files/directories to restore",
        nullable=False,
    )
    parser.add_argument(
        "strip-sc",
        type=int,
        help="Number of elements to strip in the path",
        default=0,
        nullable=True,
    )
    parser.add_argument("prefix-sc", help="Prefix to the restore path", nullable=True)
    parser.add_argument(
        "force-sc",
        type=inputs.boolean,
        help="Whether to overwrite existing files",
        default=False,
        nullable=True,
    )
    parser.add_argument(
        "restoreto-sc", help="Restore files on an other client", nullable=True
    )

    @api.disabled_on_demo()
    @ns.expect(parser)
    @ns.doc(
        responses={
            201: "Success",
            400: "Missing parameter",
            403: "Insufficient permissions",
            428: "Configuration forbid this request",
            500: "Internal failure",
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
        files_list = args["list-sc"]
        strip = args["strip-sc"]
        prefix = args["prefix-sc"]
        force = args["force-sc"]
        to = args["restoreto-sc"] or name
        json = []

        if (
            not bui.client.get_parser(agent=server).param(
                "server_can_restore", "client_conf"
            )
            and bui.noserverrestore
        ):
            self.abort(
                428,
                "Sorry this method is not available with the current " "configuration",
            )

        # Check params
        if not files_list or not name or not backup:
            self.abort(400, "Missing options")
        # Manage ACL
        if (
            not current_user.is_anonymous
            and not current_user.acl.is_admin()
            and not current_user.acl.is_client_rw(to, server)
            and not current_user.acl.is_client_allowed(to, server)
        ):
            self.abort(
                403, "You are not allowed to perform a restoration for this client"
            )
        try:
            if to == name:
                to = None
            json = bui.client.server_restore(
                name, backup, files_list, strip, force, prefix, to, server
            )
            bui.audit.logger.info(
                f"requested server-initiated restoration from {name} to {to}",
                server=server,
            )
            return json, 201
        except BUIserverException as e:
            self.abort(500, str(e))
