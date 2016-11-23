# -*- coding: utf8 -*-

# This is a submodule we can also use "from ..api import api"
from . import api, cache_key
from ..server import BUIServer  # noqa
from .custom import fields, Resource
from ..exceptions import BUIserverException

from flask import current_app

bui = current_app  # type: BUIServer
ns = api.namespace('servers', 'Servers methods')


@ns.route('/stats', endpoint='servers_stats')
class ServersStats(Resource):
    """The :class:`burpui.api.servers.ServersStats` resource allows you to
    retrieve statistics about servers/agents.

    This resource is part of the :mod:`burpui.api.servers` module.
    """
    servers_fields = ns.model('Servers', {
        'alive': fields.Boolean(required=True, description='Is the server reachable'),
        'clients': fields.Integer(required=True, description='Number of clients managed by this server'),
        'name': fields.String(required=True, description='Server name'),
    })

    @api.cache.cached(timeout=1800, key_prefix=cache_key)
    @ns.marshal_list_with(servers_fields, code=200, description='Success')
    @ns.doc(
        responses={
            500: 'Internal failure',
        },
    )
    def get(self):
        """Returns a list of servers (agents) with basic stats

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            [
              {
                'alive': true,
                'clients': 2,
                'name': 'burp1',
              },
              {
                'alive': false,
                'clients': 0,
                'name': 'burp2',
              },
            ]


        :returns: The *JSON* described above.
        """

        r = []
        restrict = []
        check = False

        if bui.standalone:
            return r

        if bui.acl and not self.is_admin:
            check = True
            restrict = bui.acl.servers(self.username)

        for serv in bui.client.servers:
            try:
                alive = bui.client.servers[serv].ping()
            except BUIserverException:
                alive = False

            if check and serv in restrict:
                r.append({
                    'name': serv,
                    'clients': len(bui.acl.clients(self.username, serv)),
                    'alive': alive
                })
            elif not check:
                try:
                    clients = bui.client.servers[serv].get_all_clients(serv)
                except BUIserverException:
                    clients = []

                r.append({
                    'name': serv,
                    'clients': len(clients),
                    'alive': alive
                })

        return r


@ns.route('/report', endpoint='servers_report')
class ServersReport(Resource):
    """The :class:`burpui.api.servers.ServersReport` resource allows you to
    retrieve a report about servers/agents.

    This resource is part of the :mod:`burpui.api.servers` module.
    """
    stats_fields = ns.model('ServersStats', {
        'total': fields.Integer(required=True, description='Number of files', default=0),
        'totsize': fields.Integer(required=True, description='Total size occupied by all the backups of this server', default=0),
        'linux': fields.Integer(required=True, description='Total number of Linux/Unix clients on this server', default=0),
        'windows': fields.Integer(required=True, description='Total number of Windows clients on this server', default=0),
        'unknown': fields.Integer(required=True, description='Total number of Unknown clients on this server', default=0),
    })
    server_fields = ns.model('ServersReport', {
        'name': fields.String(required=True, description='Server name'),
        'stats': fields.Nested(stats_fields, required=True),
    })
    backup_fields = ns.model('ServersBackup', {
        'name': fields.String(required=True, description='Server name'),
        'number': fields.Integer(required=True, description='Number of backups on this server', default=0),
    })
    report_fields = ns.model('ServersReportFull', {
        'backups': fields.Nested(backup_fields, as_list=True, required=True),
        'servers': fields.Nested(server_fields, as_list=True, required=True),
    })

    @api.cache.cached(timeout=1800, key_prefix=cache_key)
    @ns.marshal_with(report_fields, code=200, description='Success')
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def get(self):
        """Returns a global report about all the servers managed by Burp-UI

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "backups": [
                {
                  "name": "AGENT1",
                  "number": 49
                }
              ],
              "servers": [
                {
                  "name": "AGENT1",
                  "stats": {
                    "linux": 4,
                    "total": 349705,
                    "totsize": 119400711726,
                    "unknown": 0,
                    "windows": 1
                  }
                }
              ]
            }

        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients/servers you are authorized to.

        :returns: The *JSON* described above.
        """
        r = {}
        restrict = []
        check = False
        if bui.acl and not self.is_admin:
            check = True
            restrict = bui.acl.servers(self.username)

        backups = []
        servers = []
        try:
            for serv in bui.client.servers:
                out = {
                    'name': serv,
                    'stats': {
                        'total': 0,
                        'totsize': 0,
                        'linux': 0,
                        'windows': 0,
                        'unknown': 0,
                    },
                    'number': 0
                }
                if check and serv not in restrict:
                    continue
                clients = []
                if bui.acl and not self.is_admin:
                    clients = [{'name': x} for x in bui.acl.clients(self.username, serv)]
                else:
                    clients = bui.client.get_all_clients(agent=serv)

                j = bui.client.get_clients_report(clients, serv)
                if 'clients' not in j or 'backups' not in j:
                    continue
                for stats in j['clients']:
                    for key in ['total', 'totsize']:
                        out['stats'][key] += stats['stats'][key]
                    if stats['stats']['windows'] == 'true':
                        out['stats']['windows'] += 1
                    elif stats['stats']['windows'] == 'false':
                        out['stats']['linux'] += 1
                    else:
                        out['stats']['unknown'] += 1
                for bkp in j['backups']:
                    out['number'] += bkp['number']
                backups.append({'name': serv, 'number': out['number']})
                servers.append({'name': serv, 'number': out['stats']})

        except BUIserverException as e:
            self.abort(500, str(e))

        r['backups'] = backups
        r['servers'] = servers

        return r
