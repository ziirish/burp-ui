# -*- coding: utf8 -*-
import os
import struct
import select
try:
    import ujson as json
except ImportError:
    import json
import time
import sys
import pickle
import traceback
import ConfigParser
import SocketServer
from threading import Thread

g_port = '10000'
g_bind = '::'
g_ssl = 'False'
g_version = '1'
g_sslcert = ''
g_sslkey = ''
g_timeout = '5'
g_password = 'password'


class BUIAgent:
    def __init__(self, conf=None, debug=False):
        global g_port, g_bind, g_ssl, g_version, g_sslcert, g_sslkey, g_password
        self.conf = conf
        self.dbg = debug
        print 'conf: ' + self.conf
        print 'debug: ' + str(self.dbg)
        if not conf:
            raise IOError('No configuration file found')

        config = ConfigParser.ConfigParser({
            'port': g_port, 'bind': g_bind,
            'ssl': g_ssl, 'sslcert': g_sslcert, 'sslkey': g_sslkey,
            'version': g_version, 'password': g_password
        })
        with open(conf) as fp:
            config.readfp(fp)
            try:
                self.port = config.getint('Global', 'port')
                self.bind = config.get('Global', 'bind')
                self.vers = config.getint('Global', 'version')
                self.timeout = config.getint('Global', 'timeout')
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
            traceback.print_exc()
            self.debug('Failed loading backend for Burp version %d: %s', self.vers, str(e))
            sys.exit(2)

        self.methods = {
            'status': self.backend.status,
            'get_backup_logs': self.backend.get_backup_logs,
            'get_clients_report': self.backend.get_clients_report,
            'get_counters': self.backend.get_counters,
            'is_backup_running': self.backend.is_backup_running,
            'is_one_backup_running': self.backend.is_one_backup_running,
            'get_all_clients': self.backend.get_all_clients,
            'get_client': self.backend.get_client,
            'get_tree': self.backend.get_tree,
            'restore_files': self.backend.restore_files,
            'read_conf_cli': self.backend.read_conf_cli,
            'store_conf_cli': self.backend.store_conf_cli,
            'read_conf_srv': self.backend.read_conf_srv,
            'store_conf_srv': self.backend.store_conf_srv,
            'expand_path': self.backend.expand_path,
            'delete_client': self.backend.delete_client,
            'get_parser_attr': self.backend.get_parser_attr
        }

        self.server = AgentServer((self.bind, self.port), AgentTCPHandler, self)

    def run(self):
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            sys.exit(0)

    def debug(self, msg, *args):
        if self.dbg:
            print msg % (args)


class AgentTCPHandler(SocketServer.BaseRequestHandler):
    "One instance per connection.  Override handle(self) to customize action."
    def handle(self):
        # self.request is the client connection
        self.server.agent.debug('===============>')
        timeout = self.server.agent.timeout
        try:
            err = None
            r, _, _ = select.select([self.request], [], [], timeout)
            if not r:
                raise Exception('Socket timed-out 1')
            lengthbuf = self.request.recv(8)
            length, = struct.unpack('!Q', lengthbuf)
            data = self.recvall(length)
            self.server.agent.debug('####################')
            self.server.agent.debug('recv: %s', data)
            self.server.agent.debug('####################')
            j = json.loads(data)
            _, w, _ = select.select([], [self.request], [], timeout)
            if not w:
                raise Exception('Socket timed-out 2')
            if j['password'] != self.server.agent.password:
                self.server.agent.debug('-----> Wrong Password <-----')
                self.request.sendall('KO')
                return
            if j['func'] not in self.server.agent.methods:
                self.server.agent.debug('-----> Wrong method <-----')
                self.request.sendall('KO')
                return
            self.request.sendall('OK')
            if j['func'] == 'restore_files':
                res, err = self.server.agent.methods[j['func']](**j['args'])
            else:
                if j['args']:
                    if 'pickled' in j and j['pickled']:
                        # de-serialize arguments if needed
                        j['args'] = pickle.loads(j['args'])
                    res = json.dumps(self.server.agent.methods[j['func']](**j['args']))
                else:
                    res = json.dumps(self.server.agent.methods[j['func']]())
            self.server.agent.debug('####################')
            self.server.agent.debug('result: %s', res)
            self.server.agent.debug('####################')
            _, w, _ = select.select([], [self.request], [], timeout)
            if not w:
                raise Exception('Socket timed-out 3')
            if j['func'] == 'restore_files':
                if err:
                    self.request.sendall('KO')
                    size = len(err)
                    self.request.sendall(struct.pack('!Q', size))
                    self.request.sendall(err)
                    raise Exception('Restoration failed')
                self.request.sendall('OK')
                size = os.path.getsize(res)
                self.request.sendall(struct.pack('!Q', size))
                with open(res, 'rb') as f:
                    buf = f.read(1024)
                    while buf:
                        self.server.agent.debug('sending %d Bytes', len(buf))
                        self.request.sendall(buf)
                        buf = f.read(1024)
                        _, w, _ = select.select([], [self.request], [], timeout)
                        if not w:
                            raise Exception('Socket timed-out 4')
                os.unlink(res)
            else:
                self.request.sendall(struct.pack('!Q', len(res)))
                self.request.sendall(res)
            self.request.close()
        except Exception as e:
            self.server.agent.debug('ERROR: %s', str(e))
        finally:
            self.server.agent.debug('<===============')

    def recvall(self, length=1024):
        buf = b''
        bsize = 1024
        received = 0
        if length < bsize:
            bsize = length
        while received < length:
            newbuf = self.request.recv(bsize)
            if not newbuf:
                time.sleep(0.1)
                continue
            buf += newbuf
            received += len(newbuf)
        return buf


class AgentServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, agent=None):
        self.agent = agent
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

    def get_request(self):
        if self.agent.ssl:
            import ssl
            (newsocket, fromaddr) = SocketServer.TCPServer.get_request(self)
            connstream = ssl.wrap_socket(
                newsocket,
                server_side=True,
                certfile=self.agent.sslcert,
                keyfile=self.agent.sslkey,
                ssl_version=ssl.PROTOCOL_SSLv23
            )
            return connstream, fromaddr
        # if we don't use ssl, use the 'super' method
        return SocketServer.TCPServer.get_request(self)
