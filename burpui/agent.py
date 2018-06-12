# -*- coding: utf8 -*-
"""
.. module:: burpui.agent
    :platform: Unix
    :synopsis: Burp-UI agent module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import os
import struct
import re
import time
import sys
import json
import logging

from gevent.lock import RLock
from gevent.pool import Pool
from gevent.server import StreamServer
from logging.handlers import RotatingFileHandler

from .exceptions import BUIserverException
from .misc.backend.interface import BUIbackend
from ._compat import pickle, to_bytes, to_unicode
from .config import config
from .desc import __version__

try:
    from sendfile import sendfile
    USE_SENDFILE = True
except ImportError:
    USE_SENDFILE = False


BUI_DEFAULTS = {
    'Global': {
        'port': 10000,
        'bind': '::',
        'ssl': False,
        'sslcert': '',
        'sslkey': '',
        'backend': 'burp2',
        'password': 'password',
    },
}

DISCLOSURE = 5

lock = RLock()


class BurpHandler(BUIbackend):
    # These functions MUST be implemented because we inherit an abstract class.
    # The hack here is to get the list of the functions and let the interpreter
    # think we don't have to implement them.
    # Thanks to this list, we know what function are implemented by our backend.
    foreign = BUIbackend.__abstractmethods__
    BUIbackend.__abstractmethods__ = frozenset()

    def __init__(self, backend='burp2', logger=None, conf=None):
        self.backend = backend
        self.logger = logger

        top = __name__
        if '.' in self.backend:
            module = self.backend
        else:
            if '.' in top:
                top = top.split('.')[0]
            module = '{0}.misc.backend.{1}'.format(top, self.backend)
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            mod = __import__(module, fromlist=['Burp'])
            Client = mod.Burp
            self.backend = Client(conf=conf)
        except Exception as exc:
            self.logger.error('Failed loading backend {}: {}'.format(self.backend, str(exc)), exc_info=exc, stack_info=True)
            sys.exit(2)

    def __getattribute__(self, name):
        # always return this value because we need it and if we don't do that
        # we'll end up with an infinite loop
        if name == 'foreign' or name == 'backend':
            return object.__getattribute__(self, name)
        # now we can retrieve the 'foreign' list and know if the object called
        # is in the backend
        if name in self.foreign:
            return getattr(self.backend, name)
        try:
            return getattr(self.backend, name)
        except AttributeError:
            pass
        return object.__getattribute__(self, name)


class BUIAgent(BUIbackend):
    BUIbackend.__abstractmethods__ = frozenset()

    def __init__(self, conf=None, level=0, logfile=None, debug=False):
        self.debug = debug
        self.padding = 1
        level = level or 0
        if level > logging.NOTSET:
            levels = [
                logging.CRITICAL,
                logging.ERROR,
                logging.WARNING,
                logging.INFO,
                logging.DEBUG,
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
            self.logger.info('conf: {}'.format(conf))
            self.logger.info('level: {}'.format(logging.getLevelName(lvl)))
        if not conf:
            raise IOError('No configuration file found')

        # Raise exception if errors are encountered during parsing
        self.conf = config
        self.conf.parse(conf, True, BUI_DEFAULTS)
        self.conf.default_section('Global')
        self.port = self.conf.safe_get('port', 'integer')
        self.bind = self.conf.safe_get('bind')
        self.backend = self.conf.safe_get('backend')
        self.ssl = self.conf.safe_get('ssl', 'boolean')
        self.sslcert = self.conf.safe_get('sslcert')
        self.sslkey = self.conf.safe_get('sslkey')
        self.password = self.conf.safe_get('password')
        self.conf.setdefault('BUI_AGENT', True)

        self.client = BurpHandler(self.backend, self.logger, self.conf)
        pool = Pool(10000)
        if not self.ssl:
            self.server = StreamServer((self.bind, self.port), self.handle, spawn=pool)
        else:
            self.server = StreamServer((self.bind, self.port), self.handle, keyfile=self.sslkey, certfile=self.sslcert, spawn=pool)

    def run(self):
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            sys.exit(0)

    def handle(self, request, address):
        """self.request is the client connection"""
        with lock:
            try:
                self.request = request
                err = None
                res = ''
                lengthbuf = self.request.recv(8)
                if not lengthbuf:
                    return
                length, = struct.unpack('!Q', lengthbuf)
                data = self.recvall(length)
                self.logger.info('recv: {}'.format(data))
                txt = to_unicode(data)
                self.logger.info('recv2: {}'.format(txt))
                if txt == 'RE':
                    return
                j = json.loads(txt)
                if j['password'] != self.password:
                    self.logger.warning('-----> Wrong Password <-----')
                    self.request.sendall(b'KO')
                    return
                try:
                    if j['func'] == 'proxy_parser':
                        parser = self.client.get_parser()
                        if j['args']:
                            res = json.dumps(getattr(parser, j['method'])(**j['args']))
                        else:
                            res = json.dumps(getattr(parser, j['method'])())
                    elif j['func'] == 'agent_version':
                        res = json.dumps(__version__)
                    elif j['func'] == 'restore_files':
                        res, err = getattr(self.client, j['func'])(**j['args'])
                        if err:
                            self.request.sendall(b'ER')
                            self.request.sendall(struct.pack('!Q', len(err)))
                            self.request.sendall(to_bytes(err))
                            self.logger.error('Restoration failed')
                            return
                    elif j['func'] == 'get_file':
                        path = j['path']
                        path = os.path.normpath(path)
                        err = None
                        if not path.startswith('/'):
                            err = 'The path must be absolute! ({})'.format(path)
                        if not path.startswith(self.client.tmpdir):
                            err = 'You are not allowed to access this path: ' \
                                  '({})'.format(path)
                        if err:
                            self.request.sendall(b'ER')
                            self.request.sendall(struct.pack('!Q', len(err)))
                            self.request.sendall(to_bytes(err))
                            self.logger.error(err)
                            return
                        size = os.path.getsize(path)
                        self.request.sendall(b'OK')
                        self.request.sendall(struct.pack('!Q', size))
                        with open(path, 'rb') as f:
                            if not USE_SENDFILE:
                                while True:
                                    buf = f.read(1024)
                                    if not buf:
                                        break
                                    self.logger.info('sending {} Bytes'.format(len(buf)))
                                    self.request.sendall(buf)
                            else:
                                offset = 0
                                while True:
                                    sent = sendfile(self.request.fileno(), f.fileno(), offset, size)
                                    if sent == 0:
                                        break
                                    offset += sent
                        os.unlink(path)
                        lengthbuf = self.request.recv(8)
                        length, = struct.unpack('!Q', lengthbuf)
                        data = self.recvall(length)
                        txt = to_unicode(data)
                        if txt == 'RE':
                            return
                    elif j['func'] == 'del_file':
                        path = j['path']
                        path = os.path.normpath(path)
                        err = None
                        if not path.startswith('/'):
                            err = 'The path must be absolute! ({})'.format(path)
                        if not path.startswith(self.client.tmpdir):
                            err = 'You are not allowed to access this path: ' \
                                  '({})'.format(path)
                        if err:
                            self.request.sendall(b'ER')
                            self.request.sendall(struct.pack('!Q', len(err)))
                            self.request.sendall(to_bytes(err))
                            self.logger.error(err)
                            return
                        res = json.dumps(False)
                        if os.path.isfile(path):
                            os.unlink(path)
                            res = json.dumps(True)
                    else:
                        if j['args']:
                            if 'pickled' in j and j['pickled']:
                                # de-serialize arguments if needed
                                import hmac
                                import hashlib
                                from base64 import b64decode
                                pickles = to_bytes(j['args'])
                                key = '{}{}'.format(self.password, j['func'])
                                key = to_bytes(key)
                                bytes_pickles = pickles
                                digest = hmac.new(key, bytes_pickles, hashlib.sha1).hexdigest()
                                if not hmac.compare_digest(digest, j['digest']):
                                    raise BUIserverException('Integrity check failed: {} != {}'.format(digest, j['digest']))
                                # We need to replace the burpui datastructure
                                # module by our own since it's the same but
                                # burpui may not be installed
                                mod = __name__
                                if '.' in mod:
                                    mod = mod.split('.')[0]
                                data = b64decode(pickles)
                                data = data.replace(b'burpui.datastructures', to_bytes('{}.datastructures'.format(mod)))
                                j['args'] = pickle.loads(data)
                            res = json.dumps(getattr(self.client, j['func'])(**j['args']))
                        else:
                            res = json.dumps(getattr(self.client, j['func'])())
                    self.logger.info('result: {}'.format(res))
                    self.request.sendall(b'OK')
                except (BUIserverException, Exception) as exc:
                    self.request.sendall(b'ER')
                    res = str(exc)
                    self.logger.error(res, exc_info=exc)
                    self.logger.warning('Forwarding Exception: {}'.format(res))
                    self.request.sendall(struct.pack('!Q', len(res)))
                    self.request.sendall(to_bytes(res))
                    return
                self.request.sendall(struct.pack('!Q', len(res)))
                self.request.sendall(to_bytes(res))
            except AttributeError as exc:
                self.logger.warning('Wrong method => {}'.format(str(exc)), exc_info=exc)
                self.request.sendall(b'KO')
            except Exception as exc:
                self.logger.error('!!! {} !!!'.format(str(exc)), exc_info=exc)
            finally:
                try:
                    self.request.close()
                except Exception as exc:
                    self.logger.error('!!! {} !!!'.format(str(exc)), exc_info=exc)

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
