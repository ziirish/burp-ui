# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.backend.parallel
    :platform: Unix
    :synopsis: Burp-UI parallel backend module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import json
import os
import re
import ssl
import struct
import time
from asyncio import iscoroutinefunction
from functools import partial

import trio

from ..._compat import to_bytes, to_unicode
from ...decorators import implement, usetriorun
from ...exceptions import BUIserverException
from ...tools.logging import logger
from ...utils import utc_to_local
from ..parser.burp2 import Parser
from .burp2 import Burp as Burp2
from .interface import BUIBACKEND_INTERFACE_METHODS, BUIbackend
from .utils.constant import BURP_STATUS_FORMAT_V2

BUI_DEFAULTS = {
    "Parallel": {
        "host": "::1",
        "port": 11111,
        "ssl": True,
        "password": "password123456",
        "timeout": 15,
        "concurrency": 2,
        "init_wait": 15,
    },
}


class Connector:
    logger = logger

    def __init__(self, conf):
        """Connector client

        :param conf: Configuration to use
        :type conf: :class:`burpui.config.BUIConfig`
        """
        self.host = conf.safe_get("host", section="Parallel", defaults=BUI_DEFAULTS)
        self.port = conf.safe_get(
            "port", "integer", section="Parallel", defaults=BUI_DEFAULTS
        )
        self.ssl = conf.safe_get(
            "ssl", "boolean", section="Parallel", defaults=BUI_DEFAULTS
        )
        self.password = conf.safe_get(
            "password", section="Parallel", defaults=BUI_DEFAULTS
        )
        self.timeout = conf.safe_get(
            "timeout", "integer", section="Parallel", defaults=BUI_DEFAULTS
        )

        self.logger.debug(f"Monitor {self.host}:{self.port} - ssl: {self.ssl}")

        self.connected = False

    async def conn(self):
        try:
            if self.ssl:
                ctx = ssl.SSLContext()
                ctx.verify_mode = ssl.CERT_NONE
                ctx.check_hostname = False
                ctx.options |= (
                    ssl.OP_NO_SSLv2
                    | ssl.OP_NO_SSLv3
                    | ssl.OP_NO_TLSv1
                    | ssl.OP_NO_TLSv1_1
                )  # RFC 7540 Section 9.2: MUST be TLS >=1.2
                ctx.options |= (
                    ssl.OP_NO_COMPRESSION
                )  # RFC 7540 Section 9.2.1: MUST disable compression
                ctx.load_default_certs()
                self.client_stream = await trio.open_ssl_over_tcp_stream(
                    self.host, self.port, ssl_context=ctx
                )
            else:
                self.client_stream = await trio.open_tcp_stream(self.host, self.port)
        except OSError as exc:
            raise BUIserverException(str(exc))

        self.logger.debug("Connected")
        self.connected = True
        return self.client_stream

    async def _send(self, data):
        data = to_bytes(data)
        length = struct.pack("!Q", len(data))
        await self.client_stream.send_all(length)
        self.logger.debug(f"Sending: {data!r}")
        await self.client_stream.send_all(data)

    async def _do_process(self, data):
        res = "[]"
        await self._send(data)
        tmp = await self.client_stream.receive_some(2)
        tmp = to_unicode(tmp)
        if tmp == "ER":
            lengthbuf = await self.client_stream.receive_some(8)
            (length,) = struct.unpack("!Q", lengthbuf)
            err = await self.receive_all(length)
            err = to_unicode(err)
            raise BUIserverException(err)
        if tmp != "OK":
            self.logger.debug("Ooops, unsuccessful!")
            return res
        self.logger.debug("Data sent successfully")
        lengthbuf = await self.client_stream.receive_some(8)
        (length,) = struct.unpack("!Q", lengthbuf)
        res = await self.receive_all(length)
        res = to_unicode(res)
        self.logger.debug(f"Received: {res!r}")
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
            "query": query,
            "timeout": timeout,
            "cache": cache,
            "password": self.password,
        }
        request = json.dumps(request)
        result = await self._process(request)
        return json.loads(result)

    async def request(self, func, *args, **kwargs):
        req = {
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "password": self.password,
        }
        req = json.dumps(req)
        result = await self._process(req)
        return result

    async def receive_all(self, length=1024, bsize=None):
        buf = b""
        bsize = bsize if bsize is not None else 1024
        bsize = min(bsize, length)
        received = 0
        tries = 0
        while received < length:
            newbuf = await self.client_stream.receive_some(bsize)
            if not newbuf:
                # 3 successive read failure => raise exception
                if tries > 3:
                    raise IOError("Unable to read full response")
                tries += 1
                trio.sleep(0.1)
                continue
            # reset counter
            tries = 0
            buf += newbuf
            received += len(newbuf)
        return buf


# Asynchronous functions for the bui-monitor pool
class AsyncBurpMixin:
    async def _async_statistics(self, agent=None):
        return json.loads(await self._async_request("statistics"))

    async def _async_get_client_version(self, agent=None):
        if self._client_version is None:
            try:
                self._client_version = await self._async_request("client_version")
            except BUIserverException:
                return ""
        return self._client_version or ""

    async def _async_get_server_version(self, agent=None):
        if self._server_version is None:
            try:
                self._server_version = await self._async_request("server_version")
            except BUIserverException:
                return ""
        return self._server_version or ""

    async def _async_status(self, query="c:\n", timeout=None, cache=True, agent=None):
        try:
            connector = Connector(self.conf)
            return await connector.status(query, timeout, cache)
        except (OSError, IOError) as exc:
            raise BUIserverException(str(exc))
        if not self._ready:
            self.init_all()

    async def _async_request(self, func, *args, **kwargs):
        try:
            connector = Connector(self.conf)
            return await connector.request(func, *args, **kwargs)
        except (OSError, IOError) as exc:
            raise BUIserverException(str(exc))

    async def _async_get_backup_logs(
        self, number, client, forward=False, deep=False, store=None, limit=None
    ):
        async def _do_stuff():
            nonlocal client
            nonlocal number
            nonlocal forward
            nonlocal deep
            bucket1 = []
            bucket2 = []
            ret = {}
            query = await self._async_status("c:{0}:b:{1}\n".format(client, number))
            if not query:
                return ret
            try:
                logs = query["clients"][0]["backups"][0]["logs"]["list"]
            except KeyError:
                self.logger.warning("No logs found")
                return ret
            async with trio.open_nursery() as nursery:
                if "backup_stats" in logs:
                    nursery.start_soon(
                        self._async_parse_backup_stats,
                        number,
                        client,
                        forward,
                        None,
                        bucket1,
                    )
                if "backup" in logs and deep:
                    nursery.start_soon(
                        self._async_parse_backup_log, number, client, bucket2
                    )

            if bucket1:
                ret = bucket1[0]
            if bucket2:
                ret.update(bucket2[0])

            ret["encrypted"] = False
            if "files_enc" in ret and ret["files_enc"]["total"] > 0:
                ret["encrypted"] = True
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
                nursery.start_soon(
                    self._async_get_backup_logs,
                    back["number"],
                    client,
                    forward,
                    deep,
                    queue,
                    limit,
                )

        ret = sorted(queue, key=lambda x: x["number"])
        return ret

    async def _async_parse_backup_log(self, number, client, bucket=None):
        query = await self._async_status(
            "c:{0}:b:{1}:l:backup\n".format(client, number)
        )
        res = self._do_parse_backup_log(query, client)
        if bucket is not None:
            bucket.append(res)
        return res

    async def _async_parse_backup_stats(
        self, number, client, forward=False, agent=None, bucket=None
    ):
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
        backup = {"os": await self._async_guess_os(client), "number": int(number)}
        if forward:
            backup["name"] = client
        query = await self._async_status(
            "c:{0}:b:{1}:l:backup_stats\n".format(client, number)
        )
        ret = self._do_parse_backup_stats(query, backup, number, client, forward, agent)
        if bucket is not None:
            bucket.append(ret)
        return ret

    async def _async_get_clients_report(self, clients, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_clients_report`"""

        async def __compute_client_report(cli, queue, limit):
            async with limit:
                if not cli:
                    return
                client = await self._async_get_client(cli["name"])
                if not client or not client[-1]:
                    return
                stats = await self._async_get_backup_logs(
                    client[-1]["number"], cli["name"]
                )
                queue.append((cli, client, stats))

        data = []
        limiter = trio.CapacityLimiter(self.concurrency)

        async with trio.open_nursery() as nursery:
            for client in clients:
                nursery.start_soon(__compute_client_report, client, data, limiter)

        return self._do_get_clients_report(data)

    async def _async_get_counters(self, name=None, agent=None):
        ret = {}
        query = await self._async_status("c:{0}\n".format(name), cache=False)
        # check the status returned something
        if not query:
            return ret

        try:
            client = query["clients"][0]
        except KeyError:
            self.logger.warning("Client not found")
            return ret
        return self._do_get_counters(client)

    async def _async_is_backup_running(self, name=None, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.is_backup_running`
        """
        if not name:
            return False
        try:
            query = await self._async_status("c:{0}\n".format(name))
        except BUIserverException:
            return False
        return self._do_is_backup_running(query)

    async def _async_is_one_backup_running(self, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.is_one_backup_running`
        """
        ret = []
        try:
            clients = await self._async_get_all_clients(deep=False, last_attempt=False)
        except BUIserverException:
            return ret
        return self._do_is_one_backup_running(clients)

    async def _async_get_last_backup(self, name, working=True):
        """Return the last backup of a given client

        :param name: Name of the client
        :type name: str

        :param working: Also return uncomplete backups
        :type working: bool

        :returns: The last backup
        """
        try:
            clients = await self._async_status("c:{}".format(name))
            client = clients["clients"][0]
            i = 0
            while True:
                ret = client["backups"][i]
                if not working and "working" in ret["flags"]:
                    i += 1
                    continue
                return ret
        except (KeyError, IndexError, BUIserverException):
            return None

    async def _async_guess_os(self, name):
        """Return the OS of the given client based on the magic *os* label

        :param name: Name of the client
        :type name: str

        :returns: The guessed OS of the client

        ::

            grep label /etc/burp/clientconfdir/toto
            label = os: Darwin OS
        """
        ret = "Unknown"
        if name in self._os_cache:
            return self._os_cache[name]

        labels = await self._async_get_client_labels(name)
        OSES = []

        for label in labels:
            if re.match("os:", label, re.IGNORECASE):
                _os = label.split(":", 1)[1].strip()
                if _os not in OSES:
                    OSES.append(_os)

        if OSES:
            ret = OSES[-1]
        else:
            # more aggressive check
            last = await self._async_get_last_backup(name, False)
            if last:
                try:
                    tree = await self._async_get_tree(name, last["number"])

                    if tree[0]["name"] != "/":
                        ret = "Windows"
                    else:
                        ret = "Unix/Linux"
                except (IndexError, KeyError, BUIserverException):
                    pass

        self._os_cache[name] = ret
        return ret

    async def _async_get_all_clients(self, agent=None, deep=True, last_attempt=True):
        ret = []
        query = await self._async_status()
        if not query or "clients" not in query:
            return ret

        async def __compute_client_data(client, queue, limit):
            async with limit:
                cli = {}
                cli["name"] = client["name"]
                cli["state"] = self._status_human_readable(client["run_status"])
                infos = client["backups"]
                if cli["state"] in ["running"]:
                    cli["last"] = "now"
                    cli["last_attempt"] = "now"
                elif not infos:
                    cli["last"] = "never"
                    cli["last_attempt"] = "never"
                else:
                    convert = True
                    infos = infos[0]
                    server_version = await self._async_get_server_version()
                    if server_version and server_version < BURP_STATUS_FORMAT_V2:
                        cli["last"] = infos["timestamp"]
                        convert = False
                    # only do deep inspection when server >= BURP_STATUS_FORMAT_V2
                    if deep:
                        logs = await self._async_get_backup_logs(
                            infos["number"], client["name"]
                        )
                        cli["last"] = logs["start"]
                    else:
                        cli["last"] = utc_to_local(infos["timestamp"])
                    if last_attempt:
                        last_backup = await self._async_get_last_backup(client["name"])
                        if convert:
                            cli["last_attempt"] = utc_to_local(last_backup["timestamp"])
                        else:
                            cli["last_attempt"] = last_backup["timestamp"]
                queue.append(cli)

        clients = query["clients"]
        limiter = trio.CapacityLimiter(self.concurrency)

        async with trio.open_nursery() as nursery:
            for client in clients:
                nursery.start_soon(__compute_client_data, client, ret, limiter)

        return ret

    async def _async_get_client_status(self, name=None, agent=None):
        ret = {}
        if not name:
            return ret
        query = await self._async_status("c:{0}\n".format(name))
        if not query:
            return ret
        try:
            client = query["clients"][0]
        except (KeyError, IndexError):
            self.logger.warning("Client not found")
            return ret
        return self._do_get_client_status(client)

    async def _async_get_client_filtered(
        self, name=None, limit=-1, page=None, start=None, end=None, agent=None
    ):
        ret = []
        if not name:
            return ret
        query = await self._async_status("c:{0}\n".format(name))
        if not query:
            return ret
        try:
            backups = query["clients"][0]["backups"]
        except (KeyError, IndexError):
            self.logger.warning("Client not found")
            return ret

        async def __parse_log(backup, client, back, ret, limiter):
            async with limiter:
                append = True
                log = await self._async_get_backup_logs(backup["number"], client)
                try:
                    back["encrypted"] = log["encrypted"]
                    try:
                        back["received"] = log["received"]
                    except KeyError:
                        back["received"] = 0
                    try:
                        back["size"] = log["totsize"]
                    except KeyError:
                        back["size"] = 0
                    back["end"] = log["end"]
                    # override date since the timestamp is odd
                    back["date"] = log["start"]
                except Exception:
                    self.logger.warning("Unable to parse logs")
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
                if "flags" in backup and "working" in backup["flags"]:
                    continue
                back["number"] = backup["number"]
                if "flags" in backup and "deletable" in backup["flags"]:
                    back["deletable"] = True
                else:
                    back["deletable"] = False
                back["date"] = backup["timestamp"]
                # skip backups before "start"
                if start and backup["timestamp"] < start:
                    continue
                # skip backups after "end"
                if end and backup["timestamp"] > end:
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
        ret = sorted(queue, key=lambda x: x["number"])
        return ret

    async def _async_get_tree(
        self, name=None, backup=None, root=None, level=-1, agent=None
    ):
        ret = []
        if not name or not backup:
            return ret
        if not root:
            top = ""
        else:
            top = to_unicode(root)

        # we know this operation may take a while so we arbitrary increase the
        # read timeout
        timeout = None
        if top == "*":
            timeout = max(self.timeout, 300)

        query = await self._async_status(
            "c:{0}:b:{1}:p:{2}\n".format(name, backup, top), timeout
        )
        return self._format_tree(query, top, level)

    async def _async_get_client(self, name=None, agent=None):
        return await self._async_get_client_filtered(name)

    async def _async_get_client_labels(self, client=None, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_client_labels`
        """
        ret = []
        if not client:
            return ret
        # micro optimization since the status results are cached in memory for a
        # couple seconds, using the same global query and iterating over it
        # will be more efficient than filtering burp-side
        query = await self._async_status("c:\n")
        if not query:
            return ret
        try:
            for cli in query["clients"]:
                if cli["name"] == client:
                    return cli["labels"]
        except KeyError:
            return ret

    async def _async_restore_files(
        self,
        name=None,
        backup=None,
        files=None,
        strip=None,
        archive="zip",
        password=None,
        agent=None,
    ):
        return await trio.to_thread.run_sync(
            Burp2.restore_files,
            self,
            name,
            backup,
            files,
            strip,
            archive,
            password,
            agent,
        )

    async def _async_is_backup_deletable(self, name=None, backup=None, agent=None):
        if not name or not backup:
            return False
        query = await self._async_status("c:{0}:b:{1}\n".format(name, backup))
        if not query:
            return False
        return self._do_is_backup_deletable(query)


# Some functions are the same as in Burp1 backend
class Burp(Burp2, AsyncBurpMixin):
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

    _ready = False
    parser = None

    def __init__(self, server=None, conf=None):
        """
        :param server: ``Burp-UI`` server instance in order to access logger
                       and/or some global settings
        :type server: :class:`burpui.engines.server.BUIServer`

        :param conf: Configuration to use
        :type conf: :class:`burpui.config.BUIConfig`
        """

        BUIbackend.__init__(self, server, conf)

        self.conf = conf
        self.concurrency = conf.safe_get(
            "concurrency", "integer", "Parallel", BUI_DEFAULTS
        )
        self.init_wait = conf.safe_get("init_wait", "integer", "Parallel", BUI_DEFAULTS)

        if os.getenv("BUI_MODE", "") == "celery":
            # we cap the concurrency level in order not to prevent our main server
            # to talk to the monitor
            self.concurrency = max(1, self.concurrency // 2)

        self.logger.info("burp conf cli: {}".format(self.burpconfcli))
        self.logger.info("burp conf srv: {}".format(self.burpconfsrv))
        self.logger.info("command timeout: {}".format(self.timeout))
        self.logger.info("tmpdir: {}".format(self.tmpdir))
        self.logger.info("zip64: {}".format(self.zip64))
        self.logger.info("includes: {}".format(self.includes))
        self.logger.info("enforce: {}".format(self.enforce))
        self.logger.info("revoke: {}".format(self.revoke))
        self.logger.info("concurrency: {}".format(self.concurrency))
        self.logger.info("init_wait: {}".format(self.init_wait))

        if self.init_wait:
            exc = None
            for i in range(self.init_wait):
                connector = Connector(conf)
                try:
                    self.logger.warning(
                        "monitor not ready, waiting for it... {}/{}".format(
                            i, self.init_wait
                        )
                    )
                    trio.run(connector.conn)
                    if connector.connected:
                        trio.run(connector._send, "RE")
                        break
                except BUIserverException as eee:
                    exc = eee
                time.sleep(1)
            else:
                self.logger.error(f"monitor not ready, giving up!: {exc}")

        try:
            stats = self.statistics()
            if "alive" in stats and stats["alive"]:
                self.init_all()
        except BUIserverException:
            pass

    def init_all(self):
        self._ready = True
        self.parser = Parser(self)

    @property
    def client_version(self):
        return self.get_client_version()

    @property
    def server_version(self):
        return self.get_server_version()

    @property
    def batch_list_supported(self):
        if self._batch_list_supported is None:
            self._batch_list_supported = json.loads(
                trio.run(self._async_request, "batch_list_supported")
            )
        return self._batch_list_supported

    @usetriorun
    def statistics(self, agent=None):
        return trio.run(self._async_statistics)

    @usetriorun
    def get_client_version(self, agent=None):
        if self._client_version is None:
            self._client_version = trio.run(self._async_get_client_version)
        return self._client_version or ""

    @usetriorun
    def get_server_version(self, agent=None):
        if self._server_version is None:
            self._server_version = trio.run(self._async_get_server_version)
        return self._server_version or ""

    @usetriorun
    def status(self, query="c:\n", timeout=None, cache=True, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.status`"""
        return trio.run(self._async_status, query, timeout, cache)

    def get_backup_logs(self, number, client, forward=False, deep=False, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_backup_logs`
        """
        if not client or not number:
            return {} if number and number != -1 else []

        if number == -1:
            return trio.run(self._async_get_all_backup_logs, client, forward, deep)
        return trio.run(self._async_get_backup_logs, number, client, forward, deep)

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

    @usetriorun
    def get_clients_report(self, clients, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_clients_report`"""
        return trio.run(self._async_get_clients_report, clients)

    @usetriorun
    def get_counters(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_counters`"""
        return trio.run(self._async_get_counters, name)

    @usetriorun
    def is_backup_running(self, name=None, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.is_backup_running`
        """
        return trio.run(self._async_is_backup_running, name)

    @usetriorun
    def is_one_backup_running(self, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.is_one_backup_running`
        """
        return trio.run(self._async_is_one_backup_running)

    @usetriorun
    def _get_last_backup(self, name, working=True):
        """Return the last backup of a given client

        :param name: Name of the client
        :type name: str

        :param working: Also return uncomplete backups
        :type working: bool

        :returns: The last backup
        """
        return trio.run(self._async_get_last_backup, name, working)

    @usetriorun
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

    def get_all_clients(self, agent=None, last_attempt=True):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_all_clients`
        """
        # don't need async processing if burp-server < BURP_STATUS_FORMAT_V2
        if not self.deep_inspection or (
            self.server_version and self.server_version < BURP_STATUS_FORMAT_V2
        ):
            return Burp2.get_all_clients(self, last_attempt=last_attempt)
        # the deep inspection can take advantage of async processing
        callback = partial(self._async_get_all_clients, last_attempt=last_attempt)
        return trio.run(callback)

    @usetriorun
    def get_client_status(self, name=None, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_client_status`
        """
        return trio.run(self._async_get_client_status, name)

    @usetriorun
    def get_client(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client`"""
        return trio.run(self._async_get_client, name)

    @usetriorun
    def get_client_filtered(
        self, name=None, limit=-1, page=None, start=None, end=None, agent=None
    ):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_filtered`"""
        return trio.run(self._async_get_client_filtered, name, limit, page, start, end)

    @usetriorun
    def is_backup_deletable(self, name=None, backup=None, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.is_backup_deletable`
        """
        return trio.run(self._async_is_backup_deletable, name, backup)

    @usetriorun
    def get_tree(self, name=None, backup=None, root=None, level=-1, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_tree`"""
        return trio.run(self._async_get_tree, name, backup, root, level)

    @usetriorun
    def get_client_labels(self, client=None, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_client_labels`
        """
        return trio.run(self._async_get_client_labels, client)

    @usetriorun
    def restore_files(
        self,
        name=None,
        backup=None,
        files=None,
        strip=None,
        archive="zip",
        password=None,
        agent=None,
    ):
        return trio.run(
            self._async_restore_files,
            name,
            backup,
            files,
            strip,
            archive,
            password,
            agent,
        )

    # Same as in Burp1 backend

    # def read_conf_cli(self, agent=None):

    # def read_conf_srv(self, agent=None):

    # def store_conf_cli(self, data, agent=None):

    # def store_conf_srv(self, data, agent=None):

    # def get_parser_attr(self, attr=None, agent=None):


# Make every "Burp" method async
class AsyncBurp(Burp):
    @property
    async def batch_list_supported(self):
        if self._batch_list_supported is None:
            self._batch_list_supported = json.loads(
                await self._async_request("batch_list_supported")
            )
        return self._batch_list_supported

    # this method must not be async!
    @implement
    def statistics(self, agent=None):
        return Burp.statistics(self)

    # this method must not be async!
    @implement
    def get_parser(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_parser`"""
        return Burp.get_parser(self)

    @property
    def client_version(self):
        return trio.run(self.get_client_version)

    @property
    def server_version(self):
        return trio.run(self.get_server_version)

    @implement
    async def get_client_version(self, agent=None):
        if self._client_version is None:
            self._client_version = await self._async_request("client_version")
        return self._client_version

    @implement
    async def get_server_version(self, agent=None):
        if self._server_version is None:
            self._server_version = await self._async_request("server_version")
        return self._server_version

    @implement
    async def get_backup_logs(
        self, number, client, forward=False, deep=False, agent=None
    ):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_backup_logs`
        """
        if not client or not number:
            return {} if number and number != -1 else []

        if number == -1:
            return await self._async_get_all_backup_logs(client, forward, deep)
        return await self._async_get_backup_logs(number, client, forward, deep)

    @implement
    async def get_all_clients(self, agent=None, last_attempt=True):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_all_clients`
        """
        return await self._async_get_all_clients(last_attempt=last_attempt)

    @implement
    async def get_attr(self, name, default=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_attr`"""
        try:
            try:
                return await getattr(self, name, default)
            except TypeError:
                return getattr(self, name, default)
        except AttributeError:
            return default

    def __getattribute__(self, name):
        if name in BUIBACKEND_INTERFACE_METHODS or name in ["_guess_os"]:
            wrap = False
            proxy = True
            func = None
            try:
                func = object.__getattribute__(self, name)
                proxy = not getattr(func, "__ismethodimplemented__", False)
                wrap = getattr(func, "__isusingtriorun__", False)
            except:
                pass
            if func and not callable(func):
                self.logger.debug(f"{func} is not a function")
                return func
            self.logger.debug(f"async func: {func} - proxy: {proxy}, wrap: {wrap}")
            if wrap:
                realname = (
                    f"_async_{name}" if not name.startswith("_") else f"_async{name}"
                )
                realfunc = object.__getattribute__(self, realname)
                return ProxyAsyncCall(realfunc, realname, self)
            if proxy:
                return ProxyAsyncCall(func, name, self)
            elif func:
                return func
        return object.__getattribute__(self, name)


class ProxyAsyncCall(object):
    """Class to dispatch call of unknown methods in order to dynamically
    implements their async variant."""

    def __init__(self, func, name, proxy):
        """
        :param proxy: function to proxify
        :type proxy: function

        :param name: Name of the method to proxify
        :type name: str

        :param proxy: Object to proxify
        :type proxy: :class:`Burp`
        """
        self.func = func
        self.name = name
        self.proxy = proxy

    async def __call__(self, *args, **kwargs):
        """This is where the proxy call (and the magic) occurs"""
        # retrieve the original function prototype
        proto = getattr(BUIbackend, self.name, None) or getattr(self.proxy, self.name)
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

        if iscoroutinefunction(self.func):
            return await self.func(**encoded_args)
        return self.func(**encoded_args)
