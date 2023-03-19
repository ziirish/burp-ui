# -*- coding: utf8 -*-

# This is a submodule we can also use "from ..api import api"
from flask import current_app, g
from flask_login import current_user

from ..decorators import browser_cache
from ..engines.server import BUIServer  # noqa
from ..exceptions import BUIserverException
from ..ext.cache import cache
from ..filter import mask
from . import api, cache_key, force_refresh
from .custom import Resource, fields

bui = current_app  # type: BUIServer
ns = api.namespace("servers", "Servers methods")


@ns.route("/stats", endpoint="servers_stats")
class ServersStats(Resource):
    """The :class:`burpui.api.servers.ServersStats` resource allows you to
    retrieve statistics about servers/agents.

    This resource is part of the :mod:`burpui.api.servers` module.
    """

    servers_fields = ns.model(
        "Servers",
        {
            "alive": fields.Boolean(
                required=True, description="Is the server reachable"
            ),
            "clients": fields.Integer(
                required=True, description="Number of clients managed by this server"
            ),
            "name": fields.String(required=True, description="Server name"),
        },
    )

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_list_with(servers_fields, code=200, description="Success")
    @ns.doc(
        responses={
            500: "Internal failure",
        },
    )
    @browser_cache(1800)
    def get(self):
        """Returns a list of servers (agents) with basic stats

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            [
              {
                'alive': true,
                'clients': 2,
                'name': 'burp1'
              },
              {
                'alive': false,
                'clients': 0,
                'name': 'burp2'
              }
            ]


        :returns: The *JSON* described above.
        """

        r = []
        check = False

        if bui.config["STANDALONE"]:
            return r

        if not current_user.is_anonymous and mask.has_filters(current_user):
            check = True

        for serv in bui.client.servers:
            try:
                alive = bui.client.servers[serv].ping()
            except BUIserverException:
                alive = False
                g.DONOTCACHE = True

            try:
                clients = bui.client.servers[serv].get_all_clients(
                    serv, last_attempt=False
                )
            except BUIserverException:
                clients = []

            if check and mask.is_server_allowed(current_user, serv):
                allowed_clients = [
                    x
                    for x in clients
                    if mask.is_client_allowed(current_user, x["name"], serv)
                ]
                r.append(
                    {"name": serv, "clients": len(allowed_clients), "alive": alive}
                )
            elif not check:
                r.append({"name": serv, "clients": len(clients), "alive": alive})

        return r


@ns.route("/report", endpoint="servers_report")
class ServersReport(Resource):
    """The :class:`burpui.api.servers.ServersReport` resource allows you to
    retrieve a report about servers/agents.

    This resource is part of the :mod:`burpui.api.servers` module.
    """

    wild = fields.Wildcard(
        fields.Integer,
        required=False,
        description="Total number of clients of a given OS",
    )
    os_fields = ns.model(
        "OS",
        {
            "*": wild,
        },
    )
    stats_fields = ns.model(
        "ServersStats",
        {
            "total": fields.Integer(
                required=True, description="Number of files", default=0
            ),
            "totsize": fields.Integer(
                required=True,
                description="Total size occupied by all the backups of this server",
                default=0,
            ),
            "os": fields.Nested(os_fields),
        },
    )
    server_fields = ns.model(
        "ServersReport",
        {
            "name": fields.String(required=True, description="Server name"),
            "number": fields.Nested(stats_fields, required=True),
        },
    )
    backup_fields = ns.model(
        "ServersBackup",
        {
            "name": fields.String(required=True, description="Server name"),
            "number": fields.Integer(
                required=True, description="Number of backups on this server", default=0
            ),
        },
    )
    report_fields = ns.model(
        "ServersReportFull",
        {
            "backups": fields.Nested(backup_fields, as_list=True, required=True),
            "servers": fields.Nested(server_fields, as_list=True, required=True),
        },
    )

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_with(report_fields, code=200, description="Success")
    @ns.doc(
        responses={
            403: "Insufficient permissions",
            500: "Internal failure",
        },
    )
    @browser_cache(1800)
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
                  "number": {
                    "os": {
                      "linux": 4
                    },
                    "total": 349705,
                    "totsize": 119400711726
                  }
                }
              ]
            }

        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients/servers you are authorized to.

        :returns: The *JSON* described above.
        """
        r = {}
        check = False
        if not current_user.is_anonymous and mask.has_filters(current_user):
            check = True

        backups = []
        servers = []
        try:
            for serv in bui.client.servers:
                out = {
                    "name": serv,
                    "stats": {"total": 0, "totsize": 0, "os": {}},
                    "number": 0,
                }
                if check and not mask.is_server_allowed(current_user, serv):
                    continue
                try:
                    clients = bui.client.get_all_clients(agent=serv, last_attempt=False)
                except BUIserverException:
                    continue
                if check:
                    clients = [
                        x
                        for x in clients
                        if mask.is_client_allowed(current_user, x["name"], serv)
                    ]

                j = bui.client.get_clients_report(clients, serv)
                if "clients" not in j or "backups" not in j:
                    continue

                os = {}
                for stats in j["clients"]:
                    for key in ["total", "totsize"]:
                        out["stats"][key] += stats["stats"][key]
                    if stats["stats"]["os"] in os:
                        os[stats["stats"]["os"]] += 1
                    else:
                        os[stats["stats"]["os"]] = 1

                for key, val in os.items():
                    out["stats"]["os"][key] = val

                for bkp in j["backups"]:
                    out["number"] += bkp["number"]

                backups.append({"name": serv, "number": out["number"]})
                servers.append({"name": serv, "number": out["stats"]})

        except BUIserverException as e:
            self.abort(500, str(e))

        r["backups"] = backups
        r["servers"] = servers

        return r
