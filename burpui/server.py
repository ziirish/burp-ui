# -*- coding: utf8 -*-
"""
.. module:: server
    :platform: Unix
    :synopsis: Burp-UI server module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import traceback
import sys

from burpui.misc.backend.burp1 import Burp as BurpGeneric

g_port = '5000'
g_bind = '::'
g_refresh = '180'
g_liverefresh = '5'
g_ssl = 'False'
g_standalone = 'True'
g_sslcert = ''
g_sslkey = ''
g_version = '1'
g_auth = 'basic'
g_acl = ''


class BUIServer:
    """
    The :class:`burpui.server.BUIServer` class provides the ``Burp-UI`` server.
    """
    def __init__(self, app=None):
        """
        The :class:`burpui.server.BUIServer` class provides the ``Burp-UI`` server.

        :param app: The Flask application to launch
        """
        self.init = False
        self.app = app

    def setup(self, conf=None):
        """
        The :func:`burpui.server.BUIServer.setup` functions is used to setup the
        whole server by parsing the configuration file and loading the different
        backends.

        :param conf: Path to a configuration file
        :type conf: str
        """
        global g_refresh, g_port, g_bind, g_ssl, g_sslcert, g_sslkey, g_version, g_auth, g_standalone, g_acl, g_liverefresh
        self.sslcontext = None
        if not conf:
            conf = self.app.config['CFG']

        if not conf:
            raise IOError('No configuration file found')

        self.defaults = {
            'port': g_port, 'bind': g_bind,
            'refresh': g_refresh, 'ssl': g_ssl, 'sslcert': g_sslcert,
            'sslkey': g_sslkey, 'version': g_version, 'auth': g_auth,
            'standalone': g_standalone, 'acl': g_acl,
            'liverefresh': g_liverefresh
        }
        config = ConfigParser.ConfigParser(self.defaults)
        with open(conf) as fp:
            config.readfp(fp)
            try:
                self.port = self._safe_config_get(config.getint, 'port', cast=int)
                self.bind = self._safe_config_get(config.get, 'bind')
                self.vers = self._safe_config_get(config.getint, 'version', cast=int)
                self.ssl = self._safe_config_get(config.getboolean, 'ssl', cast=bool)
                self.standalone = self._safe_config_get(config.getboolean, 'standalone', cast=bool)
                self.sslcert = self._safe_config_get(config.get, 'sslcert')
                self.sslkey = self._safe_config_get(config.get, 'sslkey')
                self.auth = self._safe_config_get(config.get, 'auth')
                if self.auth and self.auth.lower() != 'none':
                    try:
                        mod = __import__(
                            'burpui.misc.auth.{0}'.format(self.auth.lower()),
                            fromlist=['UserHandler']
                        )
                        UserHandler = mod.UserHandler
                        self.uhandler = UserHandler(self.app)
                    except Exception as e:
                        traceback.print_exc()
                        self.app.logger.error('Import Exception, module \'{0}\': {1}'.format(self.auth, str(e)))
                        sys.exit(1)
                else:
                    # I know that's ugly, but hey, I need it!
                    self.app.login_manager._login_disabled = True
                self.acl_engine = self._safe_config_get(config.get, 'acl')
                if self.acl_engine and self.acl_engine.lower() != 'none':
                    try:
                        mod = __import__(
                            'burpui.misc.acl.{0}'.format(self.acl_engine.lower()),
                            fromlist=['ACLloader']
                        )
                        ACLloader = mod.ACLloader
                        self.acl_handler = ACLloader(self.app, self.standalone)
                        # for development purpose only
                        from burpui.misc.acl.interface import BUIacl
                        self.acl = BUIacl
                        self.acl = self.acl_handler.acl
                    except Exception as e:
                        traceback.print_exc()
                        self.app.logger.error('Import Exception, module \'{0}\': {1}'.format(self.acl_engine, str(e)))
                        sys.exit(1)
                else:
                    self.acl_handler = False
                    self.acl = False

                self.app.config['REFRESH'] = self._safe_config_get(config.getint, 'refresh', 'UI', cast=int)
                self.app.config['LIVEREFRESH'] = self._safe_config_get(config.getint, 'liverefresh', 'UI', cast=int)

            except ConfigParser.NoOptionError as e:
                self.app.logger.error(str(e))

        self.app.config['STANDALONE'] = self.standalone

        self.app.logger.info('burp version: {}'.format(self.vers))
        self.app.logger.info('listen port: {}'.format(self.port))
        self.app.logger.info('bind addr: {}'.format(self.bind))
        self.app.logger.info('use ssl: {}'.format(self.ssl))
        self.app.logger.info('standalone: {}'.format(self.standalone))
        self.app.logger.info('sslcert: {}'.format(self.sslcert))
        self.app.logger.info('sslkey: {}'.format(self.sslkey))
        self.app.logger.info('refresh: {}'.format(self.app.config['REFRESH']))
        self.app.logger.info('liverefresh: {}'.format(self.app.config['LIVEREFRESH']))

        if self.standalone:
            module = 'burpui.misc.backend.burp{0}'.format(self.vers)
        else:
            module = 'burpui.misc.backend.multi'
        # This instanciation is used for development purpose only
        self.cli = BurpGeneric(dummy=True)
        try:
            mod = __import__(module, fromlist=['Burp'])
            Client = mod.Burp
            self.cli = Client(self, conf=conf)
        except Exception as e:
            traceback.print_exc()
            self.app.logger.error('Failed loading backend for Burp version {0}: {1}'.format(self.vers, str(e)))
            sys.exit(2)

        self.init = True

    def _safe_config_get(self, callback, key, sect='Global', cast=None):
        """
        :func:`burpui.server.BUIServer._safe_config_get` is a wrapper to handle
        Exceptions throwed by :mod:`ConfigParser`.

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
            self.app.logger.error(str(e))
        except ConfigParser.NoSectionError as e:
            self.app.logger.warning(str(e))
            if key in self.defaults:
                if cast:
                    try:
                        return cast(self.defaults[key])
                    except ValueError:
                        return None
                return self.defaults[key]
        return None

    def run(self, debug=False):
        """
        The :func:`burpui.server.BUIServer.run` functions is used to actually
        launch the ``Burp-UI`` server.

        :param debug: Enable debug mode
        :type conf: bool
        """
        if not self.init:
            self.setup()

        if self.ssl:
            self.sslcontext = (self.sslcert, self.sslkey)

        if self.sslcontext:
            self.app.config['SSL'] = True
            self.app.run(host=self.bind, port=self.port, debug=debug, ssl_context=self.sslcontext)
        else:
            self.app.run(host=self.bind, port=self.port, debug=debug)
