# -*- coding: utf8 -*-
"""
.. module:: burpui.api.settings
    :platform: Unix
    :synopsis: Burp-UI settings api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import json

from flask import (
    current_app,
    g,
    jsonify,
    render_template_string,
    request,
    session,
    url_for,
)
from flask_babel import gettext as _
from flask_babel import refresh
from flask_login import current_user
from flask_restx import inputs
from jinja2 import Environment, meta

from .._compat import unquote
from ..datastructures import ImmutableMultiDict, MultiDict
from ..engines.server import BUIServer  # noqa
from ..ext.cache import cache
from ..utils import NOTIF_INFO
from . import api
from .custom import Resource

TEMPLATE_EXCLUDES = ["client", "agent"]

bui = current_app  # type: BUIServer
ns = api.namespace("settings", "Settings methods")


@ns.route(
    "/server-config",
    "/<server>/server-config",
    "/server-config/<path:conf>",
    "/<server>/server-config/<path:conf>",
    endpoint="server_settings",
)
@ns.doc(
    params={
        "conf": "Path of the configuration file",
        "server": "Which server to collect data from when in multi-agent mode",
    },
)
class ServerSettings(Resource):
    """The :class:`burpui.api.settings.ServerSettings` resource allows you to
    read and write the server's configuration.

    This resource is part of the :mod:`burpui.api.settings` module.
    """

    @api.disabled_on_demo()
    @api.acl_admin_required(
        message="Sorry, you don't have rights to access the setting panel"
    )
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def post(self, conf=None, server=None):
        """Saves the server configuration"""
        noti = bui.client.store_conf_srv(request.form, conf, server)
        bui.audit.logger.info(
            f"updated burp-server configuration ({conf})", server=server
        )
        return {"notif": noti}, 200

    @api.disabled_on_demo()
    @api.acl_admin_required(
        message="Sorry, you don't have rights to access the setting panel"
    )
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def delete(self, conf=None, server=None):
        """Deletes a configuration file"""
        try:
            conf = unquote(conf)
        except:
            pass
        parser = bui.client.get_parser(agent=server)
        bui.audit.logger.info(f"requested removal of {conf}", server=server)
        return parser.remove_conf(conf)

    @api.acl_admin_required(
        message="Sorry, you don't have rights to access the setting panel"
    )
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def get(self, conf=None, server=None):
        """Reads the server configuration

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "boolean": [
                "daemon",
                "fork",
                "..."
              ],
              "defaults": {
                "address": "",
                "autoupgrade_dir": "",
                "ca_burp_ca": "",
                "ca_conf": "",
                "ca_name": "",
                "ca_server_name": "",
                "client_can_delete": true,
                "...": "..."
              },
              "integer": [
                "port",
                "status_port",
                "..."
              ],
              "multi": [
                "keep",
                "restore_client",
                "..."
              ],
              "placeholders": {
                "autoupgrade_dir": "path",
                "ca_burp_ca": "path",
                "ca_conf": "path",
                "ca_name": "name",
                "ca_server_name": "name",
                "client_can_delete": "0|1",
                "...": "..."
              },
              "results": {
                "boolean": [
                  {
                    "name": "hardlinked_archive",
                    "value": false,
                    "reset": false
                  },
                  {
                    "name": "syslog",
                    "value": true,
                    "reset": false
                  },
                  { "...": "..." }
                ],
                "clients": [
                  {
                    "name": "testclient",
                    "value": "/etc/burp/clientconfdir/testclient"
                  }
                ],
                "common": [
                  {
                    "name": "mode",
                    "value": "server",
                    "reset": false
                  },
                  {
                    "name": "directory",
                    "value": "/var/spool/burp",
                    "reset": false
                  },
                  { "...": "..." }
                ],
                "includes": [],
                "includes_ext": [],
                "integer": [
                  {
                    "name": "port",
                    "value": 4971,
                    "reset": false
                  },
                  {
                    "name": "status_port",
                    "value": 4972,
                    "reset": false
                  },
                  { "...": "..." }
                ],
                "multi": [
                  {
                    "name": "keep",
                    "value": [
                      "7",
                      "4"
                    ],
                    "reset": [
                      false,
                      true
                    ]
                  },
                  { "...": "..." }
                ],
                "hierarchy": [
                  {
                    "children": [
                      {
                        "children": [],
                        "dir": "/tmp/burp/conf.d",
                        "full": "/tmp/burp/conf.d/empty.conf",
                        "name": "empty.conf",
                        "parent": "/tmp/burp/burp-server.conf"
                      },
                      {
                        "children": [],
                        "dir": "/tmp/burp/conf.d",
                        "full": "/tmp/burp/conf.d/ipv4.conf",
                        "name": "ipv4.conf",
                        "parent": "/tmp/burp/burp-server.conf"
                      }
                    ],
                    "dir": "/tmp/burp",
                    "full": "/tmp/burp/burp-server.conf",
                    "name": "burp-server.conf",
                    "parent": null
                  }
                ]
              },
              "server_doc": {
                "address": "Defines the main TCP address...",
                "...": "..."
              },
              "string": [
                "mode",
                "address",
                "..."
              ],
              "suggest": {
                "compression": [
                  "gzip1",
                  "gzip2",
                  "gzip3",
                  "gzip4",
                  "gzip5",
                  "gzip6",
                  "gzip7",
                  "gzip8",
                  "gzip9"
                ],
                "mode": [
                  "client",
                  "server"
                ],
                "...": [
                  "..."
                ]
              }
            }


        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above.
        """
        try:
            conf = unquote(conf)
        except:
            pass
        res = bui.client.read_conf_srv(conf, server)
        refresh()
        # Translate the doc and placeholder API side
        cache_keys = {
            "doc": "_doc_parser_{}-{}".format(server, g.locale),
            "placeholders": "_placeholders_parser_{}-{}".format(server, g.locale),
            "boolean_srv": "_boolean_srv_parser_{}".format(server),
            "string_srv": "_string_srv_parser_{}".format(server),
            "integer_srv": "_integer_srv_parser_{}".format(server),
            "multi_srv": "_multi_srv_parser_{}".format(server),
            "values": "_suggest_parser_{}".format(server),
            "defaults": "_defaults_parser_{}".format(server),
            "advanced_type": "_advanced_parser_{}".format(server),
            "pair_associations": "_pair_associations_parser_{}".format(server),
        }
        cache_results = {}
        for name, key in cache_keys.items():
            if not cache.cache.has(key):
                if name in ["doc", "placeholders"]:
                    _tmp = bui.client.get_parser_attr(name, server).copy()
                    _tmp2 = {}
                    for k, v in _tmp.items():
                        _tmp2[k] = _(v)
                    cache_results[name] = _tmp2
                else:
                    cache_results[name] = bui.client.get_parser_attr(name, server)
                cache.cache.set(key, cache_results[name], 3600)
            else:
                cache_results[name] = cache.cache.get(key)

        return jsonify(
            results=res,
            boolean=cache_results["boolean_srv"],
            string=cache_results["string_srv"],
            integer=cache_results["integer_srv"],
            multi=cache_results["multi_srv"],
            pair=cache_results["pair_associations"],
            advanced=cache_results["advanced_type"],
            server_doc=cache_results["doc"],
            suggest=cache_results["values"],
            placeholders=cache_results["placeholders"],
            defaults=cache_results["defaults"],
        )


@ns.route("/clients", "/<server>/clients", endpoint="clients_list")
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
    },
)
class ClientsList(Resource):
    @api.acl_admin_or_moderator_required(
        message="Sorry, you don't have rights to access the setting panel"
    )
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def get(self, server=None):
        """Returns a list of clients"""
        parser = bui.client.get_parser(agent=server)
        res = parser.list_clients()
        return jsonify(result=res)


@ns.route(
    "/static-templates", "/<server>/static-templates", endpoint="static_templates_list"
)
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
    },
)
class StaticTemplatesList(Resource):
    @api.acl_admin_or_moderator_required(
        message="Sorry, you don't have rights to access the setting panel"
    )
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def get(self, server=None):
        """Returns a list of clients"""
        parser = bui.client.get_parser(agent=server)
        res = parser.list_static_templates()
        env = Environment()
        for obj in res:
            ast = env.parse(obj["content"])
            obj["variables"] = [
                x
                for x in meta.find_undeclared_variables(ast)
                if x not in TEMPLATE_EXCLUDES
            ]
        return jsonify(result=res)


@ns.route(
    "/static-template",
    "/<server>/static-template",
    endpoint="new_static_template",
    methods=["PUT"],
)
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
    },
)
class NewStaticTemplateSettings(Resource):
    parser = ns.parser()
    parser.add_argument(
        "newstatictemplate", required=True, help="No 'newstatictemplate' provided"
    )

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(
        message="Sorry, you don't have rights to access the setting panel"
    )
    @ns.expect(parser)
    @ns.doc(
        responses={
            200: "Success",
            400: "Missing parameter",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def put(self, server=None):
        """Creates a new template"""
        if (
            not current_user.is_anonymous
            and current_user.acl.is_moderator()
            and not current_user.acl.is_server_rw(server)
        ):
            self.abort(403, "You don't have rights on this server")

        newtemplate = self.parser.parse_args()["newstatictemplate"]
        if not newtemplate:
            self.abort(400, "No template name provided")
        parser = bui.client.get_parser(agent=server)
        templates = parser.list_static_templates()
        if any(tpl["name"] == newtemplate for tpl in templates):
            self.abort(409, "Static template '{}' already exists".format(newtemplate))
        # clientconfdir = bui.client.get_parser_attr('clientconfdir', server)
        # if not clientconfdir:
        #    flash('Could not proceed, no \'clientconfdir\' find', 'warning')
        #    return redirect(request.referrer)
        noti = bui.client.store_conf_cli(
            ImmutableMultiDict(), newtemplate, None, False, True, server
        )
        if server:
            url = url_for(
                "view.cli_settings",
                server=server,
                client=newtemplate,
                statictemplate=True,
            )
        else:
            url = url_for("view.cli_settings", client=newtemplate, statictemplate=True)
        noti.append(
            [
                NOTIF_INFO,
                _(
                    "<a href=\"%(url)s\">Click here</a> to edit '%(template)s' configuration",
                    url=url,
                    template=newtemplate,
                ),
            ]
        )
        # clear the cache when we add a new client
        cache.clear()
        bui.audit.logger.info(
            f"created new static template {newtemplate}", server=server
        )
        return {"notif": noti}, 201


@ns.route("/templates", "/<server>/templates", endpoint="templates_list")
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
    },
)
class TemplatesList(Resource):
    @api.acl_admin_or_moderator_required(
        message="Sorry, you don't have rights to access the setting panel"
    )
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def get(self, server=None):
        """Returns a list of clients"""
        parser = bui.client.get_parser(agent=server)
        res = parser.list_templates()
        return jsonify(result=res)


@ns.route("/template", "/<server>/template", endpoint="new_template", methods=["PUT"])
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
    },
)
class NewTemplateSettings(Resource):
    parser = ns.parser()
    parser.add_argument("newtemplate", required=True, help="No 'newclient' provided")

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(
        message="Sorry, you don't have rights to access the setting panel"
    )
    @ns.expect(parser)
    @ns.doc(
        responses={
            200: "Success",
            400: "Missing parameter",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def put(self, server=None):
        """Creates a new template"""
        if (
            not current_user.is_anonymous
            and current_user.acl.is_moderator()
            and not current_user.acl.is_server_rw(server)
        ):
            self.abort(403, "You don't have rights on this server")

        newtemplate = self.parser.parse_args()["newtemplate"]
        if not newtemplate:
            self.abort(400, "No template name provided")
        parser = bui.client.get_parser(agent=server)
        templates = parser.list_templates()
        for tpl in templates:
            if tpl["name"] == newtemplate:
                self.abort(409, "Template '{}' already exists".format(newtemplate))
        # clientconfdir = bui.client.get_parser_attr('clientconfdir', server)
        # if not clientconfdir:
        #    flash('Could not proceed, no \'clientconfdir\' find', 'warning')
        #    return redirect(request.referrer)
        noti = bui.client.store_conf_cli(
            ImmutableMultiDict(), newtemplate, None, True, False, server
        )
        if server:
            url = url_for(
                "view.cli_settings", server=server, client=newtemplate, template=True
            )
        else:
            url = url_for("view.cli_settings", client=newtemplate, template=True)
        noti.append(
            [
                NOTIF_INFO,
                _(
                    "<a href=\"%(url)s\">Click here</a> to edit '%(template)s' configuration",
                    url=url,
                    template=newtemplate,
                ),
            ]
        )
        # clear the cache when we add a new client
        cache.clear()
        bui.audit.logger.info(f"created new template {newtemplate}", server=server)
        return {"notif": noti}, 201


@ns.route("/config", "/<server>/config", endpoint="new_client", methods=["PUT"])
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
    },
)
class NewClientSettings(Resource):
    parser = ns.parser()
    parser.add_argument("newclient", required=True, help="No 'newclient' provided")
    parser.add_argument("templates", help="Templates list", action="split")
    parser.add_argument("statictemplate", help="Static template")
    parser.add_argument("variables", help="Template variables")

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(
        message="Sorry, you don't have rights to access the setting panel"
    )
    @ns.expect(parser)
    @ns.doc(
        responses={
            200: "Success",
            400: "Missing parameter",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def put(self, server=None):
        """Creates a new client"""
        args = self.parser.parse_args()
        newclient = args["newclient"]
        templates = [x for x in args.get("templates", []) if x]
        statictemplate = args["statictemplate"]
        variables = json.loads(args["variables"]) if args["variables"] else {}
        variables["agent"] = server
        variables["client"] = newclient
        if not newclient:
            self.abort(400, "No client name provided")

        if (
            not current_user.is_anonymous
            and current_user.acl.is_moderator()
            and not current_user.acl.is_client_rw(newclient, server)
        ):
            self.abort(403, "You don't have rights on this server")

        parser = bui.client.get_parser(agent=server)
        clients = parser.list_clients()
        for cl in clients:
            if cl["name"] == newclient:
                self.abort(409, "Client '{}' already exists".format(newclient))
        # clientconfdir = bui.client.get_parser_attr('clientconfdir', server)
        # if not clientconfdir:
        #    flash('Could not proceed, no \'clientconfdir\' find', 'warning')
        #    return redirect(request.referrer)
        data = MultiDict()
        content = ""
        if templates:
            real_templates = {x["name"]: x["value"] for x in parser._list_templates()}
            if any(x not in real_templates for x in templates):
                self.abort(400, "Wrong template")
            data.setlist("templates", [real_templates[x] for x in templates])
        if statictemplate:
            statics = parser._list_static_templates()
            for tpl in statics:
                if tpl["name"] == statictemplate:
                    content = render_template_string(tpl["content"], **variables)
        noti = bui.client.store_conf_cli(
            ImmutableMultiDict(data), newclient, None, content=content, agent=server
        )
        if server:
            url = url_for("view.cli_settings", server=server, client=newclient)
        else:
            url = url_for("view.cli_settings", client=newclient)
        noti.append(
            [
                NOTIF_INFO,
                _(
                    "<a href=\"%(url)s\">Click here</a> to edit '%(client)s' configuration",
                    url=url,
                    client=newclient,
                ),
            ]
        )
        # clear the cache when we add a new client
        cache.clear()
        # clear client-side cache through the _extra META variable
        try:
            _extra = session.get("_extra", g.now)
            _extra = int(_extra)
        except ValueError:
            _extra = 0
        session["_extra"] = "{}".format(_extra + 1)
        if bui.config["WITH_CELERY"]:
            from ..tasks import force_scheduling_now

            force_scheduling_now()

        bui.audit.logger.info(
            f"created new client configuration {newclient}", server=server
        )
        return {"notif": noti}, 201


@ns.route(
    "/config/<client>",
    "/config/<client>/<path:conf>",
    "/<server>/config/<client>",
    "/<server>/config/<client>/<path:conf>",
    endpoint="client_settings",
    methods=["GET", "POST", "PUT", "DELETE"],
)
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
        "client": "Client name",
        "conf": "Path of the configuration file",
    },
)
class ClientSettings(Resource):
    parser_delete = ns.parser()
    parser_delete.add_argument(
        "revoke",
        type=inputs.boolean,
        help="Whether to revoke the certificate or not",
        default=False,
        nullable=True,
    )
    parser_delete.add_argument(
        "delcert",
        type=inputs.boolean,
        help="Whether to delete the certificate or not",
        default=False,
        nullable=True,
    )
    parser_delete.add_argument(
        "keepconf",
        type=inputs.boolean,
        help="Whether to keep the conf or not",
        default=False,
        nullable=True,
    )
    parser_delete.add_argument(
        "template",
        type=inputs.boolean,
        help="Whether we work on a template or not",
        default=False,
        nullable=True,
    )
    parser_delete.add_argument(
        "statictemplate",
        type=inputs.boolean,
        help="Whether we work on a static template or not",
        default=False,
        nullable=True,
    )
    parser_delete.add_argument(
        "delete",
        type=inputs.boolean,
        help="Whether we should remove the data as well or not",
        default=False,
        nullable=True,
    )
    parser_put = ns.parser()
    parser_put.add_argument("newname", help="New name of the client/template")
    parser_put.add_argument(
        "template",
        type=inputs.boolean,
        help="Whether we work on a template or not",
        default=False,
        nullable=True,
    )
    parser_put.add_argument(
        "statictemplate",
        type=inputs.boolean,
        help="Whether we work on a static template or not",
        default=False,
        nullable=True,
    )
    parser_put.add_argument(
        "keepcert",
        type=inputs.boolean,
        help="Whether to keep the same certificate or not",
        default=False,
        nullable=True,
    )
    parser_put.add_argument(
        "keepdata",
        type=inputs.boolean,
        help="Whether to keep the data or not",
        default=False,
        nullable=True,
    )
    parser_post = ns.parser()
    parser_post.add_argument(
        "template",
        type=inputs.boolean,
        help="Whether we work on a template or not",
        default=False,
        nullable=True,
    )
    parser_post.add_argument(
        "statictemplate",
        type=inputs.boolean,
        help="Whether we work on a static template or not",
        default=False,
        nullable=True,
    )
    parser_get = ns.parser()
    parser_get.add_argument(
        "template",
        type=inputs.boolean,
        help="Whether we work on a template or not",
        default=False,
        nullable=True,
    )
    parser_get.add_argument(
        "statictemplate",
        type=inputs.boolean,
        help="Whether we work on a static template or not",
        default=False,
        nullable=True,
    )

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(
        message=_("Sorry, you don't have rights to access the setting panel")
    )
    @ns.expect(parser_post)
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def post(self, server=None, client=None, conf=None):
        """Saves a given client configuration"""
        if (
            not current_user.is_anonymous
            and current_user.acl.is_moderator()
            and not current_user.acl.is_client_rw(client, server)
        ):
            self.abort(403, "You don't have rights on this server")

        args = self.parser_post.parse_args()
        template = args.get("template", False)
        statictemplate = args.get("statictemplate", False)
        noti = bui.client.store_conf_cli(
            request.form, client, conf, template, statictemplate, server
        )
        # clear cache
        cache.clear()
        # clear client-side cache through the _extra META variable
        try:
            _extra = session.get("_extra", g.now)
            _extra = int(_extra)
        except ValueError:
            _extra = 0
        session["_extra"] = "{}".format(_extra + 1)

        bui.audit.logger.info(
            f"updated client configuration {client} ({conf})", server=server
        )
        return {"notif": noti}

    @api.acl_admin_or_moderator_required(
        message=_("Sorry, you don't have rights to access the setting panel")
    )
    @ns.expect(parser_get)
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def get(self, server=None, client=None, conf=None):
        """Reads a given client configuration"""
        try:
            conf = unquote(conf)
        except:
            pass
        args = self.parser_get.parse_args()
        template = args.get("template", False)
        statictemplate = args.get("statictemplate", False)
        parser = bui.client.get_parser(agent=server)
        res = parser.read_client_conf(client, conf, template, statictemplate)
        refresh()
        # Translate the doc and placeholder API side
        cache_keys = {
            "doc": "_doc_parser_{}-{}".format(server, g.locale),
            "placeholders": "_placeholders_parser_{}-{}".format(server, g.locale),
            "boolean_cli": "_boolean_cli_parser_{}".format(server),
            "string_cli": "_string_cli_parser_{}".format(server),
            "integer_cli": "_integer_cli_parser_{}".format(server),
            "multi_cli": "_multi_cli_parser_{}".format(server),
            "values": "_suggest_parser_{}".format(server),
            "defaults": "_defaults_parser_{}".format(server),
        }
        cache_results = {}
        for name, key in cache_keys.items():
            if not cache.cache.has(key):
                if name in ["doc", "placeholders"]:
                    _tmp = bui.client.get_parser_attr(name, server).copy()
                    _tmp2 = {}
                    for k, v in _tmp.items():
                        _tmp2[k] = _(v)
                    cache_results[name] = _tmp2
                else:
                    cache_results[name] = bui.client.get_parser_attr(name, server)
                cache.cache.set(key, cache_results[name], 3600)
            else:
                cache_results[name] = cache.cache.get(key)

        return jsonify(
            results=res,
            boolean=cache_results["boolean_cli"],
            string=cache_results["string_cli"],
            integer=cache_results["integer_cli"],
            multi=cache_results["multi_cli"],
            server_doc=cache_results["doc"],
            suggest=cache_results["values"],
            placeholders=cache_results["placeholders"],
            defaults=cache_results["defaults"],
        )

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(
        message=_("Sorry, you don't have rights to access the setting panel")
    )
    @ns.expect(parser_delete)
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            409: "Conflict",
            500: "Internal failure",
        }
    )
    def delete(self, server=None, client=None, conf=None):
        """Deletes a given client"""
        if (
            not current_user.is_anonymous
            and current_user.acl.is_moderator()
            and not current_user.acl.is_client_rw(client, server)
        ):
            self.abort(403, "You don't have rights on this server")

        if bui.client.is_backup_running(client, server):
            self.abort(
                409,
                "There is currently a backup running for this client hence "
                "we cannot delete it for now. Please try again later",
            )

        args = self.parser_delete.parse_args()
        delcert = args.get("delcert", False)
        revoke = args.get("revoke", False)
        keepconf = args.get("keepconf", False)
        template = args.get("template", False)
        statictemplate = args.get("statictemplate", False)
        delete = args.get("delete", False)

        if not keepconf:
            # clear the cache when we remove a client
            cache.clear()
            # clear client-side cache through the _extra META variable
            try:
                _extra = session.get("_extra", g.now)
                _extra = int(_extra)
            except ValueError:
                _extra = 0
            session["_extra"] = "{}".format(_extra + 1)
            if bui.config["WITH_CELERY"]:
                from ..tasks import force_scheduling_now

                force_scheduling_now()
        parser = bui.client.get_parser(agent=server)

        bui.audit.logger.info(
            f"deleted client configuration {client}, delete certificate: {delcert}, "
            f"revoke certificate: {revoke}, keep a backup of the configuration: "
            f"{keepconf}, delete data: {delete}, is template: {template} "
            f"is static template: {statictemplate}",
            server=server,
        )
        return (
            parser.remove_client(
                client, keepconf, delcert, revoke, template, statictemplate, delete
            ),
            200,
        )

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(
        message=_("Sorry, you don't have rights to access the setting panel")
    )
    @ns.expect(parser_put)
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            409: "Conflict",
            500: "Internal failure",
        }
    )
    def put(self, server=None, client=None, conf=None):
        """Rename a given client"""
        if (
            not current_user.is_anonymous
            and current_user.acl.is_moderator()
            and not current_user.acl.is_client_rw(client, server)
        ):
            self.abort(403, "You don't have rights on this server")

        if bui.client.is_backup_running(client, server):
            self.abort(
                409,
                "There is currently a backup running for this client hence "
                "we cannot delete it for now. Please try again later",
            )

        args = self.parser_put.parse_args()
        newname = args.get("newname", None)
        keepcert = args.get("keepcert", False)
        keepdata = args.get("keepdata", False)
        template = args.get("template", False)
        statictemplate = args.get("statictemplate", False)

        # clear the cache when we remove a client
        cache.clear()
        # clear client-side cache through the _extra META variable
        try:
            _extra = session.get("_extra", g.now)
            _extra = int(_extra)
        except ValueError:
            _extra = 0
        session["_extra"] = "{}".format(_extra + 1)
        if bui.config["WITH_CELERY"]:
            from ..tasks import force_scheduling_now

            force_scheduling_now()
        parser = bui.client.get_parser(agent=server)

        bui.audit.logger.info(
            f"renaming client configuration {client} to {newname}, "
            f"keep data: {keepdata}, keep certificate: {keepcert}, "
            f"is template: {template}, is static template: {statictemplate}",
            server=server,
        )
        return (
            parser.rename_client(
                client, newname, template, statictemplate, keepcert, keepdata
            ),
            200,
        )


@ns.route(
    "/path-expander",
    "/<server>/path-expander",
    "/path-expander/<client>",
    "/<server>/path-expander/<client>",
    endpoint="path_expander",
)
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
        "client": "Client name",
    },
)
class PathExpander(Resource):
    parser = ns.parser()
    parser.add_argument("path", required=True, help="No 'path' provided")
    parser.add_argument("source", required=False, help="Which file is it included in")

    @api.acl_admin_or_moderator_required(
        message=_("Sorry, you don't have rights to access the setting panel")
    )
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def get(self, server=None, client=None):
        """Expends a given path

        For instance if it's given a glob expression it will returns a list of
        files matching the expression.
        """
        args = self.parser.parse_args()
        path = args["path"]
        source = args["source"]
        if path:
            path = unquote(path)
        if source:
            source = unquote(source)
        parser = bui.client.get_parser(agent=server)
        paths = parser.path_expander(path, source, client)
        if not paths:
            self.abort(403, "Path not found")
        return {"result": paths}


@ns.route("/options", "/<server>/options", endpoint="setting_options")
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
    },
)
class SettingOptions(Resource):
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
            500: "Internal failure",
        }
    )
    def get(self, server=None):
        """Returns various setting options"""
        return {
            "is_revocation_enabled": bui.client.revocation_enabled(server),
            "server_can_restore": not bui.noserverrestore
            or bui.client.get_parser(agent=server).param(
                "server_can_restore", "client_conf"
            ),
            "batch_list_supported": bui.client.get_attr(
                "batch_list_supported", False, server
            ),
        }
