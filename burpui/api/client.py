# -*- coding: utf8 -*-
"""
.. module:: burpui.api.client
    :platform: Unix
    :synopsis: Burp-UI client api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import os
import re

from . import api, cache_key, force_refresh
from ..server import BUIServer  # noqa
from .custom import fields, Resource
from .custom.inputs import boolean
from ..decorators import browser_cache
from ..ext.cache import cache
from ..exceptions import BUIserverException
from ..utils import NOTIF_ERROR

from six import iteritems
from flask_restplus.marshalling import marshal
from flask import current_app, request
from flask_login import current_user

bui = current_app  # type: BUIServer
ns = api.namespace('client', 'Client methods')

node_fields = ns.model('ClientTree', {
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
    'title': fields.SafeString(
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
    # Cannot use nested on own
    'children': fields.Raw(
        required=False,
        description='List of children'
    ),
})


@ns.route('/browse/<name>/<int:backup>',
          '/<server>/browse/<name>/<int:backup>',
          endpoint='client_tree')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in' +
                  ' multi-agent mode',
        'name': 'Client name',
        'backup': 'Backup number',
    },
)
class ClientTree(Resource):
    """The :class:`burpui.api.client.ClientTree` resource allows you to
    retrieve a list of files in a given backup.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    A mandatory ``GET`` parameter called ``root`` is used to know what path we
    are working on.
    """
    parser = ns.parser()
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
    parser.add_argument(
        'init',
        type=boolean,
        help='First call to load the root of the tree',
        nullable=True,
        required=False,
        default=False
    )

    @cache.cached(timeout=3600, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_list_with(node_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
    )
    @browser_cache(3600)
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

        if not current_user.is_anonymous and \
                not current_user.acl.is_admin() and \
                not current_user.acl.is_client_allowed(name, server):
            self.abort(403, 'Sorry, you are not allowed to view this client')

        from_cookie = None
        if args['init'] and not root_list:
            from_cookie = request.cookies.get('fancytree-1-expanded', '')
            if from_cookie:
                args['recursive'] = True
                _root = bui.client.get_tree(name, backup, agent=server)
                root_list = [x['name'] for x in _root]
                for path in from_cookie.split('~'):
                    if not path.endswith('/'):
                        path += '/'
                    if path not in root_list:
                        root_list.append(path)
                root_list = sorted(root_list)

        try:
            root_list_clean = []

            for root in root_list:
                if args['recursive']:
                    path = ''
                    # fetch the root first if not already loaded
                    if not root_loaded:
                        part = bui.client.get_tree(
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
                        temp = bui.client.get_tree(
                            name,
                            backup,
                            path,
                            level,
                            agent=server
                        )
                        paths_loaded.append(path)
                        part += temp
                else:
                    part = bui.client.get_tree(
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
                json = bui.client.get_tree(name, backup, agent=server)
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
                    tree[entry['fullname']] = marshal(entry, node_fields)

                for key, entry in iteritems(tree):
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


@ns.route('/browseall/<name>/<int:backup>',
          '/<server>/browseall/<name>/<int:backup>',
          endpoint='client_tree_all')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in' +
                  ' multi-agent mode',
        'name': 'Client name',
        'backup': 'Backup number',
    },
)
class ClientTreeAll(Resource):
    """The :class:`burpui.api.client.ClientTreeAll` resource allows you to
    retrieve a list of all the files in a given backup.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument(
        'serverName',
        help='Which server to collect data from when in multi-agent mode'
    )

    @cache.cached(timeout=3600, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_list_with(node_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            '403': 'Insufficient permissions',
            '405': 'Method not allowed',
            '500': 'Internal failure',
        },
    )
    @browser_cache(3600)
    def get(self, server=None, name=None, backup=None):
        """Returns a list of all 'nodes' of a given backup

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

        if not bui.client.get_attr('batch_list_supported', False, server):
            self.abort(
                405,
                'Sorry, the requested backend does not support this method'
            )

        if not current_user.is_anonymous and \
                not current_user.acl.is_admin() and \
                not current_user.acl.is_client_allowed(name, server):
            self.abort(403, 'Sorry, you are not allowed to view this client')

        try:
            json = self._get_tree_all(name, backup, server)
        except BUIserverException as e:
            self.abort(500, str(e))
        return json

    @staticmethod
    def _get_tree_all(name, backup, server):
        json = bui.client.get_tree(name, backup, '*', agent=server)
        tree = {}
        rjson = []
        roots = []

        def __expand_json(js):
            res = {}
            for entry in js:
                # /!\ after marshalling, 'fullname' will be 'key'
                res[entry['fullname']] = marshal(entry, node_fields)
            return res

        tree = __expand_json(json)

        # TODO: we can probably improve this at some point
        redo = True
        while redo:
            redo = False
            for key, entry in iteritems(tree):
                parent = entry['parent']
                if not entry['children']:
                    entry['children'] = None
                if parent:
                    if parent not in tree:
                        parent2 = parent
                        last = False
                        while parent not in tree and not last:
                            if not parent2:
                                last = True
                            json = bui.client.get_tree(
                                name,
                                backup,
                                parent2,
                                agent=server
                            )
                            if parent2 == '/':
                                parent2 = ''
                            else:
                                parent2 = os.path.dirname(parent2)
                            tree2 = __expand_json(json)
                            tree.update(tree2)
                        roots = []
                        redo = True
                        break
                    node = tree[parent]
                    if not node['children']:
                        node['children'] = []
                    elif entry in node['children']:
                        continue
                    node['children'].append(entry)
                    if node['folder']:
                        node['lazy'] = False
                        node['expanded'] = False
                else:
                    roots.append(entry['key'])

        for fullname in roots:
            rjson.append(tree[fullname])

        return rjson


@ns.route('/report/<name>',
          '/<server>/report/<name>',
          '/report/<name>/<int:backup>',
          '/<server>/report/<name>/<int:backup>',
          endpoint='client_report')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent' +
                  ' mode',
        'name': 'Client name',
        'backup': 'Backup number',
    },
)
class ClientReport(Resource):
    """The :class:`burpui.api.client.ClientStats` resource allows you to
    retrieve a report on a given backup for a given client.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument(
        'serverName',
        help='Which server to collect data from when in multi-agent mode'
    )
    report_tpl_fields = ns.model('ClientReportTpl', {
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
    report_fields = ns.model('ClientReport', {
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
        'end': fields.DateTime(
            dt_format='iso8601',
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
        'start': fields.DateTime(
            dt_format='iso8601',
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

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_with(report_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
    )
    @browser_cache(1800)
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
        json = []
        if not name:
            err = [[1, 'No client defined']]
            self.abort(400, err)

        if not current_user.is_anonymous and \
                not current_user.acl.is_admin() and \
                not current_user.acl.is_client_allowed(name, server):
            self.abort(403, 'You don\'t have rights to view this client report')
        if backup:
            try:
                json = bui.client.get_backup_logs(backup, name, agent=server)
            except BUIserverException as exp:
                self.abort(500, str(exp))
        else:
            try:
                client = bui.client.get_client(name, agent=server)
            except BUIserverException as exp:
                self.abort(500, str(exp))
            err = []
            for back in client:
                try:
                    json.append(
                        bui.client.get_backup_logs(
                            back['number'],
                            name,
                            agent=server
                        )
                    )
                except BUIserverException as exp:
                    temp = [NOTIF_ERROR, str(exp)]
                    if temp not in err:
                        err.append(temp)
            if err:
                self.abort(500, err)
        return json

    @api.disabled_on_demo()
    @ns.marshal_with(report_fields, code=202, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            '400': 'Missing arguments',
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
    )
    def delete(self, name, backup, server=None):
        """Deletes a given backup from the server

        **DELETE** method provided by the webservice.

        The access is filtered by the :mod:`burpui.misc.acl` module so that you
        can only delete backups you have access to.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :param backup: The backup we are working on
        :type backup: int
        """
        server = server or self.parser.parse_args()['serverName']
        if not name:
            err = [[1, 'No client defined']]
            self.abort(400, err)

        if not current_user.is_anonymous and \
                not current_user.acl.is_admin() and \
                (not current_user.acl.is_moderator() or
                 current_user.acl.is_moderator() and
                 not current_user.acl.is_client_rw(name, server)):
            self.abort(403, 'You don\'t have rights on this client')

        msg = bui.client.delete_backup(name, backup, server)
        if msg:
            self.abort(500, msg)
        return 202, ''


@ns.route('/stats/<name>',
          '/<server>/stats/<name>',
          endpoint='client_stats')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent' +
                  ' mode',
        'name': 'Client name',
    },
)
class ClientStats(Resource):
    """The :class:`burpui.api.client.ClientReport` resource allows you to
    retrieve a list of backups for a given client.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument(
        'serverName',
        help='Which server to collect data from when in multi-agent mode'
    )
    client_fields = ns.model('ClientStats', {
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

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_list_with(client_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
    )
    @browser_cache(1800)
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
            if not current_user.is_anonymous and \
                    not current_user.acl.is_admin() and \
                    not current_user.acl.is_client_allowed(name, server):
                self.abort(403, 'Sorry, you cannot access this client')
            json = bui.client.get_client(name, agent=server)
        except BUIserverException as exp:
            self.abort(500, str(exp))
        return json


@ns.route('/labels/<name>',
          '/<server>/labels/<name>',
          endpoint='client_labels')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent' +
                  ' mode',
        'name': 'Client name',
    },
)
class ClientLabels(Resource):
    """The :class:`burpui.api.client.ClientLabels` resource allows you to
    retrieve the labels of a given client.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument(
        'serverName',
        help='Which server to collect data from when in multi-agent mode'
    )
    parser.add_argument('clientName', help='Client name')
    labels_fields = ns.model('ClientLabels', {
        'labels': fields.List(fields.String, description='List of labels'),
    })

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_list_with(labels_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
    )
    @browser_cache(1800)
    def get(self, server=None, name=None):
        """Returns the labels of a given client

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "labels": [
                "label1",
                "label2"
              ]
            }

        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :returns: The *JSON* described above.
        """
        try:
            if not current_user.is_anonymous and \
                    not current_user.acl.is_admin() and \
                    not current_user.acl.is_client_allowed(name, server):
                self.abort(403, 'Sorry, you cannot access this client')
            labels = self._get_labels(name, server)
        except BUIserverException as exp:
            self.abort(500, str(exp))
        return {'labels': labels}

    @staticmethod
    def _get_labels(client, server):
        key = 'labels-{}-{}'.format(client, server)
        ret = cache.cache.get(key)
        if ret is not None:
            return ret
        labels = bui.client.get_client_labels(client, agent=server)
        ret = []
        for label in labels:
            if bui.ignore_labels and \
                    re.search('|'.join(bui.ignore_labels), label):
                continue
            tmp_label = label
            if bui.format_labels:
                for regex, replace in bui.format_labels:
                    tmp_label = re.sub(regex, replace, tmp_label)
            ret.append(tmp_label)
        cache.cache.set(key, ret, 1800)
        return ret


@ns.route('/running',
          '/running/<name>',
          '/<server>/running',
          '/<server>/running/<name>',
          endpoint='client_running_status')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent' +
                  ' mode',
        'name': 'Client name',
    },
)
class ClientRunningStatus(Resource):
    """The :class:`burpui.api.client.ClientRunningStatus` resource allows you to
    retrieve the running status of a given client.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument(
        'serverName',
        help='Which server to collect data from when in multi-agent mode'
    )
    parser.add_argument('clientName', help='Client name')
    running_fields = ns.model('ClientRunningStatus', {
        'state': fields.LocalizedString(required=True, description='Running state'),
        'percent': fields.Integer(
            required=False,
            description='Backup progress in percent',
            default=-1
        ),
        'phase': fields.String(
            required=False,
            description='Backup phase',
            default=None
        ),
        'last': fields.DateTime(
            required=False,
            dt_format='iso8601',
            description='Date of last backup'
        ),
    })

    @ns.marshal_list_with(running_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            '403': 'Insufficient permissions',
            '500': 'Internal failure',
        },
    )
    def get(self, server=None, name=None):
        """Returns the running status of a given client

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "state": "running",
              "percent": 42,
              "phase": "2",
              "last": "now"
            }

        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :returns: The *JSON* described above.
        """
        args = self.parser.parse_args()
        server = server or args['serverName']
        name = name or args['clientName']
        try:
            if not current_user.is_anonymous and \
                    not current_user.acl.is_admin() and \
                    not current_user.acl.is_client_allowed(name, server):
                self.abort(403, 'Sorry, you cannot access this client')
            json = bui.client.get_client_status(name, agent=server)
        except BUIserverException as exp:
            self.abort(500, str(exp))
        return json
