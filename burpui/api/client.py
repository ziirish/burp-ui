# -*- coding: utf8 -*-
"""
.. module:: burpui.api.client
    :platform: Unix
    :synopsis: Burp-UI client api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
# This is a submodule we can also use "from ..api import api"
from . import api, cache_key
from ..exceptions import BUIserverException
from flask.ext.restplus import Resource, fields
from flask.ext.login import current_user

ns = api.namespace('client', 'Client methods')


@ns.route('/client-tree.json/<name>/<int:backup>',
          '/<server>/client-tree.json/<name>/<int:backup>',
          endpoint='client_tree')
class ClientTree(Resource):
    """The :class:`burpui.api.client.ClientTree` resource allows you to
    retrieve a list of files in a given backup.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    A mandatory ``GET`` parameter called ``root`` is used to know what path we
    are working on.
    """
    parser = api.parser()
    parser.add_argument('server', type=str, help='Which server to collect data from when in multi-agent mode')
    parser.add_argument('root', type=str, help='Root path to expand')
    node_fields = api.model('ClientTree', {
        'date': fields.String(required=True, description='Human representation of the backup date'),
        'gid': fields.Integer(required=True, description='gid owner of the node'),
        'inodes': fields.Integer(required=True, description='Inodes of the node'),
        'mode': fields.String(required=True, description='Human readable mode. Example: "drwxr-xr-x"'),
        'name': fields.String(required=True, description='Node name'),
        'parent': fields.String(required=True, description='Parent node name'),
        'size': fields.String(required=True, description='Human readable size. Example: "12.0KiB"'),
        'type': fields.String(required=True, description='Node type. Example: "d"'),
        'uid': fields.Integer(required=True, description='uid owner of the node'),
    })

    @api.cache.cached(timeout=120, key_prefix=cache_key)
    @api.marshal_list_with(node_fields, code=200, description='Success')
    @api.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
            'name': 'Client name',
            'backup': 'Backup number',
            'root': 'Root path to expand',
        },
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
        parser=parser
    )
    def get(self, server=None, name=None, backup=None):
        """Returns a list of 'nodes' under a given path

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            [
              {
                "date": "2015-05-21 14:54:49",
                "gid": "0",
                "inodes": "173",
                "mode": "drwxr-xr-x",
                "name": "/",
                "parent": "",
                "size": "12.0KiB",
                "type": "d",
                "uid": "0"
              },
            ]


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :param backup: The backup we are working on
        :type backup: int

        :returns: The *JSON* described above.
        """
        if not server:
            server = self.parser.parse_args()['server']
        j = []
        if not name or not backup:  # pargma: no cover
            return j
        root = self.parser.parse_args()['root']
        try:
            if (api.bui.acl and
                    (not api.bui.acl.is_admin(current_user.get_id()) and not
                     api.bui.acl.is_client_allowed(current_user.get_id(),
                                                   name,
                                                   server))):
                api.abort(403, 'Sorry, you are not allowed to view this client')
            j = api.bui.cli.get_tree(name, backup, root, agent=server)
        except BUIserverException as e:
            api.abort(500, str(e))
        return j


@ns.route('/client-stats.json/<name>',
          '/<server>/client-stats.json/<name>',
          '/client-stats.json/<name>/<int:backup>',
          '/<server>/client-stats.json/<name>/<int:backup>',
          endpoint='client_stats')
class ClientStats(Resource):
    """The :class:`burpui.api.client.ClientStats` resource allows you to
    retrieve a statistics on a given backup for a given client.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    """
    parser = api.parser()
    parser.add_argument('server', type=str, help='Which server to collect data from when in multi-agent mode')
    stats_tpl_fields = api.model('ClientStatsTpl', {
        'changed': fields.Integer(required=True, description='Number of changed files'),
        'deleted': fields.Integer(required=True, description='Number of deleted files'),
        'new': fields.Integer(required=True, description='Number of new files'),
        'scanned': fields.Integer(required=True, description='Number of scanned files'),
        'total': fields.Integer(required=True, description='Total number of files'),
        'unchanged': fields.Integer(required=True, description='Number of scanned files'),
    })
    stats_fields = api.model('ClientStats', {
        'dir': fields.Nested(stats_tpl_fields, required=True),
        'duration': fields.Integer(required=True, description='Backup duration in seconds'),
        'efs': fields.Nested(stats_tpl_fields, required=True),
        'encrypted': fields.Boolean(required=True, description='Is the backup encrypted'),
        'end': fields.Integer(required=True, description='Timestamp of the end date of the backup'),
        'files': fields.Nested(stats_tpl_fields, required=True),
        'files_enc': fields.Nested(stats_tpl_fields, required=True),
        'hardlink': fields.Nested(stats_tpl_fields, required=True),
        'meta': fields.Nested(stats_tpl_fields, required=True),
        'meta_enc': fields.Nested(stats_tpl_fields, required=True),
        'number': fields.Integer(required=True, description='Backup number'),
        'received': fields.Integer(required=True, description='Bytes received'),
        'softlink': fields.Nested(stats_tpl_fields, required=True),
        'special': fields.Nested(stats_tpl_fields, required=True),
        'start': fields.Integer(required=True, description='Timestamp of the beginning of the backup'),
        'totsize': fields.Integer(required=True, description='Total size of the backup'),
        'vssfooter': fields.Nested(stats_tpl_fields, required=True),
        'vssfooter_enc': fields.Nested(stats_tpl_fields, required=True),
        'vssheader': fields.Nested(stats_tpl_fields, required=True),
        'vssheader_enc': fields.Nested(stats_tpl_fields, required=True),
        'windows': fields.Boolean(required=True, description='Is the client a windows system'),
    })

    @api.cache.cached(timeout=120, key_prefix=cache_key)
    @api.marshal_with(stats_fields, code=200, description='Success')
    @api.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
            'name': 'Client name',
            'backup': 'Backup number',
        },
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
        parser=parser
    )
    def get(self, server=None, name=None, backup=None):
        """Returns global statistics of a given backup/client

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            "dir": {
              "changed": 0,
              "deleted": 0,
              "new": 394,
              "scanned": 394,
              "total": 394,
              "unchanged": 0
            },
            "duration": 5,
            "efs": {
              "changed": 0,
              "deleted": 0,
              "new": 0,
              "scanned": 0,
              "total": 0,
              "unchanged": 0
            },
            "encrypted": true,
            "end": 1422189124,
            "files": {
              "changed": 0,
              "deleted": 0,
              "new": 0,
              "scanned": 0,
              "total": 0,
              "unchanged": 0
            },
            "files_enc": {
              "changed": 0,
              "deleted": 0,
              "new": 1421,
              "scanned": 1421,
              "total": 1421,
              "unchanged": 0
            },
            "hardlink": {
              "changed": 0,
              "deleted": 0,
              "new": 0,
              "scanned": 0,
              "total": 0,
              "unchanged": 0
            },
            "meta": {
              "changed": 0,
              "deleted": 0,
              "new": 0,
              "scanned": 0,
              "total": 0,
              "unchanged": 0
            },
            "meta_enc": {
              "changed": 0,
              "deleted": 0,
              "new": 0,
              "scanned": 0,
              "total": 0,
              "unchanged": 0
            },
            "number": 1,
            "received": 1679304,
            "softlink": {
              "changed": 0,
              "deleted": 0,
              "new": 1302,
              "scanned": 1302,
              "total": 1302,
              "unchanged": 0
            },
            "special": {
              "changed": 0,
              "deleted": 0,
              "new": 0,
              "scanned": 0,
              "total": 0,
              "unchanged": 0
            },
            "start": 1422189119,
            "total": {
              "changed": 0,
              "deleted": 0,
              "new": 3117,
              "scanned": 3117,
              "total": 3117,
              "unchanged": 0
            },
            "totsize": 5345361,
            "vssfooter": {
              "changed": 0,
              "deleted": 0,
              "new": 0,
              "scanned": 0,
              "total": 0,
              "unchanged": 0
            },
            "vssfooter_enc": {
              "changed": 0,
              "deleted": 0,
              "new": 0,
              "scanned": 0,
              "total": 0,
              "unchanged": 0
            },
            "vssheader": {
              "changed": 0,
              "deleted": 0,
              "new": 0,
              "scanned": 0,
              "total": 0,
              "unchanged": 0
            },
            "vssheader_enc": {
              "changed": 0,
              "deleted": 0,
              "new": 0,
              "scanned": 0,
              "total": 0,
              "unchanged": 0
            },
            "windows": "false"
          }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :param backup: The backup we are working on
        :type backup: int

        :returns: The *JSON* described above.
        """
        if not server:
            server = self.parser.parse_args()['server']
        j = []
        if not name:
            err = [[1, 'No client defined']]
            api.abort(400, err)
        if (api.bui.acl and not
                api.bui.acl.is_client_allowed(current_user.get_id(),
                                              name,
                                              server)):
            api.abort(403, 'You don\'t have rights to view this client stats')
        if backup:
            try:
                j = api.bui.cli.get_backup_logs(backup, name, agent=server)
            except BUIserverException as e:
                api.abort(500, str(e))
        else:
            try:
                cl = api.bui.cli.get_client(name, agent=server)
            except BUIserverException as e:
                api.abort(500, str(e))
            err = []
            for c in cl:
                try:
                    j.append(api.bui.cli.get_backup_logs(c['number'], name, agent=server))
                except BUIserverException as e:
                    temp = [2, str(e)]
                    if temp not in err:
                        err.append(temp)
            if err:
                api.abort(500, err)
        return j


@ns.route('/client.json/<name>',
          '/<server>/client.json/<name>',
          endpoint='client_report')
class ClientReport(Resource):
    """The :class:`burpui.api.client.ClientReport` resource allows you to
    retrieve a list of backups for a given client.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    """
    parser = api.parser()
    parser.add_argument('server', type=str, help='Which server to collect data from when in multi-agent mode')
    client_fields = api.model('ClientReport', {
        'number': fields.Integer(required=True, description='Backup number'),
        'received': fields.Integer(required=True, description='Bytes received'),
        'size': fields.Integer(required=True, description='Total size'),
        'encrypted': fields.Boolean(required=True, description='Is the backup encrypted'),
        'deletable': fields.Boolean(required=True, description='Is the backup deletable'),
        'date': fields.String(required=True, description='Human representation of the backup date'),
    })

    @api.cache.cached(timeout=120, key_prefix=cache_key)
    @api.marshal_list_with(client_fields, code=200, description='Success')
    @api.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
            'name': 'Client name',
        },
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
        parser=parser
    )
    def get(self, server=None, name=None):
        """Returns a list of backups for a given client

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            [
              {
                "date": "2015-01-25 13:32:00",
                "deletable": true,
                "encrypted": true,
                "received": 123,
                "size": 1234,
                "number": 1
              },
            ]

        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :returns: The *JSON* described above.
        """
        if not server:
            server = self.parser.parse_args()['server']
        try:
            if (api.bui.acl and (
                    not api.bui.acl.is_admin(current_user.get_id()) and
                    not api.bui.acl.is_client_allowed(current_user.get_id(),
                                                      name,
                                                      server))):
                api.abort(403, 'Sorry, you cannot access this client')
            j = api.bui.cli.get_client(name, agent=server)
        except BUIserverException as e:
            api.abort(500, str(e))
        return j
