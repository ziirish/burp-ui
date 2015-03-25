# -*- coding: utf8 -*-

from burpui import bui
from burpui.api import api
from burpui.misc.backend.interface import BUIserverException
from flask.ext.restful import reqparse, Resource
from flask.ext.login import current_user, login_required
from flask import jsonify

@api.resource('/api/servers.json')
class ServersStats(Resource):

    @login_required
    def get(self):
        r = []
        if hasattr(bui.cli, 'servers'):
            check = False
            allowed = []
            if bui.acl_handler and not bui.acl_handler.get_acl().is_admin(current_user.name):
                check = True
                allowed = bui.acl_handler.get_acl().servers(current_user.name)
            for serv in bui.cli.servers:
                if check:
                    if serv in allowed:
                        r.append({'name': serv, 'clients': len(bui.cli.servers[serv].get_all_clients(serv)), 'alive': bui.cli.servers[serv].ping()})
                else:
                    r.append({'name': serv, 'clients': len(bui.cli.servers[serv].get_all_clients(serv)), 'alive': bui.cli.servers[serv].ping()})
        return jsonify(results=r)

@api.resource('/api/live.json', '/api/<server>/live.json')
class Live(Resource):

@login_required
def live(server=None):
    """
    API: live
    :returns: the live status of the server
    """
    if not server:
        server = request.args.get('server')
    r = []
    if server:
        l = (bui.cli.is_one_backup_running(server))[server]
    else:
        l = bui.cli.is_one_backup_running()
    if isinstance(l, dict):
        for k, a in l.iteritems():
            for c in a:
                s = {}
                s['client'] = c
                s['agent'] = k
                try:
                    s['status'] = bui.cli.get_counters(c, agent=k)
                except BUIserverException:
                    s['status'] = []
                r.append(s)
    else:
        for c in l:
            s = {}
            s['client'] = c
            try:
                s['status'] = bui.cli.get_counters(c, agent=server)
            except BUIserverException:
                s['status'] = []
            r.append(s)
    return jsonify(results=r)
