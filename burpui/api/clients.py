# -*- coding: utf8 -*-
"""
.. module:: clients
    :platform: Unix
    :synopsis: Burp-UI clients api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
from burpui.api import api
from burpui.misc.backend.interface import BUIserverException
from flask.ext.restful import reqparse, Resource
from flask.ext.login import current_user, login_required
from flask import jsonify, make_response


@api.resource('/api/running-clients.json',
              '/api/<server>/running-clients.json',
              '/api/running-clients.json/<client>',
              '/api/<server>/running-clients.json/<client>',
              endpoint='api.running_clients')
class RunningClients(Resource):
    """
    The :class:`burpui.api.clients.RunningClients` resource allows you to
    retrieve a list of clients that are currently running a backup.

    This resource is part of the :mod:`burpui.api.clients` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, client=None, server=None):
        """
        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
                "results": [ ]
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param client: Ask a specific client in order to know if it is running a backup
        :type client: str

        :returns: The *JSON* described above.
        """
        if not server:
            server = self.parser.parse_args()['server']
        if client:
            if api.bui.acl:
                if (not api.bui.acl.is_admin(current_user.name) and not
                        api.bui.acl.is_client_allowed(current_user.name,
                                                      client,
                                                      server)):
                    r = []
                    return jsonify(results=r)
            if api.bui.cli.is_backup_running(client, server):
                r = [client]
                return jsonify(results=r)
            else:
                r = []
                return jsonify(results=r)

        r = api.bui.cli.is_one_backup_running(server)
        # Manage ACL
        if (api.bui.acl and not
                api.bui.acl.is_admin(current_user.name)):
            if isinstance(r, dict):
                new = {}
                for serv in api.bui.acl.servers(current_user.name):
                    allowed = api.bui.acl.clients(current_user.name, serv)
                    new[serv] = [x for x in r[serv] if x in allowed]
                r = new
            else:
                allowed = api.bui.acl.clients(current_user.name, server)
                r = [x for x in r if x in allowed]
        return jsonify(results=r)


@api.resource('/api/running.json',
              '/api/<server>/running.json',
              endpoint='api.running_backup')
class RunningBackup(Resource):
    """
    The :class:`burpui.api.clients.RunningBackup` resource allows you to access
    the status of the server in order to know if there is a running backup
    currently.

    This resource is part of the :mod:`burpui.api.clients` module.
    """

    @login_required
    def get(self, server=None):
        """
        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
                "results": false
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above.
        """
        j = api.bui.cli.is_one_backup_running(server)
        # Manage ACL
        if (api.bui.acl and not
                api.bui.acl.is_admin(current_user.name)):
            if isinstance(j, dict):
                new = {}
                for serv in api.bui.acl.servers(current_user.name):
                    allowed = api.bui.acl.clients(current_user.name, serv)
                    new[serv] = [x for x in j[serv] if x in allowed]
                j = new
            else:
                allowed = api.bui.acl.clients(current_user.name, server)
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


@api.resource('/api/clients-report.json',
              '/api/<server>/clients-report.json',
              endpoint='api.clients_report')
class ClientsReport(Resource):
    """
    The :class:`burpui.api.clients.ClientsReport` resource allows you to access
    general reports about your clients.

    This resource is part of the :mod:`burpui.api.clients` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, server=None):
        """
        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "results": [
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
                        "windows": "false"
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
              ]
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above
        """

        if not server:
            server = self.parser.parse_args()['server']
        j = []
        try:
            # Manage ACL
            if (not api.bui.standalone and api.bui.acl and
                    (not api.bui.acl.is_admin(current_user.name) and
                     server not in
                     api.bui.acl.servers(current_user.name))):
                raise BUIserverException('Sorry, you don\'t have rights on this server')
            clients = api.bui.cli.get_all_clients(agent=server)
        except BUIserverException as e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        cl = []
        ba = []
        # Filter only allowed clients
        allowed = []
        check = False
        if (api.bui.acl and not
                api.bui.acl.is_admin(current_user.name)):
            check = True
            allowed = api.bui.acl.clients(current_user.name, server)
        aclients = []
        for c in clients:
            if check and c['name'] not in allowed:
                continue
            aclients.append(c)
        j = api.bui.cli.get_clients_report(aclients, server)
        return jsonify(results=j)


@api.resource('/api/clients.json',
              '/api/<server>/clients.json',
              endpoint='api.clients_stats')
class ClientsStats(Resource):
    """
    The :class:`burpui.api.clients.ClientsStats` resource allows you to access
    general statistics about your clients.

    This resource is part of the :mod:`burpui.api.clients` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, server=None):
        """
        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "results": [
                {
                  "last": "2015-05-17 11:40:02",
                  "name": "client1",
                  "state": "idle"
                },
                {
                  "last": "never",
                  "name": "client2",
                  "state": "idle"
                }
              ]
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above
        """

        if not server:
            server = self.parser.parse_args()['server']
        try:
            if (not api.bui.standalone and
                    api.bui.acl and
                    (not api.bui.acl.is_admin(current_user.name) and
                     server not in
                     api.bui.acl.servers(current_user.name))):
                raise BUIserverException('Sorry, you don\'t have any rights on this server')
            j = api.bui.cli.get_all_clients(agent=server)
            if (api.bui.acl and not
                    api.bui.acl.is_admin(current_user.name)):
                j = [x for x in j if x['name'] in api.bui.acl.clients(current_user.name, server)]
        except BUIserverException as e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        return jsonify(results=j)
