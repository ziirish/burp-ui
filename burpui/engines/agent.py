# -*- coding: utf8 -*-
"""
.. module:: burpui.engines.agent
    :platform: Unix
    :synopsis: Burp-UI agent module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import json
import logging
import os
import ssl
import struct
import sys
import time
from functools import partial

import trio

from .._compat import pickle, to_bytes, to_unicode
from ..config import config
from ..desc import __version__
from ..exceptions import BUIserverException
from ..misc.backend.interface import BUIbackend

# TODO: sendfile is not yet supported by trio
# try:
#     from sendfile import sendfile
#     USE_SENDFILE = True
# except ImportError:
#     USE_SENDFILE = False


BUI_DEFAULTS = {
    "Global": {
        "port": 10000,
        "bind": "::",
        "ssl": False,
        "sslcert": "",
        "sslkey": "",
        "backend": "burp2",
        "password": "azerty",
        "init_wait": 15,
    },
}


class BurpHandler(BUIbackend):
    # These functions MUST be implemented because we inherit an abstract class.
    # The hack here is to get the list of the functions and let the interpreter
    # think we don't have to implement them.
    # Thanks to this list, we know what function are implemented by our backend.
    foreign = BUIbackend.__abstractmethods__
    BUIbackend.__abstractmethods__ = frozenset()

    def __init__(self, backend="burp2", logger=None, conf=None, init_wait=0):
        self.backend_name = backend
        self.is_async = backend == "parallel"
        self.logger = logger
        wait = init_wait

        top = __name__
        if "." in self.backend_name:
            module = self.backend_name
        else:
            if "." in top:
                top = top.split(".")[0]
            module = "{0}.misc.backend.{1}".format(top, self.backend_name)
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            mod = __import__(module, fromlist=["Burp"])
            if self.is_async:
                Client = mod.AsyncBurp
            else:
                Client = mod.Burp
            self.backend = Client(conf=conf)

            def __backend_alive():
                stats = self.backend.statistics()
                return "alive" in stats and stats["alive"]

            alive = __backend_alive()
            while not alive and wait > 0:
                self.logger.debug(
                    "Waiting for the backend to become alive... {}/{}".format(
                        init_wait - wait, init_wait
                    )
                )
                time.sleep(1)
                alive = __backend_alive()
                wait -= 1
            if not alive:
                raise BUIserverException("Cannot talk to burp server")
        except Exception as exc:
            self.logger.error(
                "Failed loading backend {}: {}".format(self.backend_name, str(exc)),
                exc_info=exc,
                stack_info=True,
            )
            sys.exit(2)

    def __getattribute__(self, name):
        # always return this value because we need it and if we don't do that
        # we'll end up with an infinite loop
        if name in ["foreign", "backend", "logger", "is_async"]:
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

    def __init__(self, conf=None, level=0, logfile=None):
        self.padding = 1
        level = level or 0
        self.logger.init_logger(config=dict(level=level, logfile=logfile))
        lvl = self.logger.getEffectiveLevel()
        self.logger.info("conf: {}".format(conf))
        self.logger.info("level: {}".format(logging.getLevelName(lvl)))
        if not conf:
            raise IOError("No configuration file found")

        # Raise exception if errors are encountered during parsing
        self.conf = config
        self.conf.parse(conf, BUI_DEFAULTS)
        self.conf.default_section("Global")
        self.port = self.conf.safe_get("port", "integer")
        self.bind = self.conf.safe_get("bind")
        self.backend = self.conf.safe_get("backend")
        self.ssl = self.conf.safe_get("ssl", "boolean")
        self.sslcert = self.conf.safe_get("sslcert")
        self.sslkey = self.conf.safe_get("sslkey")
        self.password = self.conf.safe_get("password")
        self.init_wait = self.conf.safe_get("init_wait", "integer")
        self.conf.setdefault("BUI_AGENT", True)

        self.client = BurpHandler(self.backend, self.logger, self.conf, self.init_wait)

    def _ssl_context(self):
        if not self.ssl:
            return None
        ctx = ssl.SSLContext()
        ctx.load_cert_chain(self.sslcert, self.sslkey)
        return ctx

    async def run(self):
        try:
            self.logger.debug(f"Starting server on {self.bind}:{self.port}")
            ctx = self._ssl_context()
            if ctx:
                await trio.serve_ssl_over_tcp(
                    self.handle, self.port, ctx, host=self.bind
                )
            else:
                await trio.serve_tcp(self.handle, self.port, host=self.bind)
        except KeyboardInterrupt:
            self.logger.debug("Stopping server")
            sys.exit(0)

    async def handle(self, server_stream: trio.StapledStream):
        """self.request is the client connection"""
        self.logger.debug("handle request")
        try:
            err = None
            res = ""
            lengthbuf = await server_stream.receive_some(8)
            if not lengthbuf:
                return
            (length,) = struct.unpack("!Q", lengthbuf)
            data = await self.receive_all(server_stream, length)
            self.logger.info(f"recv: {data!r}")
            txt = to_unicode(data)
            if txt == "RE":
                return
            j = json.loads(txt)
            if j["password"] != self.password:
                self.logger.warning("-----> Wrong Password <-----")
                await server_stream.send_all(b"KO")
                return
            try:
                if j["func"] == "proxy_parser":
                    parser = self.client.get_parser()
                    if j["args"]:
                        wrap = partial(getattr(parser, j["method"]), **j["args"])
                    else:
                        wrap = getattr(parser, j["method"])
                    temp = await trio.to_thread.run_sync(wrap)
                    res = json.dumps(temp)
                elif j["func"] == "agent_version":
                    res = json.dumps(__version__)
                elif j["func"] == "restore_files":
                    wrap = partial(getattr(self.client, j["func"]), **j["args"])
                    if self.client.is_async:
                        res, err = await wrap()
                    else:
                        res, err = await trio.to_thread.run_sync(wrap)
                    if err:
                        await server_stream.send_all(b"ER")
                        await server_stream.send_all(struct.pack("!Q", len(err)))
                        await server_stream.send_all(to_bytes(err))
                        self.logger.error("Restoration failed")
                        return
                elif j["func"] == "get_file":
                    path = j["path"]
                    path = os.path.normpath(path)
                    err = None
                    if not path.startswith("/"):
                        err = f"The path must be absolute! ({path})"
                    if not path.startswith(self.client.tmpdir):
                        err = f"You are not allowed to access this path: " f"({path})"
                    if err:
                        await server_stream.send_all(b"ER")
                        await server_stream.send_all(struct.pack("!Q", len(err)))
                        await server_stream.send_all(to_bytes(err))
                        self.logger.error(err)
                        return
                    count = 0
                    size = os.path.getsize(path)
                    await server_stream.send_all(b"OK")
                    await server_stream.send_all(struct.pack("!Q", size))
                    async with await trio.open_file(path, "rb") as f:
                        while True:
                            buf = await f.read(1024)
                            if not buf:
                                break
                            buflen = len(buf)
                            count += buflen
                            percent = count / size * 100
                            self.logger.info(f"sending {buflen} Bytes - {percent:.1f}%")
                            await server_stream.send_all(buf)
                    os.unlink(path)
                    lengthbuf = await server_stream.receive_some(8)
                    (length,) = struct.unpack("!Q", lengthbuf)
                    data = await self.receive_all(server_stream, length)
                    txt = to_unicode(data)
                    if txt == "RE":
                        return
                elif j["func"] == "del_file":
                    path = j["path"]
                    path = os.path.normpath(path)
                    err = None
                    if not path.startswith("/"):
                        err = f"The path must be absolute! ({path})"
                    if not path.startswith(self.client.tmpdir):
                        err = f"You are not allowed to access this path: " f"({path})"
                    if err:
                        berr = to_bytes(err)
                        await server_stream.send_all(b"ER")
                        await server_stream.send_all(struct.pack("!Q", len(berr)))
                        await server_stream.send_all(berr)
                        self.logger.error(err)
                        return
                    res = json.dumps(False)
                    if os.path.isfile(path):
                        os.unlink(path)
                        res = json.dumps(True)
                else:
                    callback = getattr(self.client, j["func"])
                    if j["args"]:
                        if "pickled" in j and j["pickled"]:
                            # de-serialize arguments if needed
                            import hashlib
                            import hmac
                            from base64 import b64decode

                            pickles = to_bytes(j["args"])
                            key = "{}{}".format(self.password, j["func"])
                            key = to_bytes(key)
                            bytes_pickles = pickles
                            digest = hmac.new(
                                key, bytes_pickles, hashlib.sha1
                            ).hexdigest()
                            if not hmac.compare_digest(digest, j["digest"]):
                                raise BUIserverException(
                                    "Integrity check failed: {} != {}".format(
                                        digest, j["digest"]
                                    )
                                )
                            # We need to replace the burpui datastructure
                            # module by our own since it's the same but
                            # burpui may not be installed
                            mod = __name__
                            if "." in mod:
                                mod = mod.split(".")[0]
                            data = b64decode(pickles)
                            data = data.replace(
                                b"burpui.datastructures",
                                to_bytes(f"{mod}.datastructures"),
                            )
                            j["args"] = pickle.loads(data)

                        wrap = partial(callback, **j["args"])
                        if self.client.is_async:
                            res = json.dumps(await wrap())
                        else:
                            res = json.dumps(await trio.to_thread.run_sync(wrap))
                    else:
                        if self.client.is_async:
                            res = json.dumps(await callback())
                        else:
                            res = json.dumps(await trio.to_thread.run_sync(callback))
                self.logger.info(f"result: {res}")
                await server_stream.send_all(b"OK")
            except (BUIserverException, Exception) as exc:
                await server_stream.send_all(b"ER")
                res = str(exc)
                self.logger.error(res, exc_info=exc)
                self.logger.warning(f"Forwarding Exception: {res}")

            res = to_bytes(res)
            await server_stream.send_all(struct.pack("!Q", len(res)))
            await server_stream.send_all(res)
        except AttributeError as exc:
            self.logger.warning(f"Wrong method => {exc}", exc_info=exc)
            await server_stream.send_all(b"KO")
        except Exception as exc:
            self.logger.error(f"!!! {exc} !!!", exc_info=exc)

    async def receive_all(self, stream: trio.StapledStream, length=1024, bsize=None):
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
                    raise Exception("Unable to read full response")
                tries += 1
                await trio.sleep(0.1)
                continue
            # reset counter
            tries = 0
            buf += newbuf
            received += len(newbuf)
        return buf
