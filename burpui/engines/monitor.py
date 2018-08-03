# -*- coding: utf8 -*-
"""
.. module:: burpui.engines.monitor
    :platform: Unix
    :synopsis: Burp-UI monitor pool module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import ssl
import trio
import json
import struct
import logging
import datetime

from itertools import count
from async_generator import asynccontextmanager
from logging.handlers import RotatingFileHandler

from ..exceptions import BUIserverException
from ..misc.backend.burp.utils import Monitor
from ..config import config
from .._compat import to_bytes, to_unicode
from ..desc import __version__


CONNECTION_COUNTER = count()


BUI_DEFAULTS = {
    'Global': {
        'port': 11111,
        'bind': '::1',
        'ssl': False,
        'sslcert': '',
        'sslkey': '',
        'password': 'password123456',
        'pool': 5,
    },
}


class MonitorPool:
    logger = logging.getLogger('burp-ui')  # type: logging.Logger

    # cache status results
    _status_cache = {}
    _last_status_cleanup = datetime.datetime.now()
    _time_to_cache = datetime.timedelta(seconds=5)

    def __init__(self, conf=None, level=0, logfile=None, debug=False):
        self.debug = debug
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
            self.logger.info(f'conf: {conf}')
            self.logger.info('level: {}'.format(logging.getLevelName(lvl)))
        if not conf:
            raise IOError('No configuration file found')

        # Raise exception if errors are encountered during parsing
        self.conf = config
        self.conf.parse(conf, True, BUI_DEFAULTS)
        self.conf.default_section('Global')
        self.port = self.conf.safe_get('port', 'integer')
        self.bind = self.conf.safe_get('bind')
        self.ssl = self.conf.safe_get('ssl', 'boolean')
        self.sslcert = self.conf.safe_get('sslcert')
        self.sslkey = self.conf.safe_get('sslkey')
        self.password = self.conf.safe_get('password')
        self.pool = self.conf.safe_get('pool', 'integer')

        self.burpbin = self.conf.safe_get('burpbin', section='Burp')
        self.bconfcli = self.conf.safe_get('bconfcli', section='Burp')
        self.timeout = self.conf.safe_get('timeout', 'integer', section='Burp')

        self.conf.setdefault('BUI_MONITOR', True)

        self.monitor_pool = trio.Queue(self.pool)

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

    async def receive_all(self, stream: trio.StapledStream, length=1024, bsize=None):
        buf = b''
        bsize = bsize if bsize is not None else 1024
        bsize = min(bsize, length)
        received = 0
        tries = 0
        while received < length:
            newbuf = await stream.receive_some(bsize)
            if not newbuf:
                # 3 successive read failure => raise exception
                if tries > 3:
                    raise Exception('Unable to read full response')
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
        self.logger.info(f'{ident} - Waiting for a monitor...')
        t1 = trio.current_time()
        mon = await self.monitor_pool.get()  # type: Monitor
        t2 = trio.current_time()
        t = t2 - t1
        self.logger.info(f'{ident} - Waited {t:.3f}s')
        yield mon
        self.logger.info(f'{ident} - Releasing monitor')
        await self.monitor_pool.put(mon)

    async def handle(self, server_stream: trio.StapledStream):
        try:
            ident = next(CONNECTION_COUNTER)
            self.logger.info(f'{ident} - handle_request: started')
            t0 = trio.current_time()
            lengthbuf = await server_stream.receive_some(8)
            if not lengthbuf:
                return
            length, = struct.unpack('!Q', lengthbuf)
            data = await self.receive_all(server_stream, length)
            self.logger.info(f'{ident} - recv: {data!r}')
            txt = to_unicode(data)
            if txt == 'RE':
                return
            req = json.loads(txt)
            if req['password'] != self.password:
                self.logger.warning(f'{ident} -----> Wrong Password <-----')
                await server_stream.send_all(b'KO')
                return
            try:
                func = req.get('func')
                if func == 'monitor_version':
                    response = __version__
                elif func in ['client_version', 'server_version', 'batch_list_supported']:
                    async with self.get_mon(ident) as mon:
                        response = getattr(mon, func, '')
                        if func in ['batch_list_supported']:
                            response = json.dumps(response)
                else:
                    query = req['query']
                    cache = req.get('cache', True)

                    self._cleanup_cache()
                    # return cached results
                    if cache and query in self._status_cache:
                        response = self._status_cache[query]
                    else:
                        async with self.get_mon(ident) as mon:
                            response = mon.status(query, timeout=self.timeout, cache=False, raw=True)

                        if cache:
                            self._status_cache[query] = response
                self.logger.debug(f'{ident} - Sending: {response}')
                await server_stream.send_all(b'OK')
            except BUIserverException as exc:
                await server_stream.send_all(b'ER')
                response = str(exc)
                self.logger.error(response, exc_info=exc)
                self.logger.warning(f'Forwarding Exception: {response}')

            await server_stream.send_all(struct.pack('!Q', len(response)))
            await server_stream.send_all(to_bytes(response))

            t3 = trio.current_time()
            t = t3 - t0
            self.logger.info(f'{ident} - Completed in {t:.3f}s')
        except Exception as exc:
            self.logger.error(f'Unexpected error: {exc}')

    async def launch_monitor(self, id):
        self.logger.info(f'Starting client n°{id}')
        mon = Monitor(self.burpbin, self.bconfcli, timeout=self.timeout, ident=id)
        # warm up monitor
        mon.status()
        await self.monitor_pool.put(mon)

    async def cleanup_monitor(self):
        while not self.monitor_pool.empty():
            self.logger.info('killing proc')
            mon = await self.monitor_pool.get()  # noqa
            del mon

    async def run(self):
        self.logger.info('Starting clients...')
        async with trio.open_nursery() as nursery:
            for i in range(self.pool):
                nursery.start_soon(self.launch_monitor, i + 1)
        self.logger.info(f'Ready to serve requests on {self.bind}:{self.port}')
        try:
            ctx = self._ssl_context()
            if ctx:
                await trio.serve_ssl_over_tcp(self.handle, self.port, ctx, host=self.bind)
            else:
                await trio.serve_tcp(self.handle, self.port, host=self.bind)
        except KeyboardInterrupt:
            pass

        self.logger.info('Cleaning up')
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self.cleanup_monitor)
