# -*- coding: utf8 -*-
"""
.. module:: burpui.server
    :platform: Unix
    :synopsis: Burp-UI server module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import os
import re
import sys
import logging
import traceback

from .misc.auth.handler import UserAuthHandler
from .misc.acl.handler import ACLloader
from .config import config
from .plugins import PluginManager

from datetime import timedelta
from flask import Flask
from six import iteritems


G_PORT = 5000
G_BIND = u'::'
G_REFRESH = 180
G_LIVEREFRESH = 5
G_IGNORE_LABELS = ["color:.*"]
G_FORMAT_LABELS = [r"s/^os:\s*//"]
G_DEFAULT_STRIP = 0
G_SSL = False
G_SINGLE = True
G_SSLCERT = u''
G_SSLKEY = u''
G_VERSION = 2
G_AUTH = [u'basic']
G_ACL = u'none'
G_STORAGE = u''
G_CACHE = u''
G_SESSION = u''
G_REDIS = u''
G_LIMITER = False
G_RATIO = u'60/minute'
G_CELERY = False
G_SCOOKIE = True
G_DEMO = False
G_DSN = u''
G_PIWIK_URL = u''
G_PIWIK_SCRIPT = u'piwik.php'
G_PIWIK_ID = 0
G_APPSECRET = u'random'
G_COOKIETIME = 14
G_SESSIONTIME = 5
G_DATABASE = u''
G_PREFIX = u''
G_PLUGINS = []
G_NO_SERVER_RESTORE = False
G_WS_ENABLED = True
G_WS_EMBEDDED = False
G_WS_BROKER = u'redis'
G_WS_URL = u''
G_WS_DEBUG = False


class BUIServer(Flask):
    """
    The :class:`burpui.server.BUIServer` class provides the ``Burp-UI`` server.
    """
    gunicorn = False

    defaults = {
        'Global': {
            'port': G_PORT,
            'bind': G_BIND,
            'ssl': G_SSL,
            'standalone': G_SINGLE,
            'single': G_SINGLE,
            'sslcert': G_SSLCERT,
            'sslkey': G_SSLKEY,
            'version': G_VERSION,
            'auth': G_AUTH,
            'acl': G_ACL,
            'prefix': G_PREFIX,
            'plugins': G_PLUGINS,
            'demo': G_DEMO,
            'dsn': G_DSN,
            'piwik_url': G_PIWIK_URL,
            'piwik_script': G_PIWIK_SCRIPT,
            'piwik_id': G_PIWIK_ID,
        },
        'UI': {
            'refresh': G_REFRESH,
            'liverefresh': G_LIVEREFRESH,
            'ignore_labels': G_IGNORE_LABELS,
            'format_labels': G_FORMAT_LABELS,
            'default_strip': G_DEFAULT_STRIP,
        },
        'Security': {
            'scookie': G_SCOOKIE,
            'appsecret': G_APPSECRET,
            'cookietime': G_COOKIETIME,
            'sessiontime': G_SESSIONTIME,
        },
        'Production': {
            'storage': G_STORAGE,
            'session': G_SESSION,
            'cache': G_CACHE,
            'redis': G_REDIS,
            'celery': G_CELERY,
            'database': G_DATABASE,
            'limiter': G_LIMITER,
            'ratio': G_RATIO,
        },
        'WebSocket': {
            'enabled': G_WS_ENABLED,
            'embedded': G_WS_EMBEDDED,
            'broker': G_WS_BROKER,
            'url': G_WS_URL,
            'debug': G_WS_DEBUG,
        },
        'Experimental': {
            'noserverrestore': G_NO_SERVER_RESTORE,
        }
    }

    def __init__(self):
        """The :class:`burpui.server.BUIServer` class provides the ``Burp-UI``
        server.

        :param app: The Flask application to launch
        """
        super(BUIServer, self).__init__('burpui')
        self.init = False
        # We cannot override the Flask's logger so we use our own
        self._logger = logging.getLogger('burp-ui')
        self._logger.disabled = True
        self.conf = config
        # switch the flask config with our magic config object
        self.conf.update(self.config)
        self.config = self.conf

    def enable_logger(self, enable=True):
        """Enable or disable the logger"""
        self._logger.disabled = not enable

    @property
    def logger(self):
        """
        :rtype: :class:`logging.Logger`
        """
        return self._logger

    def setup(self, conf=None, unittest=False, cli=False):
        """The :func:`burpui.server.BUIServer.setup` functions is used to setup
        the whole server by parsing the configuration file and loading the
        different backends.

        :param conf: Path to a configuration file
        :type conf: str

        :param unittest: Whether we are unittesting or not (used to avoid burp2
                         strict requirements checks)
        :type unittest: bool

        :param cli: Whether we are in cli mode or not
        :type cli: bool
        """
        self.sslcontext = None
        if not conf:
            conf = self.config['CFG']

        if not conf:
            raise IOError('No configuration file found')

        # Raise exception if errors are encountered during parsing
        self.conf.parse(conf, True, self.defaults)
        self.conf.default_section('Global')

        self.port = self.config['BUI_PORT'] = self.conf.safe_get(
            'port',
            'integer'
        )
        self.demo = self.config['BUI_DEMO'] = self.conf.safe_get(
            'demo',
            'boolean'
        )
        self.config['BUI_DSN'] = self.conf.safe_get('dsn')
        self.config['BUI_PIWIK_URL'] = self.conf.safe_get('piwik_url')
        self.config['BUI_PIWIK_SCRIPT'] = self.conf.safe_get('piwik_script')
        self.config['BUI_PIWIK_ID'] = self.conf.safe_get('piwik_id', 'integer')
        self.bind = self.config['BUI_BIND'] = self.conf.safe_get('bind')
        version = self.conf.safe_get('version', 'integer')
        if unittest and version != 1:
            version = 1
        self.vers = self.config['BUI_VERS'] = version
        self.ssl = self.config['BUI_SSL'] = self.conf.safe_get(
            'ssl',
            'boolean'
        )
        # option standalone has been renamed for less confusion
        key = 'standalone' if 'standalone' in \
            self.conf.conf.get(self.conf.section, {}) else 'single'
        if key == 'standalone':
            # TODO: remove the compatibility in v0.7.0
            self.logger.warning(
                'The "standalone" option is DEPRECATED and has been replaced '
                'by the "single" option. Please update your conf before we '
                'remove the compatibility in v0.7.0'
            )
        self.standalone = self.config['STANDALONE'] = self.conf.safe_get(
            key,
            'boolean'
        )
        self.sslcert = self.config['BUI_SSLCERT'] = self.conf.safe_get(
            'sslcert'
        )
        self.sslkey = self.config['BUI_SSLKEY'] = self.conf.safe_get(
            'sslkey'
        )
        self.prefix = self.config['BUI_PREFIX'] = self.conf.safe_get(
            'prefix'
        )
        if self.prefix and not self.prefix.startswith('/'):
            if self.prefix.lower() != 'none':
                self.logger.warning("'prefix' must start with a '/'!")
            self.prefix = self.config['BUI_PREFIX'] = ''

        self.plugins = self.config['BUI_PLUGINS'] = self.conf.safe_get(
            'plugins',
            'string_lower_list'
        )
        if len(self.plugins) == 1 and self.plugins[0] == 'none':
            self.plugins = self.config['BUI_PLUGINS'] = []

        self.auth = self.config['BUI_AUTH'] = self.conf.safe_get(
            'auth',
            'string_lower_list'
        )

        # UI options
        self.config['REFRESH'] = self.conf.safe_get(
            'refresh',
            'integer',
            'UI'
        )
        self.config['LIVEREFRESH'] = self.conf.safe_get(
            'liverefresh',
            'integer',
            'UI'
        )
        self.config['DEFAULT_STRIP'] = self.conf.safe_get(
            'default_strip',
            'integer',
            'UI'
        )
        self.ignore_labels = self.conf.safe_get(
            'ignore_labels',
            'force_list',
            'UI'
        )
        format_labels = self.conf.safe_get(
            'format_labels',
            'force_list',
            'UI'
        )
        self.format_labels = []
        for format_label in format_labels:
            search = re.search(r'^s(?P<separator>.)(?P<regex>.*?)(?P=separator)(?P<replace>.*?)(?P=separator)$', format_label)
            if search:
                self.format_labels.append((search.group('regex'), search.group('replace')))

        # Production options
        self.storage = self.config['BUI_STORAGE'] = self.conf.safe_get(
            'storage',
            section='Production'
        )
        self.cache_db = self.config['BUI_CACHE_DB'] = self.conf.safe_get(
            'cache',
            section='Production'
        )
        self.session_db = self.config['BUI_SESSION_DB'] = self.conf.safe_get(
            'session',
            section='Production'
        )
        self.redis = self.config['BUI_REDIS'] = self.conf.safe_get(
            'redis',
            section='Production'
        )
        self.limiter = self.config['BUI_LIMITER'] = self.conf.safe_get(
            'limiter',
            'boolean_or_string',
            section='Production'
        )
        if isinstance(self.limiter, bool) and not self.limiter:
            self.limiter = self.config['BUI_LIMITER'] = 'none'
        self.ratio = self.config['BUI_RATIO'] = self.conf.safe_get(
            'ratio',
            section='Production'
        )
        self.use_celery = self.config['BUI_CELERY'] = self.conf.safe_get(
            'celery',
            'boolean_or_string',
            section='Production'
        )
        self.database = self.config['SQLALCHEMY_DATABASE_URI'] = \
            self.conf.safe_get(
                'database',
                'boolean_or_string',
                section='Production'
        )
        self.config['WITH_LIMIT'] = False
        if isinstance(self.database, bool):
            self.config['WITH_SQL'] = self.database
        else:
            self.config['WITH_SQL'] = self.database and \
                self.database.lower() != 'none'
        if isinstance(self.use_celery, bool):
            self.config['WITH_CELERY'] = self.use_celery
        else:
            self.config['WITH_CELERY'] = self.use_celery and \
                self.use_celery.lower() != 'none'

        # WebSocket options
        self.ws_enabled = self.config['WS_ENABLED'] = self.conf.safe_get(
            'enabled',
            'boolean',
            section='WebSocket'
        )
        self.websocket = self.config['WITH_WS'] = self.conf.safe_get(
            'embedded',
            'boolean',
            section='WebSocket'
        )
        self.ws_broker = self.config['BUI_WS_BROKER'] = self.conf.safe_get(
            'broker',
            'boolean_or_string',
            section='WebSocket'
        )
        self.config['WS_DEBUG'] = self.conf.safe_get(
            'debug',
            'boolean',
            section='WebSocket'
        )
        self.config['WS_URL'] = self.conf.safe_get(
            'url',
            section='WebSocket'
        )
        if self.config.get('WS_URL', '').lower() == 'none' or self.websocket:
            self.config['WS_URL'] = None

        # Experimental options
        self.noserverrestore = self.conf.safe_get(
            'noserverrestore',
            'boolean',
            section='Experimental'
        )

        # Security options
        self.scookie = self.config['BUI_SCOOKIE'] = self.conf.safe_get(
            'scookie',
            'boolean',
            section='Security'
        )
        self.config['SECRET_KEY'] = self.conf.safe_get(
            'appsecret',
            section='Security'
        )
        days = self.conf.safe_get('cookietime', 'integer', section='Security') \
            or G_COOKIETIME
        self.config['REMEMBER_COOKIE_DURATION'] = \
            self.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
                days=days
        )
        self.config['REMEMBER_COOKIE_NAME'] = 'remember_token'
        days = self.conf.safe_get(
            'sessiontime',
            'integer',
            section='Security'
        ) or G_SESSIONTIME
        self.config['SESSION_INACTIVE'] = timedelta(days=days)

        self.logger.info('burp version: {}'.format(self.vers))
        self.logger.info('listen port: {}'.format(self.port))
        self.logger.info('bind addr: {}'.format(self.bind))
        self.logger.info('use ssl: {}'.format(self.ssl))
        self.logger.info('standalone: {}'.format(self.standalone))
        self.logger.info('sslcert: {}'.format(self.sslcert))
        self.logger.info('sslkey: {}'.format(self.sslkey))
        self.logger.info('prefix: {}'.format(self.prefix))
        self.logger.info('secure cookie: {}'.format(self.scookie))
        self.logger.info(
            'cookietime: {}'.format(self.config['REMEMBER_COOKIE_DURATION'])
        )
        self.logger.info(
            'session inactive: {}'.format(self.config['SESSION_INACTIVE'])
        )
        self.logger.info('refresh: {}'.format(self.config['REFRESH']))
        self.logger.info('liverefresh: {}'.format(self.config['LIVEREFRESH']))
        self.logger.info('auth: {}'.format(self.auth))
        self.logger.info('celery: {}'.format(self.use_celery))
        self.logger.info('redis: {}'.format(self.redis))
        self.logger.info('limiter: {}'.format(self.limiter))
        self.logger.info('database: {}'.format(self.database))
        self.logger.info('with SQL: {}'.format(self.config['WITH_SQL']))
        self.logger.info('with Celery: {}'.format(self.config['WITH_CELERY']))
        self.logger.info('with WebSocket: {}'.format(self.config['WITH_WS']))
        self.logger.info('demo: {}'.format(self.config['BUI_DEMO']))

        self.init = True
        if not cli:
            self.load_modules()

    def load_modules(self, strict=False):
        """Load the extensions"""
        self.plugin_manager = PluginManager(self, self.plugins)
        if self.plugins:
            self.plugin_manager.load_all()

        if self.auth and 'none' not in self.auth:
            try:
                self.uhandler = UserAuthHandler(self)
                for back, err in iteritems(self.uhandler.errors):
                    self.logger.critical(
                        'Unable to load \'{}\' authentication backend:\n{}'
                        .format(back, err)
                    )
            except ImportError as e:
                self.logger.critical(
                    'Import Exception, module \'{0}\': {1}'.format(
                        self.auth,
                        str(e)
                    )
                )
                raise e
            self.acl_engine = self.config['BUI_ACL'] = self.conf.safe_get(
                'acl',
                'string_lower_list'
            )
            self.config['LOGIN_DISABLED'] = False
        else:
            self.config['LOGIN_DISABLED'] = True
            # No login => no ACL
            self.acl_engine = self.config['BUI_ACL'] = ['none']
            self.auth = self.config['BUI_AUTH'] = 'none'

        if self.acl_engine and 'none' not in self.acl_engine:
            try:
                self.acl_handler = ACLloader(self)
            except Exception as e:
                self.logger.critical(
                    'Import Exception, module \'{0}\': {1}'.format(
                        self.acl_engine,
                        str(e)
                    )
                )
                raise e
        else:
            self.acl_handler = False

        self.logger.info('acl: {}'.format(self.acl_engine))

        if self.standalone:
            module = 'burpui.misc.backend.burp{0}'.format(self.vers)
        else:
            module = 'burpui.misc.backend.multi'

        # This is used for development purpose only
        from .misc.backend.burp1 import Burp as BurpGeneric
        self.client = BurpGeneric(dummy=True)
        self.strict = strict
        try:
            # Try to load submodules from our current environment
            # first
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            mod = __import__(module, fromlist=['Burp'])
            Client = mod.Burp
            self.client = Client(self, conf=self.conf)
        except Exception as e:
            msg = 'Failed loading backend for Burp version {0}: {1}'.format(
                self.vers,
                str(e)
            )
            if strict:
                self.logger.critical(traceback.format_exc())
                self.logger.critical(msg)
                sys.exit(2)
            else:
                raise Exception(msg)

    @property
    def acl(self):
        """ACL module

        :returns: :class:`burpui.misc.acl.interface.BUIacl`
        """
        if self.acl_engine and 'none' not in self.acl_engine:
            # refresh acl to detect config changes
            from .misc.acl.interface import BUIacl  # noqa
            acl = self.acl_handler.acl  # type: BUIacl
            return acl
        return None

    def get_send_file_max_age(self, name):
        """Provides default cache_timeout for the send_file() functions."""
        if name:
            lname = name.lower()
            extensions = ['js', 'css', 'woff']
            for ext in extensions:
                if lname.endswith('.{}'.format(ext)):
                    return 3600 * 24 * 30  # 30 days
        return Flask.get_send_file_max_age(self, name)

    def manual_run(self):
        """The :func:`burpui.server.BUIServer.manual_run` functions is used to
        actually launch the ``Burp-UI`` server.

        .. deprecated:: 0.4.0
           You should now run the Flask's run command.
        """
        if not self.init:
            self.setup()

        if self.ssl:
            self.sslcontext = (self.sslcert, self.sslkey)

        if self.sslcontext:
            self.config['SSL'] = True
            self.run(
                host=self.bind,
                port=self.port,
                debug=self.config['DEBUG'],
                ssl_context=self.sslcontext
            )
        else:
            self.run(host=self.bind, port=self.port, debug=self.config['DEBUG'])
