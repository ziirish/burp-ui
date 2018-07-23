# -*- coding: utf8 -*-
import re
import errno
import json
import struct
import trio
import ssl

from werkzeug.datastructures import ImmutableMultiDict as _ImmutableMultiDict

from .interface import BUIbackend
from ..parser.interface import BUIparser
from ...exceptions import BUIserverException
from ..._compat import pickle, to_unicode, to_bytes
from ...decorators import implement
from ...datastructures import ImmutableMultiDict


INTERFACE_METHODS = BUIbackend.__abstractmethods__
PARSER_INTERFACE_METHODS = BUIparser.__abstractmethods__
AGENT_VERSION_CAST = '0.4.9999'


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
            return json.loads(trio.run(self.proxy.do_command, data))
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
        :type agent: :class:`burpui.misc.backend.multi.NetClient`

        :param method: Name of the method to proxify
        :type method: str
        """
        self.agent = agent
        self.method = method

    async def __call__(self, *args, **kwargs):
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
        return json.loads(trio.run(self.agent.do_command, data))


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
        :type agent: :class:`burpui.misc.backend.multi.NetClient`
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
    :class:`burpui.misc.backend.multi.NetClient` class.

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
        if conf:
            for sect in conf.options.keys():
                r = re.match('^Agent:(.+)$', sect)
                if r:
                    host = conf.safe_get('host', section=sect)
                    port = conf.safe_get('port', 'integer', section=sect) or 10000
                    password = conf.safe_get('password', section=sect)
                    ssl = conf.safe_get('ssl', 'boolean', section=sect) or False
                    timeout = conf.safe_get('timeout', 'integer', section=sect) or 5

                    self.servers[r.group(1)] = NetClient(self.app, host, port, password, ssl, timeout)
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
        res = []
        if agent:
            try:
                res = self.servers[agent].is_one_backup_running(agent)
            except BUIserverException:
                pass
        else:
            res = {}
            for name, serv in self.servers.items():
                try:
                    res[name] = serv.is_one_backup_running()
                except BUIserverException:
                    res[name] = []
        return res

    def _get_version(self, method=None):
        """get versions"""

        if not method:
            raise BUIserverException('Wrong method call')

        r = {}

        for name, serv in self.servers.items():
            func = getattr(serv, method)
            try:
                r[name] = func()
            except BUIserverException:
                r[name] = 'Unknown'

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


class TCPsocket():
    def __init__(self, host, port, ssl=False):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.connected = False

    async def conn(self):
        if self.ssl:
            ctx = ssl.SSLContext()
            ctx.verify_mode = ssl.CERT_NONE
            ctx.check_hostname = False
            ctx.load_default_certs()
            self.client_stream = await trio.open_ssl_over_tcp_stream(self.host, self.port, ssl_context=ctx)
        else:
            self.client_stream = await trio.open_tcp_stream(self.host, self.port)
        self.connected = True

    async def __aenter__(self):
        #    def __enter__(self):
        if not self.connected:
            await self.conn()
        return self.client_stream, self

    async def __aexit__(self, exc_type, exc, tb):
        #   def __exit__(self, type, value, traceback):
        self.connected = False

    async def receive_all(self, length=1024):
        """Read the answer of the agent"""
        buf = b''
        bsize = min(1024, length)
        received = 0
        tries = 0
        while received < length:
            newbuf = await self.client_stream.receive_some(bsize)
            if not newbuf:
                if tries > 3:
                    raise Exception('Unable to read full response')
                tries += 1
                await trio.sleep(0.1)
                continue
            tries = 0
            buf += newbuf
            received += len(newbuf)
        return buf


class NetClient(BUIbackend):
    """The :class:`burpui.misc.backend.multi.NetClient` class provides a
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
        self._agent_version = None

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

    async def _get_agent_version(self):
        if await self.ping() and not self._agent_version:
            data = {'func': 'agent_version'}
            try:
                vers = await self.do_command(data)
                self._agent_version = json.loads(to_unicode(vers))
            except BUIserverException:
                # just ignore the error if this custom function is not
                # implemented
                pass
        return self._agent_version

    async def ping(self):
        """Check if we are connected to the agent"""
        res = False
        try:
            async with TCPsocket(self.host, self.port, self.ssl) as (client_stream, _):
                await client_stream.send_all(struct.pack('!Q', 2))
                await client_stream.send_all(b'RE')
                res = True
        except OSError:
            pass
        return res

    async def setup(self, client_stream: trio.SocketStream, tcp_sock: TCPsocket, data):
        length = struct.pack('!Q', len(data))
        await client_stream.send_all(length)
        data = to_unicode(data)
        await client_stream.send_all(to_bytes(data))
        self.logger.debug(f"Sending: {data!r}")
        tmp = await client_stream.receive_some(2)
        tmp = to_unicode(tmp)
        self.logger.debug(f"recv: '{tmp!r}'")
        if 'ER' == tmp:
            lengthbuf = await client_stream.receive_some(8)
            length, = struct.unpack('!Q', lengthbuf)
            err = await TCPsocket.receive_all(length)
            err = to_unicode(err)
            raise BUIserverException(err)
        if 'OK' != tmp:
            self.logger.debug('Ooops, unsuccessful!')
            return False
        self.logger.debug("Data sent successfully")
        return True

    async def do_command(self, data=None, restarted=False):
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
                tcp_socket = TCPsocket(self.host, self.port, self.ssl)
                await tcp_socket.conn()
                raw = json.dumps(data)
                async with tcp_socket.client_stream:
                    setup = await self.setup(tcp_socket.client_stream, tcp_socket, raw)
                if not setup:
                    return res
                return tcp_socket.client_stream

            async def __inner_job():
                nonlocal res
                nonlocal err
                async with TCPsocket(self.host, self.port, self.ssl) as (client_stream, tcp_socket):
                    async with client_stream:
                        try:
                            raw = json.dumps(data)
                            setup = await self.setup(client_stream, tcp_socket, raw)
                            if not setup:
                                return res
                            lengthbuf = await client_stream.receive_some(8)
                            length, = struct.unpack('!Q', lengthbuf)
                            res = await tcp_socket.receive_all(length)
                            res = to_unicode(res)
                        except IOError as exc:
                            if not restarted and exc.errno == errno.EPIPE:
                                self.logger.warning('Broken pipe, restarting the request')
                                return await self.do_command(data, True)
                            elif exc.errno == errno.ECONNRESET:
                                self.logger.error('!!! {} !!!\nPlease check your SSL configuration on both sides!'.format(str(exc)))
                            else:
                                self.logger.error('!!! {} !!!'.format(str(exc)), exc_info=True)
                            raise exc
                        # catch all
                        except Exception as exc:
                            self.logger.error('!!! {} !!!'.format(str(exc)), exc_info=exc)
                            if data['func'] == 'restore_files':
                                err = str(exc)
                            elif isinstance(exc, BUIserverException):
                                raise exc
                            else:
                                raise BUIserverException(str(exc))
                return res
            timedout = True
            if notimeout:
                timedout = False
                res = await __inner_job()
            else:
                with trio.move_on_after(timeout) as cancel_scope:
                    res = await __inner_job()
                    timedout = cancel_scope.cancelled_caught
            if timedout:
                if self.app.gunicorn and not restarted:
                    self.logger.warning('Socket timed-out, restarting the request')
                    return await self.do_command(data, True)
                self.logger.error('!!! TimeoutError !!!')
                raise TimeoutError()
        except Exception as exc:
            self.logger.error('!!! {} !!!'.format(str(exc)), exc_info=exc)
            raise BUIserverException(str(exc))

        if data['func'] == 'restore_files':
            if err:
                res = None
            return res, err

        return res

    """
    Utilities functions
    """

    @implement
    def store_conf_cli(self, data, client=None, conf=None, template=False, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.store_conf_cli`"""
        # serialize data as it is a nested dict
        import hmac
        import hashlib
        from base64 import b64encode
        if not isinstance(data, (_ImmutableMultiDict, ImmutableMultiDict)):
            msg = 'Wrong data type'
            self.logger.warning(msg)
            raise BUIserverException(msg)
        vers = trio.run(self._get_agent_version)
        if vers and vers >= AGENT_VERSION_CAST:
            # convert the data to our custom ImmutableMultiDict
            data = ImmutableMultiDict(data.to_dict(False))
        key = '{}{}'.format(self.password, 'store_conf_cli')
        key = to_bytes(key)
        pickles = to_unicode(b64encode(pickle.dumps({'data': data, 'conf': conf, 'client': client, 'template': template}, 2)))
        bytes_pickles = to_bytes(pickles)
        digest = to_unicode(hmac.new(key, bytes_pickles, hashlib.sha1).hexdigest())
        data = {'func': 'store_conf_cli', 'args': pickles, 'pickled': True, 'digest': digest}
        return json.loads(trio.run(self.do_command, data))

    @implement
    def store_conf_srv(self, data, conf=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.store_conf_srv`"""
        # serialize data as it is a nested dict
        import hmac
        import hashlib
        from base64 import b64encode
        if not isinstance(data, (_ImmutableMultiDict, ImmutableMultiDict)):
            msg = 'Wrong data type'
            self.logger.warning(msg)
            raise BUIserverException(msg)
        vers = trio.run(self._get_agent_version)
        if vers and vers >= AGENT_VERSION_CAST:
            # convert the data to our custom ImmutableMultiDict
            data = ImmutableMultiDict(data.to_dict(False))
        key = '{}{}'.format(self.password, 'store_conf_srv')
        key = to_bytes(key)
        pickles = to_unicode(b64encode(pickle.dumps({'data': data, 'conf': conf}, 2)))
        bytes_pickles = to_bytes(pickles)
        digest = to_unicode(hmac.new(key, bytes_pickles, hashlib.sha1).hexdigest())
        data = {'func': 'store_conf_srv', 'args': pickles, 'pickled': True, 'digest': digest}
        return json.loads(trio.run(self.do_command, data))

    @implement
    def restore_files(self, name=None, backup=None, files=None, strip=None, archive='zip', password=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.restore_files`"""
        data = {'func': 'restore_files', 'args': {'name': name, 'backup': backup, 'files': files, 'strip': strip, 'archive': archive, 'password': password}}
        return trio.run(self.do_command, data)

    @implement
    def get_file(self, path, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_file`"""
        data = {'func': 'get_file', 'path': path}
        return trio.run(self.do_command, data)

    @implement
    def del_file(self, path, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.del_file`"""
        data = {'func': 'del_file', 'path': path}
        return json.loads(trio.run(self.do_command, data))
