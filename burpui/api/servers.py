# -*- coding: utf8 -*-

# This is a submodule we can also use "from ..api import api"
from . import api
from ..exceptions import BUIserverException

from future.utils import iteritems
from flask.ext.restplus import Resource, fields
from flask.ext.login import current_user

ns = api.namespace('servers', 'Servers methods')


@ns.route('/servers.json', endpoint='servers_stats')
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

    @api.marshal_list_with(servers_fields, code=200, description='Success')
    @api.doc(
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


        :returns: The *JSON* described above.
        """

        r = []
        if hasattr(api.bui.cli, 'servers'):  # pragma: no cover
            check = False
            allowed = []
            if (api.bui.acl and not
                    api.bui.acl.is_admin(current_user.get_id())):
                check = True
                allowed = api.bui.acl.servers(current_user.get_id())
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
                    api.abort(500, str(e))
        return r


@ns.route('/live.json',
          '/<server>/live.json',
          endpoint='live')
class Live(Resource):
    """The :class:`burpui.api.servers.Live` resource allows you to
    retrieve a list of servers that are currently *alive*.

    This resource is part of the :mod:`burpui.api.servers` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    """
    parser = api.parser()
    parser.add_argument('server', type=str, help='Which server to collect data from when in multi-agent mode')
    counters_fields = api.model('Counters', {
        'phase': fields.Integer(description='Backup phase'),
        'Total': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'Files': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'Files (encrypted)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'Metadata': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'Metadata (enc)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'Directories': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'Softlink': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'Hardlink': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'Special files': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'VSS header': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'VSS header (enc)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'VSS footer': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'VSS footer (enc)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'Grand total': fields.List(fields.Integer, description='new/deleted/scanned/unchanged'),
        'warning': fields.Integer(description='Number of warnings so far'),
        'estimated_bytes': fields.Integer(description='Estimated Bytes in backup'),
        'bytes': fields.Integer(description='Bytes in backup'),
        'bytes_in': fields.Integer(description='Bytes received since backup started'),
        'bytes_out': fields.Integer(description='Bytes sent since backup started'),
        'start': fields.String(description='Timestamp of the start date of the backup'),
        'path': fields.String(description='File that is currently treated by burp'),
    })
    live_fields = api.model('Live', {
        'client': fields.String(required=True, description='Client name'),
        'agent': fields.String(description='Server (agent) name'),
        'status': fields.Nested(counters_fields, description='Various statistics about the running backup'),
    })

    @api.marshal_list_with(live_fields, code=200, description='Success')
    @api.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
        },
        parser=parser
    )
    def get(self, server=None):
        """Returns a list of clients that are currently running a backup

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            [
              {
                'client': 'client1',
                'agent': 'burp1',
                'status': {
                    'phase': 2,
                    'path': '/etc/some/configuration',
                    '...': '...',
                },
              },
              {
                'client': 'client12',
                'agent': 'burp2',
                'status': {
                    'phase': 3,
                    'path': '/etc/some/other/configuration',
                    '...': '...',
                },
              },

        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above
        """

        if not server:
            server = self.parser.parse_args()['server']
        r = []
        if server:
            l = (api.bui.cli.is_one_backup_running(server))[server]
        else:
            l = api.bui.cli.is_one_backup_running()
        if isinstance(l, dict):  # pragma: no cover
            for (k, a) in iteritems(l):
                for c in a:
                    s = {}
                    s['client'] = c
                    s['agent'] = k
                    try:
                        s['status'] = api.bui.cli.get_counters(c, agent=k)
                    except BUIserverException:
                        s['status'] = []
                    r.append(s)
        else:  # pragma: no cover
            for c in l:
                s = {}
                s['client'] = c
                try:
                    s['status'] = api.bui.cli.get_counters(c, agent=server)
                except BUIserverException:
                    s['status'] = []
                r.append(s)
        return r
