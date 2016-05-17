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
from ._compat import ConfigParser
from datetime import timedelta

from flask import Flask


G_PORT = '5000'
G_BIND = '::'
G_REFRESH = '180'
G_LIVEREFRESH = '5'
G_SSL = 'False'
G_STANDALONE = 'True'
G_SSLCERT = ''
G_SSLKEY = ''
G_VERSION = '1'
G_AUTH = 'basic'
G_ACL = ''
G_STORAGE = ''
G_REDIS = ''
G_SCOOKIE = 'False'
G_APPSECRET = 'random'
G_COOKIETIME = '14'
G_PREFIX = ''


class BUIServer(Flask):
    """
    The :class:`burpui.server.BUIServer` class provides the ``Burp-UI`` server.
    """
    gunicorn = False

    def __init__(self):
        """The :class:`burpui.server.BUIServer` class provides the ``Burp-UI``
        server.

        :param app: The Flask application to launch
        """
        self.init = False
        # We cannot override the Flask's logger so we use our own
        self.builogger = logging.getLogger('burp-ui')
        self.builogger.disabled = True
        super(BUIServer, self).__init__(__name__)

    def enable_logger(self, enable=True):
        """Enable or disable the logger"""
        self.builogger.disabled = not enable

    @property
    def logger(self):
        return self.builogger

    def setup(self, conf=None):
        """The :func:`burpui.server.BUIServer.setup` functions is used to setup
        the whole server by parsing the configuration file and loading the
        different backends.

        :param conf: Path to a configuration file
        :type conf: str
        """
        self.sslcontext = None
        if not conf:
            conf = self.config['CFG']

        if not conf:
            raise IOError('No configuration file found')

        self.defaults = {
            'port': G_PORT,
            'bind': G_BIND,
            'refresh': G_REFRESH,
            'ssl': G_SSL,
            'sslcert': G_SSLCERT,
            'sslkey': G_SSLKEY,
            'version': G_VERSION,
            'auth': G_AUTH,
            'standalone': G_STANDALONE,
            'acl': G_ACL,
            'liverefresh': G_LIVEREFRESH,
            'storage': G_STORAGE,
            'redis': G_REDIS,
            'scookie': G_SCOOKIE,
            'appsecret': G_APPSECRET,
            'cookietime': G_COOKIETIME,
            'prefix': G_PREFIX,
        }
        config = ConfigParser.ConfigParser(self.defaults)
        with open(conf) as fp:
            config.readfp(fp)
            try:
                self.port = self._safe_config_get(
                    config.getint,
                    'port',
                    cast=int
                )
                self.bind = self._safe_config_get(config.get, 'bind')
                self.vers = self._safe_config_get(
                    config.getint,
                    'version',
                    cast=int
                )
                self.ssl = self._safe_config_get(
                    config.getboolean,
                    'ssl',
                    cast=bool
                )
                self.standalone = self._safe_config_get(
                    config.getboolean,
                    'standalone',
                    cast=bool
                )
                self.sslcert = self._safe_config_get(config.get, 'sslcert')
                self.sslkey = self._safe_config_get(config.get, 'sslkey')
                self.prefix = self._safe_config_get(config.get, 'prefix')
                if self.prefix and not self.prefix.startswith('/'):
                    if self.prefix.lower() != 'none':
                        self.logger.warning("'prefix' must start with a '/'!")
                    self.prefix = ''
                self.auth = self._safe_config_get(config.get, 'auth')
                if self.auth and self.auth.lower() != 'none':
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
                    self.acl_engine = self._safe_config_get(config.get, 'acl')
                else:
                    self.config['LOGIN_DISABLED'] = True
                    # No login => no ACL
                    self.acl_engine = 'none'
                    self.auth = 'none'

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

                # UI options
                self.config['REFRESH'] = self._safe_config_get(
                    config.getint,
                    'refresh',
                    'UI',
                    cast=int
                )
                self.config['LIVEREFRESH'] = self._safe_config_get(
                    config.getint,
                    'liverefresh',
                    'UI',
                    cast=int
                )

                # Production options
                self.storage = self._safe_config_get(
                    config.get,
                    'storage',
                    'Production'
                )
                self.redis = self._safe_config_get(
                    config.get,
                    'redis',
                    'Production'
                )

                # Security options
                self.scookie = self._safe_config_get(
                    config.getboolean,
                    'scookie',
                    'Security',
                    cast=bool
                )
                self.config['SECRET_KEY'] = self._safe_config_get(
                    config.get,
                    'appsecret',
                    'Security'
                )
                self.config['REMEMBER_COOKIE_DURATION'] = \
                    self.config['PERMANENT_SESSION_LIFETIME'] = \
                    timedelta(
                        days=self._safe_config_get(
                            config.getint,
                            'cookietime',
                            'Security',
                            cast=int
                        )
                    )

            except ConfigParser.NoOptionError as e:
                self.logger.error(str(e))

        self.config['STANDALONE'] = self.standalone

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
        self.logger.info('refresh: {}'.format(self.config['REFRESH']))
        self.logger.info('liverefresh: {}'.format(self.config['LIVEREFRESH']))
        self.logger.info('auth: {}'.format(self.auth))
        self.logger.info('acl: {}'.format(self.acl_engine))

        if self.standalone:
            module = 'burpui.misc.backend.burp{0}'.format(self.vers)
        else:
            module = 'burpui.misc.backend.multi'

        # This is used for development purpose only
        from .misc.backend.burp1 import Burp as BurpGeneric
        self.cli = BurpGeneric(dummy=True)
        try:
            # Try to load submodules from our current environment
            # first
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            mod = __import__(module, fromlist=['Burp'])
            Client = mod.Burp
            self.cli = Client(self, conf=conf)
        except Exception as e:
            traceback.print_exc()
            self.logger.critical(
                'Failed loading backend for Burp version {0}: {1}'.format(
                    self.vers,
                    str(e)
                )
            )
            sys.exit(2)

        self.init = True

    def _safe_config_get(self, callback, key, sect='Global', cast=None):
        """:func:`burpui.server.BUIServer._safe_config_get` is a wrapper to
        handle Exceptions throwed by :mod:`ConfigParser`.

        :param callback: Function to wrap
        :type callback: callable

        :param key: Key to retrieve
        :type key: str

        :param sect: Section of the config file to read
        :type sect: str

        :param cast: Cast the returned value if provided
        :type case: callable

        :returns: The value returned by the `callback`
        """
        try:
            return callback(sect, key)
        except ConfigParser.NoOptionError as e:
            self.logger.error(str(e))
        except ConfigParser.NoSectionError as e:
            self.logger.warning(str(e))
            if key in self.defaults:
                if cast:
                    try:
                        return cast(self.defaults[key])
                    except ValueError:
                        return None
                return self.defaults[key]
        return None

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
