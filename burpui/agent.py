# -*- coding: utf8 -*-
import os
import struct
import select
try:
    import ujson as json
except ImportError:
    import json
import re
import time
import sys
import logging
import pickle
import traceback
import ConfigParser
import SocketServer
from threading import Thread
from logging import Formatter, StreamHandler
from logging.handlers import RotatingFileHandler
from burpui.misc.utils import BUIlogging

g_port = '10000'
g_bind = '::'
g_ssl = 'False'
g_version = '1'
g_sslcert = ''
g_sslkey = ''
g_timeout = '5'
g_password = 'password'


class BUIAgent(BUIlogging):
    def __init__(self, conf=None, debug=False, logfile=None):
        global g_port, g_bind, g_ssl, g_version, g_sslcert, g_sslkey, g_password
        self.conf = conf
        self.dbg = debug
        self.logger = None
        if debug > logging.NOTSET:
            levels = [0, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
            if debug >= len(levels):
                debug = len(levels) - 1
            lvl = levels[debug]
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(lvl)
            if logfile:
                handler = RotatingFileHandler(logfile, maxBytes=1024 * 1024 * 100, backupCount=20)
                LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
            else:
                handler = StreamHandler()
                LOG_FORMAT = (
                    '-' * 80 + '\n' +
                    '%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
                    '%(message)s\n' +
                    '-' * 80
                )
            handler.setLevel(lvl)
            handler.setFormatter(Formatter(LOG_FORMAT))
            self.logger.addHandler(handler)
            self.logger.info('conf: ' + self.conf)
            self.logger.info('level: ' + logging.getLevelName(lvl))
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
                self.port = self._safe_config_get(config.getint, 'port', cast=int)
                self.bind = self._safe_config_get(config.get, 'bind')
                self.vers = self._safe_config_get(config.getint, 'version', cast=int)
                self.timeout = self._safe_config_get(config.getint, 'timeout', cast=int)
                try:
                    self.ssl = config.getboolean('Global', 'ssl')
                except ValueError:
                    self.app.logger.error("Wrong value for 'ssl' key! Assuming 'false'")
                    self.ssl = False
                self.sslcert = self._safe_config_get(config.get, 'sslcert')
                self.sslkey = self._safe_config_get(config.get, 'sslkey')
                self.password = self._safe_config_get(config.get, 'password')
            except ConfigParser.NoOptionError, e:
                raise e

        module = 'burpui.misc.backend.burp{0}'.format(self.vers)
        try:
            mod = __import__(module, fromlist=['Burp'])
            Client = mod.Burp
            self.backend = Client(conf=conf)
            self.backend.set_logger(self.logger)
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

    def _safe_config_get(self, callback, key, sect='Global', cast=None):
        """
        :func:`burpui.agent._safe_config_get` is a wrapper to handle
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
            self._logger('error', str(e))
        except ConfigParser.NoSectionError as e:
            self._logger('warning', str(e))
            if key in self.defaults:
                if cast:
                    return cast(self.defaults[key])
                return self.defaults[key]
        return None

    def run(self):
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            sys.exit(0)

    def _logger(self, level, message):
        # hide password from logs
        msg = message
        if self.logger.getEffectiveLevel() != logging.DEBUG:
            msg = re.sub(r'"password": \S+', '"password": "*****",', message)
        super(BUIAgent, self)._logger(level, msg)


class AgentTCPHandler(SocketServer.BaseRequestHandler):
    "One instance per connection.  Override handle(self) to customize action."
    def handle(self):
        # self.request is the client connection
        timeout = self.server.agent.timeout
        try:
            err = None
            r, _, _ = select.select([self.request], [], [], timeout)
            if not r:
                raise Exception('Socket timed-out 1')
            lengthbuf = self.request.recv(8)
            length, = struct.unpack('!Q', lengthbuf)
            data = self.recvall(length)
            self.server.agent._logger('info','recv: {}'.format(data))
            j = json.loads(data)
            _, w, _ = select.select([], [self.request], [], timeout)
            if not w:
                raise Exception('Socket timed-out 2')
            if j['password'] != self.server.agent.password:
                self.server.agent._logger('warning', '-----> Wrong Password <-----')
                self.request.sendall('KO')
                return
            if j['func'] not in self.server.agent.methods:
                self.server.agent._logger('warning', '-----> Wrong method <-----')
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
            self.server.agent._logger('info', 'result: {}'.format(res))
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
                        self.server.agent._logger('info', 'sending {} Bytes'.format(len(buf)))
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
            self.server.agent._logger('error', '{}'.format(str(e)))

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
