# -*- coding: utf8 -*-
"""
.. module:: burpui.api.misc
    :platform: Unix
    :synopsis: Burp-UI misc api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
# This is a submodule we can also use "from ..api import api"
from . import api
from ..exceptions import BUIserverException

from future.utils import iteritems
from flask.ext.restplus import Resource, fields
from flask.ext.login import current_user
from flask import flash

ns = api.namespace('misc', 'Misc methods')

counters_fields = api.model('Counters', {
    'phase': fields.Integer(description='Backup phase'),
    'Total': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'Files': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'Files (encrypted)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'Metadata': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'Metadata (enc)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'Directories': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'Softlink': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'Hardlink': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'Special files': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'VSS header': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'VSS header (enc)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'VSS footer': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'VSS footer (enc)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'Grand total': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total'),
    'warning': fields.Integer(description='Number of warnings so far'),
    'estimated_bytes': fields.Integer(description='Estimated Bytes in backup'),
    'bytes': fields.Integer(description='Bytes in backup'),
    'bytes_in': fields.Integer(description='Bytes received since backup started'),
    'bytes_out': fields.Integer(description='Bytes sent since backup started'),
    'start': fields.String(description='Timestamp of the start date of the backup'),
    'timeleft': fields.Integer(description='Estimated time left'),
    'percent': fields.Integer(required=True, description='Percentage done'),
    'path': fields.String(description='File that is currently treated by burp'),
})


@ns.route('/counters.json',
          '/<server>/counters.json',
          '/counters.json/<name>',
          '/<server>/counters.json/<name>',
          endpoint='counters')
class Counters(Resource):
    """The :class:`burpui.api.misc.Counters` resource allows you to
    render the *live view* template of a given client.

    This resource is part of the :mod:`burpui.api.api` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    A mandatory ``GET`` parameter called ``name`` is used to know what client we
    are working on.
    """
    parser = api.parser()
    parser.add_argument('server', type=str, help='Which server to collect data from when in multi-agent mode')
    parser.add_argument('name', type=str, help='Client name')

    @api.marshal_with(counters_fields, code=200, description='Success')
    @api.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
            'name': 'Client name',
        },
        responses={
            400: 'Missing argument',
            403: 'Insufficient permissions',
            404: 'Client not found in the running clients list',
        },
        parser=parser
    )
    def get(self, server=None, name=None):
        """Returns counters for a given client

        **GET** method provided by the webservice.

        :param name: the client name if any. You can also use the GET parameter
        'name' to achieve the same thing

        :returns: Counters
        """
        if not server:
            server = self.parser.parse_args()['server']
        if not name:
            name = self.parser.parse_args()['name']
        # Check params
        if not name:
            api.abort(400, 'No client name provided')
        # Manage ACL
        if (api.bui.acl and
            (not api.bui.acl.is_client_allowed(current_user.get_id(), name, server) or
             not api.bui.acl.is_admin(current_user.get_id()))):
            api.abort(403)
        api.bui.cli.is_one_backup_running()
        if isinstance(api.bui.cli.running, dict):
            if server and name not in api.bui.cli.running[server]:
                api.abort(404, "'{}' not found in the list of running clients for '{}'".format(name, server))
            else:
                found = False
                for (k, a) in iteritems(api.bui.cli.running):
                    found = found or (name in a)
                if not found:
                    api.bort(404, "'{}' not found in running clients".format(name))
        else:
            if name not in api.bui.cli.running:
                api.abort(404, "'{}' not found in running clients".format(name))
        try:
            counters = api.bui.cli.get_counters(name, agent=server)
        except BUIserverException:
            counters = {}
        return counters


@ns.route('/live.json',
          '/<server>/live.json',
          endpoint='live')
class Live(Resource):
    """The :class:`burpui.api.misc.Live` resource allows you to
    retrieve a list of servers that are currently *alive*.

    This resource is part of the :mod:`burpui.api.misc` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    """
    parser = api.parser()
    parser.add_argument('server', type=str, help='Which server to collect data from when in multi-agent mode')
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


@ns.route('/alert', endpoint='alert')
class Alert(Resource):
    """The :class:`burpui.api.misc.Alert` resource allows you to propagate a
    message to the next screen.

    This resource is part of the :mod:`burpui.api.misc` module.
    """
    parser = api.parser()
    parser.add_argument('message', required=True, help='Message to display', type=str, location='form')
    parser.add_argument('level', help='Alert level', location='form')

    @api.doc(
        responses={
            200: 'Success',
        },
        parser=parser
    )
    def post(self):
        """Propagate a message to the next screen"""
        args = self.parser.parse_args()
        message = args['message']
        level = args['level']
        if not level:
            level = 'danger'
        flash(args['message'], level)
        return {'message': message}, 200


@ns.route('/about', endpoint='about')
class About(Resource):
    """The :class:`burpui.api.misc.About` resource allows you to retrieve
    various informations about ``Burp-UI``
    """
    about_fields = api.model('About', {
        'version': fields.String(required=True, description='Burp-UI version'),
        'client': fields.String(description='Burp client version'),
        'server': fields.String(description='Burp server version'),
    })

    @api.marshal_with(about_fields, code=200, description='Success')
    def get(self):
        """Returns various informations about Burp-UI"""
        r = {}
        r['version'] = api.version
        try:
            r['client'] = api.bui.cli.client_version
        except:
            pass
        try:
            v = getattr(api.bui.cli, 'server_version', -1)
            if not v or v == -1:
                api.bui.cli.status()
            r['server'] = api.bui.cli.server_version
        except:
            pass
        return r
