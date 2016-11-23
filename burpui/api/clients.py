# -*- coding: utf8 -*-
"""
.. module:: burpui.api.clients
    :platform: Unix
    :synopsis: Burp-UI clients api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from . import api, cache_key
from ..server import BUIServer  # noqa
from .custom import fields, Resource
from ..exceptions import BUIserverException

from six import iteritems
from flask import current_app

bui = current_app  # type: BUIServer
ns = api.namespace('clients', 'Clients methods')


# Seem to not be used anymore
# TODO: we can probably remove this someday
@ns.route('/running',
          '/<server>/running',
          '/running/<client>',
          '/<server>/running/<client>',
          endpoint='running_clients')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
        'client': 'Client name',
    },
)
class RunningClients(Resource):
    """The :class:`burpui.api.clients.RunningClients` resource allows you to
    retrieve a list of clients that are currently running a backup.

    This resource is part of the :mod:`burpui.api.clients` module.

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')

    @ns.expect(parser)
    def get(self, client=None, server=None):
        """Returns a list of clients currently running a backup

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            [ 'client1', 'client2' ]


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param client: Ask a specific client in order to know if it is running a backup
        :type client: str

        :returns: The *JSON* described above.
        """
        server = server or self.parser.parse_args()['serverName']
        if client:
            if bui.acl:
                if (not self.is_admin and not
                        bui.acl.is_client_allowed(self.username,
                                                  client,
                                                  server)):
                    r = []
                    return r
            if bui.client.is_backup_running(client, server):
                r = [client]
                return r
            else:
                r = []
                return r

        r = bui.client.is_one_backup_running(server)
        # Manage ACL
        if bui.acl and not self.is_admin:
            if isinstance(r, dict):
                new = {}
                for serv in bui.acl.servers(self.username):
                    allowed = bui.acl.clients(self.username, serv)
                    new[serv] = [x for x in r[serv] if x in allowed]
                r = new
            else:
                allowed = bui.acl.clients(self.username, server)
                r = [x for x in r if x in allowed]
        return r


@ns.route('/backup-running',
          '/<server>/backup-running',
          endpoint='running_backup')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
    }
)
class RunningBackup(Resource):
    """The :class:`burpui.api.clients.RunningBackup` resource allows you to
    access the status of the server in order to know if there is a running
    backup currently.

    This resource is part of the :mod:`burpui.api.clients` module.
    """
    running_fields = ns.model('Running', {
        'running': fields.Boolean(required=True, description='Is there a backup running right now'),
    })

    @ns.marshal_with(running_fields, code=200, description='Success')
    def get(self, server=None):
        """Tells if a backup is running right now

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
                "running": false
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above.
        """
        return {
            'running': self._is_one_backup_running(
                bui.client.is_one_backup_running(server),
                server
            )
        }

    def _is_one_backup_running(self, res, server):
        """Check if a backup is running"""
        # Manage ACL
        if bui.acl and not self.is_admin:
            if isinstance(res, dict):
                new = {}
                for serv in bui.acl.servers(self.username):
                    allowed = bui.acl.clients(self.username, serv)
                    new[serv] = [x for x in res[serv] if x in allowed]
                res = new
            else:
                allowed = bui.acl.clients(self.username, server)
                res = [x for x in res if x in allowed]
        running = False
        if isinstance(res, dict):
            for (_, run) in iteritems(res):
                running = running or (len(run) > 0)
                if running:
                    break
        else:
            running = len(res) > 0

        return running


@ns.route('/report',
          '/<server>/report',
          endpoint='clients_report')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
    },
)
class ClientsReport(Resource):
    """The :class:`burpui.api.clients.ClientsReport` resource allows you to
    access general reports about your clients.

    This resource is part of the :mod:`burpui.api.clients` module.

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
    parser.add_argument('limit', type=int, default=8, help='Number of elements to return')
    parser.add_argument('aggregation', help='What aggregation to operate', default='number', choices=('number', 'files', 'size'))

    translation = {
        'number': 'number',
        'files': 'total',
        'size': 'totsize',
    }

    stats_fields = ns.model('ClientsStats', {
        'total': fields.Integer(required=True, description='Number of files', default=0),
        'totsize': fields.Integer(required=True, description='Total size occupied by all the backups of this client', default=0),
        'windows': fields.String(required=True, description='Is the client a windows machine', default='unknown'),
    })
    client_fields = ns.model('ClientsReport', {
        'name': fields.String(required=True, description='Client name'),
        'stats': fields.Nested(stats_fields, required=True),
    })
    backup_fields = ns.model('ClientsBackup', {
        'name': fields.String(required=True, description='Client name'),
        'number': fields.Integer(required=True, description='Number of backups on this client', default=0),
    })
    report_fields = ns.model('Report', {
        'backups': fields.Nested(backup_fields, as_list=True, required=True),
        'clients': fields.Nested(client_fields, as_list=True, required=True),
    })

    @api.cache.cached(timeout=1800, key_prefix=cache_key)
    @ns.marshal_with(report_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def get(self, server=None):
        """Returns a global report about all the clients of a given server

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "backups": [
                {
                  "name": "client1",
                  "number": 15
                },
                {
                  "name": "client2",
                  "number": 1
                }
              ],
              "clients": [
                {
                  "name": "client1",
                  "stats": {
                    "total": 296377,
                    "totsize": 57055793698,
                    "windows": "unknown"
                  }
                },
                {
                  "name": "client2",
                  "stats": {
                    "total": 3117,
                    "totsize": 5345361,
                    "windows": "true"
                  }
                }
              ]
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above
        """

        server = server or self.parser.parse_args()['serverName']
        self._check_acl(server)
        return self._get_clients_reports(server=server)

    def _check_acl(self, server):
        # Manage ACL
        if (not bui.standalone and bui.acl and
                (not self.is_admin and
                 server not in
                 bui.acl.servers(self.username))):
            self.abort(403, 'Sorry, you don\'t have any rights on this server')

    def _get_clients_reports(self, res=None, server=None):
        args = self.parser.parse_args()
        limit = args['limit']
        aggregation = self.translation.get(args['aggregation'], 'number')
        ret = self._parse_clients_reports(res, server)
        backups = backups_orig = ret.get('backups', [])
        clients = clients_orig = ret.get('clients', [])
        aggregate = False
        if limit > 1:
            limit -= 1
            aggregate = True
        # limit the number of elements to return so the graphs stay readable
        if len(backups) > limit and limit > 0:
            if aggregation == 'number':
                backups = (
                    sorted(backups, key=lambda x: x.get('number'), reverse=True)
                )[:limit]
            else:
                clients = (
                    sorted(clients, key=lambda x: x.get('stats', {}).get(aggregation), reverse=True)
                )[:limit]
        else:
            aggregate = False
        if aggregation == 'number':
            clients_name = [x.get('name') for x in backups]
            ret['backups'] = backups
            ret['clients'] = [
                x for x in clients_orig
                if x.get('name') in clients_name
            ]
        else:
            clients_name = [x.get('name') for x in clients]
            ret['clients'] = clients
            ret['backups'] = [
                x for x in backups_orig
                if x.get('name') in clients_name
            ]
        if aggregate:
            backups = {'name': 'others', 'number': 0}
            for client in backups_orig:
                if client.get('name') not in clients_name:
                    backups['number'] += client.get('number', 0)

            complement = {
                'name': 'others',
                'stats': {
                    'total': 0,
                    'totsize': 0,
                    'windows': None
                }
            }
            for client in clients_orig:
                if client.get('name') not in clients_name:
                    complement['stats']['total'] += client.get('stats', {}).get('total', 0)
                    complement['stats']['totsize'] += client.get('stats', {}).get('totsize', 0)
                    os = client.get('stats', {}).get('windows', 'unknown')
                    if not complement['stats']['windows']:
                        complement['stats']['windows'] = os
                    elif os != complement['stats']['windows']:
                        complement['stats']['windows'] = 'unknown'

            ret['clients'].append(complement)
            ret['backups'].append(backups)

        return ret

    def _parse_clients_reports(self, res=None, server=None):
        if not res:
            clients = []
            if bui.acl and not self.is_admin:
                clients = [{'name': x} for x in bui.acl.clients(self.username, server)]
            else:
                try:
                    clients = bui.client.get_all_clients(agent=server)
                except BUIserverException as e:
                    self.abort(500, str(e))
            return bui.client.get_clients_report(clients, server)
        if bui.standalone:
            ret = res
        else:
            ret = res.get(server, {})
        if bui.acl and not self.is_admin:
            ret['backups'] = [x for x in ret.get('backups', []) if bui.acl.is_client_allowed(self.username, x.get('name'), server)]
            ret['clients'] = [x for x in ret.get('clients', []) if bui.acl.is_client_allowed(self.username, x.get('name'), server)]
        return ret


@ns.route('/stats',
          '/<server>/stats',
          endpoint='clients_stats')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
    },
)
class ClientsStats(Resource):
    """The :class:`burpui.api.clients.ClientsStats` resource allows you to
    access general statistics about your clients.

    This resource is part of the :mod:`burpui.api.clients` module.

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
    client_fields = ns.model('ClientsStatsSingle', {
        'last': fields.DateTime(required=True, dt_format='iso8601', description='Date of last backup'),
        'human': fields.DateTimeHuman(required=True, attribute='last', description='Human readable date of the last backup'),
        'name': fields.String(required=True, description='Client name'),
        'state': fields.LocalizedString(required=True, description='Current state of the client (idle, backup, etc.)'),
        'phase': fields.String(description='Phase of the current running backup'),
        'percent': fields.Integer(description='Percentage done', default=0),
    })

    @api.cache.cached(timeout=1800, key_prefix=cache_key)
    @ns.marshal_list_with(client_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def get(self, server=None):
        """Returns a list of clients with their states

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              [
                {
                  "last": "2015-05-17 11:40:02",
                  "name": "client1",
                  "state": "idle",
                  "phase": "phase1",
                  "percent": 12,
                },
                {
                  "last": "never",
                  "name": "client2",
                  "state": "idle",
                  "phase": "phase2",
                  "percent": 42,
                }
              ]
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above
        """

        server = server or self.parser.parse_args()['serverName']
        try:
            if (not bui.standalone and
                    bui.acl and
                    (not self.is_admin and
                     server not in
                     bui.acl.servers(self.username))):
                self.abort(403, 'Sorry, you don\'t have any rights on this server')
            j = bui.client.get_all_clients(agent=server)
            if bui.acl and not self.is_admin:
                j = [x for x in j if x['name'] in bui.acl.clients(self.username, server)]
        except BUIserverException as e:
            self.abort(500, str(e))
        return j


@ns.route('/all',
          '/<server>/all',
          endpoint='clients_all')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
    },
)
class AllClients(Resource):
    """The :class:`burpui.api.clients.AllClients` resource allows you to
    retrieve a list of all clients with their associated server (if any).

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
    client_fields = ns.model('AllClients', {
        'name': fields.String(required=True, description='Client name'),
        'agent': fields.String(required=False, default=None, description='Associated Agent name'),
    })

    @api.cache.cached(timeout=1800, key_prefix=cache_key)
    @ns.marshal_list_with(client_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            200: 'Success',
            403: 'Insufficient permissions',
        },
    )
    def get(self, server=None):
        """Returns a list of all clients with their associated Agent if any

        **GET** method provided by the webservice.

        The *JSON* returned is:

        ::

            [
              {
                "name": "client1",
                "agent": "agent1"
              },
              {
                "name": "client2",
                "agent": "agent1"
              },
              {
                "name": "client3",
                "agent": "agent2"
              }
            ]


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above
        """
        ret = []
        args = self.parser.parse_args()
        server = server or args['serverName']

        if (server and bui.acl and not self.is_admin and
                server not in bui.acl.servers(self.username)):
            self.abort(403, "You are not allowed to view this server infos")

        if server:
            clients = bui.client.get_all_clients(agent=server)
            if bui.acl and not self.is_admin:
                ret = [{'name': x, 'agent': server} for x in bui.acl.clients(self.username, server)]
            else:
                ret = [{'name': x['name'], 'agent': server} for x in clients]
            return ret

        if bui.standalone:
            if bui.acl and not self.is_admin:
                ret = [{'name': x} for x in bui.acl.clients(self.username)]
            else:
                ret = [{'name': x['name']} for x in bui.client.get_all_clients()]
        else:
            grants = {}
            if bui.acl and not self.is_admin:
                for serv in bui.acl.servers(self.username):
                    grants[serv] = bui.acl.clients(self.username, serv)
            else:
                for serv in bui.client.servers:
                    grants[serv] = 'all'
            for (serv, clients) in iteritems(grants):
                if not isinstance(clients, list):
                    clients = [x['name'] for x in bui.client.get_all_clients(agent=serv)]
                ret += [{'name': x, 'agent': serv} for x in clients]

        return ret
