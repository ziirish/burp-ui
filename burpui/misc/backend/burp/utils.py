# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.backend.burp.utils
    :platform: Unix
    :synopsis: Burp-UI burp utils module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import re
import subprocess
import json
import datetime
import logging

from select import select

from ...._compat import to_bytes, to_unicode
from ....exceptions import BUIserverException
from ....security import sanitize_string

BURP_MINIMAL_VERSION = 'burp-2.0.18'
BURP_LIST_BATCH = '2.0.48'
BURP_STATUS_FORMAT_V2 = '2.1.10'


class Monitor(object):
    """The :class:`burpui.misc.backend.burp.utils.Monitor` class provides a ``burp-2``
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
    logger = logging.getLogger('burp-ui')

    # cache status results
    _status_cache = {}
    _last_status_cleanup = datetime.datetime.now()
    _time_to_cache = datetime.timedelta(seconds=3)

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
        self.client_version = None
        self.server_version = None
        self.batch_list_supported = False
        self.ident = ident or id(self)

        self._burp_client_ok = False
        version = ''
        # check the burp version because this backend only supports clients
        # newer than BURP_MINIMAL_VERSION
        try:
            if self.burpbin:
                cmd = [self.burpbin, '-v']
                version = subprocess.check_output(
                    cmd,
                    universal_newlines=True
                ).rstrip()
                if version < BURP_MINIMAL_VERSION and \
                        getattr(self.app, 'strict', True):
                    self.logger.critical(
                        'Your burp version ({}) does not fit the minimal'
                        ' requirements: {}'.format(version, BURP_MINIMAL_VERSION)
                    )
                elif version >= BURP_MINIMAL_VERSION:
                    self._burp_client_ok = True
        except subprocess.CalledProcessError as exp:
            if getattr(self.app, 'strict', True):
                self.logger.critical(
                    'Unable to determine your burp version: {}'.format(str(exp))
                )

        self.client_version = version.replace('burp-', '')

        if self.app and not self.app.config['BUI_CLI']:
            try:
                # make the connection
                self._spawn_burp(True)
                self.status()
            except BUIserverException:
                pass
            except OSError as exp:
                msg = str(exp)
                self.logger.critical(msg)

    def _exit(self):
        """try not to leave child process server side"""
        self.logger.debug(f'Exiting {self.ident}')
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
            raise BUIserverException('No suitable burp client found')
        cmd = [self.burpbin, '-c', self.burpconf, '-a', 'm']
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            bufsize=0
        )
        if not self._proc_is_alive():
            details = ''
            if verbose:
                details = ':\n'
                out, _ = self.proc.communicate()
                details += to_unicode(out)
            raise OSError('Unable to spawn burp process{}'.format(details))
        _, write, _ = select([], [self.proc.stdin], [], self.timeout)
        if self.proc.stdin not in write:
            self._kill_burp()
            raise OSError('Unable to setup burp client')
        self.proc.stdin.write(to_bytes('j:pretty-print-off\n'))
        self._read_proc_stdout(self.timeout)
        # try to switch to new JSON status
        if self.client_version < BURP_STATUS_FORMAT_V2:
            self.proc.stdin.write(to_bytes('j:peer_version=2.1.10\n'))
            self._read_proc_stdout(self.timeout)

    def _proc_is_alive(self):
        """Check if the burp client process is still alive"""
        if self.proc:
            return self.proc.poll() is None
        return False

    def _is_ignored(self, jso):
        """We ignore the 'logline' lines"""
        if not jso:
            return True
        if not self.server_version:
            if 'logline' in jso:
                ret = re.search(
                    r'^Server version: (\d+\.\d+\.\d+).*$',
                    jso['logline']
                )
                if ret:
                    self.server_version = ret.group(1)
                    if self.server_version >= BURP_LIST_BATCH:
                        self.batch_list_supported = True
        return 'logline' in jso

    @staticmethod
    def _is_warning(jso):
        """Returns True if the document is a warning"""
        if not jso:
            return False
        return 'warning' in jso

    @staticmethod
    def _is_valid_json(doc):
        """Determine if the retrieved string is a valid json document or not"""
        try:
            jso = json.loads(doc)
            return jso
        except ValueError:
            return None

    def _read_proc_stdout(self, timeout):
        """reads the burp process stdout and returns a document or None"""
        doc = ''
        jso = None
        while True:
            try:
                if not self._proc_is_alive():
                    raise Exception('process died while reading its output')
                read, _, _ = select([self.proc.stdout], [], [], timeout)
                if self.proc.stdout not in read:
                    raise TimeoutError('Read operation timed out')
                doc += to_unicode(self.proc.stdout.readline()).rstrip('\n')
                jso = self._is_valid_json(doc)
                # if the string is a valid json and looks like a logline, we
                # simply ignore it
                if jso and self._is_ignored(jso):
                    doc = ''
                    continue
                elif jso:
                    break
            except (TimeoutError, IOError, Exception) as exp:
                # the os throws an exception if there is no data or timeout
                self.logger.warning(str(exp))
                self._kill_burp()
                return None
        return jso

    def _cleanup_cache(self):
        now = datetime.datetime.now()
        if now - self._last_status_cleanup > self._time_to_cache:
            self._status_cache.clear()
            self._last_status_cleanup = now

    def status(self, query='c:\n', timeout=None, cache=True):
        """Send the given query to the status port and parses the output"""
        try:
            timeout = timeout or self.timeout
            query = sanitize_string(query.rstrip())
            self.logger.info(f"{self.ident} - query: '{query}'")
            query = '{0}\n'.format(query)

            self._cleanup_cache()
            # return cached results
            if cache and query in self._status_cache:
                return self._status_cache[query]

            if not self._proc_is_alive():
                self._spawn_burp()

            _, write, _ = select([], [self.proc.stdin], [], self.timeout)
            if self.proc.stdin not in write:
                raise TimeoutError('Write operation timed out')
            self.proc.stdin.write(to_bytes(query))
            jso = self._read_proc_stdout(timeout)
            if self._is_warning(jso):
                self.logger.warning(jso['warning'])
                self.logger.debug('Nothing interesting to return')
                return None

            self.logger.debug(f'=> {jso}')

            if cache:
                self._status_cache[query] = jso

            return jso
        except TimeoutError as exp:
            msg = 'Cannot send command: {}'.format(str(exp))
            self.logger.error(msg)
            self._kill_burp()
            raise BUIserverException(msg)
        except (OSError, Exception) as exp:
            msg = 'Cannot launch burp process: {}'.format(str(exp))
            self.logger.error(msg)
            if getattr(self.app, 'strict', True):
                raise BUIserverException(msg)
        return None
