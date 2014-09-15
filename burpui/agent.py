# -*- coding: utf8 -*-
import sys
import struct
import json
import ConfigParser
import SocketServer
from threading import Thread

g_port = 10000
g_bind = '::'
g_ssl  = False
g_version = 1
g_sslcert = ''
g_sslkey  = ''
g_password = 'password'

class BUIAgent:
    def __init__(self, conf=None):
        global g_port, g_bind, g_ssl, g_version, g_sslcert, g_sslkey, g_password
        self.conf = conf
        if not conf:
            raise IOError('No configuration file found')

        config = ConfigParser.ConfigParser({'port': g_port,'bind': g_bind,
                    'ssl': g_ssl, 'sslcert': g_sslcert, 'sslkey': g_sslkey,
                    'version': g_version, 'password': g_password})
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
                self.sslcert = config.get('Global', 'sslcert')
                self.sslkey = config.get('Global', 'sslkey')
                self.password = config.get('Global', 'password')
            except ConfigParser.NoOptionError, e:
                raise e

        module = 'burpui.misc.backend.burp{0}'.format(self.vers)
        try:
            mod = __import__(module, fromlist=['Burp'])
            Client = mod.Burp
            self.backend = Client(conf=conf)
        except Exception, e:
            self.app.logger.error('Failed loading backend for Burp version %d: %s', self.vers, str(e))
            sys.exit(2)

        self.methods = {
                'status': self.backend.status,
                'parse_backup_log': self.backend.parse_backup_log,
                'get_counters': self.backend.get_counters,
                'is_backup_running': self.backend.is_backup_running,
                'is_one_backup_running': self.backend.is_one_backup_running,
                'get_all_clients': self.backend.get_all_clients,
                'get_client': self.backend.get_client,
                'get_tree': self.backend.get_tree
            }

        self.server = AgentServer((self.bind, self.port), AgentTCPHandler, self)

    def run(self):
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            sys.exit(0)


class AgentTCPHandler(SocketServer.BaseRequestHandler):
    "One instance per connection.  Override handle(self) to customize action."
    def handle(self):
        # self.request is the client connection
        lengthbuf = self.request.recv(8)
        length, = struct.unpack('!Q', lengthbuf)
        data = self.request.recv(length)
        print '--------------------'
        print 'recv: '+data
        print '--------------------'
        j = json.loads(data)
        if j['password'] != self.server.agent.password:
            print '-----> Wrong Password <-----'
            self.request.sendall('KO')
            return
        if j['func'] not in self.server.agent.methods:
            print '-----> Wrong method <-----'
            self.request.sendall('KO')
            return
        self.request.sendall('OK')
        if j['args']:
            res = json.dumps(self.server.agent.methods[j['func']](**j['args']))
        else:
            res = json.dumps(self.server.agent.methods[j['func']]())
        print '--------------------'
        print 'result: '+res
        print '--------------------'
        self.request.sendall(struct.pack('!Q', len(res)))
        self.request.sendall(res)
        self.request.close()

class AgentServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, agent=None):
        self.agent = agent
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
