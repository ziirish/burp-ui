# -*- coding: utf8 -*-
import os
import struct
import re
import time
import sys
import logging
import pickle
import traceback
import socket
try:
    import ujson as json
except ImportError:
    import json
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

from logging.handlers import RotatingFileHandler
from .misc.backend.interface import BUIbackend

g_port = '10000'
g_bind = '::'
g_ssl = 'False'
g_version = '1'
g_sslcert = ''
g_sslkey = ''
g_password = 'password'

DISCLOSURE = 5


class BUIAgent(BUIbackend):
    # These functions MUST be implemented because we inherit an abstract class.
    # The hack here is to get the list of the functions and let the interpreter
    # think we don't have to implement them.
    # Thanks to this list, we know what function are implemented by our backend.
    foreign = BUIbackend.__abstractmethods__
    BUIbackend.__abstractmethods__ = frozenset()

    def __init__(self, conf=None, debug=False, logfile=None):
        global g_port, g_bind, g_ssl, g_version, g_sslcert, g_sslkey, g_password
        self.conf = conf
        self.dbg = debug
        self.padding = 1
        if debug > logging.NOTSET:
            logging.addLevelName(DISCLOSURE, 'DISCLOSURE')
            levels = [0, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG, DISCLOSURE]
            if debug >= len(levels):
                debug = len(levels) - 1
            lvl = levels[debug]
            self.app.logger = logging.getLogger(__name__)
            self.set_logger(self.app.logger)
            self.logger.setLevel(lvl)
            if logfile:
                handler = RotatingFileHandler(logfile, maxBytes=1024 * 1024 * 100, backupCount=20)
                LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s'
            else:
                handler = logging.StreamHandler()
                LOG_FORMAT = (
                    '-' * 80 + '\n' +
                    '%(levelname)s in %(module)s.%(funcName)s [%(pathname)s:%(lineno)d]:\n' +
                    '%(message)s\n' +
                    '-' * 80
                )
            handler.setLevel(lvl)
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            self.logger.addHandler(handler)
            self._logger('info', 'conf: ' + self.conf)
            self._logger('info', 'level: ' + logging.getLevelName(lvl))
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
                self.port = self._safe_config_get(config.getint, 'port', 'Global', cast=int)
                self.bind = self._safe_config_get(config.get, 'bind', 'Global')
                self.vers = self._safe_config_get(config.getint, 'version', 'Global', cast=int)
                try:
                    self.ssl = config.getboolean('Global', 'ssl')
                except ValueError:
                    self._logger('warning', "Wrong value for 'ssl' key! Assuming 'false'")
                    self.ssl = False
                self.sslcert = self._safe_config_get(config.get, 'sslcert', 'Global')
                self.sslkey = self._safe_config_get(config.get, 'sslkey', 'Global')
                self.password = self._safe_config_get(config.get, 'password', 'Global')
            except ConfigParser.NoOptionError as e:
                raise e

        module = 'burpui.misc.backend.burp{0}'.format(self.vers)
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            mod = __import__(module, fromlist=['Burp'])
            Client = mod.Burp
            self.backend = Client(conf=conf)
            self.backend.set_logger(self.logger)
        except Exception as e:
            self._logger('error', '{}\n\nFailed loading backend for Burp version {}: {}'.format(traceback.format_exc(), self.vers, str(e)))
            sys.exit(2)

        self.server = AgentServer((self.bind, self.port), AgentTCPHandler, self)

    def __getattribute__(self, name):
        # always return this value because we need it and if we don't do that
        # we'll end up with an infinite loop
        if name == 'foreign':
            return object.__getattribute__(self, name)
        # now we can retrieve the 'foreign' list and know if the object called
        # is in the backend
        if name in self.foreign:
            return getattr(self.backend, name)
        return object.__getattribute__(self, name)

    def run(self):
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            sys.exit(0)

    def _logger(self, level, message):
        # hide password from logs
        msg = message
        if not self.logger:
            return
        if self.logger.getEffectiveLevel() != DISCLOSURE:
            msg = re.sub(r'([\'"])password\1(\s*:\s*)([\'"])[^\3]+?\3', r'\1password\1\2\3*****\3', message)
        super(BUIAgent, self)._logger(level, msg)


class AgentTCPHandler(SocketServer.BaseRequestHandler):
    "One instance per connection.  Override handle(self) to customize action."
    def handle(self):
        # self.request is the client connection
        try:
            self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            while True:
                err = None
                lengthbuf = self.request.recv(8)
                length, = struct.unpack('!Q', lengthbuf)
                data = self.recvall(length)
                self.server.agent._logger('info', 'recv: {}'.format(data))
                txt = data.decode('UTF-8')
                if txt == 'RE':
                    break
                j = json.loads(txt)
                if j['password'] != self.server.agent.password:
                    self.server.agent._logger('warning', '-----> Wrong Password <-----')
                    self.request.sendall(b'KO')
                    return
                self.request.sendall(b'OK')
                if j['func'] == 'restore_files':
                    res, err = getattr(self.server.agent, j['func'])(**j['args'])
                else:
                    if j['args']:
                        if 'pickled' in j and j['pickled']:
                            # de-serialize arguments if needed
                            j['args'] = pickle.loads(j['args'])
                        res = json.dumps(getattr(self.server.agent, j['func'])(**j['args']))
                    else:
                        res = json.dumps(getattr(self.server.agent, j['func'])())
                self.server.agent._logger('info', 'result: {}'.format(res))
                if j['func'] == 'restore_files':
                    if err:
                        self.request.sendall(b'KO')
                        size = len(err)
                        self.request.sendall(struct.pack('!Q', size))
                        self.request.sendall(err.encode('UTF-8'))
                        raise Exception('Restoration failed')
                    self.request.sendall(b'OK')
                    size = os.path.getsize(res)
                    self.request.sendall(struct.pack('!Q', size))
                    with open(res, 'rb') as f:
                        buf = f.read(1024)
                        while buf:
                            self.server.agent._logger('info', 'sending {} Bytes'.format(len(buf)))
                            self.request.sendall(buf)
                            buf = f.read(1024)
                    os.unlink(res)
                else:
                    self.request.sendall(struct.pack('!Q', len(res)))
                    self.request.sendall(res.encode('UTF-8'))
        except AttributeError as e:
            self.server.agent._logger('warning', '{}\nWrong method => {}'.format(traceback.format_exc(), str(e)))
            self.request.sendall(b'KO')
            return
        except Exception as e:
            self.server.agent._logger('error', '!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))
        finally:
            try:
                self.request.close()
            except Exception as e:
                self.server.agent._logger('error', '!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))

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
        if self.agent.ssl:
            import ssl
            self.socket = ssl.wrap_socket(
                self.socket,
                server_side=True,
                certfile=self.agent.sslcert,
                keyfile=self.agent.sslkey,
                ssl_version=ssl.PROTOCOL_SSLv23
            )
