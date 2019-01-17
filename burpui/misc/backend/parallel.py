# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.backend.parallel
    :platform: Unix
    :synopsis: Burp-UI parallel backend module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import re
import json
import ssl
import trio
import struct
import logging

from .burp2 import Burp as Burp2
from .interface import BUIbackend
from .utils.constant import BURP_STATUS_FORMAT_V2
from ..parser.burp2 import Parser
from ...exceptions import BUIserverException
from ..._compat import to_unicode, to_bytes

BUI_DEFAULTS = {
    'Parallel': {
        'host': '::1',
        'port': 11111,
        'ssl': True,
        'password': 'password123456',
        'timeout': 15,
        'concurrency': 2,
    },
}


class Parallel:
    logger = logging.getLogger('burp-ui')  # type: logging.Logger

    def __init__(self, conf):
        """Parallel client

        :param conf: Configuration to use
        :type conf: :class:`burpui.config.BUIConfig`
        """

        self.host = conf.safe_get('host', section='Parallel', defaults=BUI_DEFAULTS)
        self.port = conf.safe_get('port', 'integer', section='Parallel', defaults=BUI_DEFAULTS)
        self.ssl = conf.safe_get('ssl', 'boolean', section='Parallel', defaults=BUI_DEFAULTS)
        self.password = conf.safe_get('password', section='Parallel', defaults=BUI_DEFAULTS)
        self.timeout = conf.safe_get('timeout', 'integer', section='Parallel', defaults=BUI_DEFAULTS)

        self.logger.debug(f'Monitor {self.host}:{self.port} - ssl: {self.ssl}')

        self.connected = False

    async def conn(self):
        try:
            if self.ssl:
                ctx = ssl.SSLContext()
                ctx.verify_mode = ssl.CERT_NONE
                ctx.check_hostname = False
                ctx.options |= (
                    ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
                )  # RFC 7540 Section 9.2: MUST be TLS >=1.2
                ctx.options |= ssl.OP_NO_COMPRESSION  # RFC 7540 Section 9.2.1: MUST disable compression
                ctx.load_default_certs()
                self.client_stream = await trio.open_ssl_over_tcp_stream(self.host, self.port, ssl_context=ctx)
            else:
                self.client_stream = await trio.open_tcp_stream(self.host, self.port)
        except OSError as exc:
            raise BUIserverException(str(exc))

        self.logger.debug('Connected')
        self.connected = True
        return self.client_stream

    async def _do_process(self, data):
        res = '[]'
        data = to_bytes(data)
        length = struct.pack('!Q', len(data))
        await self.client_stream.send_all(length)
        self.logger.debug(f'Sending: {data!r}')
        await self.client_stream.send_all(data)
        tmp = await self.client_stream.receive_some(2)
        tmp = to_unicode(tmp)
        if tmp == 'ER':
            lengthbuf = await self.client_stream.receive_some(8)
            length, = struct.unpack('!Q', lengthbuf)
            err = await self.receive_all(length)
            err = to_unicode(err)
            raise BUIserverException(err)
        if tmp != 'OK':
            self.logger.debug('Ooops, unsuccessful!')
            return res
        self.logger.debug("Data sent successfully")
        lengthbuf = await self.client_stream.receive_some(8)
        length, = struct.unpack('!Q', lengthbuf)
        res = await self.receive_all(length)
        res = to_unicode(res)
        self.logger.debug(f'Received: {res!r}')
        return res

    async def _process(self, data):
        if not self.connected:
            await self.conn()
            async with self.client_stream:
                result = await self._do_process(data)
            self.connected = False
        else:
            result = await self._do_process(data)
        return result

    async def status(self, query, timeout=None, cache=True):

        request = {
            'query': query,
            'timeout': timeout,
            'cache': cache,
            'password': self.password,
        }
        request = json.dumps(request)
        result = await self._process(request)
        return json.loads(result)

    async def request(self, func, *args, **kwargs):
        req = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'password': self.password,
        }
        req = json.dumps(req)
        result = await self._process(req)
        return result

    async def receive_all(self, length=1024, bsize=None):
        buf = b''
        bsize = bsize if bsize is not None else 1024
        bsize = min(bsize, length)
        received = 0
        tries = 0
        while received < length:
            newbuf = await self.client_stream.receive_some(bsize)
            if not newbuf:
                # 3 successive read failure => raise exception
                if tries > 3:
                    raise Exception('Unable to read full response')
                tries += 1
                trio.sleep(0.1)
                continue
            # reset counter
            tries = 0
            buf += newbuf
            received += len(newbuf)
        return buf


# Some functions are the same as in Burp1 backend
class Burp(Burp2):
    """The :class:`burpui.misc.backend.parallel.Burp` class provides a consistent
    backend for ``burp-2`` servers through the bui-monitor pool. It is also able to
    perform some operations asynchronously to speedup the whole API.

    It extends the :class:`burpui.misc.backend.burp2.Burp` class because a few
    functions can be reused. The rest is just overridden.

    :param server: ``Burp-UI`` server instance in order to access logger
                   and/or some global settings
    :type server: :class:`burpui.engines.server.BUIServer`

    :param conf: Configuration to use
    :type conf: :class:`burpui.config.BUIConfig`
    """

    # backend version
    _vers = 2
    # cache to store the guessed OS
    _os_cache = {}

    _client_version = None
    _server_version = None
    _batch_list_supported = None

    def __init__(self, server=None, conf=None):
        """
        :param server: ``Burp-UI`` server instance in order to access logger
                       and/or some global settings
        :type server: :class:`burpui.engines.server.BUIServer`

        :param conf: Configuration to use
        :type conf: :class:`burpui.config.BUIConfig`
        """

        BUIbackend.__init__(self, server, conf)

        self.parser = Parser(self)
        self.conf = conf

        self.concurrency = conf.safe_get('concurrency', 'integer', section='Parallel', defaults=BUI_DEFAULTS)

        self.logger.info('burp conf cli: {}'.format(self.burpconfcli))
        self.logger.info('burp conf srv: {}'.format(self.burpconfsrv))
        self.logger.info('command timeout: {}'.format(self.timeout))
        self.logger.info('tmpdir: {}'.format(self.tmpdir))
        self.logger.info('zip64: {}'.format(self.zip64))
        self.logger.info('includes: {}'.format(self.includes))
        self.logger.info('enforce: {}'.format(self.enforce))
        self.logger.info('revoke: {}'.format(self.revoke))
        self.logger.info('concurrency: {}'.format(self.concurrency))

    @property
    def client_version(self):
        if self._client_version is None:
            self._client_version = trio.run(self._async_request, 'client_version')
        return self._client_version

    @property
    def server_version(self):
        if self._server_version is None:
            self._server_version = trio.run(self._async_request, 'server_version')
        return self._server_version

    @property
    def batch_list_supported(self):
        if self._batch_list_supported is None:
            self._batch_list_supported = json.loads(trio.run(self._async_request, 'batch_list_supported'))
        return self._batch_list_supported

    def statistics(self, agent=None):
        return json.loads(trio.run(self._async_request, 'statistics'))

    async def _async_status(self, query='c:\n', timeout=None, cache=True):
        async_client = Parallel(self.conf)
        try:
            return await async_client.status(query, timeout, cache)
        except OSError as exc:
            raise BUIserverException(str(exc))

    async def _async_request(self, func, *args, **kwargs):
        async_client = Parallel(self.conf)
        try:
            return await async_client.request(func, *args, **kwargs)
        except OSError as exc:
            raise BUIserverException(str(exc))

    def status(self, query='c:\n', timeout=None, cache=True, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.status`"""
        return trio.run(self._async_status, query, timeout, cache)

    async def _async_get_backup_logs(self, number, client, forward=False, deep=False, store=None, limit=None):
        async def _do_stuff():
            nonlocal client
            nonlocal number
            nonlocal forward
            nonlocal deep
            bucket1 = []
            bucket2 = []
            ret = {}
            query = await self._async_status('c:{0}:b:{1}\n'.format(client, number))
            if not query:
                return ret
            try:
                logs = query['clients'][0]['backups'][0]['logs']['list']
            except KeyError:
                self.logger.warning('No logs found')
                return ret
            async with trio.open_nursery() as nursery:
                if 'backup_stats' in logs:
                    nursery.start_soon(self._async_parse_backup_stats, number, client, forward, None, bucket1)
                if 'backup' in logs and deep:
                    nursery.start_soon(self._async_parse_backup_log, number, client, bucket2)

            if bucket1:
                ret = bucket1[0]
            if bucket2:
                ret.update(bucket2[0])

            ret['encrypted'] = False
            if 'files_enc' in ret and ret['files_enc']['total'] > 0:
                ret['encrypted'] = True
            return ret

        if limit is not None:
            async with limit:
                res = await _do_stuff()
        else:
            res = await _do_stuff()

        if store is not None:
            store.append(res)
        else:
            return res

    async def _async_get_all_backup_logs(self, client, forward=False, deep=False):
        ret = []
        backups = await self._async_get_client(client)
        queue = []
        limit = trio.CapacityLimiter(self.concurrency)
        async with trio.open_nursery() as nursery:
            for back in backups:
                nursery.start_soon(self._async_get_backup_logs, back['number'], client, forward, deep, queue, limit)

        ret = sorted(queue, key=lambda x: x['number'])
        return ret

    def get_backup_logs(self, number, client, forward=False, deep=False, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_backup_logs`
        """
        if not client or not number:
            return {} if number and number != -1 else []

        if number == -1:
            return trio.run(self._async_get_all_backup_logs, client, forward, deep)
        return trio.run(self._async_get_backup_logs, number, client, forward, deep)

    async def _async_parse_backup_log(self, number, client, bucket=None):
        query = await self._async_status('c:{0}:b:{1}:l:backup\n'.format(client, number))
        res = self._do_parse_backup_log(query, client)
        if bucket is not None:
            bucket.append(res)
        return res

    def _parse_backup_log(self, number, client):
        """The :func:`burpui.misc.backend.burp2.Burp._parse_backup_log`
        function helps you determine if the backup is protocol 2 or 1 and various
        useful details.

        :param number: Backup number to work on
        :type number: int

        :param client: Client name to work on
        :type client: str

        :returns: a dict with some useful details
        """
        return trio.run(self._async_parse_backup_log, number, client)

    async def _async_parse_backup_stats(self, number, client, forward=False, agent=None, bucket=None):
        """The :func:`burpui.misc.backend.parallel.Burp._async_parse_backup_stats`
        function is used to parse the burp logs.

        :param number: Backup number to work on
        :type number: int

        :param client: Client name to work on
        :type client: str

        :param forward: Is the client name needed in later process
        :type forward: bool

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: Dict containing the backup log
        """
        backup = {'os': await self._async_guess_os(client), 'number': int(number)}
        if forward:
            backup['name'] = client
        query = await self._async_status(
            'c:{0}:b:{1}:l:backup_stats\n'.format(client, number)
        )
        ret = self._do_parse_backup_stats(query, backup, number, client, forward, agent)
        if bucket is not None:
            bucket.append(ret)
        return ret

    # def get_clients_report(self, clients, agent=None):

    # inherited
    # def get_counters(self, name=None, agent=None):

    # def is_backup_running(self, name=None, agent=None):

    # def is_one_backup_running(self, agent=None):

    async def _async_get_last_backup(self, name):
        """Return the last backup of a given client

        :param name: Name of the client
        :type name: str

        :returns: The last backup
        """
        try:
            clients = await self._async_status('c:{}'.format(name))
            client = clients['clients'][0]
            return client['backups'][0]
        except (KeyError, BUIserverException):
            return None

    def _get_last_backup(self, name):
        """Return the last backup of a given client

        :param name: Name of the client
        :type name: str

        :returns: The last backup
        """
        return trio.run(self._async_get_last_backup, name)

    async def _async_guess_os(self, name):
        """Return the OS of the given client based on the magic *os* label

        :param name: Name of the client
        :type name: str

        :returns: The guessed OS of the client

        ::

            grep label /etc/burp/clientconfdir/toto
            label = os: Darwin OS
        """
        ret = 'Unknown'
        if name in self._os_cache:
            return self._os_cache[name]

        labels = await self._async_get_client_labels(name)
        OSES = []

        for label in labels:
            if re.match('os:', label, re.IGNORECASE):
                _os = label.split(':', 1)[1].strip()
                if _os not in OSES:
                    OSES.append(_os)

        if OSES:
            ret = OSES[-1]
        else:
            # more aggressive check
            last = await self._async_get_last_backup(name)
            if last:
                try:
                    tree = await self._async_get_tree(name, last['number'])

                    if tree[0]['name'] != '/':
                        ret = 'Windows'
                    else:
                        ret = 'Unix/Linux'
                except (IndexError, KeyError, BUIserverException):
                    pass

        self._os_cache[name] = ret
        return ret

    def _guess_os(self, name):
        """Return the OS of the given client based on the magic *os* label

        :param name: Name of the client
        :type name: str

        :returns: The guessed OS of the client

        ::

            grep label /etc/burp/clientconfdir/toto
            label = os: Darwin OS
        """
        return trio.run(self._async_guess_os, name)

    async def _async_get_all_clients(self):
        ret = []
        query = await self._async_status()
        if not query or 'clients' not in query:
            return ret

        async def __compute_client_data(client, limit, queue):
            async with limit:
                cli = {}
                cli['name'] = client['name']
                cli['state'] = self._status_human_readable(client['run_status'])
                infos = client['backups']
                if cli['state'] in ['running']:
                    cli['last'] = 'now'
                elif not infos:
                    cli['last'] = 'never'
                else:
                    infos = infos[0]
                    logs = await self._async_get_backup_logs(infos['number'], client['name'])
                    cli['last'] = logs['start']
                queue.append(cli)

        clients = query['clients']
        limiter = trio.CapacityLimiter(self.concurrency)

        async with trio.open_nursery() as nursery:
            for client in clients:
                nursery.start_soon(__compute_client_data, client, limiter, ret)

        return ret

    def get_all_clients(self, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_all_clients`
        """
        # don't need async processing if burp-server < BURP_STATUS_FORMAT_V2
        if not self.deep_inspection or (self.server_version and
                                        self.server_version < BURP_STATUS_FORMAT_V2):
            return Burp2.get_all_clients(self)
        # the deep inspection can take advantage of async processing
        return trio.run(self._async_get_all_clients)

    # def get_client_status(self, name=None, agent=None):

    async def _async_get_client(self, name=None):
        return await self._async_get_client_filtered(name)

    def get_client(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client`"""
        return trio.run(self._async_get_client, name)

    async def _async_get_client_filtered(self, name=None, limit=-1, page=None, start=None, end=None):
        ret = []
        if not name:
            return ret
        query = await self._async_status('c:{0}\n'.format(name))
        if not query:
            return ret
        try:
            backups = query['clients'][0]['backups']
        except (KeyError, IndexError):
            self.logger.warning('Client not found')
            return ret

        async def __parse_log(backup, client, back, ret, limiter):
            async with limiter:
                append = True
                log = await self._async_get_backup_logs(backup['number'], client)
                try:
                    back['encrypted'] = log['encrypted']
                    try:
                        back['received'] = log['received']
                    except KeyError:
                        back['received'] = 0
                    try:
                        back['size'] = log['totsize']
                    except KeyError:
                        back['size'] = 0
                    back['end'] = log['end']
                    # override date since the timestamp is odd
                    back['date'] = log['start']
                except Exception:
                    self.logger.warning('Unable to parse logs')
                    append = False

                if append:
                    ret.append(back)

        queue = []
        limiter = trio.CapacityLimiter(self.concurrency)

        async with trio.open_nursery() as nursery:
            for idx, backup in enumerate(backups):
                back = {}
                # skip the first elements if we are in a page
                if page and page > 1 and limit > 0:
                    if idx < (page - 1) * limit:
                        continue

                # skip running backups since data will be inconsistent
                if 'flags' in backup and 'working' in backup['flags']:
                    continue
                back['number'] = backup['number']
                if 'flags' in backup and 'deletable' in backup['flags']:
                    back['deletable'] = True
                else:
                    back['deletable'] = False
                back['date'] = backup['timestamp']
                # skip backups before "start"
                if start and backup['timestamp'] < start:
                    continue
                # skip backups after "end"
                if end and backup['timestamp'] > end:
                    continue

                nursery.start_soon(__parse_log, backup, name, back, queue, limiter)

                # stop after "limit" elements
                if page and page > 1 and limit > 0:
                    if idx >= page * limit:
                        break
                elif limit > 0 and idx >= limit:
                    break

        # Here we need to reverse the array so the backups are sorted by num
        # ASC
        ret = sorted(queue, key=lambda x: x['number'])
        return ret

    def get_client_filtered(self, name=None, limit=-1, page=None, start=None, end=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_filtered`"""
        return trio.run(self._async_get_client_filtered, name, limit, page, start, end)

    # def is_backup_deletable(self, name=None, backup=None, agent=None):

    async def _async_get_tree(self, name=None, backup=None, root=None, level=-1):
        ret = []
        if not name or not backup:
            return ret
        if not root:
            top = ''
        else:
            top = to_unicode(root)

        # we know this operation may take a while so we arbitrary increase the
        # read timeout
        timeout = None
        if top == '*':
            timeout = max(self.timeout, 300)

        query = await self._async_status(
            'c:{0}:b:{1}:p:{2}\n'.format(name, backup, top),
            timeout
        )
        return self._format_tree(query, top, level)

    def get_tree(self, name=None, backup=None, root=None, level=-1, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_tree`"""
        return trio.run(self._async_get_tree, name, backup, root, level)

    # def get_client_version(self, agent=None):

    # def get_server_version(self, agent=None):

    async def _async_get_client_labels(self, client=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_client_labels`
        """
        ret = []
        if not client:
            return ret
        # micro optimization since the status results are cached in memory for a
        # couple seconds, using the same global query and iterating over it
        # will be more efficient than filtering burp-side
        query = await self._async_status('c:\n')
        if not query:
            return ret
        try:
            for cli in query['clients']:
                if cli['name'] == client:
                    return cli['labels']
        except KeyError:
            return ret

    def get_client_labels(self, client=None, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_client_labels`
        """
        return trio.run(self._async_get_client_labels, client)

    # Same as in Burp1 backend
    # def restore_files(
    #     self,
    #     name=None,
    #     backup=None,
    #     files=None,
    #     strip=None,
    #     archive='zip',
    #     password=None,
    #     agent=None):

    # def read_conf_cli(self, agent=None):

    # def read_conf_srv(self, agent=None):

    # def store_conf_cli(self, data, agent=None):

    # def store_conf_srv(self, data, agent=None):

    # def get_parser_attr(self, attr=None, agent=None):
