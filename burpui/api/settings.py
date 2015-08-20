# -*- coding: utf8 -*-
"""
.. module:: settings
    :platform: Unix
    :synopsis: Burp-UI settings api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""

from burpui.api import api
from flask.ext.restful import reqparse, abort, Resource
from flask.ext.login import current_user, login_required
from flask import jsonify, flash, request, redirect, url_for
from urllib import unquote


@api.resource('/api/server-config',
              '/api/<server>/server-config',
              '/api/server-config/<path:conf>',
              '/api/<server>/server-config/<path:conf>',
              endpoint='api.server_settings')
class ServerSettings(Resource):
    """
    The :class:`burpui.api.settings.ServerSettings` resource allows you to
    retrieve the server's configuration.

    This resource is part of the :mod:`burpui.api.settings` module.
    """

    @login_required
    def get(self, conf=None, server=None):
        """
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
                    "value": false
                  },
                  {
                    "name": "syslog",
                    "value": true
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
                    "value": "server"
                  },
                  {
                    "name": "directory",
                    "value": "/var/spool/burp"
                  },
                  { "...": "..." }
                ],
                "includes": [],
                "includes_ext": [],
                "integer": [
                  {
                    "name": "port",
                    "value": 4971
                  },
                  {
                    "name": "status_port",
                    "value": 4972
                  },
                  { "...": "..." }
                ],
                "multi": [
                  {
                    "name": "keep",
                    "value": [
                      "7",
                      "4"
                    ]
                  },
                  { "...": "..." }
                ]
              },
              "server_doc": {
                "address": "Defines the main TCP address that the server listens on. The default is either '::' or '0.0.0.0', dependent upon compile time options.",
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
                "...": []
              }
            }


        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above.
        """
        # Only the admin can edit the configuration
        if (api.bui.acl and not
                api.bui.acl.is_admin(current_user.name)):
            abort(403, message='Sorry, you don\'t have rights to access the setting panel')

        try:
            conf = unquote(conf)
        except:
            pass
        r = api.bui.cli.read_conf_srv(conf, server)
        return jsonify(results=r,
                       boolean=api.bui.cli.get_parser_attr('boolean_srv', server),
                       string=api.bui.cli.get_parser_attr('string_srv', server),
                       integer=api.bui.cli.get_parser_attr('integer_srv', server),
                       multi=api.bui.cli.get_parser_attr('multi_srv', server),
                       server_doc=api.bui.cli.get_parser_attr('doc', server),
                       suggest=api.bui.cli.get_parser_attr('values', server),
                       placeholders=api.bui.cli.get_parser_attr('placeholders', server),
                       defaults=api.bui.cli.get_parser_attr('defaults', server))


@api.resource('/api/<client>/client-config',
              '/api/<client>/client-config/<path:conf>',
              '/api/<server>/<client>/client-config',
              '/api/<server>/<client>/client-config/<path:conf>',
              endpoint='api.client_settings')
class ClientSettings(Resource):

    @login_required
    def get(self, server=None, client=None, conf=None):
        # Only the admin can edit the configuration
        if (api.bui.acl and not
                api.bui.acl.is_admin(current_user.name)):
            abort(403, message='Sorry, you don\'t have rights to access the setting panel')

        try:
            conf = unquote(conf)
        except:
            pass
        r = api.bui.cli.read_conf_cli(client, conf, server)
        return jsonify(results=r,
                       boolean=api.bui.cli.get_parser_attr('boolean_cli', server),
                       string=api.bui.cli.get_parser_attr('string_cli', server),
                       integer=api.bui.cli.get_parser_attr('integer_cli', server),
                       multi=api.bui.cli.get_parser_attr('multi_cli', server),
                       server_doc=api.bui.cli.get_parser_attr('doc', server),
                       suggest=api.bui.cli.get_parser_attr('values', server),
                       placeholders=api.bui.cli.get_parser_attr('placeholders', server),
                       defaults=api.bui.cli.get_parser_attr('defaults', server))


@api.resource('/api/new-client',
              '/api/<server>/new-client',
              endpoint='api.new_client')
class NewClient(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('newclient', type=str)

    @login_required
    def post(self, server=None):
        # Only the admin can edit the configuration
        if (api.bui.acl and not
                api.bui.acl.is_admin(current_user.name)):
            abort(403, message='Sorry, you don\'t have rights to access the setting panel')

        newclient = self.parser.parse_args()['newclient']
        if not newclient:
            flash('No client name provided', 'danger')
            return redirect(request.referrer)
        # clientconfdir = api.bui.cli.get_parser_attr('clientconfdir', server)
        # if not clientconfdir:
        #    flash('Could not proceed, no \'clientconfdir\' find', 'warning')
        #    return redirect(request.referrer)
        return redirect(url_for('view.cli_settings', server=server, client=newclient))


@api.resource('/api/path-expander',
              '/api/<server>/path-expander',
              '/api/path-expander/<client>',
              '/api/<server>/path-expander/<client>',
              endpoint='api.path_expander')
class PathExpander(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('path')

    @login_required
    def post(self, server=None, client=None):
        # Only the admin can edit the configuration
        if (api.bui.acl and not
                api.bui.acl.is_admin(current_user.name)):
            noti = [2, 'Sorry, you don\'t have rights to access the setting panel']
            return jsonify(notif=noti)

        path = self.parser.parse_args()['path']
        paths = api.bui.cli.expand_path(path, client, server)
        if not paths:
            noti = [2, "Path not found"]
            return jsonify(notif=noti)
        return jsonify(result=paths)


@api.resource('/api/delete-client',
              '/api/<server>/delete-client',
              '/api/delete-client/<client>',
              '/api/<server>/delete-client/<client>',
              endpoint='api.delete_client')
class DeleteClient(Resource):

    @login_required
    def post(self, server=None, client=None):
        # Only the admin can edit the configuration
        if (api.bui.acl and not
                api.bui.acl.is_admin(current_user.name)):
            noti = [2, 'Sorry, you don\'t have rights to access the setting panel']
            return jsonify(notif=noti)

        return jsonify(notif=api.bui.cli.delete_client(client, server))
