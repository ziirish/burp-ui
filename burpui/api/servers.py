# -*- coding: utf8 -*-

# This is a submodule we can also use "from ..api import api"
from . import api, cache_key, parallel_loop
from ..exceptions import BUIserverException

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

    @api.cache.cached(timeout=1800, key_prefix=cache_key)
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
            allowed = []
            if (api.bui.acl and not
                    api.bui.acl.is_admin(current_user.get_id())):
                allowed = api.bui.acl.servers(current_user.get_id())

            def get_servers_info(serv, output, allowed, username):
                try:
                    if allowed and serv in allowed:
                        output.put({
                            'name': serv,
                            'clients': len(api.bui.acl.clients(username, serv)),
                            'alive': api.bui.cli.servers[serv].ping()
                        })
                        return
                    elif not allowed:
                        output.put({
                            'name': serv,
                            'clients': len(api.bui.cli.servers[serv].get_all_clients(serv)),
                            'alive': api.bui.cli.servers[serv].ping()
                        })
                        return
                    output.put(None)
                except BUIserverException as e:
                    output.put(str(e))

            r = parallel_loop(get_servers_info, api.bui.cli.servers, allowed, current_user.get_id())

        return r
