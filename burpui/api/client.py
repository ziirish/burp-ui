# -*- coding: utf8 -*-
"""
.. module:: burpui.api.client
    :platform: Unix
    :synopsis: Burp-UI client api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import os

from . import api, cache_key
from .custom import fields, Resource
from .custom.inputs import boolean
from ..exceptions import BUIserverException
from flask_restplus.marshalling import marshal

ns = api.namespace('client', 'Client methods')


@ns.route('/browse/<name>/<int:backup>',
          '/<server>/browse/<name>/<int:backup>',
          endpoint='client_tree')
class ClientTree(Resource):
    """The :class:`burpui.api.client.ClientTree` resource allows you to
    retrieve a list of files in a given backup.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    A mandatory ``GET`` parameter called ``root`` is used to know what path we
    are working on.
    """
    parser = api.parser()
    parser.add_argument(
        'serverName',
        help='Which server to collect data from when in multi-agent mode'
    )
    parser.add_argument(
        'root',
        help='Root path to expand. You may specify several of them',
        action='append'
    )
    parser.add_argument(
        'recursive',
        type=boolean,
        help='Returns the whole tree instead of just the sub-tree',
        nullable=True,
        required=False,
        default=False
    )
    parser.add_argument(
        'selected',
        type=boolean,
        help='Make the returned path selected at load time. Only works' +
             ' if \'recursive\' is True',
        nullable=True,
        required=False,
        default=False
    )
    node_fields = api.model('ClientTree', {
        'date': fields.DateTime(
            required=True,
            dt_format='iso8601',
            description='Human representation of the backup date'
        ),
        'gid': fields.Integer(
            required=True,
            description='gid owner of the node'
        ),
        'inodes': fields.Integer(
            required=True,
            description='Inodes of the node'
        ),
        'mode': fields.String(
            required=True,
            description='Human readable mode. Example: "drwxr-xr-x"'
        ),
        'name': fields.String(
            required=True,
            description='Node name'
        ),
        'title': fields.String(
            required=True,
            description='Node name (alias)',
            attribute='name'
        ),
        'fullname': fields.String(
            required=True,
            description='Full name of the Node'
        ),
        'key': fields.String(
            required=True,
            description='Full name of the Node (alias)',
            attribute='fullname'
        ),
        'parent': fields.String(
            required=True,
            description='Parent node name'
        ),
        'size': fields.String(
            required=True,
            description='Human readable size. Example: "12.0KiB"'
        ),
        'type': fields.String(
            required=True,
            description='Node type. Example: "d"'
        ),
        'uid': fields.Integer(
            required=True,
            description='uid owner of the node'
        ),
        'selected': fields.Boolean(
            required=False,
            description='Is path selected',
            default=False
        ),
        'lazy': fields.Boolean(
            required=False,
            description='Do the children have been loaded during this' +
                        ' request or not',
            default=True
        ),
        'folder': fields.Boolean(
            required=True,
            description='Is it a folder'
        ),
        'expanded': fields.Boolean(
            required=False,
            description='Should we expand the node',
            default=False
        ),
        'children': fields.Raw(
            required=False,
            description='List of children'
        ),
    })

    @api.cache.cached(timeout=3600, key_prefix=cache_key)
    @ns.marshal_list_with(node_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        params={
            'server': 'Which server to collect data from when in' +
                      ' multi-agent mode',
            'name': 'Client name',
            'backup': 'Backup number',
        },
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
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
                "selected": false,
                "expanded": false,
                "children": [],
                "mode": "drwxr-xr-x",
                "name": "/",
                "key": "/",
                "title": "/",
                "fullname": "/",
                "parent": "",
                "size": "12.0KiB",
                "type": "d",
                "uid": "0"
              }
            ]


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :param backup: The backup we are working on
        :type backup: int

        :returns: The *JSON* described above.
        """
        args = self.parser.parse_args()
        server = server or args['serverName']
        json = []
        if not name or not backup:
            return json

        root_list = sorted(args['root']) if args['root'] else []
        root_loaded = False
        paths_loaded = []
        to_select_list = []

        if (api.bui.acl and
                (not self.is_admin and not
                 api.bui.acl.is_client_allowed(self.username,
                                               name,
                                               server))):
            self.abort(403, 'Sorry, you are not allowed to view this client')

        try:
            root_list_clean = []

            for root in root_list:
                if args['recursive']:
                    path = ''
                    # fetch the root first if not already loaded
                    if not root_loaded:
                        part = api.bui.cli.get_tree(
                            name,
                            backup,
                            level=0,
                            agent=server
                        )
                        root_loaded = True
                    else:
                        part = []
                    root = root.rstrip('/')
                    to_select = root.rsplit('/', 1)
                    if not to_select[0]:
                        to_select[0] = '/'
                    if len(to_select) == 1:
                        # special case we want to select '/'
                        to_select = ('', '/')
                    if not root:
                        root = '/'
                    to_select_list.append(to_select)
                    root_list_clean.append(root)
                    paths = root.split('/')
                    for level, sub in enumerate(paths, start=1):
                        path = os.path.join(path, sub)
                        if not path:
                            path = '/'
                        if path in paths_loaded:
                            continue
                        temp = api.bui.cli.get_tree(
                            name,
                            backup,
                            path,
                            level,
                            agent=server
                        )
                        paths_loaded.append(path)
                        part += temp
                else:
                    part = api.bui.cli.get_tree(
                        name,
                        backup,
                        root,
                        agent=server
                    )
                json += part

            if args['selected']:
                for entry in json:
                    for parent, fold in to_select_list:
                        if entry['parent'] == parent and entry['name'] == fold:
                            entry['selected'] = True
                            break
                    if entry['parent'] in root_list_clean:
                        entry['selected'] = True

            if not root_list:
                json = api.bui.cli.get_tree(name, backup, agent=server)
                if args['selected']:
                    for entry in json:
                        if not entry['parent']:
                            entry['selected'] = True

            if args['recursive']:
                tree = {}
                rjson = []
                roots = []
                for entry in json:
                    # /!\ after marshalling, 'fullname' will be 'key'
                    tree[entry['fullname']] = marshal(entry, self.node_fields)

                for key, entry in tree.iteritems():
                    parent = entry['parent']
                    if not entry['children']:
                        entry['children'] = None
                    if parent:
                        node = tree[parent]
                        if not node['children']:
                            node['children'] = []
                        node['children'].append(entry)
                        if node['folder']:
                            node['lazy'] = False
                            node['expanded'] = True
                    else:
                        roots.append(entry['key'])

                for fullname in roots:
                    rjson.append(tree[fullname])

                json = rjson
            else:
                for entry in json:
                    entry['children'] = None
                    if not entry['folder']:
                        entry['lazy'] = False

        except BUIserverException as e:
            self.abort(500, str(e))
        return json


@ns.route('/report/<name>',
          '/<server>/report/<name>',
          '/report/<name>/<int:backup>',
          '/<server>/report/<name>/<int:backup>',
          endpoint='client_report')
class ClientReport(Resource):
    """The :class:`burpui.api.client.ClientStats` resource allows you to
    retrieve a report on a given backup for a given client.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """
    parser = api.parser()
    parser.add_argument(
        'serverName',
        help='Which server to collect data from when in multi-agent mode'
    )
    report_tpl_fields = api.model('ClientReportTpl', {
        'changed': fields.Integer(
            required=True,
            description='Number of changed files',
            default=0
        ),
        'deleted': fields.Integer(
            required=True,
            description='Number of deleted files',
            default=0
        ),
        'new': fields.Integer(
            required=True,
            description='Number of new files',
            default=0
        ),
        'scanned': fields.Integer(
            required=True,
            description='Number of scanned files',
            default=0
        ),
        'total': fields.Integer(
            required=True,
            description='Total number of files',
            default=0
        ),
        'unchanged': fields.Integer(
            required=True,
            description='Number of scanned files',
            default=0
        ),
    })
    report_fields = api.model('ClientReport', {
        'dir': fields.Nested(
            report_tpl_fields,
            required=True
        ),
        'duration': fields.Integer(
            required=True,
            description='Backup duration in seconds'
        ),
        'efs': fields.Nested(
            report_tpl_fields,
            required=True
        ),
        'encrypted': fields.Boolean(
            required=True,
            description='Is the backup encrypted'
        ),
        'end': fields.Integer(
            required=True,
            description='Timestamp of the end date of the backup'
        ),
        'files': fields.Nested(
            report_tpl_fields,
            required=True
        ),
        'files_enc': fields.Nested(
            report_tpl_fields,
            required=True
        ),
        'hardlink': fields.Nested(
            report_tpl_fields,
            required=True
        ),
        'meta': fields.Nested(
            report_tpl_fields,
            required=True
        ),
        'meta_enc': fields.Nested(
            report_tpl_fields,
            required=True
        ),
        'number': fields.Integer(
            required=True,
            description='Backup number'
        ),
        'received': fields.Integer(
            required=True,
            description='Bytes received'
        ),
        'softlink': fields.Nested(report_tpl_fields, required=True),
        'special': fields.Nested(report_tpl_fields, required=True),
        'start': fields.Integer(
            required=True,
            description='Timestamp of the beginning of the backup'
        ),
        'totsize': fields.Integer(
            required=True,
            description='Total size of the backup'
        ),
        'vssfooter': fields.Nested(report_tpl_fields, required=True),
        'vssfooter_enc': fields.Nested(report_tpl_fields, required=True),
        'vssheader': fields.Nested(report_tpl_fields, required=True),
        'vssheader_enc': fields.Nested(report_tpl_fields, required=True),
        'windows': fields.Boolean(
            required=True,
            description='Is the client a windows system'
        ),
    })

    @api.cache.cached(timeout=1800, key_prefix=cache_key)
    @ns.marshal_with(report_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent' +
                      ' mode',
            'name': 'Client name',
            'backup': 'Backup number',
        },
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
    )
    def get(self, server=None, name=None, backup=None):
        """Returns a global report of a given backup/client

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
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

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :param backup: The backup we are working on
        :type backup: int

        :returns: The *JSON* described above.
        """
        server = server or self.parser.parse_args()['serverName']
        j = []
        if not name:
            err = [[1, 'No client defined']]
            self.abort(400, err)
        if (api.bui.acl and not
                api.bui.acl.is_client_allowed(self.username,
                                              name,
                                              server)):
            self.abort(403, 'You don\'t have rights to view this client report')
        if backup:
            try:
                j = api.bui.cli.get_backup_logs(backup, name, agent=server)
            except BUIserverException as e:
                self.abort(500, str(e))
        else:
            try:
                cl = api.bui.cli.get_client(name, agent=server)
            except BUIserverException as e:
                self.abort(500, str(e))
            err = []
            for c in cl:
                try:
                    j.append(
                        api.bui.cli.get_backup_logs(
                            c['number'],
                            name,
                            agent=server
                        )
                    )
                except BUIserverException as e:
                    temp = [2, str(e)]
                    if temp not in err:
                        err.append(temp)
            if err:
                self.abort(500, err)
        return j


@ns.route('/stats/<name>',
          '/<server>/stats/<name>',
          endpoint='client_stats')
class ClientStats(Resource):
    """The :class:`burpui.api.client.ClientReport` resource allows you to
    retrieve a list of backups for a given client.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """
    parser = api.parser()
    parser.add_argument(
        'serverName',
        help='Which server to collect data from when in multi-agent mode'
    )
    client_fields = api.model('ClientStats', {
        'number': fields.Integer(required=True, description='Backup number'),
        'received': fields.Integer(required=True, description='Bytes received'),
        'size': fields.Integer(required=True, description='Total size'),
        'encrypted': fields.Boolean(
            required=True,
            description='Is the backup encrypted'
        ),
        'deletable': fields.Boolean(
            required=True,
            description='Is the backup deletable'
        ),
        'date': fields.DateTime(
            required=True,
            dt_format='iso8601',
            description='Human representation of the backup date'
        ),
    })

    @api.cache.cached(timeout=1800, key_prefix=cache_key)
    @ns.marshal_list_with(client_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent' +
                      ' mode',
            'name': 'Client name',
        },
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
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

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :returns: The *JSON* described above.
        """
        server = server or self.parser.parse_args()['serverName']
        try:
            if (api.bui.acl and (
                    not self.is_admin and
                    not api.bui.acl.is_client_allowed(self.username,
                                                      name,
                                                      server))):
                self.abort(403, 'Sorry, you cannot access this client')
            j = api.bui.cli.get_client(name, agent=server)
        except BUIserverException as e:
            self.abort(500, str(e))
        return j
