# -*- coding: utf8 -*-
import json

from burpui import app, bui
from burpui.api import api
from burpui.misc.backend.interface import BUIserverException
from flask.ext.restful import reqparse, Resource
from flask.ext.login import current_user, login_required
from flask import jsonify, make_response

@api.resource('/api/running-clients.json', '/api/<server>/running-clients.json', '/api/<client>/running-clients.json', '/api/<server>/<client>/running-clients.json')
class RunningClients(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, client=None, server=None):
        """
        API: running_clients
        :returns: a list of running clients
        """
        if not server:
            server = self.parser.parse_args()['server']
        if client:
            if bui.acl_handler:
                if not bui.acl_handler.acl.is_admin(current_user.name) and not bui.acl_handler.acl.is_client_allowed(current_user.name, client, server):
                    r = []
                    return jsonify(results=r)
            if bui.cli.is_backup_running(client, server):
                r = [bui.cli.get_client(client, server)]
                return jsonify(results=r)
            else:
                r = []
                return jsonify(results=r)

        r = bui.cli.is_one_backup_running(server)
        # Manage ACL
        if bui.acl_handler and not bui.acl_handler.acl.is_admin(current_user.name):
            if isinstance(r, dict):
                new = {}
                for serv in bui.acl_handler.acl.servers(current_user.name):
                    allowed = bui.acl_handler.acl.clients(current_user.name, serv)
                    new[serv] = [x for x in r[serv] if x in allowed]
                r = new
            else:
                allowed = bui.acl_handler.acl.clients(current_user.name, server)
                r = [x for x in r if x in allowed]
        return jsonify(results=r)

@api.resource('/api/running.json', '/api/<server>/running.json')
class BackupRunning(Resource):

    @login_required
    def get(self, server=None):
        """
        API: backup_running
        :returns: true if at least one backup is running
        """
        j = bui.cli.is_one_backup_running(server)
        # Manage ACL
        if bui.acl_handler and not bui.acl_handler.acl.is_admin(current_user.name):
            if isinstance(j, dict):
                new = {}
                for serv in bui.acl_handler.acl.servers(current_user.name):
                    allowed = bui.acl_handler.acl.clients(current_user.name, serv)
                    new[serv] = [x for x in j[serv] if x in allowed]
                j = new
            else:
                allowed = bui.acl_handler.acl.clients(current_user.name, server)
                j = [x for x in j if x in allowed]
        r = False
        if isinstance(j, dict):
            for k, v in j.iteritems():
                if r:
                    break
                r = r or (len(v) > 0)
        else:
            r = len(j) > 0
        return jsonify(results=r)

@api.resource('/api/clients-report.json', '/api/<server>/clients-report.json')
class ClientsReport(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, server=None):
        """
        WebService: return a JSON with global stats
        """
        if not server:
            server = self.parser.parse_args()['server']
        j = []
        try:
            # Manage ACL
            if not bui.standalone and bui.acl_handler and \
                    (not bui.acl_handler.acl.is_admin(current_user.name) \
                    and server not in bui.acl_handler.acl.servers(current_user.name)):
                raise BUIserverException('Sorry, you don\'t have rights on this server')
            clients = bui.cli.get_all_clients(agent=server)
        except BUIserverException, e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        cl = []
        ba = []
        # Filter only allowed clients
        allowed = []
        check = False
        if bui.acl_handler and not bui.acl_handler.acl.is_admin(current_user.name):
            check = True
            allowed = bui.acl_handler.acl.clients(current_user.name, server)
        aclients = []
        for c in clients:
            if check and c['name'] not in allowed:
                continue
            aclients.append(c)
        j = bui.cli.get_clients_report(aclients, server)
        app.logger.debug(j)
        return jsonify(results=j)

@api.resource('/api/clients.json', '/api/<server>/clients.json')
class ClientsStats(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, server=None):
        """
        WebService: return a JSON listing all clients
        """
        if not server:
            server = self.parser.parse_args()['server']
        try:
            if not bui.standalone and bui.acl_handler and \
                    (not bui.acl_handler.acl.is_admin(current_user.name) \
                    and server not in bui.acl_handler.acl.servers(current_user.name)):
                raise BUIserverException('Sorry, you don\'t have any rights on this server')
            j = bui.cli.get_all_clients(agent=server)
            if bui.acl_handler and not bui.acl_handler.acl.is_admin(current_user.name):
                j = [x for x in j if x['name'] in bui.acl_handler.acl.clients(current_user.name, server)]
        except BUIserverException, e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        return jsonify(results=j)
