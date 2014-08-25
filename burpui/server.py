# -*- coding: utf8 -*-
import ConfigParser
import sys

g_burpport = 4972
g_burphost = '127.0.0.1'
g_port = 5000
g_bind = '::'
g_refresh = 15
g_ssl = False
g_sslcert = ''
g_sslkey = ''
g_version = 1
g_auth = 'ldap'

class Server:
    def __init__(self, app=None):
        self.init = False
        self.app = app

    def setup(self, conf=None):
        global g_refresh, g_burpport, g_burphost, g_port, g_bind, g_ssl, g_sslcert, g_sslkey, g_version, g_auth
        self.sslcontext = None
        if not conf:
            conf = self.app.config['CFG']

        config = ConfigParser.ConfigParser({'bport': g_burpport, 'bhost': g_burphost, 'port': g_port,
                    'bind': g_bind, 'refresh': g_refresh, 'ssl': g_ssl, 'sslcert': g_sslcert,
                    'sslkey': g_sslkey, 'version': g_version, 'auth': g_auth})
        with open(conf) as fp:
            config.readfp(fp)
            try:
                self.burpport = config.getint('Global', 'bport')
                self.burphost = config.get('Global', 'bhost')
                self.port = config.getint('Global', 'port')
                self.bind = config.get('Global', 'bind')
                self.vers = config.getint('Global', 'version')
                try:
                    self.ssl = config.getboolean('Global', 'ssl')
                except ValueError:
                    self.app.logger.error("Wrong value for 'ssl' key! Assuming 'false'")
                    self.ssl = False
                self.sslcert = config.get('Global', 'sslcert')
                self.sslkey = config.get('Global', 'sslkey')
                try:
                    mod = __import__('burpui.misc.auth.{0}'.format(config.get('Global', 'auth')), fromlist=['UserHandler'])
                    UserHandler = mod.UserHandler
                    self.uhandler = UserHandler(self.app)
                except Exception:
                    self.app.logger.error('Import Exception, module \'%s\'', config.get('Global', 'auth'))
                    sys.exit(1)
            except ConfigParser.NoOptionError:
                self.app.logger.error("Missing option")

            self.app.config['REFRESH'] = config.getint('UI', 'refresh')

        self.app.logger.info('burp port: %d', self.burpport)
        self.app.logger.info('burp host: %s', self.burphost)
        self.app.logger.info('burp version: %d', self.vers)
        self.app.logger.info('listen port: %d', self.port)
        self.app.logger.info('bind addr: %s', self.bind)
        self.app.logger.info('use ssl: %s', self.ssl)
        self.app.logger.info('sslcert: %s', self.sslcert)
        self.app.logger.info('sslkey: %s', self.sslkey)
        self.app.logger.info('refresh: %d', self.app.config['REFRESH'])

        try:
            mod = __import__('burpui.misc.backend.burp{0}'.format(self.vers), fromlist=['Burp'])
            Client = mod.Burp
            self.cli = Client(self.app, self.burphost, self.burpport)
        except Exception:
            self.app.logger.error('Failed loading backend for Burp version %d', self.vers)
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
            self.app.run(host=self.bind, port=self.port, debug=debug, ssl_context=self.sslcontext)
        else:
            self.app.run(host=self.bind, port=self.port, debug=debug)

