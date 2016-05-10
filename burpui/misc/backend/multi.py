# -*- coding: utf8 -*-
import re
import socket
import errno
import time
import json
import struct
import traceback
import logging

from six import iteritems

from .interface import BUIbackend
from ...exceptions import BUIserverException
from ..._compat import IS_GUNICORN, ConfigParser, pickle
from ...utils import implement


INTERFACE_METHODS = BUIbackend.__abstractmethods__


class ProxyCall(object):
    """Class to dispatch call of unknown methods in order to dynamically
    call agents one without maintaining the explicit list of methods.
    """
    def __init__(self, proxy, method, network=False):
        """
        :param proxy: Class to proxify
        :type proxy: :class:`burpui.misc.backend.multi.Burp`

        :param method: Name of the method to proxify
        :type method: str

        :param network: Is it a custom call over network
        :type network: bool
        """
        self.proxy = proxy
        self.method = method
        self.network = network

    def __call__(self, *args, **kwargs):
        """This is were the proxy call (and the magic) occurs"""
        # retrieve the original function prototype
        proto = getattr(BUIbackend, self.method)
        args_name = list(proto.__code__.co_varnames)
        # skip self
        args_name.pop(0)
        # we transform unnamed arguments to named ones
        # example:
        #     def my_function(toto, tata=None, titi=None):
        #
        #     x = my_function('blah', titi='blih')
        #
        # => {'toto': 'blah', 'titi': 'blih'}
        encoded_args = {}
        for idx, opt in enumerate(args):
            encoded_args[args_name[idx]] = opt
        encoded_args.update(kwargs)

        # Special case for network calls
        if self.network:
            data = {'func': self.method, 'args': encoded_args}
            if self.method == 'restore_files':
                return self.proxy.do_command(data)
            return json.loads(self.proxy.do_command(data))
        # normal case for "standard" interface
        if 'agent' not in encoded_args:
            raise AttributeError()
        agentName = encoded_args['agent']
        # we don't need this argument anymore
        del encoded_args['agent']
        agent = self.proxy.servers[agentName]
        return getattr(agent, self.method)(**encoded_args)


class Burp(BUIbackend):
    """The :class:`burpui.misc.backend.multi.Burp` class provides a consistent
    backend to interact with ``agents``.

    It is actually the *real* multi backend implementing the
    :class:`burpui.misc.backend.interface.BUIbackend` class.

    For each agent found in the configuration, it will load a
    :class:`burpui.misc.backend.multi.NClient` class.

    :param server: ``Burp-UI`` server instance in order to access logger
                   and/or some global settings
    :type server: :class:`burpui.server.BUIServer`

    :param conf: Configuration file to use
    :type conf: str
    """
    # These functions MUST be implemented because we inherit an abstract class.
    # The hack here is to get the list of the functions and let the interpreter
    # think we don't have to implement them.
    # Thanks to this list, we know what function are implemented by our backend.
    foreign = INTERFACE_METHODS
    BUIbackend.__abstractmethods__ = frozenset()

    def __init__(self, server=None, conf=None):
        """
        :param server: Application context
        :type server: :class:`burpui.server.BUIServer`
        """
        self.app = server
        self.acl_handler = server.acl_handler
        self.servers = {}
        self.app.config['SERVERS'] = []
        self.running = {}
        if conf:
            config = ConfigParser.ConfigParser()
            with open(conf) as fp:
                config.readfp(fp)
                for sec in config.sections():
                    r = re.match('^Agent:(.+)$', sec)
                    if r:
                        ssl = False
                        host = self._safe_config_get(config.get, 'host', sec)
                        port = self._safe_config_get(config.getint, 'port', sec, cast=int)
                        password = self._safe_config_get(config.get, 'password', sec)
                        ssl = self._safe_config_get(config.getboolean, 'ssl', sec, cast=bool)
                        timeout = self._safe_config_get(config.getint, 'timeout', sec, cast=int)

                        self.servers[r.group(1)] = NClient(self.app, host, port, password, ssl, timeout)

        if not self.servers:
            self.logger.error('No agent configured!')
        else:
            self.logger.debug(self.servers)
        for (key, serv) in iteritems(self.servers):
            self.app.config['SERVERS'].append(key)

    def __getattribute__(self, name):
        # always return this value because we need it and if we don't do that
        # we'll end up with an infinite loop
        if name == 'foreign':
            return object.__getattribute__(self, name)
        # now we can retrieve the 'foreign' list and know if the object called
        # needs to be "proxyfied"
        if name in self.foreign:
            proxy = True
            func = None
            try:
                func = object.__getattribute__(self, name)
                proxy = not getattr(func, '__ismethodimplemented__', False)
            except:
                pass
            self.logger.debug('func: {} - {}'.format(name, proxy))
            if proxy:
                return ProxyCall(self, name)
            elif func:
                return func
        return object.__getattribute__(self, name)

    def _backup_running_parallel(self):
        """Use :mod:`multiprocessing` or :mod:`gevent` to retrieve a list of
        running backups
        """
        if IS_GUNICORN:
            import gevent
            from gevent.queue import Queue
        else:
            import multiprocessing
            Queue = multiprocessing.Queue

        r = {}
        output = Queue()

        def get_running(a, i, output):
            output.put((i, self.servers[a].is_one_backup_running(a)))

        # If we are running under gunicorn, use a gevent-safe method
        if IS_GUNICORN:
            processes = [
                (
                    gevent.spawn(
                        get_running,
                        a,
                        i,
                        output
                    ),
                    a
                ) for (i, a) in enumerate(self.servers)
            ]
            greens = [p for (p, a) in processes]
            gevent.joinall(greens)
        else:
            processes = [
                (
                    multiprocessing.Process(
                        target=get_running,
                        args=(a, i, output)
                    ),
                    a
                ) for (i, a) in enumerate(self.servers)
            ]
            [p.start() for (p, a) in processes]
            [p.join() for (p, a) in processes]

        results = [output.get() for (p, a) in processes]
        results.sort()

        for (i, (p, a)) in enumerate(processes):
            # results contains a tuple (index, response) so we 'split' it
            _, r[a] = results[i]

        return r

    @implement
    def is_one_backup_running(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.is_one_backup_running`"""
        r = []
        if agent:
            r = self.servers[agent].is_one_backup_running(agent)
            self.running[agent] = r
        else:
            r = self._backup_running_parallel()

            self.running = r
        self.refresh = time.time()
        return r

    def _get_version_parallel(self, method=None):
        """Use :mod:`multiprocessing` or :mod:`gevent` to retrieve versions"""
        if IS_GUNICORN:
            import gevent
            from gevent.queue import Queue
        else:
            import multiprocessing
            Queue = multiprocessing.Queue

        if not method:
            raise BUIserverException('Wrong method call')

        r = {}
        output = Queue()

        def get_client_vers(key, i, output):
            output.put((i, self.servers[key].get_client_version()))

        def get_server_vers(key, i, output):
            output.put((i, self.servers[key].get_server_version()))

        if method == 'get_client_version':
            func = get_client_vers
        else:
            func = get_server_vers

        # If we are running under gunicorn, use a gevent-safe method
        if IS_GUNICORN:
            processes = [
                (
                    gevent.spawn(
                        func,
                        k,
                        i,
                        output
                    ),
                    k
                ) for (i, (k, s)) in enumerate(iteritems(self.servers))
            ]
            greens = [p for (p, a) in processes]
            gevent.joinall(greens)
        else:
            processes = [
                (
                    multiprocessing.Process(
                        target=func,
                        args=(k, i, output)
                    ),
                    k
                ) for (i, (k, s)) in enumerate(iteritems(self.servers))
            ]
            [p.start() for (p, k) in processes]
            [p.join() for (p, k) in processes]

        results = [output.get() for (p, k) in processes]
        results.sort()

        for (i, (p, k)) in enumerate(processes):
            _, r[k] = results[i]

        return r

    @implement
    def get_client_version(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_version`"""
        if not agent:
            return self._get_version_parallel('get_client_version')
        return self.servers[agent].get_client_version()

    @implement
    def get_server_version(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_server_version`"""
        if not agent:
            return self._get_version_parallel('get_server_version')
        return self.servers[agent].get_server_version()


class NClient(BUIbackend):
    """The :class:`burpui.misc.backend.multi.NClient` class provides a
    consistent backend to interact with ``agents``.

    It acts as a proxy so it works with any agent running a backend implementing
    the :class:`burpui.misc.backend.interface.BUIbackend` class.

    :param app: The application context
    :type app: :class:`burpui.server.BUIServer`

    :param host: Address of the remote agent
    :type host: str

    :param port: Port of the remote agent
    :type port: int

    :param password: Secret between the agent and the burp-ui server
    :type password: str

    :param ssl: Use SSL to communicate with the agent
    :type ssl: bool
    """
    # These functions MUST be implemented because we inherit an abstract class.
    # The hack here is to get the list of the functions and let the interpreter
    # think we don't have to implement them.
    # Thanks to this list, we know what function are implemented by our backend.
    foreign = INTERFACE_METHODS
    BUIbackend.__abstractmethods__ = frozenset()

    def __init__(self, app=None, host=None, port=None, password=None, ssl=None, timeout=5):
        self.host = host
        self.port = port
        self.password = password
        self.ssl = ssl
        self.connected = False
        self.app = app
        self.timeout = timeout or 5

    def __getattribute__(self, name):
        # always return this value because we need it and if we don't do that
        # we'll end up with an infinite loop
        if name == 'foreign':
            return object.__getattribute__(self, name)
        # now we can retrieve the 'foreign' list and know if the object called
        # needs a dynamic implementation
        #if name in self.foreign and name not in dir(self):
        if name in self.foreign:
            proxy = True
            func = None
            try:
                func = object.__getattribute__(self, name)
                proxy = not getattr(func, '__ismethodimplemented__', False)
            except:
                pass
            self.logger.debug('func: {} - {}'.format(name, proxy))
            if proxy:
                return ProxyCall(self, name, network=True)
            elif func:
                return func
        return object.__getattribute__(self, name)

    def conn(self, notimeout=False):
        """Connects to the agent if needed"""
        try:
            if self.connected:
                return
            self.sock = self.do_conn(notimeout)
            self.connected = True
            self.logger.debug('OK, connected to agent %s:%s', self.host, self.port)
        except Exception as e:
            self.connected = False
            self.logger.error('Could not connect to %s:%s => %s', self.host, self.port, str(e))

    def do_conn(self, notimeout=False):
        """Do the actual connection to the agent"""
        ret = None
        if self.ssl:
            import ssl
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not notimeout:
                s.settimeout(self.timeout)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            ret = ssl.wrap_socket(s, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
            try:
                ret.connect((self.host, self.port))
            except Exception as e:
                self.logger.error('ERROR: %s', str(e))
                raise e
        else:
            if not notimeout:
                ret = socket.create_connection((self.host, self.port), timeout=self.timeout)
            else:
                ret = socket.create_connection((self.host, self.port))
            ret.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return ret

    def ping(self):
        """Check if we are connected to the agent"""
        self.conn()
        res = self.connected
        return res

    def close(self, force=True):
        """Disconnect from the agent"""
        if self.connected and force:
            self.sock.sendall(struct.pack('!Q', 2))
            self.sock.sendall(b'RE')
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.connected = False

    def do_command(self, data=None, restarted=False):
        """Send a command to the remote agent"""
        self.conn()
        res = '[]'
        toclose = False
        if not data or not self.connected:
            return res
        try:
            data['password'] = self.password
            if data['func'] == 'restore_files':
                self.close()
                self.conn(True)
            raw = json.dumps(data)
            length = len(raw)
            self.sock.sendall(struct.pack('!Q', length))
            self.sock.sendall(raw.encode('UTF-8'))
            self.logger.debug("Sending: %s", raw)
            tmp = self.sock.recv(2).decode('UTF-8')
            self.logger.debug("recv: '%s'", tmp)
            if 'ER' == tmp:
                lengthbuf = self.sock.recv(8)
                length, = struct.unpack('!Q', lengthbuf)
                err = self.recvall(length).decode('UTF-8')
                raise BUIserverException(err)
            if 'OK' != tmp:
                self.logger.debug('Ooops, unsuccessful!')
                return res
            self.logger.debug("Data sent successfully")
            tmp = 'OK'
            if data['func'] == 'restore_files':
                tmp = self.sock.recv(2)
            lengthbuf = self.sock.recv(8)
            length, = struct.unpack('!Q', lengthbuf)
            if data['func'] == 'restore_files':
                err = None
                if tmp == 'KO':
                    err = self.recvall(length).decode('UTF-8')
                res = (self.sock, length, err)
                self.connected = False
            else:
                res = self.recvall(length).decode('UTF-8')
        except BUIserverException as e:
            raise e
        except IOError as e:
            if not restarted and e.errno == errno.EPIPE:
                self.connected = False
                return self.do_command(data, True)
            elif e.errno == errno.ECONNRESET:
                self.connected = False
                self.logger.error('!!! {} !!!\nPlease check your SSL configuration on both sides!'.format(str(e)))
            else:
                toclose = True
                self.logger.error('!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))
        except socket.timeout as e:
            if self.app.gunicorn and not restarted:
                self.connected = False
                return self.do_command(data, True)
            toclose = True
            self.logger.error('!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))
        except Exception as e:
            toclose = True
            self.logger.error('!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))
        finally:
            self.close(toclose)

        return res

    def recvall(self, length=1024):
        """Read the answer of the agent"""
        buf = b''
        bsize = 1024
        received = 0
        if length < bsize:
            bsize = length
        while received < length:
            newbuf = self.sock.recv(bsize)
            if not newbuf:
                return None
            buf += newbuf
            received += len(newbuf)
        return buf

    """
    Utilities functions
    """

    @implement
    def store_conf_cli(self, data, client=None, conf=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.store_conf_cli`"""
        # serialize data as it is a nested dict
        # TODO: secure the serialization
        from base64 import b64encode
        data = {'func': 'store_conf_cli', 'args': b64encode(pickle.dumps({'data': data, 'conf': conf, 'client': client}, -1)), 'pickled': True}
        return json.loads(self.do_command(data))

    @implement
    def store_conf_srv(self, data, conf=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.store_conf_srv`"""
        # serialize data as it is a nested dict
        # TODO: secure the serialization
        from base64 import b64encode
        data = {'func': 'store_conf_srv', 'args': b64encode(pickle.dumps({'data': data, 'conf': conf}, -1)), 'pickled': True}
        return json.loads(self.do_command(data))

