# -*- coding: utf8 -*-
import re
import socket
import errno
import time
import json
import struct
import traceback

from six import iteritems

from .interface import BUIbackend
from ..parser.interface import BUIparser
from ...exceptions import BUIserverException
from ..._compat import pickle, to_unicode, to_bytes
from ...utils import implement


INTERFACE_METHODS = BUIbackend.__abstractmethods__
PARSER_INTERFACE_METHODS = BUIparser.__abstractmethods__


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
        """This is where the proxy call (and the magic) occurs"""
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
            return json.loads(self.proxy.do_command(data))
        # normal case for "standard" interface
        if 'agent' not in encoded_args:
            raise AttributeError(str(encoded_args))
        agentName = encoded_args['agent']
        # we don't need this argument anymore
        del encoded_args['agent']
        try:
            agent = self.proxy.servers[agentName]
        except KeyError:
            # This exception should be forwarded to the final user
            if not agentName:
                msg = "You must provide an agent name"
            else:
                msg = "Agent '{}' not found".format(agentName)
            raise BUIserverException(msg)
        return getattr(agent, self.method)(**encoded_args)


class ProxyParserCall(object):
    """Class that actually calls the Parser method"""
    def __init__(self, agent, method):
        """
        :param agent: Agent to use
        :type agent: :class:`burpui.misc.backend.multi.NClient`

        :param method: Name of the method to proxify
        :type method: str
        """
        self.agent = agent
        self.method = method

    def __call__(self, *args, **kwargs):
        """This is where the proxy call (and the magic) occurs"""
        # retrieve the original function prototype
        proto = getattr(BUIparser, self.method)
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

        data = {'func': 'proxy_parser', 'method': self.method, 'args': encoded_args}
        return json.loads(self.agent.do_command(data))


class ProxyParser(BUIparser):
    """Class to generate a "virtual" parser object"""
    # These functions MUST be implemented because we inherit an abstract class.
    # The hack here is to get the list of the functions and let the interpreter
    # think we don't have to implement them.
    # Thanks to this list, we know what function are implemented by our backend.
    foreign = PARSER_INTERFACE_METHODS
    BUIparser.__abstractmethods__ = frozenset()

    def __init__(self, agent):
        """
        :param agent: Agent to use
        :type agent: :class:`burpui.misc.backend.multi.NClient`
        """
        self.agent = agent

    def __getattribute__(self, name):
        # always return this value because we need it and if we don't do that
        # we'll end up with an infinite loop
        if name == 'foreign':
            return object.__getattribute__(self, name)
        # now we can retrieve the 'foreign' list and know if the object called
        # needs to be "proxyfied"
        if name in self.foreign:
            return ProxyParserCall(self.agent, name)
        return object.__getattribute__(self, name)


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

        :param conf: Configuration
        :type conf: :class:`burpui.config.BUIConfig`
        """
        self.app = server
        self.acl_handler = server.acl_handler
        self.servers = {}
        self.app.config['SERVERS'] = []
        self.running = {}
        if conf:
            for sect in conf.options.keys():
                r = re.match('^Agent:(.+)$', sect)
                if r:
                    host = conf.safe_get('host', section=sect)
                    port = conf.safe_get('port', 'integer', section=sect) or 10000
                    password = conf.safe_get('password', section=sect)
                    ssl = conf.safe_get('ssl', 'boolean', section=sect) or False
                    timeout = conf.safe_get('timeout', 'integer', section=sect) or 5

                    self.servers[r.group(1)] = NClient(self.app, host, port, password, ssl, timeout)
                    self.app.config['SERVERS'].append(r.group(1))

        if not self.servers:
            self.logger.error('No agent configured!')
        else:
            self.logger.debug(self.servers)

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

    @implement
    def is_one_backup_running(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.is_one_backup_running`"""
        r = []
        if agent:
            r = self.servers[agent].is_one_backup_running(agent)
            self.running[agent] = r
        else:
            r = {}
            for name, serv in iteritems(self.servers):
                r[name] = serv.is_one_backup_running()

            self.running = r
        self.refresh = time.time()
        return r

    def _get_version(self, method=None):
        """get versions"""

        if not method:
            raise BUIserverException('Wrong method call')

        r = {}

        for name, serv in iteritems(self.servers):
            func = getattr(serv, method)
            r[name] = func()

        return r

    @implement
    def get_parser(self, agent=None):
        # Need to return a proxy object to interact with a remote parser
        if not agent:
            raise BUIserverException('No agent provided')

        return ProxyParser(self.servers.get(agent))

    @implement
    def get_client_version(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_version`"""
        if not agent:
            return self._get_version('get_client_version')
        return self.servers[agent].get_client_version()

    @implement
    def get_server_version(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_server_version`"""
        if not agent:
            return self._get_version('get_server_version')
        return self.servers[agent].get_server_version()


class Gsocket():
    def __init__(self, host, port, ssl=False, timeout=5, notimeout=False):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.timeout = timeout
        self.notimeout = notimeout

    def conn(self):
        if self.ssl:
            import ssl
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not self.notimeout:
                s.settimeout(self.timeout)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            ret = ssl.wrap_socket(s, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
            ret.connect((self.host, self.port))
        else:
            if not self.notimeout:
                ret = socket.create_connection((self.host, self.port), timeout=self.timeout)
            else:
                ret = socket.create_connection((self.host, self.port))
            ret.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock = ret
        self.connected = True

    def __enter__(self):
        self.conn()
        return self.sock, self

    def __exit__(self, type, value, traceback):
        if self.connected:
            self.sock.close()
        self.connected = False

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
        self.app = app
        self.timeout = timeout or 5

    def __getattribute__(self, name):
        # always return this value because we need it and if we don't do that
        # we'll end up with an infinite loop
        if name == 'foreign':
            return object.__getattribute__(self, name)
        # now we can retrieve the 'foreign' list and know if the object called
        # needs a dynamic implementation
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

    def ping(self):
        """Check if we are connected to the agent"""
        res = False
        try:
            with Gsocket(self.host, self.port, self.ssl, self.timeout) as (sock, gsock):
                sock.sendall(struct.pack('!Q', 2))
                sock.sendall(b'RE')
                res = True
        except socket.error:
            pass
        return res

    def setup(self, sock, gsock, data):
        length = struct.pack('!Q', len(data))
        sock.sendall(length)
        data = to_unicode(data)
        sock.sendall(to_bytes(data))
        self.logger.debug("Sending: {}".format(data))
        tmp = to_unicode(sock.recv(2))
        self.logger.debug("recv: '{}'".format(tmp))
        if 'ER' == tmp:
            lengthbuf = sock.recv(8)
            length, = struct.unpack('!Q', lengthbuf)
            err = to_unicode(gsock.recvall(length))
            raise BUIserverException(err)
        if 'OK' != tmp:
            self.logger.debug('Ooops, unsuccessful!')
            return False
        self.logger.debug("Data sent successfully")
        return True

    def do_command(self, data=None, restarted=False):
        """Send a command to the remote agent"""
        res = '[]'
        err = None
        notimeout = False
        timeout = self.timeout
        if not data:
            raise BUIserverException('Missing data')
        data['password'] = self.password
        # manage long running operations
        if data['func'] in ['restore_files', 'get_file', 'del_file']:
            notimeout = True
        if data['func'] == 'get_tree' and data['args'].get('root') == '*':
            # arbitrary raise timeout
            timeout = max(timeout, 300)
        try:
            # don't need a context manager here
            if data['func'] == 'get_file':
                gsock = Gsocket(self.host, self.port, self.ssl, notimeout=True)
                gsock.conn()
                raw = json.dumps(data)
                if not self.setup(gsock.sock, gsock, raw):
                    return res
                return gsock.sock
            with Gsocket(self.host, self.port, self.ssl, timeout, notimeout) as (sock, gsock):
                try:
                    raw = json.dumps(data)
                    if not self.setup(gsock.sock, gsock, raw):
                        return res
                    lengthbuf = sock.recv(8)
                    length, = struct.unpack('!Q', lengthbuf)
                    res = to_unicode(gsock.recvall(length))
                except IOError as e:
                    if not restarted and e.errno == errno.EPIPE:
                        self.logger.warning('Broken pipe, restarting the request')
                        return self.do_command(data, True)
                    elif e.errno == errno.ECONNRESET:
                        self.logger.error('!!! {} !!!\nPlease check your SSL configuration on both sides!'.format(str(e)))
                    else:
                        self.logger.error('!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))
                    raise e
                except socket.timeout as e:
                    if self.app.gunicorn and not restarted:
                        self.logger.warning('Socket timed-out, restarting the request')
                        return self.do_command(data, True)
                    self.logger.error('!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))
                    raise e
                # catch all
                except Exception as e:
                    self.logger.error('!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))
                    if data['func'] == 'restore_files':
                        err = str(e)
                    elif isinstance(e, BUIserverException):
                        raise e
                    else:
                        raise BUIserverException(str(e))
        except Exception as e:
            self.logger.error('!!! {} !!!\n{}'.format(str(e), traceback.format_exc()))
            raise BUIserverException(str(e))

        if data['func'] == 'restore_files':
            if err:
                res = None
            return res, err

        return res

    """
    Utilities functions
    """

    @implement
    def store_conf_cli(self, data, client=None, conf=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.store_conf_cli`"""
        # serialize data as it is a nested dict
        import hmac
        import hashlib
        from base64 import b64encode
        from werkzeug.datastructures import ImmutableMultiDict
        if not isinstance(data, ImmutableMultiDict):
            msg = 'Wrong data type'
            self.logger.warning(msg)
            raise BUIserverException(msg)
        key = '{}{}'.format(self.password, 'store_conf_cli')
        key = to_bytes(key)
        pickles = b64encode(pickle.dumps({'data': data, 'conf': conf, 'client': client}, 2))
        bytes_pickles = to_bytes(pickles)
        digest = hmac.new(key, bytes_pickles, hashlib.sha1).hexdigest()
        data = {'func': 'store_conf_cli', 'args': pickles, 'pickled': True, 'digest': digest}
        return json.loads(self.do_command(data))

    @implement
    def store_conf_srv(self, data, conf=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.store_conf_srv`"""
        # serialize data as it is a nested dict
        import hmac
        import hashlib
        from base64 import b64encode
        from werkzeug.datastructures import ImmutableMultiDict
        if not isinstance(data, ImmutableMultiDict):
            msg = 'Wrong data type'
            self.logger.warning(msg)
            raise BUIserverException(msg)
        key = u'{}{}'.format(self.password, 'store_conf_srv')
        key = to_bytes(key)
        pickles = b64encode(pickle.dumps({'data': data, 'conf': conf}, 2))
        bytes_pickles = to_bytes(pickles)
        digest = hmac.new(key, bytes_pickles, hashlib.sha1).hexdigest()
        data = {'func': 'store_conf_srv', 'args': pickles, 'pickled': True, 'digest': digest}
        return json.loads(self.do_command(data))

    @implement
    def restore_files(self, name=None, backup=None, files=None, strip=None, archive='zip', password=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.restore_files`"""
        data = {'func': 'restore_files', 'args': {'name': name, 'backup': backup, 'files': files, 'strip': strip, 'archive': archive, 'password': password}}
        return self.do_command(data)

    @implement
    def get_file(self, path, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_file`"""
        data = {'func': 'get_file', 'path': path}
        return self.do_command(data)

    @implement
    def del_file(self, path, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.del_file`"""
        data = {'func': 'del_file', 'path': path}
        return json.loads(self.do_command(data))
