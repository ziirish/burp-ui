# -*- coding: utf8 -*-
"""
.. module:: burpui.engines.monitor
    :platform: Unix
    :synopsis: Burp-UI monitor pool module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import datetime
import json
import logging
import math
import ssl
import struct
from functools import partial
from itertools import count

import trio
from async_generator import asynccontextmanager

from .._compat import to_bytes, to_unicode
from ..config import config
from ..desc import __version__
from ..exceptions import BUIserverException
from ..misc.backend.utils.burp2 import Monitor
from ..tools.logging import logger

CONNECTION_COUNTER = count()


BUI_DEFAULTS = {
    "Global": {
        "port": 11111,
        "bind": "::1",
        "ssl": False,
        "sslcert": "",
        "sslkey": "",
        "password": "password123456",
        "pool": 5,
    },
}


class Pool:
    def __init__(self, pool_size):
        self._size = pool_size
        self.send_channel, self.receive_channel = trio.open_memory_channel(pool_size)

    @property
    def size(self):
        return self._size

    @property
    def stats(self):
        return self.send_channel.statistics()

    async def put(self, data):
        await self.send_channel.send(data)

    async def get(self):
        return await self.receive_channel.receive()

    def empty(self):
        stats = self.stats
        if self.size != 0 and stats.current_buffer_used == 0:
            return True
        return False

    def full(self):
        stats = self.stats
        max_buffer = self.size
        if max_buffer > 0 and max_buffer != math.inf:
            return stats.current_buffer_used == max_buffer
        return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.send_channel.aclose()
        await self.receive_channel.aclose()


class MonitorPool:
    logger = logger

    # cache status results
    _status_cache = {}
    _last_status_cleanup = datetime.datetime.now()
    _time_to_cache = datetime.timedelta(seconds=5)

    def __init__(self, conf=None, level=0, logfile=None):
        level = level or 0
        self.logger.init_logger(config=dict(level=level, logfile=logfile))
        lvl = logging.getLevelName(self.logger.getEffectiveLevel())
        self.logger.info(f"conf: {conf}")
        self.logger.info(f"level: {lvl}")
        if not conf:
            raise IOError("No configuration file found")

        # Raise exception if errors are encountered during parsing
        self.conf = config
        self.conf.parse(conf, BUI_DEFAULTS)
        self.conf.default_section("Global")
        self.port = self.conf.safe_get("port", "integer")
        self.bind = self.conf.safe_get("bind")
        self.ssl = self.conf.safe_get("ssl", "boolean")
        self.sslcert = self.conf.safe_get("sslcert")
        self.sslkey = self.conf.safe_get("sslkey")
        self.password = self.conf.safe_get("password")
        self.pool_size = self.conf.safe_get("pool", "integer")

        self.burpbin = self.conf.safe_get("burpbin", section="Burp")
        self.bconfcli = self.conf.safe_get("bconfcli", section="Burp")
        self.timeout = self.conf.safe_get(
            "timeout", "integer", section="Burp", defaults=15
        )

        self.conf.setdefault("BUI_MONITOR", True)

        self.pool = Pool(self.pool_size)

    def _ssl_context(self):
        if not self.ssl:
            return None
        ctx = ssl.SSLContext()
        ctx.load_cert_chain(self.sslcert, self.sslkey)
        return ctx

    def _cleanup_cache(self):
        now = datetime.datetime.now()
        if now - self._last_status_cleanup > self._time_to_cache:
            self._status_cache.clear()
            self._last_status_cleanup = now

    async def receive_all(self, stream: trio.abc.Stream, length=1024, bsize=None):
        buf = b""
        bsize = bsize if bsize is not None else 1024
        bsize = min(bsize, length)
        received = 0
        tries = 0
        while received < length:
            newbuf = await stream.receive_some(bsize)
            if not newbuf:
                # 3 successive read failure => raise exception
                if tries > 3:
                    raise IOError("Unable to read full response")
                tries += 1
                await trio.sleep(0.1)
                continue
            # reset counter
            tries = 0
            buf += newbuf
            received += len(newbuf)
        return buf

    @asynccontextmanager
    async def get_mon(self, ident) -> Monitor:
        self.logger.info(f"{ident} - Waiting for a monitor...")
        t1 = trio.current_time()
        mon = await self.pool.get()  # type: Monitor
        t2 = trio.current_time()
        t = t2 - t1
        self.logger.info(f"{ident} - Waited {t:.3f}s")
        yield mon
        self.logger.info(f"{ident} - Releasing monitor")
        await self.pool.put(mon)

    async def handle(self, server_stream: trio.abc.Stream):
        try:
            ident = next(CONNECTION_COUNTER)
            self.logger.info(f"{ident} - handle_request: started")
            t0 = trio.current_time()
            lengthbuf = await server_stream.receive_some(8)
            if not lengthbuf:
                return
            (length,) = struct.unpack("!Q", lengthbuf)
            data = await self.receive_all(server_stream, length)
            self.logger.info(f"{ident} - recv: {data!r}")
            txt = to_unicode(data)
            if txt == "RE":
                return
            req = json.loads(txt)
            if req["password"] != self.password:
                self.logger.warning(f"{ident} -----> Wrong Password <-----")
                await server_stream.send_all(b"KO")
                return
            try:
                func = req.get("func")
                if func == "monitor_version":
                    response = __version__
                elif func in [
                    "client_version",
                    "server_version",
                    "batch_list_supported",
                ]:
                    async with self.get_mon(ident) as mon:
                        response = getattr(mon, func, "")
                        if func in ["batch_list_supported"]:
                            response = json.dumps(response)
                elif func == "statistics":
                    tmp = []
                    res = {
                        "alive": False,
                        "server_version": "unknown",
                        "client_version": "unknown",
                    }
                    while not res["alive"] and len(tmp) < self.pool.size:
                        mon = await self.pool.get()
                        tmp.append(mon)
                        if mon.alive:
                            res = {
                                "alive": True,
                                "server_version": getattr(mon, "server_version", ""),
                                "client_version": getattr(mon, "client_version", ""),
                            }
                            break
                        await trio.sleep(0.5)
                    for mon in tmp:
                        await self.pool.put(mon)
                    response = json.dumps(res)
                else:
                    query = req["query"]
                    cache = req.get("cache", True)

                    self._cleanup_cache()
                    # return cached results
                    if cache and query in self._status_cache:
                        response = self._status_cache[query]
                    else:
                        async with self.get_mon(ident) as mon:
                            wrap = partial(
                                mon.status,
                                query,
                                timeout=self.timeout,
                                cache=False,
                                raw=True,
                            )
                            response = await trio.to_thread.run_sync(wrap)

                        if cache:
                            self._status_cache[query] = response
                self.logger.debug(f"{ident} - Sending: {response}")
                if response:
                    await server_stream.send_all(b"OK")
                else:
                    await server_stream.send_all(b"KO")
            except BUIserverException as exc:
                await server_stream.send_all(b"ER")
                response = str(exc)
                self.logger.error(response, exc_info=exc)
                self.logger.warning(f"Forwarding Exception: {response}")

            if response:
                response = to_bytes(response)
                await server_stream.send_all(struct.pack("!Q", len(response)))
                await server_stream.send_all(response)

            t3 = trio.current_time()
            t = t3 - t0
            self.logger.info(f"{ident} - Completed in {t:.3f}s")
        except Exception as exc:
            self.logger.error(f"Unexpected error: {exc}")
            response = str(exc)
            self.logger.error(response, exc_info=exc)
            try:
                await server_stream.send_all(b"ER")
                self.logger.warning(f"Forwarding Exception: {response}")

                response = to_bytes(response)
                await server_stream.send_all(struct.pack("!Q", len(response)))
                await server_stream.send_all(response)
            except trio.BrokenResourceError:
                # Broken Pipe, we cannot forward the error
                pass

    async def launch_monitor(self, id):
        self.logger.info(f"Starting client n°{id}")
        try:
            if self.pool.full():
                self.logger.warning("pool full!")
                return
            mon = Monitor(self.burpbin, self.bconfcli, timeout=self.timeout, ident=id)
            # warm up monitor
            await trio.to_thread.run_sync(mon.status)
            await self.pool.put(mon)
        except (BUIserverException, OSError):
            pass

    async def cleanup_monitor(self):
        while not self.monitor_pool.empty():
            self.logger.info("killing proc")
            mon = await self.monitor_pool.get()  # noqa
            del mon

    async def fill_pool(self):
        self.logger.info("Starting clients...")
        async with trio.open_nursery() as nursery:
            for i in range(self.pool_size):
                nursery.start_soon(self.launch_monitor, i + 1)

    async def _run(self):
        self.logger.info(f"Ready to serve requests on {self.bind}:{self.port}")
        ctx = self._ssl_context()
        if ctx:
            await trio.serve_ssl_over_tcp(self.handle, self.port, ctx, host=self.bind)
        else:
            await trio.serve_tcp(self.handle, self.port, host=self.bind)

    async def run(self):
        async with self.pool:
            try:
                async with trio.open_nursery() as nursery:
                    # listen to connections as soon as possible
                    nursery.start_soon(self._run)
                    # in parallel we start to populate the pool
                    nursery.start_soon(self.fill_pool)
            except KeyboardInterrupt:
                pass
