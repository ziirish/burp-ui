# -*- coding: utf8 -*-
"""
.. module:: burpui.api.misc
    :platform: Unix
    :synopsis: Burp-UI misc api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from . import api, cache_key
from .custom import fields, Resource
from ..exceptions import BUIserverException

from six import iteritems
from flask import flash, url_for

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
    'speed': fields.Integer(description='Backup speed', default=-1),
    'timeleft': fields.Integer(description='Estimated time left'),
    'percent': fields.Integer(required=True, description='Percentage done'),
    'path': fields.String(description='File that is currently treated by burp'),
})


@ns.route('/counters',
          '/<server>/counters',
          '/counters/<name>',
          '/<server>/counters/<name>',
          endpoint='counters')
class Counters(Resource):
    """The :class:`burpui.api.misc.Counters` resource allows you to
    render the *live view* template of a given client.

    This resource is part of the :mod:`burpui.api.api` module.

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.
    A mandatory ``GET`` parameter called ``clientName`` is used to know what client we
    are working on.
    """
    parser = api.parser()
    parser.add_argument('serverName', type=str, help='Which server to collect data from when in multi-agent mode')
    parser.add_argument('clientName', type=str, help='Client name')
    monitor_fields = api.model('Monitor', {
        'client': fields.String(required=True, description='Client name'),
        'agent': fields.String(description='Server (agent) name'),
        'counters': fields.Nested(counters_fields, description='Various statistics about the running backup'),
    })

    @api.marshal_with(monitor_fields, code=200, description='Success')
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
        args = self.parser.parse_args()
        server = server or args['serverName']
        name = name or args['clientName']
        # Check params
        if not name:
            api.abort(400, 'No client name provided')
        # Manage ACL
        if (api.bui.acl and
            (not api.bui.acl.is_client_allowed(self.username, name, server) or
             not self.is_admin)):
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
        res = {}
        res['client'] = name
        res['agent'] = server
        res['counters'] = counters
        return res


@ns.route('/monitor',
          '/<server>/monitor',
          endpoint='live')
class Live(Resource):
    """The :class:`burpui.api.misc.Live` resource allows you to
    retrieve a list of servers that are currently *alive*.

    This resource is part of the :mod:`burpui.api.misc` module.

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.
    """
    parser = api.parser()
    parser.add_argument('serverName', type=str, help='Which server to collect data from when in multi-agent mode')
    live_fields = api.model('Live', {
        'client': fields.String(required=True, description='Client name'),
        'agent': fields.String(description='Server (agent) name'),
        'counters': fields.Nested(counters_fields, description='Various statistics about the running backup'),
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
                'counters': {
                    'phase': 2,
                    'path': '/etc/some/configuration',
                    '...': '...',
                },
              },
              {
                'client': 'client12',
                'agent': 'burp2',
                'counters': {
                    'phase': 3,
                    'path': '/etc/some/other/configuration',
                    '...': '...',
                },
              },
            ]

        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above
        """

        args = self.parser.parse_args()
        server = server or args['serverName']
        r = []
        # ACL
        if (api.bui.acl and
                not self.is_admin and
                server and
                server not in api.bui.acl.servers(self.username)):
            api.abort(403, 'You are not allowed to view stats of this server')
        if server:
            l = api.bui.cli.is_one_backup_running(server)[server]
            # ACL
            if api.bui.acl and not self.is_admin:
                allowed = api.bui.acl.clients(self.username, server)
                l = [x for x in l if x in allowed]
        else:
            l = api.bui.cli.is_one_backup_running()
        if isinstance(l, dict):
            for (k, a) in iteritems(l):
                for c in a:
                    # ACL
                    if (api.bui.acl and
                            not self.is_admin and
                            not api.bui.acl.is_client_allowed(
                                self.username,
                                c,
                                k)):
                        continue
                    s = {}
                    s['client'] = c
                    s['agent'] = k
                    try:
                        s['counters'] = api.bui.cli.get_counters(c, agent=k)
                    except BUIserverException:
                        s['counters'] = {}
                    r.append(s)
        else:
            for c in l:
                s = {}
                s['client'] = c
                try:
                    s['counters'] = api.bui.cli.get_counters(c, agent=server)
                except BUIserverException:
                    s['counters'] = {}
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
    parser.add_argument('level', help='Alert level', location='form', type=str, choices=('danger', 'warning', 'info', 'success'), default='danger')

    @api.doc(
        responses={
            200: 'Success',
        },
        parser=parser
    )
    def post(self):
        """Propagate a message to the next screen (or whatever reads the session)"""
        args = self.parser.parse_args()
        message = args['message']
        level = args['level'] or 'danger'
        flash(args['message'], level)
        return {'message': message}, 201


@ns.route('/about',
          '/<server>/about',
          endpoint='about')
class About(Resource):
    """The :class:`burpui.api.misc.About` resource allows you to retrieve
    various informations about ``Burp-UI``

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.
    """
    api.LOGIN_NOT_REQUIRED.append('about')
    parser = api.parser()
    parser.add_argument('serverName', type=str, help='Which server to collect data from when in multi-agent mode')
    burp_fields = api.model('Burp', {
        'name': fields.String(required=True, description='Instance name', default='Burp{}'.format(api.bui.vers)),
        'client': fields.String(description='Burp client version'),
        'server': fields.String(description='Burp server version'),
    })
    about_fields = api.model('About', {
        'version': fields.String(required=True, description='Burp-UI version'),
        'release': fields.String(description='Burp-UI release (commit number)'),
        'api': fields.String(description='Burp-UI API documentation URL'),
        'burp': fields.Nested(burp_fields, as_list=True, description='Burp version'),
    })

    @api.cache.cached(timeout=3600, key_prefix=cache_key)
    @api.marshal_with(about_fields, code=200, description='Success')
    @api.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
        },
        parser=parser
    )
    def get(self, server=None):
        """Returns various informations about Burp-UI"""
        args = self.parser.parse_args()
        r = {}
        server = server or args['serverName']
        r['version'] = api.version
        r['release'] = api.release
        r['api'] = url_for('api.doc')
        r['burp'] = []
        cli = api.bui.cli.get_client_version(server)
        srv = api.bui.cli.get_server_version(server)
        multi = {}
        if isinstance(cli, dict):
            for (name, v) in iteritems(cli):
                multi[name] = {'client': v}
        if isinstance(srv, dict):
            for (name, v) in iteritems(srv):
                multi[name]['server'] = v
        if not multi:
            r['burp'].append({'client': cli, 'server': srv})
        else:
            for (name, v) in iteritems(multi):
                a = v
                a.update({'name': name})
                r['burp'].append(a)
        return r


@ns.route('/history',
          '/history/<name>',
          '/<server>/history',
          '/<server>/history/<name>',
          endpoint='history')
class History(Resource):
    """The :class:`burpui.api.misc.History` resource allows you to retrieve
    an history of the backups

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.

    TODO:

    ::

        $('#calendar').fullCalendar({

            eventSources: [

                // your event source
                {
                    events: [ // put the array in the `events` property
                        {
                            title  : 'event1',
                            start  : '2010-01-01'
                        },
                        {
                            title  : 'event2',
                            start  : '2010-01-05',
                            end    : '2010-01-07'
                        },
                        {
                            title  : 'event3',
                            start  : '2010-01-09T12:30:00',
                        }
                    ],
                    color: 'black',     // an option!
                    textColor: 'yellow' // an option!
                }

                // any other event sources...

            ]

        });

    """
    parser = api.parser()
    parser.add_argument('serverName', type=str, help='Which server to collect data from when in multi-agent mode')
    parser.add_argument('clientName', type=str, help='Which client to collect data from')
    event_fields = api.model('Event', {
        'title': fields.String(required=True, description='Event name'),
        'start': fields.DateTime(dt_format='iso8601', description='Start time of the event'),
        'end': fields.DateTime(dt_format='iso8601', description='End time of the event'),
        'name': fields.String(description='Client name'),
        'backup': fields.Integer(description='Backup number'),
        'url': fields.String(description='Callback URL'),
    })
    history_fields = api.model('History', {
        'events': fields.Nested(event_fields, as_list=True, description='Events list'),
        'color': fields.String(description='Background color'),
        'textColor': fields.String(description='Text color'),
        'name': fields.String(description='Feed name'),
    })

    @api.marshal_list_with(history_fields, code=200, description='Success')
    @api.doc(
        responses={
            200: 'Success',
        },
        parser=parser
    )
    def get(self, client=None, server=None):
        args = self.parser.parse_args()
        client = client or args['clientName']
        server = server or args['serverName']

        if (server and api.bui.acl and not self.is_admin and
                server not in api.bui.acl.servers(self.username)):
            api.abort(403, "You are not allowed to view this server infos")

        if (client and api.bui.acl and not self.is_admin and not
                api.bui.acl.is_client_allowed(self.username, client, server)):
            api.abort(403, "You are not allowed to view this client infos")

        from datetime import date, datetime
        import time
        import random
        rand = lambda: random.randint(0,255)
        red = rand()
        green = rand()
        blue = rand()
        yiq = ((red * 299) + (green * 587) + (blue * 114)) / 1000
        text = 'black' if yiq >= 128 else 'white'
        return [
            {
                'events': [
                    {'title': 'blah', 'start': date.fromtimestamp(time.time())},
                    {'title': 'blih', 'start': "2016-01-30T11:42:02+02:00"},
                    {'title': 'bloh', 'start': datetime.utcnow()},
                    {'title': 'bluh', 'start': 1454614802},
                ],
                'color': '#{:02X}{:02X}{:02X}'.format(red, green, blue),
                'textColor': text,
            },
        ]
