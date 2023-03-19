# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.backend.utils.burp2
    :platform: Unix
    :synopsis: Burp-UI burp utils module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import datetime
import json
import re
import subprocess
from select import select

from ...._compat import to_bytes, to_unicode
from ....exceptions import BUIserverException
from ....security import sanitize_string
from ....tools.logging import logger
from .constant import (
    BURP_LIST_BATCH,
    BURP_MINIMAL_VERSION,
    BURP_STATUS_DELIMITER,
    BURP_STATUS_FORMAT_V2,
)


class Monitor(object):
    """The :class:`burpui.misc.backend.utils.burp2.Monitor` class provides a ``burp-2``
    Monitor object to interact with the server.

    :param app: ``Burp-UI`` server instance in order to access logger
                   and/or some global settings
    :type app: :class:`burpui.engines.server.BUIServer`

    :param burpbin: Burp binary path
    :type burpbin: str

    :param burpconf: Burp configuration path
    :type burpconf: str

    :param timeout: Time to wait for an answer
    :type timeout: int
    """

    logger = logger

    # cache status results
    _status_cache = {}
    _last_status_cleanup = datetime.datetime.now()
    _time_to_cache = datetime.timedelta(seconds=3)

    _ignore_logs = re.compile(r"^Server version: (\d+\.\d+\.\d+).*$")

    def __init__(self, burpbin, burpconf, app=None, timeout=5, ident=None):
        """
        :param app: ``Burp-UI`` server instance in order to access logger
                       and/or some global settings
        :type app: :class:`burpui.engines.server.BUIServer`

        :param burpbin: Burp binary path
        :type burpbin: str

        :param burpconf: Burp configuration path
        :type burpconf: str

        :param timeout: Time to wait for an answer
        :type timeout: int
        """
        self.burpbin = burpbin
        self.burpconf = burpconf
        self.timeout = timeout
        self.app = app
        self.proc = None
        self._client_version = None
        self._server_version = None
        self.batch_list_supported = False
        self.status_delimiter = False
        self.ident = ident or id(self)

        self._burp_client_ok = False
        version = ""
        # check the burp version because this backend only supports clients
        # newer than BURP_MINIMAL_VERSION
        try:
            if self.burpbin:
                # the '--version' flag changed in burp 2.2.12
                cmd = [self.burpbin, "-V"]
                version = None
                try:
                    version = to_unicode(
                        subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                    ).rstrip()
                except subprocess.CalledProcessError:
                    pass
                if version is None:
                    cmd = [self.burpbin, "-v"]
                    version = to_unicode(
                        subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                    ).rstrip()
                if version < BURP_MINIMAL_VERSION and getattr(self.app, "strict", True):
                    self.logger.critical(
                        f"Your burp version ({version}) does not fit the minimal"
                        f" requirements: {BURP_MINIMAL_VERSION}"
                    )
                elif version >= BURP_MINIMAL_VERSION:
                    self._burp_client_ok = True
        except subprocess.CalledProcessError as exp:
            if getattr(self.app, "strict", True):
                self.logger.critical(f"Unable to determine your burp version: {exp}")

        self._client_version = version.replace("burp-", "")

        if self.app and not self.app.config["BUI_CLI"]:
            try:
                # make the connection
                self._spawn_burp(True)
                self.status()
            except BUIserverException:
                pass
            except OSError as exp:
                msg = str(exp)
                self.logger.critical(msg)

    @property
    def client_version(self):
        return self._client_version or ""

    @property
    def server_version(self):
        if self._server_version is None:
            try:
                self.status()
            except BUIserverException:
                return ""
        return self._server_version or ""

    @property
    def alive(self):
        # clients may be idle for some time, in that case we may need to start them again
        if not self._proc_is_alive():
            try:
                self._spawn_burp()
            except OSError:
                pass
        return self._proc_is_alive()

    def _exit(self):
        """try not to leave child process server side"""
        self.logger.debug(f"Exiting {self.ident}")
        self._terminate_burp()
        self._kill_burp()

    def __exit__(self, typ, value, traceback):
        self._exit()

    def __del__(self):
        self._exit()

    def _kill_burp(self):
        """Terminate the process"""
        if self._proc_is_alive():
            try:
                self.proc.terminate()
            except Exception:
                pass
        if self._proc_is_alive():
            try:
                self.proc.kill()
            except Exception:
                pass

    def _terminate_burp(self):
        """Terminate cleanly the process"""
        if self._proc_is_alive():
            self.proc.stdin.close()
            self.proc.wait()
            self.proc = None

    def _spawn_burp(self, verbose=False):
        """Launch the burp client process"""
        if not self._burp_client_ok:
            raise BUIserverException("No suitable burp client found")
        cmd = [self.burpbin, "-c", self.burpconf, "-a", "m"]
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            bufsize=0,
        )
        if not self._proc_is_alive():
            details = ""
            if verbose:
                details = ":\n"
                out, _ = self.proc.communicate()
                details += to_unicode(out)
            raise OSError(f"Unable to spawn burp process{details}")
        _, write, _ = select([], [self.proc.stdin], [], self.timeout)
        if self.proc.stdin not in write:
            self._kill_burp()
            raise OSError("Unable to setup burp client")
        self.proc.stdin.write(to_bytes("j:pretty-print-off\n"))
        self._read_proc_stdout(self.timeout)
        # try to switch to new JSON status
        if self.client_version < BURP_STATUS_FORMAT_V2:
            self.proc.stdin.write(to_bytes("j:peer_version=2.1.10\n"))
            self._read_proc_stdout(self.timeout)
        if self.status_delimiter:
            self.proc.stdin.write(to_bytes("j:response-markers-on\n"))
            self._read_proc_stdout(self.timeout, "j:response-markers-on")

    def _proc_is_alive(self):
        """Check if the burp client process is still alive"""
        if self.proc:
            return self.proc.poll() is None
        return False

    def _is_ignored(self, jso, watching=None):
        """We ignore the 'logline' lines"""
        if not jso:
            return True
        if not self._server_version:
            if "logline" in jso:
                ret = self._ignore_logs.search(jso["logline"])
                if ret:
                    self._server_version = ret.group(1)
                    if self.server_version >= BURP_LIST_BATCH:
                        self.batch_list_supported = True
                    if self.server_version >= BURP_STATUS_DELIMITER:
                        self.status_delimiter = True
        if (
            self.status_delimiter
            and watching is None
            and ("response-start" in jso or "response-end" in jso)
        ):
            return True
        return "logline" in jso

    @staticmethod
    def _is_warning(jso):
        """Returns True if the document is a warning"""
        if not jso:
            return False
        return "warning" in jso

    @staticmethod
    def _is_valid_json(doc):
        """Determine if the retrieved string is a valid json document or not"""
        try:
            jso = json.loads(doc)
            return jso
        except ValueError:
            return None

    def _read_proc_stdout(self, timeout, watching=None):
        """reads the burp process stdout and returns a document or None"""
        doc = ""
        tmp = ""
        jso = None
        cache = {}
        if watching:
            watching = watching.rstrip()
        while True:
            try:
                if not self._proc_is_alive():
                    raise OSError("process died while reading its output")
                read, _, _ = select([self.proc.stdout], [], [], timeout)
                if self.proc.stdout not in read:
                    raise TimeoutError("Read operation timed out")
                tmp += to_unicode(self.proc.stdout.readline()).rstrip("\n")
                jso = self._is_valid_json(tmp)
                # if the string is a valid json and looks like a logline, we
                # simply ignore it
                if jso and self._is_ignored(jso, watching):
                    tmp = ""
                    continue
                elif jso:
                    if not self.status_delimiter or (
                        self.status_delimiter and watching is None
                    ):
                        doc = tmp
                        break
                    start = jso.get("response-start")
                    end = jso.get("response-end")
                    if not start and not end:
                        cache["raw"] = tmp
                        cache["json"] = jso
                    elif start and start != watching:
                        doc = ""
                        jso = None
                        break
                    elif end and end != watching:
                        doc = ""
                        jso = None
                        break
                    elif end:
                        doc = cache.get("raw", "")
                        jso = cache.get("json")
                        break
                    tmp = ""
            except (TimeoutError, IOError, OSError) as exp:
                # the os throws an exception if there is no data or timeout
                self.logger.warning(str(exp))
                self._kill_burp()
                return None, None
        return jso, doc

    def _cleanup_cache(self):
        now = datetime.datetime.now()
        if now - self._last_status_cleanup > self._time_to_cache:
            self._status_cache.clear()
            self._last_status_cleanup = now

    def status(self, query="c:\n", timeout=None, cache=True, raw=False):
        """Send the given query to the status port and parses the output"""
        try:
            timeout = timeout or self.timeout
            query = sanitize_string(query.rstrip())
            self.logger.info(
                f"{self.ident} - query: '{query}' (cache: {cache}, raw: {raw})"
            )
            query = "{0}\n".format(query)

            self._cleanup_cache()
            # return cached results
            key = f"{query}-{raw}"
            if cache and key in self._status_cache:
                return self._status_cache[key]

            if not self._proc_is_alive():
                self._spawn_burp()

            _, write, _ = select([], [self.proc.stdin], [], timeout)
            if self.proc.stdin not in write:
                raise TimeoutError("Write operation timed out")
            self.proc.stdin.write(to_bytes(query))
            jso, doc = self._read_proc_stdout(timeout, query)
            if self._is_warning(jso):
                self.logger.warning(jso["warning"])
                self.logger.debug("Nothing interesting to return")
                return None

            if raw:
                res = doc
            else:
                res = jso

            self.logger.debug(f"{self.ident} => {res}")

            if cache:
                self._status_cache[key] = res

            return res
        except TimeoutError as exp:
            msg = f"Cannot send command: {exp}"
            self.logger.error(msg)
            self._kill_burp()
            if getattr(self.app, "strict", True):
                raise BUIserverException(msg)
        except (OSError, Exception) as exp:
            msg = f"Cannot launch burp process: {exp}"
            self.logger.error(msg)
            if getattr(self.app, "strict", True):
                raise BUIserverException(msg)
        return None
