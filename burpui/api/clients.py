# -*- coding: utf8 -*-
"""
.. module:: burpui.api.clients
    :platform: Unix
    :synopsis: Burp-UI clients api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask import current_app, g
from flask_login import current_user

from ..decorators import browser_cache
from ..engines.server import BUIServer  # noqa
from ..exceptions import BUIserverException
from ..ext.cache import cache
from ..filter import mask
from . import api, cache_key, force_refresh
from .client import ClientLabels
from .custom import Resource, fields

bui = current_app  # type: BUIServer
ns = api.namespace("clients", "Clients methods")


@ns.route(
    "/running",
    "/<server>/running",
    "/running/<client>",
    "/<server>/running/<client>",
    endpoint="running_clients",
)
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
        "client": "Client name",
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
    parser.add_argument(
        "serverName", help="Which server to collect data from when in multi-agent mode"
    )

    @ns.expect(parser)
    def get(self, client=None, server=None):
        """Returns a list of clients currently running a backup

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            [
              'client1',
              'client2'
            ]


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to see.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param client: Ask a specific client in order to know if it is running a backup
        :type client: str

        :returns: The *JSON* described above.
        """
        server = server or self.parser.parse_args()["serverName"]
        return self._running_clients(None, client, server)

    def _running_clients(self, res, client, server):
        if client:
            if mask.has_filters(current_user):
                if not mask.is_client_allowed(current_user, client):
                    return []

            if bui.client.is_backup_running(client, server):
                return [client]
            else:
                return []

        running = res or bui.client.is_one_backup_running(server)
        # Manage ACL
        if mask.has_filters(current_user):
            if isinstance(running, dict):
                ret = {}

                def __extract_running_clients(serv):
                    try:
                        clients = [
                            x["name"]
                            for x in bui.client.get_all_clients(
                                serv, last_attempt=False
                            )
                        ]
                    except BUIserverException:
                        clients = []
                    allowed = [
                        x
                        for x in clients
                        if mask.is_client_allowed(current_user, x, serv)
                    ]
                    return [x for x in running[serv] if x in allowed]

                if server:
                    return __extract_running_clients(server)

                for serv in bui.client.servers:
                    ret[serv] = __extract_running_clients(serv)
                return ret
            else:
                try:
                    clients = [
                        x["name"]
                        for x in bui.client.get_all_clients(server, last_attempt=False)
                    ]
                except BUIserverException:
                    clients = []
                allowed = [
                    x
                    for x in clients
                    if mask.is_client_allowed(current_user, x, server)
                ]
                running = [x for x in running if x in allowed]
        elif server and isinstance(running, dict):
            return running.get(server, [])
        return running


@ns.route("/backup-running", "/<server>/backup-running", endpoint="running_backup")
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
    }
)
class RunningBackup(Resource):
    """The :class:`burpui.api.clients.RunningBackup` resource allows you to
    access the status of the server in order to know if there is a running
    backup currently.

    This resource is part of the :mod:`burpui.api.clients` module.
    """

    running_fields = ns.model(
        "Running",
        {
            "running": fields.Boolean(
                required=True, description="Is there a backup running right now"
            ),
        },
    )

    @ns.marshal_with(running_fields, code=200, description="Success")
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
            "running": self._is_one_backup_running(
                bui.client.is_one_backup_running(server), server
            )
        }

    def _is_one_backup_running(self, res, server):
        """Check if a backup is running"""
        # Manage ACL
        if mask.has_filters(current_user):
            if isinstance(res, dict):
                new = {}
                for serv in bui.client.servers:
                    try:
                        clients = [
                            x["name"]
                            for x in bui.client.get_all_clients(
                                serv, last_attempt=False
                            )
                        ]
                    except BUIserverException:
                        clients = []
                    allowed = [
                        x
                        for x in clients
                        if mask.is_client_allowed(current_user, x, serv)
                    ]
                    new[serv] = [x for x in res[serv] if x in allowed]
                res = new
            else:
                try:
                    clients = [
                        x["name"]
                        for x in bui.client.get_all_clients(server, last_attempt=False)
                    ]
                except BUIserverException:
                    clients = []
                allowed = [
                    x
                    for x in clients
                    if mask.is_client_allowed(current_user, x, server)
                ]
                res = [x for x in res if x in allowed]
        running = False
        if isinstance(res, dict):
            for _, run in res.items():
                running = running or (len(run) > 0)
                if running:
                    break
        else:
            running = len(res) > 0

        return running


@ns.route("/report", "/<server>/report", endpoint="clients_report")
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
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
    parser.add_argument(
        "serverName", help="Which server to collect data from when in multi-agent mode"
    )
    parser.add_argument(
        "limit", type=int, default=8, help="Number of elements to return"
    )
    parser.add_argument(
        "aggregation",
        help="What aggregation to operate",
        default="number",
        choices=("number", "files", "size", "none"),
    )

    translation = {
        "number": "number",
        "files": "total",
        "size": "totsize",
    }

    stats_fields = ns.model(
        "ClientsStats",
        {
            "total": fields.Integer(
                required=True, description="Number of files", default=0
            ),
            "totsize": fields.Integer(
                required=True,
                description="Total size occupied by all the backups of this client",
                default=0,
            ),
            "os": fields.String(
                required=True, description="OS of the client", default="unknown"
            ),
        },
    )
    client_fields = ns.model(
        "ClientsReport",
        {
            "name": fields.String(required=True, description="Client name"),
            "stats": fields.Nested(stats_fields, required=True),
        },
    )
    backup_fields = ns.model(
        "ClientsBackup",
        {
            "name": fields.String(required=True, description="Client name"),
            "number": fields.Integer(
                required=True, description="Number of backups on this client", default=0
            ),
        },
    )
    report_fields = ns.model(
        "Report",
        {
            "backups": fields.Nested(backup_fields, as_list=True, required=True),
            "clients": fields.Nested(client_fields, as_list=True, required=True),
        },
    )

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_with(report_fields, code=200, description="Success")
    @ns.expect(parser)
    @ns.doc(
        responses={
            403: "Insufficient permissions",
            500: "Internal failure",
        },
    )
    @browser_cache(1800)
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
                    "os": "unknown"
                  }
                },
                {
                  "name": "client2",
                  "stats": {
                    "total": 3117,
                    "totsize": 5345361,
                    "os": "windows"
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

        server = server or self.parser.parse_args()["serverName"]
        self._check_acl(server)
        return self._get_clients_reports(server=server)

    def _check_acl(self, server):
        # Manage ACL
        if (
            not bui.config["STANDALONE"]
            and not current_user.is_anonymous
            and (
                not current_user.acl.is_admin()
                and not current_user.acl.is_server_allowed(server)
            )
        ):
            self.abort(403, "Sorry, you don't have any rights on this server")

    def _get_clients_reports(self, res=None, server=None):
        args = self.parser.parse_args()
        limit = args["limit"]
        aggregation = self.translation.get(args["aggregation"], "number")
        ret = self._parse_clients_reports(res, server)
        backups = backups_orig = ret.get("backups", [])
        clients = clients_orig = ret.get("clients", [])
        aggregate = False
        if limit > 1:
            limit -= 1
            aggregate = True
        if aggregation == "none":
            aggregate = False
            limit = 0
        # limit the number of elements to return so the graphs stay readable
        if len(backups) > limit and limit > 0:
            if aggregation == "number":
                backups = (
                    sorted(backups, key=lambda x: x.get("number"), reverse=True)
                )[:limit]
            else:
                clients = (
                    sorted(
                        clients,
                        key=lambda x: x.get("stats", {}).get(aggregation),
                        reverse=True,
                    )
                )[:limit]
        else:
            aggregate = False
        if aggregation == "number":
            clients_name = [x.get("name") for x in backups]
            ret["backups"] = backups
            ret["clients"] = [x for x in clients_orig if x.get("name") in clients_name]
        else:
            clients_name = [x.get("name") for x in clients]
            ret["clients"] = clients
            ret["backups"] = [x for x in backups_orig if x.get("name") in clients_name]
        if aggregate:
            backups = {"name": "others", "number": 0}
            for client in backups_orig:
                if client.get("name") not in clients_name:
                    backups["number"] += client.get("number", 0)

            complement = {
                "name": "others",
                "stats": {"total": 0, "totsize": 0, "os": None},
            }
            # TODO: fix OS aggregation
            for client in clients_orig:
                if client.get("name") not in clients_name:
                    complement["stats"]["total"] += client.get("stats", {}).get(
                        "total", 0
                    )
                    complement["stats"]["totsize"] += client.get("stats", {}).get(
                        "totsize", 0
                    )
                    os = client.get("stats", {}).get("os", "unknown")
                    if not complement["stats"]["os"]:
                        complement["stats"]["os"] = os
                    elif os != complement["stats"]["os"]:
                        complement["stats"]["os"] = "unknown"

            ret["clients"].append(complement)
            ret["backups"].append(backups)

        return ret

    def _parse_clients_reports(self, res=None, server=None):
        if not res:
            try:
                clients = bui.client.get_all_clients(agent=server, last_attempt=False)
            except BUIserverException as e:
                self.abort(500, str(e))
            if mask.has_filters(current_user):
                clients = [
                    x
                    for x in clients
                    if mask.is_client_allowed(current_user, x["name"], server)
                ]
            return bui.client.get_clients_report(clients, server)
        if bui.config["STANDALONE"]:
            ret = res
        else:
            ret = res.get(server, {})
        if mask.has_filters(current_user):
            ret["backups"] = [
                x
                for x in ret.get("backups", [])
                if mask.is_client_allowed(current_user, x.get("name"), server)
            ]
            ret["clients"] = [
                x
                for x in ret.get("clients", [])
                if mask.is_client_allowed(current_user, x.get("name"), server)
            ]
        return ret


@ns.route("/stats", "/<server>/stats", endpoint="clients_stats")
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
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
    parser.add_argument(
        "serverName", help="Which server to collect data from when in multi-agent mode"
    )
    client_fields = ns.model(
        "ClientsStatsSingle",
        {
            "last": fields.DateTime(
                required=True, dt_format="iso8601", description="Date of last backup"
            ),
            "last_attempt": fields.DateTime(
                dt_format="iso8601", description="Date of last backup attempt"
            ),
            "name": fields.String(required=True, description="Client name"),
            "state": fields.LocalizedString(
                required=True,
                description="Current state of the client (idle, backup, etc.)",
            ),
            "phase": fields.String(description="Phase of the current running backup"),
            "percent": fields.Integer(description="Percentage done", default=0),
            "labels": fields.List(fields.String, description="List of labels"),
        },
    )

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_list_with(client_fields, code=200, description="Success")
    @ns.expect(parser)
    @ns.doc(
        responses={
            403: "Insufficient permissions",
            500: "Internal failure",
        },
    )
    @browser_cache(1800)
    def get(self, server=None):
        """Returns a list of clients with their states

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              [
                {
                  "last": "2015-05-17 11:40:02",
                  "last_attempt": "2015-05-17 11:40:02",
                  "name": "client1",
                  "state": "idle",
                  "phase": "phase1",
                  "percent": 12,
                  "labels": [
                    "toto"
                  ]
                },
                {
                  "last": "never",
                  "last_attempt": "never",
                  "name": "client2",
                  "state": "idle",
                  "phase": "phase2",
                  "percent": 42,
                  "labels": [
                    "titi"
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

        server = server or self.parser.parse_args()["serverName"]
        try:
            if (
                not bui.config["STANDALONE"]
                and not current_user.is_anonymous
                and (
                    not current_user.acl.is_admin()
                    and not current_user.acl.is_server_allowed(server)
                )
            ):
                self.abort(403, "Sorry, you don't have any rights on this server")
            jso = bui.client.get_all_clients(agent=server)
            if mask.has_filters(current_user):
                jso = [
                    x
                    for x in jso
                    if mask.is_client_allowed(current_user, x["name"], server)
                ]
        except BUIserverException as e:
            self.abort(500, str(e))
        ret = []
        for client in jso:
            tmp_client = client
            try:
                labels = ClientLabels._get_labels(client["name"], server)
            except BUIserverException as exp:
                self.abort(500, str(exp))
            tmp_client["labels"] = labels
            ret.append(tmp_client)
            if tmp_client["state"] != "idle":
                g.DONOTCACHE = True

        return ret


@ns.route("/all", "/<server>/all", endpoint="clients_all")
@ns.doc(
    params={
        "server": "Which server to collect data from when in multi-agent mode",
    },
)
class AllClients(Resource):
    """The :class:`burpui.api.clients.AllClients` resource allows you to
    retrieve a list of all clients with their associated server (if any).

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """

    parser = ns.parser()
    parser.add_argument(
        "serverName", help="Which server to collect data from when in multi-agent mode"
    )
    parser.add_argument(
        "user", help="For which user do we want the data (only works for admins"
    )
    client_fields = ns.model(
        "AllClients",
        {
            "name": fields.String(required=True, description="Client name"),
            "agent": fields.String(
                required=False, default=None, description="Associated Agent name"
            ),
        },
    )

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_list_with(client_fields, code=200, description="Success")
    @ns.expect(parser)
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
        },
    )
    @browser_cache(1800)
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
        is_admin = True
        args = self.parser.parse_args()
        server = server or args["serverName"]

        is_admin = current_user.is_anonymous or current_user.acl.is_admin()
        is_moderator = current_user.is_anonymous or current_user.acl.is_moderator()

        user = (
            (args.get("user", current_user.name) or current_user.name)
            if is_admin or is_moderator
            else current_user.name
        )

        # drop privileges when switching user
        if user != current_user.name:
            is_admin = False
            is_moderator = False

        if (
            server
            and not is_admin
            and not is_moderator
            and not current_user.acl.is_server_allowed(server)
        ):
            self.abort(403, "You are not allowed to view this server infos")

        if server:
            try:
                clients = [
                    x["name"]
                    for x in bui.client.get_all_clients(
                        agent=server, last_attempt=False
                    )
                ]
            except BUIserverException:
                clients = []
            if not is_admin:
                # use the bui.acl module since we impersonalized the user
                ret = [
                    {"name": x, "agent": server}
                    for x in clients
                    if bui.acl.is_client_allowed(user, x, server)
                ]
            else:
                ret = [{"name": x, "agent": server} for x in clients]
            return ret

        if bui.config["STANDALONE"]:
            try:
                clients = [
                    x["name"] for x in bui.client.get_all_clients(last_attempt=False)
                ]
            except BUIserverException:
                clients = []
            if not is_admin:
                ret = [
                    {"name": x} for x in clients if bui.acl.is_client_allowed(user, x)
                ]
            else:
                ret = [{"name": x} for x in clients]
        else:
            grants = {}
            clients_cache = {}
            for serv in bui.client.servers:
                try:
                    clients = [
                        x["name"]
                        for x in bui.client.get_all_clients(serv, last_attempt=False)
                    ]
                    clients_cache[serv] = clients
                except BUIserverException:
                    clients = []
            if not is_admin:
                for serv in bui.client.servers:
                    grants[serv] = [
                        x
                        for x in clients_cache.get(serv, [])
                        if bui.acl.is_client_allowed(user, x, serv)
                    ]
            else:
                for serv in bui.client.servers:
                    grants[serv] = "all"
            for serv, clients in grants.items():
                if not isinstance(clients, list):
                    clients = clients_cache.get(serv, [])
                ret += [{"name": x, "agent": serv} for x in clients]

        return ret
