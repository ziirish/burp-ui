# -*- coding: utf8 -*-
import os
import struct
import re
import time
import sys
import json
import logging
import traceback

from gevent.server import StreamServer
from logging.handlers import RotatingFileHandler
from .exceptions import BUIserverException
from .misc.backend.interface import BUIbackend
from ._compat import pickle
from .utils import BUIlogging, BUIConfig

G_PORT = 10000
G_BIND = u'::'
G_SSL = False
G_VERSION = 1
G_SSLCERT = u''
G_SSLKEY = u''
G_PASSWORD = u'password'

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
        except Exception as e:
            self.logger.error('{}\n\nFailed loading backend for Burp version {}: {}'.format(traceback.format_exc(), self.vers, str(e)))
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


class BUIAgent(BUIbackend, BUIlogging):
    BUIbackend.__abstractmethods__ = frozenset()
    defaults = {
        'Global': {
            'port': G_PORT,
            'bind': G_BIND,
            'ssl': G_SSL,
            'sslcert': G_SSLCERT,
            'sslkey': G_SSLKEY,
            'version': G_VERSION,
            'password': G_PASSWORD,
        },
    }

    def __init__(self, conf=None, level=0, logfile=None, debug=False):
        self.debug = debug
        self.padding = 1
        if level > logging.NOTSET:
            logging.addLevelName(DISCLOSURE, 'DISCLOSURE')
            levels = [
                logging.CRITICAL,
                logging.ERROR,
                logging.WARNING,
                logging.INFO,
                logging.DEBUG,
                DISCLOSURE
            ]
            if level >= len(levels):
                level = len(levels) - 1
            lvl = levels[level]
            self.logger.setLevel(lvl)
            if lvl > logging.DEBUG:
                LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s'
            else:
                LOG_FORMAT = (
                    '-' * 80 + '\n' +
                    '%(levelname)s in %(module)s.%(funcName)s [%(pathname)s:%(lineno)d]:\n' +
                    '%(message)s\n' +
                    '-' * 80
                )
            if logfile:
                handler = RotatingFileHandler(logfile, maxBytes=1024 * 1024 * 100, backupCount=20)
            else:
                handler = logging.StreamHandler()
            handler.setLevel(lvl)
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            self.logger.addHandler(handler)
            self._logger('info', 'conf: ' + conf)
            self._logger('info', 'level: ' + logging.getLevelName(lvl))
        if not conf:
            raise IOError('No configuration file found')

        # Raise exception if errors are encountered during parsing
        self.conf = BUIConfig(conf, True, self.defaults)
        self.conf.default_section('Global')
        self.port = self.conf.safe_get('port', 'integer')
        self.bind = self.conf.safe_get('bind')
        self.vers = self.conf.safe_get('version', 'integer')
        self.ssl = self.conf.safe_get('ssl', 'boolean')
        self.sslcert = self.conf.safe_get('sslcert')
        self.sslkey = self.conf.safe_get('sslkey')
        self.password = self.conf.safe_get('password')

        self.cli = BurpHandler(self.vers, self.logger, self.conf)
        if not self.ssl:
            self.server = StreamServer((self.bind, self.port), self.handle)
        else:
            self.server = StreamServer((self.bind, self.port), self.handle, keyfile=self.sslkey, certfile=self.sslcert)

    def run(self):
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            sys.exit(0)

    def handle(self, request, address):
        """self.request is the client connection"""
        try:
            self.request = request
            err = None
            lengthbuf = self.request.recv(8)
            length, = struct.unpack('!Q', lengthbuf)
            data = self.recvall(length)
            self._logger('info', 'recv: {}'.format(data))
            txt = data.decode('UTF-8')
            if txt == 'RE':
                return
            j = json.loads(txt)
            if j['password'] != self.password:
                self._logger('warning', '-----> Wrong Password <-----')
                self.request.sendall(b'KO')
                return
            try:
                if j['func'] == 'proxy_parser':
                    parser = self.cli.get_parser()
                    if j['args']:
                        res = json.dumps(getattr(parser, j['method'])(**j['args']))
                    else:
                        res = json.dumps(getattr(parser, j['method'])())
                elif j['func'] == 'restore_files':
                    res, err = getattr(self.cli, j['func'])(**j['args'])
                else:
                    if j['args']:
                        if 'pickled' in j and j['pickled']:
                            # de-serialize arguments if needed
                            import hmac
                            import hashlib
                            from base64 import b64decode
                            pickles = j['args']
                            key = u'{}{}'.format(self.password, j['func'])
                            key = key.encode(encoding='utf-8')
                            bytes_pickles = pickles.encode(encoding='utf-8')
                            digest = hmac.new(key, bytes_pickles, hashlib.sha1).hexdigest()
                            if digest != j['digest']:
                                raise BUIserverException('Integrity check failed')
                            j['args'] = pickle.loads(b64decode(pickles))
                        res = json.dumps(getattr(self.cli, j['func'])(**j['args']))
                    else:
                        res = json.dumps(getattr(self.cli, j['func'])())
                self._logger('info', 'result: {}'.format(res))
                self.request.sendall(b'OK')
            # should not happen
            except Exception as e:
                raise BUIserverException(str(e))
            except BUIserverException as e:
                self.request.sendall(b'ER')
                res = str(e)
                self._logger('error', 'Forwarding Exception: {}'.format(res))
                self.request.sendall(struct.pack('!Q', len(res)))
                self.request.sendall(res.encode('UTF-8'))
                return
            if j['func'] == 'restore_files':
                if err:
                    self.request.sendall(b'KO')
                    self.request.sendall(struct.pack('!Q', len(err)))
                    self.request.sendall(err.encode('UTF-8'))
                    self._logger('error', 'Restoration failed')
                    return
                self.request.sendall(b'OK')
                size = os.path.getsize(res)
                self.request.sendall(struct.pack('!Q', size))
                with open(res, 'rb') as f:
                    buf = f.read(1024)
                    while buf:
                        self._logger('info', 'sending {} Bytes'.format(len(buf)))
                        self.request.sendall(buf)
                        buf = f.read(1024)
                os.unlink(res)
                lengthbuf = self.request.recv(8)
                length, = struct.unpack('!Q', lengthbuf)
                data = self.recvall(length)
                txt = data.decode('UTF-8')
                if txt == 'RE':
                    return
            else:
                self.request.sendall(struct.pack('!Q', len(res)))
                self.request.sendall(res.encode('UTF-8'))
        except AttributeError as e:
            self._logger('warning', '{}\nWrong method => {}'.format(traceback.format_exc(), str(e)))
            self.request.sendall(b'KO')
            return
        except Exception as e:
            self._logger('error', '!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))
        finally:
            try:
                self.request.close()
            except Exception as e:
                self._logger('error', '!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))

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

    def _logger(self, level, message):
        # hide password from logs
        msg = message
        if not self.logger:
            return
        if self.logger.getEffectiveLevel() != DISCLOSURE:
            msg = re.sub(r'([\'"])password\1(\s*:\s*)([\'"])[^\3]+?\3', r'\1password\1\2\3*****\3', message)
        super(BUIAgent, self)._logger(level, msg)
