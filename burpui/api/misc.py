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

import random
import re

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
          '/counters/<client>',
          '/<server>/counters/<client>',
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
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
    parser.add_argument('clientName', help='Client name')
    monitor_fields = api.model('Monitor', {
        'client': fields.String(required=True, description='Client name'),
        'agent': fields.String(description='Server (agent) name'),
        'counters': fields.Nested(counters_fields, description='Various statistics about the running backup'),
    })

    @ns.marshal_with(monitor_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
            'client': 'Client name',
        },
        responses={
            400: 'Missing argument',
            403: 'Insufficient permissions',
            404: 'Client not found in the running clients list',
        },
    )
    def get(self, server=None, client=None):
        """Returns counters for a given client

        **GET** method provided by the webservice.

        :param name: the client name if any. You can also use the GET parameter
        'name' to achieve the same thing

        :returns: Counters
        """
        args = self.parser.parse_args()
        server = server or args['serverName']
        client = client or args['clientName']
        # Check params
        if not client:
            self.abort(400, 'No client name provided')
        # Manage ACL
        if (api.bui.acl and
            (not api.bui.acl.is_client_allowed(self.username, client, server) or
             not self.is_admin)):
            self.abort(403)
        api.bui.cli.is_one_backup_running()
        if isinstance(api.bui.cli.running, dict):
            if server and client not in api.bui.cli.running[server]:
                self.abort(404, "'{}' not found in the list of running clients for '{}'".format(client, server))
            else:
                found = False
                for (k, a) in iteritems(api.bui.cli.running):
                    found = found or (client in a)
                if not found:
                    api.bort(404, "'{}' not found in running clients".format(client))
        else:
            if client not in api.bui.cli.running:
                self.abort(404, "'{}' not found in running clients".format(client))
        try:
            counters = api.bui.cli.get_counters(client, agent=server)
        except BUIserverException:
            counters = {}
        res = {}
        res['client'] = client
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
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
    live_fields = api.model('Live', {
        'client': fields.String(required=True, description='Client name'),
        'agent': fields.String(description='Server (agent) name'),
        'counters': fields.Nested(counters_fields, description='Various statistics about the running backup'),
    })

    @ns.marshal_list_with(live_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
        },
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
            self.abort(403, 'You are not allowed to view stats of this server')
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
    parser.add_argument('message', required=True, help='Message to display', location='form')
    parser.add_argument('level', help='Alert level', location='form', choices=('danger', 'warning', 'info', 'success'), default='danger')

    @ns.expect(parser)
    @ns.doc(
        responses={
            200: 'Success',
        },
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
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
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
    @ns.marshal_with(about_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
        },
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
          '/history/<client>',
          '/<server>/history',
          '/<server>/history/<client>',
          endpoint='history')
class History(Resource):
    """The :class:`burpui.api.misc.History` resource allows you to retrieve
    an history of the backups

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode and ``clientName`` is also allowed to filter
    by client.

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
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
    parser.add_argument('clientName', help='Which client to collect data from')
    event_fields = api.model('Event', {
        'title': fields.String(required=True, description='Event name'),
        'start': fields.DateTime(dt_format='iso8601', description='Start time of the event', attribute='date'),
        'end': fields.DateTime(dt_format='iso8601', description='End time of the event'),
        'name': fields.String(description='Client name'),
        'backup': fields.BackupNumber(description='Backup number', attribute='number'),
        'url': fields.String(description='Callback URL'),
    })
    history_fields = api.model('History', {
        'events': fields.Nested(event_fields, as_list=True, description='Events list'),
        'color': fields.String(description='Background color'),
        'textColor': fields.String(description='Text color'),
        'name': fields.String(description='Feed name'),
    })

    @api.cache.cached(timeout=1800, key_prefix=cache_key)
    @ns.marshal_list_with(history_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        params={
            'server': 'Which server to collect data from when in multi-agent mode',
            'client': 'Client name',
        },
        responses={
            200: 'Success',
        },
    )
    def get(self, client=None, server=None):
        """Returns a list of calendars describing the backups that have been
        completed so far

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            [
              {
                "color": "#7C6F44",
                "events": [
                  {
                    "backup": "0000001",
                    "end": "2015-01-25 13:32:04+01:00",
                    "name": "toto-test",
                    "start": "2015-01-25 13:32:00+01:00",
                    "title": "Client: toto-test, Backup n°0000001",
                    "url": "/client/toto-test"
                  }
                ],
                "name": "toto-test",
                "textColor": "white"
              }
            ]


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str
        :param client: Which client to collect data from
        :type client: str

        :returns: The *JSON* described above
        """
        ret = []
        args = self.parser.parse_args()
        client = client or args['clientName']
        server = server or args['serverName']

        if (server and api.bui.acl and not self.is_admin and
                server not in api.bui.acl.servers(self.username)):
            self.abort(403, "You are not allowed to view this server infos")

        if (client and api.bui.acl and not self.is_admin and not
                api.bui.acl.is_client_allowed(self.username, client, server)):
            self.abort(403, "You are not allowed to view this client infos")

        if client:
            (color, text) = self.gen_colors(client, server)
            feed = {
                'color': color,
                'textColor': text,
                'events': self.gen_events(client, server),
            }
            name = client
            if server:
                name += ' on {}'.format(server)
            feed['name'] = name
            ret.append(feed)
            return ret
        elif server:
            clients = api.bui.cli.get_all_clients(agent=server)
            if api.bui.acl and not self.is_admin:
                clients = [x for x in clients if x['name'] in api.bui.acl.clients(self.username, server)]
            for cl in clients:
                (color, text) = self.gen_colors(cl['name'], server)
                feed = {
                    'events': self.gen_events(cl['name'], server),
                    'textColor': text,
                    'color': color,
                    'name': '{} on {}'.format(cl['name'], server),
                }
                ret.append(feed)
            return ret

        if api.bui.standalone:
            if api.bui.acl and not self.is_admin:
                clients_list = api.bui.acl.clients(self.username)
            else:
                clients_list = [x['name'] for x in api.bui.cli.get_all_clients()]
            for cl in clients_list:
                (color, text) = self.gen_colors(cl)
                feed = {
                    'events': self.gen_events(cl),
                    'textColor': text,
                    'color': color,
                    'name': cl,
                }
                ret.append(feed)
            return ret
        else:
            grants = {}
            if api.bui.acl and not self.is_admin:
                for serv in api.bui.acl.servers(self.username):
                    grants[serv] = api.bui.acl.clients(self.username, serv)
            else:
                for serv in api.bui.cli.servers:
                    grants[serv] = 'all'
            for (serv, clients) in iteritems(grants):
                if not isinstance(clients, list):
                    clients = [x['name'] for x in api.bui.cli.get_all_clients(agent=serv)]
                for cl in clients:
                    (color, text) = self.gen_colors(cl, serv)
                    feed = {
                        'events': self.gen_events(cl, serv),
                        'textColor': text,
                        'color': color,
                        'name': '{} on {}'.format(cl, serv),
                    }
                    ret.append(feed)

        return ret

    def gen_colors(self, client=None, agent=None):
        """Generates color for an events feed"""
        labels = api.bui.cli.get_client_labels(client, agent)
        HTML_COLOR = r'((?P<hex>#(?P<red_hex>[0-9a-f]{1,2})(?P<green_hex>[0-9a-f]{1,2})(?P<blue_hex>[0-9a-f]{1,2}))|(?P<rgb>rgb\s*\(\s*(?P<red>2[0-5]{2}|2[0-4]\d|[0-1]?\d\d?)\s*,\s*(?P<green>2[0-5]{2}|2[0-4]\d|[0-1]?\d\d?)\s*,\s*(?P<blue>2[0-5]{2}|2[0-4]\d|[0-1]?\d\d?)\s*\))|(?P<plain>[\w-]+$))'
        color_found = False
        color = None
        text = None
        for label in labels:
            # We are looking for labels starting with "color:" or "text:"
            if re.search(r'^color:', label, re.IGNORECASE):
                search = re.search(r'^color:\s*{}'.format(HTML_COLOR), label, re.IGNORECASE)
                # we allow various color forms. For instance:
                # hex: #fa12e6
                # rgb: rgb (123, 42, 9)
                # plain: black
                if search.group('hex'):
                    red = search.group('red_hex')
                    green = search.group('green_hex')
                    blue = search.group('blue_hex')
                    # ensure ensure the hex part is of the form XX
                    red = red + red if len(red) == 1 else red
                    green = green + green if len(green) == 1 else green
                    blue = blue + blue if len(blue) == 1 else blue
                    # Now convert the hex to an int
                    red = int(red, 16)
                    green = int(green, 16)
                    blue = int(blue, 16)
                elif search.group('rgb'):
                    red = int(search.group('red'))
                    green = int(search.group('green'))
                    blue = int(search.group('blue'))
                elif search.group('plain'):
                    # if plain color is provided, we cannot guess the adapted
                    # text color, so we assume white (unless text is specified)
                    red = 0
                    green = 0
                    blue = 0
                    color = search.group('plain')
                else:
                    continue
                color = color or '#{:02X}{:02X}{:02X}'.format(red, green, blue)
                color_found = True
            if re.search(r'^text:', label, re.IGNORECASE):
                search = re.search(r'^text:\s*{}'.format(HTML_COLOR), label, re.IGNORECASE)
                # if we don't find anything, we'll generate a color based on
                # the value of the red, green and blue variables
                text = search.group('hex') or search.group('rgb') or search.group('plain')
            if color and text:
                break

        if not color_found:
            rand = lambda: random.randint(0, 255)
            red = rand()
            green = rand()
            blue = rand()

        text = text or self._get_text_color(red, green, blue)
        color = color or '#{:02X}{:02X}{:02X}'.format(red, green, blue)
        return (color, text)

    def _get_text_color(self, red=0, green=0, blue=0):
        """Generates the text color for a given color"""
        yiq = ((red * 299) + (green * 587) + (blue * 114)) / 1000
        return 'black' if yiq >= 128 else 'white'

    def gen_events(self, client, server=None):
        """Creates events for a given client"""
        events = api.bui.cli.get_client(client, agent=server)
        for ev in events:
            ev['title'] = 'Client: {0}, Backup n°{1:07d}'.format(client, int(ev['number']))
            if server:
                ev['title'] += ', Server: {0}'.format(server)
            ev['name'] = client
            ev['url'] = url_for('view.backup_report', name=client, server=server, backup=int(ev['number']))

        return events
