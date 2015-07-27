# -*- coding: utf8 -*-
"""
.. module:: settings
    :platform: Unix
    :synopsis: Burp-UI settings api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""

from burpui import app, bui, login_manager
from burpui.api import api
from flask.ext.restful import reqparse, abort, Resource
from flask.ext.login import current_user, login_required
from flask import jsonify


@api.resource('/api/server-config',
              '/api/<server>/server-config',
              endpoint='api.server_settings')
class ServerSettings(Resource):
    """
    The :class:`burpui.api.settings.ServerSettings` resource allows you to
    retrieve the server's configuration.

    This resource is part of the :mod:`burpui.api.settings` module.
    """

    @login_required
    def get(self, server=None):
        """
        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "boolean": [
                "daemon",
                "fork",
                ...
              ],
              "defaults": {
                "address": "",
                "autoupgrade_dir": "",
                "ca_burp_ca": "",
                "ca_conf": "",
                "ca_name": "",
                "ca_server_name": "",
                "client_can_delete": true,
                ...
              },
              "integer": [
                "port",
                "status_port",
                ...
              ],
              "multi": [
                "keep",
                "restore_client",
                ...
              ],
              "placeholders": {
                "autoupgrade_dir": "path",
                "ca_burp_ca": "path",
                "ca_conf": "path",
                "ca_name": "name",
                "ca_server_name": "name",
                "client_can_delete": "0|1",
                ...
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
                  ...
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
                  ...
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
                  ...
                ],
                "multi": [
                  {
                    "name": "keep",
                    "value": [
                      "7",
                      "4"
                    ]
                  },
                  ...
                ]
              },
              "server_doc": {
                "address": "Defines the main TCP address that the server listens on. The default is either '::' or '0.0.0.0', dependent upon compile time options.",
                ...
              },
              "string": [
                "mode",
                "address",
                ...
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
                ...
              }
            }


        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above.
        """
        # Only the admin can edit the configuration
        if (bui.acl and not
                bui.acl.is_admin(current_user.name)):
            abort(403, message='Sorry, you don\'t have rights to access the setting panel')
        r = bui.cli.read_conf_srv(server)
        return jsonify(results=r,
                       boolean=bui.cli.get_parser_attr('boolean_srv', server),
                       string=bui.cli.get_parser_attr('string_srv', server),
                       integer=bui.cli.get_parser_attr('integer_srv', server),
                       multi=bui.cli.get_parser_attr('multi_srv', server),
                       server_doc=bui.cli.get_parser_attr('doc', server),
                       suggest=bui.cli.get_parser_attr('values', server),
                       placeholders=bui.cli.get_parser_attr('placeholders', server),
                       defaults=bui.cli.get_parser_attr('defaults', server))


@api.resource('/api/client-config/<client>',
              '/api/<server>/client-config/<client>')
class ClientSettings(Resource):

    @login_required
    def get(self, server=None, client=None):
        # Only the admin can edit the configuration
        if (bui.acl and not
                bui.acl.is_admin(current_user.name)):
            abort(403, message='Sorry, you don\'t have rights to access the setting panel')
        r = bui.cli.read_conf_cli(client, server)
        return jsonify(results=r)
