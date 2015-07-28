# -*- coding: utf8 -*-

from burpui.api import api
from burpui.misc.backend.interface import BUIserverException
from flask.ext.restful import reqparse, Resource
from flask.ext.login import current_user, login_required
from flask import jsonify


@api.resource('/api/servers.json', endpoint='api.servers_stats')
class ServersStats(Resource):
    """
    The :class:`burpui.api.servers.ServersStats` resource allows you to
    retrieve statistics about servers/agents.

    This resource is part of the :mod:`burpui.api.servers` module.
    """

    @login_required
    def get(self):
        r = []
        if hasattr(api.bui.cli, 'servers'):
            check = False
            allowed = []
            if (api.bui.acl and not
                    api.bui.acl.is_admin(current_user.name)):
                check = True
                allowed = api.bui.acl.servers(current_user.name)
            for serv in api.bui.cli.servers:
                try:
                    if check:
                        if serv in allowed:
                            r.append({'name': serv,
                                      'clients': len(api.bui.cli.servers[serv].get_all_clients(serv)),
                                      'alive': api.bui.cli.servers[serv].ping()})
                    else:
                        r.append({'name': serv,
                                  'clients': len(api.bui.cli.servers[serv].get_all_clients(serv)),
                                  'alive': api.bui.cli.servers[serv].ping()})
                except BUIserverException as e:
                    err = [[2, str(e)]]
                    return jsonify(notif=err)
        return jsonify(results=r)


@api.resource('/api/live.json',
              '/api/<server>/live.json',
              endpoint='api.live')
class Live(Resource):
    """
    The :class:`burpui.api.servers.Live` resource allows you to
    retrieve a list of servers that are currently *alive*.

    This resource is part of the :mod:`burpui.api.servers` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, server=None):
        """
        API: live
        :returns: the live status of the server
        """
        if not server:
            server = self.parser.parse_args()['server']
        r = []
        if server:
            l = (api.bui.cli.is_one_backup_running(server))[server]
        else:
            l = api.bui.cli.is_one_backup_running()
        if isinstance(l, dict):
            for k, a in l.iteritems():
                for c in a:
                    s = {}
                    s['client'] = c
                    s['agent'] = k
                    try:
                        s['status'] = api.bui.cli.get_counters(c, agent=k)
                    except BUIserverException:
                        s['status'] = []
                    r.append(s)
        else:
            for c in l:
                s = {}
                s['client'] = c
                try:
                    s['status'] = api.bui.cli.get_counters(c, agent=server)
                except BUIserverException:
                    s['status'] = []
                r.append(s)
        return jsonify(results=r)
