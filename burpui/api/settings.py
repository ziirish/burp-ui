# -*- coding: utf8 -*-

from burpui import app, bui, login_manager
from burpui.api import api
from flask.ext.restful import reqparse, abort, Resource
from flask.ext.login import current_user, login_required
from flask import request, render_template, jsonify

@api.resource('/api/server-config', '/api/<server>/server-config')
class ServerSettings(Resource):
    
    @login_required
    def get(self, server=None):
        # Only the admin can edit the configuration
        if bui.acl_handler and not bui.acl_handler.acl.is_admin(current_user.name):
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

@api.resource('/api/client-config/<client>', '/api/<server>/client-config/<client>')
class ClientSettings(Resource):
    
    @login_required
    def get(self, server=None, client=None):
        # Only the admin can edit the configuration
        if bui.acl_handler and not bui.acl_handler.acl.is_admin(current_user.name):
            abort(403, message='Sorry, you don\'t have rights to access the setting panel')
        r = bui.cli.read_conf_cli(client, server)
        return jsonify(results=r)
