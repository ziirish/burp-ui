# -*- coding: utf8 -*-
import ConfigParser
import sys

g_port = '5000'
g_bind = '::'
g_refresh = '15'
g_ssl = 'False'
g_standalone = 'True'
g_sslcert = ''
g_sslkey = ''
g_version = '1'
g_auth = 'basic'

class BUIServer:
    def __init__(self, app=None):
        self.init = False
        self.app = app

    def setup(self, conf=None):
        global g_refresh, g_port, g_bind, g_ssl, g_sslcert, g_sslkey, g_version, g_auth, g_standalone
        self.sslcontext = None
        if not conf:
            conf = self.app.config['CFG']

        if not conf:
            raise IOError('No configuration file found')

        config = ConfigParser.ConfigParser({'port': g_port,'bind': g_bind,
                    'refresh': g_refresh, 'ssl': g_ssl, 'sslcert': g_sslcert,
                    'sslkey': g_sslkey, 'version': g_version, 'auth': g_auth,
                    'standalone': g_standalone})
        with open(conf) as fp:
            config.readfp(fp)
            try:
                self.port = config.getint('Global', 'port')
                self.bind = config.get('Global', 'bind')
                self.vers = config.getint('Global', 'version')
                try:
                    self.ssl = config.getboolean('Global', 'ssl')
                except ValueError:
                    self.app.logger.error("Wrong value for 'ssl' key! Assuming 'false'")
                    self.ssl = False
                try:
                    self.standalone = config.getboolean('Global', 'standalone')
                except ValueError:
                    self.app.logger.error("Wrong value for 'standalone' key! Assuming 'True'")
                    self.standalone = True
                self.sslcert = config.get('Global', 'sslcert')
                self.sslkey = config.get('Global', 'sslkey')
                self.auth = config.get('Global', 'auth')
                if self.auth != 'none':
                    try:
                        mod = __import__('burpui.misc.auth.{0}'.format(config.get('Global', 'auth')), fromlist=['UserHandler'])
                        UserHandler = mod.UserHandler
                        self.uhandler = UserHandler(self.app)
                    except Exception, e:
                        self.app.logger.error('Import Exception, module \'%s\': %s', config.get('Global', 'auth'), str(e))
                        sys.exit(1)
                else:
                    # I know that's ugly, but hey, I need it!
                    self.app.login_manager._login_disabled = True
            except ConfigParser.NoOptionError, e:
                self.app.logger.error(str(e))

            self.app.config['REFRESH'] = config.getint('UI', 'refresh')

        self.app.config['STANDALONE'] = self.standalone

        self.app.logger.info('burp version: %d', self.vers)
        self.app.logger.info('listen port: %d', self.port)
        self.app.logger.info('bind addr: %s', self.bind)
        self.app.logger.info('use ssl: %s', self.ssl)
        self.app.logger.info('standalone: %s', self.standalone)
        self.app.logger.info('sslcert: %s', self.sslcert)
        self.app.logger.info('sslkey: %s', self.sslkey)
        self.app.logger.info('refresh: %d', self.app.config['REFRESH'])

        if self.standalone:
            module = 'burpui.misc.backend.burp{0}'.format(self.vers)
        else:
            module = 'burpui.misc.backend.multi'
        try:
            mod = __import__(module, fromlist=['Burp'])
            Client = mod.Burp
            self.cli = Client(self.app, conf=conf)
        except Exception, e:
            self.app.logger.error('Failed loading backend for Burp version %d: %s', self.vers, str(e))
            sys.exit(2)

        self.init = True

    def run(self, debug=False):
        if not self.init:
            self.setup()

        if self.ssl:
            from OpenSSL import SSL
            self.sslcontext = SSL.Context(SSL.SSLv23_METHOD)
            self.sslcontext.use_privatekey_file(self.sslkey)
            self.sslcontext.use_certificate_file(self.sslcert)

        if self.sslcontext:
            self.app.config['SSL'] = True
            self.app.run(host=self.bind, port=self.port, debug=debug, ssl_context=self.sslcontext)
        else:
            self.app.run(host=self.bind, port=self.port, debug=debug)

