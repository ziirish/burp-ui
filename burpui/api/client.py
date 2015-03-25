# -*- coding: utf8 -*-
import json

from burpui import app, bui
from burpui.api import api
from burpui.misc.backend.interface import BUIserverException
from flask.ext.restful import reqparse, Resource
from flask.ext.login import current_user, login_required
from flask import jsonify

@api.resource('/api/client-tree.json/<name>/<int:backup>', '/api/<server>/client-tree.json/<name>/<int:backup>')
class ClientTree(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)
        self.parser.add_argument('root', type=str)

    @login_required
    def get(self, server=None, name=None, backup=None):
        """
        WebService: return a specific client files tree
        :param name: the client name (mandatory)
        :param backup: the backup number (mandatory)

        """
        if not server:
            server = self.parser.parse_args()['server']
        j = []
        if not name or not backup:
            return jsonify(results=j)
        root = self.parser.parse_args()['root']
        try:
            if bui.acl_handler and\
                    (not bui.acl_handler.get_acl().is_admin(current_user.name)\
                    and not bui.acl_handler.get_acl().is_client_allowed(current_user.name, name, server)):
                raise BUIserverException('Sorry, you are not allowed to view this client')
            j = bui.cli.get_tree(name, backup, root, agent=server)
        except BUIserverException, e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        return jsonify(results=j)

@api.resource('/api/client-stat.json/<name>', '/api/<server>/client-stat.json/<name>', '/api/client-stat.json/<name>/<int:backup>', '/api/<server>/client-stat.json/<name>/<int:backup>')
class ClientStats(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, server=None, name=None, backup=None):
        """
        WebService: return a specific client detailed report
        """
        if not server:
            server = self.parser.parse_args()['server']
        j = []
        if not name:
            err = [[1, 'No client defined']]
            return jsonify(notif=err)
        if bui.acl_handler and not bui.acl_handler.get_acl().is_client_allowed(current_user.name, name, server):
            err = [[2, 'You don\'t have rights to view this client stats']]
            return jsonify(notif=err)
        if backup:
            try:
                j = bui.cli.get_backup_logs(backup, name, agent=server)
            except BUIserverException, e:
                err = [[2, str(e)]]
                return jsonify(notif=err)
        else:
            try:
                cl = bui.cli.get_client(name, agent=server)
            except BUIserverException, e:
                err = [[2, str(e)]]
                return jsonify(notif=err)
            for c in cl:
                j.append(bui.cli.get_backup_logs(c['number'], name, agent=server))
        return jsonify(results=j)

@api.resource('/api/client.json/<name>', '/api/<server>/client.json/<name>')
class ClientReport(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, server=None, name=None):
        """
        WebService: return a specific client backups overview
        """
        if not server:
            server = self.parser.parse_args()['server']
        try:
            if bui.acl_handler and ( \
                    not bui.acl_handler.get_acl().is_admin(current_user.name) \
                    and not bui.acl_handler.get_acl().is_client_allowed(current_user.name, name, server)):
                raise BUIserverException('Sorry, you cannot access this client')
            j = bui.cli.get_client(name, agent=server)
        except BUIserverException, e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        return jsonify(results=j)

