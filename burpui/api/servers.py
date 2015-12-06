# -*- coding: utf8 -*-

# This is a submodule we can also use "from ..api import api"
from . import api
from ..exceptions import BUIserverException

from flask.ext.restplus import Resource, fields
from flask.ext.login import current_user
import multiprocessing

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

            def get_server_infos(serv, output):
                try:
                    if check:
                        if serv in allowed:
                            output.put({
                                'name': serv,
                                'clients': len(api.bui.cli.servers[serv].get_all_clients(serv)),
                                'alive': api.bui.cli.servers[serv].ping()
                            })
                            return
                    else:
                        output.put({
                            'name': serv,
                            'clients': len(api.bui.cli.servers[serv].get_all_clients(serv)),
                            'alive': api.bui.cli.servers[serv].ping()
                        })
                        return
                    output.put(None)
                except BUIserverException as e:
                    output.put(str(e))

            output = multiprocessing.Queue()
            pools = [multiprocessing.Process(target=get_server_infos, args=(s, output)) for s in api.bui.cli.servers]
            for p in pools:
                p.start()

            for p in pools:
                p.join()

            for p in pools:
                tmp = output.get()
                if tmp and isinstance(tmp, dict):
                    r.append(tmp)
                elif tmp:
                    api.abort(500, tmp)

        return r
