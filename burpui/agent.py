# -*- coding: utf8 -*-
import os
import struct
import re
import time
import sys
import logging
import traceback
import threading
import socket
try:
    import cPickle as pickle
except ImportError:
    import pickle
try:
    import ujson as json
except ImportError:
    import json
try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

from logging.handlers import RotatingFileHandler
from .exceptions import BUIserverException
from .misc.backend.interface import BUIbackend
from ._compat import ConfigParser

from Queue import Queue

g_port = u'10000'
g_bind = u'::'
g_ssl = u'False'
g_version = u'1'
g_sslcert = u''
g_sslkey = u''
g_password = u'password'
g_threads = u'5'

DISCLOSURE = 5


class BurpHandler(BUIbackend):
    # These functions MUST be implemented because we inherit an abstract class.
    # The hack here is to get the list of the functions and let the interpreter
    # think we don't have to implement them.
    # Thanks to this list, we know what function are implemented by our backend.
    foreign = BUIbackend.__abstractmethods__
    BUIbackend.__abstractmethods__ = frozenset()

    def __init__(self, vers=1, logger=None, conf=None):
        self.vers = vers
        self.logger = logger

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


class BUIAgent(BUIbackend):
    BUIbackend.__abstractmethods__ = frozenset()
    defaults = {
        'port': g_port, 'bind': g_bind,
        'ssl': g_ssl, 'sslcert': g_sslcert, 'sslkey': g_sslkey,
        'version': g_version, 'password': g_password, 'threads': g_threads
    }

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
        if not self.conf:
            raise IOError('No configuration file found')

        config = ConfigParser.ConfigParser({
            'port': g_port, 'bind': g_bind,
            'ssl': g_ssl, 'sslcert': g_sslcert, 'sslkey': g_sslkey,
            'version': g_version, 'password': g_password, 'threads': g_threads
        })
        with open(self.conf) as fp:
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
                self.threads = self._safe_config_get(config.getint, 'threads', 'Global', cast=int)
            except ConfigParser.NoOptionError as e:
                raise e

        self.server = AgentServer((self.bind, self.port), AgentTCPHandler, self)

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
        """self.request is the client connection"""
        try:
            self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # try to pick the first available client
            self.idx = -1
            for (i, l) in enumerate(self.server.locks):
                if l.acquire(False):
                    self.cli = self.server.clients[i]
                    self.idx = i

            # if none of them are available pick one randomly and wait for it
            if self.idx == -1:
                from random import randint
                self.idx = randint(0, len(self.server.locks) - 1)
                self.server.locks[self.idx].acquire()
                self.cli = self.server.clients[self.idx]

            err = None
            lengthbuf = self.request.recv(8)
            length, = struct.unpack('!Q', lengthbuf)
            data = self.recvall(length)
            self.server.agent._logger('info', 'recv: {}'.format(data))
            txt = data.decode('UTF-8')
            if txt == 'RE':
                return
            j = json.loads(txt)
            if j['password'] != self.server.agent.password:
                self.server.agent._logger('warning', '-----> Wrong Password <-----')
                self.request.sendall(b'KO')
                return
            try:
                if j['func'] == 'restore_files':
                    res, err = getattr(self.cli, j['func'])(**j['args'])
                else:
                    if j['args']:
                        if 'pickled' in j and j['pickled']:
                            # de-serialize arguments if needed
                            from base64 import b64decode
                            j['args'] = pickle.loads(b64decode(j['args']))
                        res = json.dumps(getattr(self.cli, j['func'])(**j['args']))
                    else:
                        res = json.dumps(getattr(self.cli, j['func'])())
                self.server.agent._logger('info', 'result: {}'.format(res))
                self.request.sendall(b'OK')
            except BUIserverException as e:
                self.request.sendall(b'ER')
                res = str(e)
                self.request.sendall(struct.pack('!Q', len(res)))
                self.request.sendall(res.encode('UTF-8'))
                return
            if j['func'] == 'restore_files':
                if err:
                    self.request.sendall(b'KO')
                    self.request.sendall(struct.pack('!Q', len(err)))
                    self.request.sendall(err.encode('UTF-8'))
                    self.server.agent._logger('error', 'Restoration failed')
                    return
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
            self.server.locks[self.idx].release()
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
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, agent=None):
        """
        :param agent: Agent instance
        :type agent: :class:`BUIAgent`
        """
        self.agent = agent
        self.numThreads = self.agent.threads
        self.locks = []
        self.clients = []
        for i in range(self.numThreads):
            cli = BurpHandler(self.agent.vers, self.agent.logger, self.agent.conf)
            lock = threading.Lock()
            self.clients.append(cli)
            self.locks.append(lock)

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

    def serve_forever(self):
        """Handle one request at a time until doomsday"""
        # set up the threadpool
        self.requests = Queue(self.numThreads)

        for x in range(self.numThreads):
            t = threading.Thread(target=self.process_request_thread)
            t.setDaemon(1)
            t.start()

        # server main loop
        while True:
            self.handle_request()

        self.server_close()

    def process_request_thread(self):
        """obtain request from queue instead of directly from server socket"""
        while True:
            SocketServer.ThreadingMixIn.process_request_thread(self, *self.requests.get())

    def handle_request(self):
        """simply collect requests and put them on the queue for the workers"""
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        if self.verify_request(request, client_address):
            self.requests.put((request, client_address))
