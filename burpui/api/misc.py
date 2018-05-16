# -*- coding: utf8 -*-
"""
.. module:: burpui.api.misc
    :platform: Unix
    :synopsis: Burp-UI misc api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from . import api, cache_key, force_refresh
from ..server import BUIServer  # noqa
from .custom import fields, Resource
from ..exceptions import BUIserverException
from ..decorators import browser_cache
from ..ext.cache import cache
from ..ext.i18n import LANGUAGES

from six import iteritems
from flask import flash, url_for, current_app, session
from flask_login import current_user

import random
import re

bui = current_app  # type: BUIServer
ns = api.namespace('misc', 'Misc methods')

counters_fields = ns.model('Counters', {
    'phase': fields.String(description='Backup phase'),
    'Total': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='total'),
    'Files': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='files'),
    'Files (encrypted)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='files_encrypted'),
    'Meta data': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='meta_data'),
    'Meta data (enc)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='meta_data_encrypted'),
    'Directories': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='directories'),
    'Soft links': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='soft_links'),
    'Hard links': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='hard_links'),
    'Special files': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='special_files'),
    'VSS headers': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='vss_headers'),
    'VSS headers (enc)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='vss_headers_encrypted'),
    'VSS footers': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='vss_footers'),
    'VSS footers (enc)': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='vss_footers_encrypted'),
    'Grand total': fields.List(fields.Integer, description='new/deleted/scanned/unchanged/total', attribute='grand_total'),
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
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
        'client': 'Client name',
    },
)
class Counters(Resource):
    """The :class:`burpui.api.misc.Counters` resource allows you to
    render the *live view* template of a given client.

    This resource is part of the :mod:`burpui.api.api` module.

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.
    A mandatory ``GET`` parameter called ``clientName`` is used to know what client we
    are working on.
    """
    parser = ns.parser()
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
    parser.add_argument('clientName', help='Client name')
    monitor_fields = ns.model('Monitor', {
        'client': fields.String(required=True, description='Client name'),
        'agent': fields.String(description='Server (agent) name'),
        'counters': fields.Nested(counters_fields, description='Various statistics about the running backup'),
    })

    @ns.marshal_with(monitor_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
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
        if not current_user.is_anonymous and \
                not current_user.acl.is_admin() and \
                not current_user.acl.is_client_allowed(client, server):
            self.abort(403, "Not allowed to view '{}' counters".format(client))
        running = bui.client.is_one_backup_running()
        if isinstance(running, dict):
            if server and client not in running[server]:
                self.abort(404, "'{}' not found in the list of running clients for '{}'".format(client, server))
            else:
                found = False
                for (_, cls) in iteritems(running):
                    if client in cls:
                        found = True
                        break
                if not found:
                    api.bort(404, "'{}' not found in running clients".format(client))
        else:
            if client not in running:
                self.abort(404, "'{}' not found in running clients".format(client))
        try:
            counters = bui.client.get_counters(client, agent=server)
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
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
    },
)
class Live(Resource):
    """The :class:`burpui.api.misc.Live` resource allows you to
    retrieve a list of servers that are currently *alive*.

    This resource is part of the :mod:`burpui.api.misc` module.

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.
    """
    parser = ns.parser()
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
    live_fields = ns.model('Live', {
        'client': fields.String(required=True, description='Client name'),
        'agent': fields.String(description='Server (agent) name'),
        'counters': fields.Nested(counters_fields, description='Various statistics about the running backup'),
    })

    @ns.marshal_list_with(live_fields, code=200, description='Success')
    @ns.expect(parser)
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
                }
              },
              {
                'client': 'client12',
                'agent': 'burp2',
                'counters': {
                    'phase': 3,
                    'path': '/etc/some/other/configuration',
                    '...': '...',
                }
              }
            ]


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :returns: The *JSON* described above
        """

        args = self.parser.parse_args()
        server = server or args['serverName']
        res = []
        is_admin = True
        has_acl = not current_user.is_anonymous

        if has_acl:
            is_admin = current_user.acl.is_admin()

        # ACL
        if has_acl and \
                not is_admin and \
                server and not current_user.acl.is_server_allowed(server):
            self.abort(403, 'You are not allowed to view stats of this server')
        if server:
            running = bui.client.is_one_backup_running(server)
            # ACL
            if has_acl and not is_admin:
                running = [x for x in running if current_user.acl.is_client_allowed(x, server)]
        else:
            running = bui.client.is_one_backup_running()
        if isinstance(running, dict):
            for (serv, clients) in iteritems(running):
                for client in clients:
                    # ACL
                    if has_acl and not is_admin and \
                            not current_user.acl.is_client_allowed(client, serv):
                        continue
                    data = {}
                    data['client'] = client
                    data['agent'] = serv
                    try:
                        data['counters'] = bui.client.get_counters(client, agent=serv)
                    except BUIserverException:
                        data['counters'] = {}
                    res.append(data)
        else:
            for client in running:
                # ACL
                if has_acl and not is_admin and \
                        not current_user.acl.is_client_allowed(client, server):
                    continue
                data = {}
                data['client'] = client
                try:
                    data['counters'] = bui.client.get_counters(client, agent=server)
                except BUIserverException:
                    data['counters'] = {}
                res.append(data)
        return res


@ns.route('/alert', endpoint='alert')
class Alert(Resource):
    """The :class:`burpui.api.misc.Alert` resource allows you to propagate a
    message to the next screen.

    This resource is part of the :mod:`burpui.api.misc` module.
    """
    parser = ns.parser()
    parser.add_argument('message', required=True, help='Message to display')
    parser.add_argument('level', help='Alert level', choices=('danger', 'warning', 'info', 'success', '0', '1', '2', '3'), default='danger')

    @ns.expect(parser)
    @ns.doc(
        responses={
            201: 'Success',
        },
    )
    def post(self):
        """Propagate a message to the next screen (or whatever reads the session)"""
        def translate(level):
            levels = ['danger', 'warning', 'info', 'success']
            convert = {
                '0': 'success',
                '1': 'warning',
                '2': 'error',
                '3': 'info'
            }
            if not level:
                return 'danger'
            # return the converted value or the one we already had
            new = convert.get(level, level)
            # if the level is not handled, assume 'danger'
            if new not in levels:
                return 'danger'
            return new

        args = self.parser.parse_args()
        message = args['message']
        level = translate(args['level'])
        flash(message, level)
        return {'message': message, 'level': level}, 201


@ns.route('/languages', endpoint='languages')
class Languages(Resource):
    """The :class:`burpui.api.misc.Languages` resource allows you to retrieve
    a list of supported languages.

    This resource is part of the :mod:`burpui.api.misc` module.
    """
    wild = fields.Wildcard(fields.String, description='Supported languages')
    languages_fields = ns.model('Languages', {
        '*': wild,
    })

    @cache.cached(timeout=3600, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_with(languages_fields, code=200, description='Success')
    @browser_cache(3600)
    def get(self):
        """Returns a list of supported languages

        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "en": "English",
              "fr": "Français"
            }


        :returns: The *JSON* described above.
        """
        return LANGUAGES


@ns.route('/about',
          '/<server>/about',
          endpoint='about')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
    },
)
class About(Resource):
    """The :class:`burpui.api.misc.About` resource allows you to retrieve
    various informations about ``Burp-UI``

    An optional ``GET`` parameter called ``serverName`` is supported when running
    in multi-agent mode.
    """
    # Login not required on this view
    login_required = False

    parser = ns.parser()
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
    burp_fields = ns.model('Burp', {
        'name': fields.String(required=True, description='Instance name', default='Burp'),
        'client': fields.String(description='Burp client version'),
        'server': fields.String(description='Burp server version'),
    })
    about_fields = ns.model('About', {
        'version': fields.String(required=True, description='Burp-UI version'),
        'release': fields.String(description='Burp-UI release (commit number)'),
        'api': fields.String(description='Burp-UI API documentation URL'),
        'burp': fields.Nested(burp_fields, as_list=True, description='Burp version'),
    })

    @cache.cached(timeout=3600, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_with(about_fields, code=200, description='Success')
    @ns.expect(parser)
    @browser_cache(3600)
    def get(self, server=None):
        """Returns various informations about Burp-UI"""
        args = self.parser.parse_args()
        res = {}
        server = server or args['serverName']
        res['version'] = api.version
        res['release'] = api.release
        res['api'] = url_for('api.doc')
        res['burp'] = []
        cli = bui.client.get_client_version(server)
        srv = bui.client.get_server_version(server)
        multi = {}
        if isinstance(cli, dict):
            for (name, val) in iteritems(cli):
                multi[name] = {'client': val}
        if isinstance(srv, dict):
            for (name, val) in iteritems(srv):
                multi[name]['server'] = val
        if not multi:
            res['burp'].append({'client': cli, 'server': srv})
        else:
            for (name, val) in iteritems(multi):
                tmp = val
                tmp.update({'name': name})
                res['burp'].append(tmp)
        return res


@ns.route('/ping', endpoint='ping')
class Ping(Resource):
    """The :class:`burpui.api.misc.Ping` resource allows you to ping the API.
    It is actually a Dummy endpoint that does nothing"""
    # Login not required on this view
    login_required = False

    ping_fields = ns.model('Ping', {
        'alive': fields.Boolean(required=True, description="API alive?"),
    })

    @ns.marshal_list_with(ping_fields, code=200, description='Success')
    @ns.doc(
        responses={
            200: 'Success',
            403: 'Insufficient permissions',
        },
    )
    def get(self):
        """Tells if the API is alive"""
        return {'alive': True}


@ns.route('/history',
          '/history/<client>',
          '/<server>/history',
          '/<server>/history/<client>',
          endpoint='history')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
        'client': 'Client name',
    },
)
class History(Resource):
    """The :class:`burpui.api.misc.History` resource allows you to retrieve
    an history of the backups

    An optional ``GET`` parameter called ``serverName`` is supported when
    running in multi-agent mode and ``clientName`` is also allowed to filter
    by client.

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
    parser = ns.parser()
    parser.add_argument('serverName', help='Which server to collect data from when in multi-agent mode')
    parser.add_argument('clientName', help='Which client to collect data from')
    parser.add_argument('start', help='Return events after this date')
    parser.add_argument('end', help='Return events before this date')

    event_fields = ns.model('Event', {
        'title': fields.String(required=True, description='Event name'),
        'start': fields.DateTime(dt_format='iso8601', description='Start time of the event', attribute='date'),
        'end': fields.DateTime(dt_format='iso8601', description='End time of the event'),
        'name': fields.String(description='Client name'),
        'backup': fields.BackupNumber(description='Backup number', attribute='number'),
        'url': fields.String(description='Callback URL'),
    })
    history_fields = ns.model('History', {
        'events': fields.Nested(event_fields, as_list=True, description='Events list'),
        'color': fields.String(description='Background color'),
        'textColor': fields.String(description='Text color'),
        'name': fields.String(description='Feed name'),
    })

    @cache.cached(timeout=1800, key_prefix=cache_key, unless=force_refresh)
    @ns.marshal_list_with(history_fields, code=200, description='Success')
    @ns.expect(parser)
    @ns.doc(
        responses={
            200: 'Success',
            403: 'Insufficient permissions',
        },
    )
    @browser_cache(1800)
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
        self._check_acl(client, server)
        return self._get_backup_history(client, server)

    def _check_acl(self, client=None, server=None):
        args = self.parser.parse_args()
        client = client or args['clientName']
        server = server or args['serverName']
        is_admin = True
        has_acl = not current_user.is_anonymous

        if has_acl:
            is_admin = current_user.acl.is_admin()

        if server and has_acl and not is_admin and \
                not current_user.acl.is_server_allowed(server):
            self.abort(403, "You are not allowed to view this server infos")

        if client and has_acl and not is_admin and \
                not current_user.acl.is_client_allowed(client, server):
            self.abort(403, "You are not allowed to view this client infos")

    def _get_backup_history(self, client=None, server=None, data=None):
        import arrow
        ret = []
        args = self.parser.parse_args()
        is_admin = True
        client = client or args['clientName']
        server = server or args['serverName']
        moments = {
            'start': None,
            'end': None
        }
        has_acl = not current_user.is_anonymous

        if has_acl:
            is_admin = current_user.acl.is_admin()

        for moment in moments.keys():
            if moment in args:
                try:
                    if args[moment] is not None:
                        moments[moment] = arrow.get(args[moment]).timestamp
                except arrow.parser.ParserError:
                    pass

        if client:
            (color, text) = self.gen_colors(client, server)
            feed = {
                'color': color,
                'textColor': text,
                'events': self.gen_events(client, moments, server, data),
            }
            name = client
            if server:
                name += ' on {}'.format(server)
            feed['name'] = name
            ret.append(feed)
            return ret
        elif server:
            if data and server in data:
                clients = [{'name': x} for x in data[server].keys()]
            else:
                clients = bui.client.get_all_clients(agent=server)
            # manage ACL
            if has_acl and not is_admin:
                clients = [x for x in clients if current_user.acl.is_client_allowed(x['name'], server)]
            for cl in clients:
                (color, text) = self.gen_colors(cl['name'], server)
                feed = {
                    'events': self.gen_events(cl['name'], moments, server, data),
                    'textColor': text,
                    'color': color,
                    'name': '{} on {}'.format(cl['name'], server),
                }
                ret.append(feed)
            return ret

        if bui.standalone:
            if data:
                clients_list = data.keys()
            else:
                try:
                    clients_list = [x['name'] for x in bui.client.get_all_clients()]
                except BUIserverException:
                    clients_list = []
                if has_acl and not is_admin:
                    clients_list = [x for x in clients_list if current_user.acl.is_client_allowed(x)]
            for cl in clients_list:
                (color, text) = self.gen_colors(cl)
                feed = {
                    'events': self.gen_events(cl, moments, data=data),
                    'textColor': text,
                    'color': color,
                    'name': cl,
                }
                ret.append(feed)
            return ret
        else:
            grants = {}
            for serv in bui.client.servers:
                if has_acl and not is_admin:
                    try:
                        all_clients = [x['name'] for x in bui.client.get_all_clients(serv)]
                    except BUIserverException:
                        all_clients = []
                    grants[serv] = [x for x in all_clients if current_user.acl.is_client_allowed(x, serv)]
                else:
                    grants[serv] = 'all'
            for (serv, clients) in iteritems(grants):
                if not isinstance(clients, list):
                    if data and serv in data:
                        clients = data[serv].keys()
                    else:
                        clients = [x['name'] for x in bui.client.get_all_clients(agent=serv)]
                for cl in clients:
                    (color, text) = self.gen_colors(cl, serv)
                    feed = {
                        'events': self.gen_events(cl, moments, serv, data),
                        'textColor': text,
                        'color': color,
                        'name': '{} on {}'.format(cl, serv),
                    }
                    ret.append(feed)

        return ret

    def gen_colors(self, client=None, agent=None):
        """Generates color for an events feed"""
        cache = self._get_color_session(client, agent)
        if cache:
            return (cache['color'], cache['text'])
        labels = bui.client.get_client_labels(client, agent)
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
            def rand():
                return random.randint(0, 255)
            red = rand()
            green = rand()
            blue = rand()

        text = text or self._get_text_color(red, green, blue)
        color = color or '#{:02X}{:02X}{:02X}'.format(red, green, blue)
        self._set_color_session(color, text, client, agent)
        return (color, text)

    def _get_text_color(self, red=0, green=0, blue=0):
        """Generates the text color for a given color"""
        yiq = ((red * 299) + (green * 587) + (blue * 114)) / 1000
        return 'black' if yiq >= 128 else 'white'

    def _get_color_session(self, client, agent=None):
        """Since we can *paginate* the rendering, we need to store the already
        generated colors

        This method allows to retrieve already generated colors if any
        """
        sess = session._get_current_object()
        if 'colors' in sess:
            colors = sess['colors']
            if agent and agent in colors:
                return colors[agent].get(client)
            elif not agent:
                return colors.get(client)
        return None

    def _set_color_session(self, color, text, client, agent=None):
        """Since we can *paginate* the rendering, we need to store the already
        generated colors

        This method allows to store already generated colors in the session
        """
        sess = session._get_current_object()
        dic = {}
        if agent:
            if 'colors' in sess and agent in sess['colors']:
                dic[agent] = sess['colors'][agent]
            else:
                dic[agent] = {}
            dic[agent][client] = {
                'color': color,
                'text': text
            }
        else:
            dic[client] = {
                'color': color,
                'text': text
            }
        if 'colors' in sess:
            sess['colors'].update(dic)
        else:
            sess['colors'] = dic

    def gen_events(self, client, moments, server=None, data=None):
        """Creates events for a given client"""
        events = []
        filtered = False
        if data:
            if bui.standalone:
                events = data.get(client, [None])
            else:
                events = data.get(server, {}).get(client, [None])
        if not events:
            events = bui.client.get_client_filtered(client, start=moments['start'], end=moments['end'], agent=server)
            filtered = True

        ret = []
        for ev in events:
            if not ev:
                continue
            if data and not filtered:
                # events are sorted by date DESC
                if moments['start'] and ev['date'] < moments['start']:
                    continue
                if moments['end'] and ev['date'] > moments['end']:
                    continue
            ev['title'] = 'Client: {0}, Backup n°{1:07d}'.format(client, int(ev['number']))
            if server:
                ev['title'] += ', Server: {0}'.format(server)
            ev['name'] = client
            ev['url'] = url_for('view.backup_report', name=client, server=server, backup=int(ev['number']))
            ret.append(ev)

        return ret
