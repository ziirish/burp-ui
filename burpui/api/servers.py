# -*- coding: utf8 -*-

# This is a submodule we can also use "from ..api import api"
from . import api, cache_key, parallel_loop
from .custom import fields, Resource
from ..exceptions import BUIserverException

ns = api.namespace('servers', 'Servers methods')


@ns.route('/stats', endpoint='servers_stats')
class ServersStats(Resource):
    """The :class:`burpui.api.servers.ServersStats` resource allows you to
    retrieve statistics about servers/agents.

    This resource is part of the :mod:`burpui.api.servers` module.
    """
    servers_fields = api.model('Servers', {
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
        if hasattr(api.bui.cli, 'servers'):
            restrict = []
            check = False
            if api.bui.acl and not self.is_admin:
                check = True
                restrict = api.bui.acl.servers(self.username)

            def get_servers_info(serv, output, restrict, check, username):
                try:
                    if check and serv in restrict:
                        output.put({
                            'name': serv,
                            'clients': len(api.bui.acl.clients(username, serv)),
                            'alive': api.bui.cli.servers[serv].ping()
                        })
                        return
                    elif not check:
                        output.put({
                            'name': serv,
                            'clients': len(api.bui.cli.servers[serv].get_all_clients(serv)),
                            'alive': api.bui.cli.servers[serv].ping()
                        })
                        return
                    output.put(None)
                except BUIserverException as e:
                    output.put(str(e))

            r = parallel_loop(get_servers_info, api.bui.cli.servers, restrict, check, self.username)

        return r


@ns.route('/report', endpoint='servers_report')
class ServersReport(Resource):
    """The :class:`burpui.api.servers.ServersReport` resource allows you to
    retrieve a report about servers/agents.

    This resource is part of the :mod:`burpui.api.servers` module.
    """
    stats_fields = api.model('ServersStats', {
        'total': fields.Integer(required=True, description='Number of files', default=0),
        'totsize': fields.Integer(required=True, description='Total size occupied by all the backups of this server', default=0),
        'linux': fields.Integer(required=True, description='Total number of Linux/Unix clients on this server', default=0),
        'windows': fields.Integer(required=True, description='Total number of Windows clients on this server', default=0),
        'unknown': fields.Integer(required=True, description='Total number of Unknown clients on this server', default=0),
    })
    server_fields = api.model('ServersReport', {
        'name': fields.String(required=True, description='Server name'),
        'stats': fields.Nested(stats_fields, required=True),
    })
    backup_fields = api.model('ServersBackup', {
        'name': fields.String(required=True, description='Server name'),
        'number': fields.Integer(required=True, description='Number of backups on this server', default=0),
    })
    report_fields = api.model('ServersReportFull', {
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
        if hasattr(api.bui.cli, 'servers'):
            restrict = []
            check = False
            if api.bui.acl and not self.is_admin:
                check = True
                restrict = api.bui.acl.servers(self.username)

            stats = []

            def get_servers_stats(serv, output, restrict, check, username):
                try:
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
                        output.put(None)
                        return
                    clients = []
                    if (api.bui.acl and not
                            api.bui.acl.is_admin(username)):
                        clients = [{'name': x} for x in api.bui.acl.clients(username, serv)]
                    else:
                        clients = api.bui.cli.get_all_clients(agent=serv)

                    j = api.bui.cli.get_clients_report(clients, serv)
                    if 'clients' not in j or 'backups' not in j:
                        output.put(None)
                        return
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
                    output.put(out)
                except BUIserverException as e:
                    output.put(str(e))

            stats = parallel_loop(get_servers_stats, api.bui.cli.servers, restrict, check, self.username)
            backups = []
            servers = []
            for serv in stats:
                backups.append({'name': serv['name'], 'number': serv['number']})
                servers.append({'name': serv['name'], 'stats': serv['stats']})

            r['backups'] = backups
            r['servers'] = servers

        return r
