# -*- coding: utf8 -*-
"""
.. module:: burpui.server
    :platform: Unix
    :synopsis: Burp-UI server module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import os
import sys
import logging
import traceback

from .misc.auth.handler import UserAuthHandler
from .config import config

from datetime import timedelta
from flask import Flask


G_PORT = 5000
G_BIND = u'::'
G_REFRESH = 180
G_LIVEREFRESH = 5
G_SSL = False
G_STANDALONE = True
G_SSLCERT = u''
G_SSLKEY = u''
G_VERSION = 2
G_AUTH = [u'basic']
G_ACL = u'none'
G_STORAGE = u''
G_CACHE = u''
G_SESSION = u''
G_REDIS = u''
G_CELERY = False
G_SCOOKIE = True
G_DEMO = False
G_APPSECRET = u'random'
G_COOKIETIME = 14
G_SESSIONTIME = 5
G_DATABASE = u''
G_PREFIX = u''
G_NO_SERVER_RESTORE = False


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
            'standalone': G_STANDALONE,
            'sslcert': G_SSLCERT,
            'sslkey': G_SSLKEY,
            'version': G_VERSION,
            'auth': G_AUTH,
            'acl': G_ACL,
            'prefix': G_PREFIX,
            'demo': G_DEMO,
        },
        'UI': {
            'refresh': G_REFRESH,
            'liverefresh': G_LIVEREFRESH,
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
        self.init = False
        # We cannot override the Flask's logger so we use our own
        self.builogger = logging.getLogger('burp-ui')
        self.builogger.disabled = True
        super(BUIServer, self).__init__('burpui')

    def enable_logger(self, enable=True):
        """Enable or disable the logger"""
        self.builogger.disabled = not enable

    @property
    def logger(self):
        return self.builogger

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
        self.conf = config
        self.conf.parse(conf, True, self.defaults)
        self.conf.default_section('Global')

        # switch the flask config with our magic config object
        self.conf.update(self.config)
        self.config = self.conf

        self.port = self.config['BUI_PORT'] = self.conf.safe_get(
            'port',
            'integer'
        )
        self.demo = self.config['BUI_DEMO'] = self.conf.safe_get(
            'demo',
            'boolean'
        )
        self.bind = self.config['BUI_BIND'] = self.conf.safe_get('bind')
        version = self.conf.safe_get('version', 'integer')
        if unittest and version != 1:
            version = 1
        self.vers = self.config['BUI_VERS'] = version
        self.ssl = self.config['BUI_SSL'] = self.conf.safe_get(
            'ssl',
            'boolean'
        )
        self.standalone = self.config['STANDALONE'] = self.conf.safe_get(
            'standalone',
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
        self.logger.info('database: {}'.format(self.database))
        self.logger.info('with SQL: {}'.format(self.config['WITH_SQL']))
        self.logger.info('with Celery: {}'.format(self.config['WITH_CELERY']))
        self.logger.info('demo: {}'.format(self.config['BUI_DEMO']))

        self.init = True
        if not cli:
            self.load_modules()

    def load_modules(self, strict=True):
        if self.auth and 'none' not in self.auth:
            try:
                self.uhandler = UserAuthHandler(self)
            except Exception as e:
                self.logger.critical(
                    'Import Exception, module \'{0}\': {1}'.format(
                        self.auth,
                        str(e)
                    )
                )
                raise e
            self.acl_engine = self.config['BUI_ACL'] = self.conf.safe_get(
                'acl'
            )
            self.config['LOGIN_DISABLED'] = False
        else:
            self.config['LOGIN_DISABLED'] = True
            # No login => no ACL
            self.acl_engine = self.config['BUI_ACL'] = 'none'
            self.auth = self.config['BUI_AUTH'] = 'none'

        if self.acl_engine and self.acl_engine.lower() != 'none':
            try:
                # Try to load submodules from our current environment
                # first
                sys.path.insert(
                    0,
                    os.path.dirname(os.path.abspath(__file__))
                )
                mod = __import__(
                    'burpui.misc.acl.{0}'.format(
                        self.acl_engine.lower()
                    ),
                    fromlist=['ACLloader']
                )
                ACLloader = mod.ACLloader
                self.acl_handler = ACLloader(self)
                # for development purpose only
                from .misc.acl.interface import BUIacl
                self.acl = BUIacl
                self.acl = self.acl_handler.acl
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
            self.acl = False

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
            self.logger.critical(traceback.format_exc())
            self.logger.critical(
                'Failed loading backend for Burp version {0}: {1}'.format(
                    self.vers,
                    str(e)
                )
            )
            sys.exit(2)

    def manual_run(self):
        """The :func:`burpui.server.BUIServer.manual_run` functions is used to
        actually launch the ``Burp-UI`` server.
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
