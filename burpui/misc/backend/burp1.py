# -*- coding: utf8 -*-
"""
.. module:: burp1
    :platform: Unix
    :synopsis: Burp-UI burp1 backend module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
import re
import os
import socket
import time
import json
import datetime
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import shutil
import subprocess
import tempfile
import codecs

from pipes import quote
from urllib import unquote

from burpui.misc.utils import human_readable as _hr, BUIlogging, BUIcompress
from burpui.misc.backend.interface import BUIbackend, BUIserverException
from burpui.misc.parser.burp1 import Parser


g_burpport = '4972'
g_burphost = '::1'
g_burpbin = u'/usr/sbin/burp'
g_stripbin = u'/usr/sbin/vss_strip'
g_burpconfcli = None
g_burpconfsrv = u'/etc/burp/burp-server.conf'
g_tmpdir = u'/tmp/bui'


class Burp(BUIbackend, BUIlogging):
    """
    The :class:`burpui.misc.backend.Burp1` class provides a consistent
    backend for ``burp-1`` servers.
    """
    states = {
        'i': 'idle',
        'r': 'running',
        'c': 'client crashed',
        'C': 'server crashed',
        '1': 'scanning',
        '2': 'backup',
        '3': 'merging',
        '4': 'shuffling',
        '7': 'listing',
        '8': 'restoring',
        '9': 'verifying',
        '0': 'deleting'
    }

    counters = [
        'phase',
        'Total',
        'Files',
        'Files (encrypted)',
        'Metadata',
        'Metadata (enc)',
        'Directories',
        'Softlink',
        'Hardlink',
        'Special files',
        'VSS header',
        'VSS header (enc)',
        'VSS footer',
        'VSS footer (enc)',
        'Grand total',
        'warning',
        'estimated_bytes',
        'bytes',
        'bytes_in',
        'bytes_out',
        'start',
        'path'
    ]

    def __init__(self, server=None, conf=None, dummy=False):
        """
        The :class:`burpui.misc.backend.Burp1` class provides a consistent
        backend for ``burp-1`` servers.

        :param server: ``Burp-UI`` server instance in order to access logger and/or some global settings
        :type server: :class:`burpui.server.BUIServer`

        :param conf: Configuration file to use
        :type conf: str

        :param dummy: Does not instanciate the object (used for development purpose)
        :type dummy: boolean
        """
        global g_burpport, g_burphost, g_burpbin, g_stripbin, g_burpconfcli, g_burpconfsrv, g_tmpdir
        if dummy:
            return
        self.app = None
        self.acl_handler = False
        if server:
            if hasattr(server, 'app'):
                self.app = server.app
            self.acl_handler = server.acl_handler
        self.host = g_burphost
        self.port = int(g_burpport)
        self.burpbin = g_burpbin
        self.stripbin = g_stripbin
        self.burpconfcli = g_burpconfcli
        self.burpconfsrv = g_burpconfsrv
        self.tmpdir = g_tmpdir
        self.running = []
        self.defaults = {'bport': g_burpport, 'bhost': g_burphost, 'burpbin': g_burpbin, 'stripbin': g_stripbin, 'bconfcli': g_burpconfcli, 'bconfsrv': g_burpconfsrv, 'tmpdir': g_tmpdir}
        if conf:
            config = ConfigParser.ConfigParser(self.defaults)
            with codecs.open(conf, 'r', 'utf-8') as fp:
                config.readfp(fp)

                self.port = self._safe_config_get(config.getint, 'bport', cast=int)
                self.host = self._safe_config_get(config.get, 'bhost')
                bbin = self._safe_config_get(config.get, 'burpbin')
                strip = self._safe_config_get(config.get, 'stripbin')
                confcli = self._safe_config_get(config.get, 'bconfcli')
                confsrv = self._safe_config_get(config.get, 'bconfsrv')
                tmpdir = self._safe_config_get(config.get, 'tmpdir')

                if tmpdir and os.path.exists(tmpdir) and not os.path.isdir(tmpdir):
                    self._logger('warning', "'%s' is not a directory", tmpdir)
                    tmpdir = g_tmpdir

                if confcli and not os.path.isfile(confcli):
                    self._logger('warning', "The file '%s' does not exist", confcli)
                    confcli = None

                if confsrv and not os.path.isfile(confsrv):
                    self._logger('warning', "The file '%s' does not exist", confsrv)
                    confsrv = None

                if self.host not in ['127.0.0.1', '::1']:
                    self._logger('warning', "Invalid value for 'bhost'. Must be '127.0.0.1' or '::1'. Falling back to '%s'", g_burphost)
                    self.host = g_burphost

                if strip and not strip.startswith('/'):
                    self._logger('warning', "Please provide an absolute path for the 'stripbin' option. Fallback to '%s'", g_stripbin)
                    strip = g_stripbin
                elif strip and not re.match('^\S+$', strip):
                    self._logger('warning', "Incorrect value for the 'stripbin' option. Fallback to '%s'", g_stripbin)
                    strip = g_stripbin
                elif strip and (not os.path.isfile(strip) or not os.access(strip, os.X_OK)):
                    self._logger('warning', "'%s' does not exist or is not executable. Fallback to '%s'", strip, g_stripbin)
                    strip = g_stripbin

                if strip and (not os.path.isfile(strip) or not os.access(strip, os.X_OK)):
                    self._logger('error', "Ooops, '%s' not found or is not executable", strip)
                    strip = None

                if bbin and not bbin.startswith('/'):
                    self._logger('warning', "Please provide an absolute path for the 'burpbin' option. Fallback to '%s'", g_burpbin)
                    bbin = g_burpbin
                elif bbin and not re.match('^\S+$', bbin):
                    self._logger('warning', "Incorrect value for the 'burpbin' option. Fallback to '%s'", g_burpbin)
                    bbin = g_burpbin
                elif bbin and (not os.path.isfile(bbin) or not os.access(bbin, os.X_OK)):
                    self._logger('warning', "'%s' does not exist or is not executable. Fallback to '%s'", bbin, g_burpbin)
                    bbin = g_burpbin

                if bbin and (not os.path.isfile(bbin) or not os.access(bbin, os.X_OK)):
                    self._logger('error', "Ooops, '%s' not found or is not executable", bbin)
                    bbin = None

                self.burpbin = bbin
                self.stripbin = strip
                self.burpconfcli = confcli
                self.burpconfsrv = confsrv
                self.tmpdir = tmpdir

        self.parser = Parser(self.app, self.burpconfsrv)

        self.family = self._get_inet_family(self.host)
        self._test_burp_server_address(self.host)

        self._logger('info', 'burp port: %d', self.port)
        self._logger('info', 'burp host: %s', self.host)
        self._logger('info', 'burp binary: %s', self.burpbin)
        self._logger('info', 'strip binary: %s', self.stripbin)
        self._logger('info', 'burp conf cli: %s', self.burpconfcli)
        self._logger('info', 'burp conf srv: %s', self.burpconfsrv)
        self._logger('info', 'tmpdir: %s', self.tmpdir)

    """
    Utilities functions
    """

    def _safe_config_get(self, callback, key, sect='Burp1', cast=None):
        """
        :func:`burpui.misc.backend.burp1._safe_config_get` is a wrapper to handle
        Exceptions throwed by :mod:`ConfigParser`.

        :param callback: Function to wrap
        :type callback: callable

        :param key: Key to retrieve
        :type key: str

        :param sect: Section of the config file to read
        :type sect: str

        :param cast: Cast the returned value if provided
        :type case: callable

        :returns: The value returned by the `callback`
        """
        try:
            return callback(sect, key)
        except ConfigParser.NoOptionError as e:
            self._logger('error', str(e))
        except ConfigParser.NoSectionError as e:
            self._logger('warning', str(e))
            if key in self.defaults:
                if cast:
                    return cast(self.defaults[key])
                return self.defaults[key]
        return None

    def _get_inet_family(self, addr):
        """
        The :func:`burpui.misc.backend.Burp1._get_inet_family` function
        determines the inet family of a given address.

        :param addr: Address to look at
        :type addr: str

        :returns: Inet family of the given address: :const:`socket.AF_INET` of :const:`socket.AF_INET6`
        """
        if addr == '127.0.0.1':
            return socket.AF_INET
        else:
            return socket.AF_INET6

    def _test_burp_server_address(self, addr, retry=False):
        """
        The :func:`burpui.misc.backend.Burp1._test_burp_server_address` function
        determines if the given address is reachable or not.

        :param addr: Address to look at
        :type addr: str

        :param retry: Flag to stop trying because this function is recursive
        :type retry: bool

        :returns: True or False wether we could find a valid address or not
        """
        family = self._get_inet_family(addr)
        try:
            s = socket.socket(family, socket.SOCK_STREAM)
            s.connect((addr, self.port))
            s.close()
            return True
        except socket.error:
            self._logger('warning', 'Cannot contact burp server at %s:%s', addr, self.port)
            if not retry:
                new_addr = ''
                if self.host == '127.0.0.1':
                    new_addr = '::1'
                else:
                    new_addr = '127.0.0.1'
                self._logger('info', 'Trying %s:%s instead', new_addr, self.port)
                if self._test_burp_server_address(new_addr, True):
                    self._logger('info', '%s:%s is reachable, switching to it for this runtime', new_addr, self.port)
                    self.host = new_addr
                    self.family = self._get_inet_family(new_addr)
                    return True
                self._logger('error', 'Cannot guess burp server address')
        return False

    def status(self, query='\n', agent=None):
        """
        Send queries to the Burp server

        :param query: Query to send to the server
        :type query: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: The output returned by the server parsed as an array
        """
        r = []
        try:
            if not query.endswith('\n'):
                q = '{0}\n'.format(query)
            else:
                q = query
            s = socket.socket(self.family, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.send(q)
            s.shutdown(socket.SHUT_WR)
            f = s.makefile()
            s.close()
            for l in f.readlines():
                line = l.rstrip('\n')
                if not line:
                    continue
                ap = ''
                try:
                    ap = line.decode('utf-8', 'replace')
                except UnicodeDecodeError:
                    ap = line
                r.append(ap)
            f.close()
            return r
        except socket.error:
            self._logger('error', 'Cannot contact burp server at %s:%s', self.host, self.port)
            raise BUIserverException('Cannot contact burp server at {0}:{1}'.format(self.host, self.port))

    def get_backup_logs(self, number, client, forward=False, agent=None):
        """
        The :func:`burpui.misc.backend.Burp1.get_backup_logs` function is used
        to retrieve the burp logs based on the :func:`_parse_backup_stats` or
        :func:`_parse_backup_log` functions depending the burp-server version.

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
        if not client or not number:
            return {}

        f = self.status('c:{0}:b:{1}\n'.format(client, number))
        found = False
        ret = {}
        for line in f:
            if line == 'backup_stats':
                found = True
                break

        if not found:
            cl = None
            if forward:
                cl = client

            f = self.status('c:{0}:b:{1}:f:log.gz\n'.format(client, number))
            ret = self._parse_backup_log(f, number, cl)
        else:
            ret = self._parse_backup_stats(number, client, forward)

        ret['encrypted'] = False
        if 'files_enc' in ret and ret['files_enc']['total'] > 0:
            ret['encrypted'] = True
        return ret

    def _parse_backup_stats(self, number, client, forward=False, agent=None):
        """
        The :func:`burpui.misc.backend.Burp1._parse_backup_stats` function is
        used to parse the burp logs.

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
        backup = {'windows': 'unknown', 'number': int(number)}
        if forward:
            backup['name'] = client
        keys = {
            'time_start': 'start',
            'time_end': 'end',
            'time_taken': 'duration',
            'bytes_in_backup': 'totsize',
            'bytes_received': 'received',
            'files': ['files', 'new'],
            'files_changed': ['files', 'changed'],
            'files_same': ['files', 'unchanged'],
            'files_deleted': ['files', 'deleted'],
            'files_scanned': ['files', 'scanned'],
            'files_total': ['files', 'total'],
            'files_encrypted': ['files_enc', 'new'],
            'files_encrypted_changed': ['files_enc', 'changed'],
            'files_encrypted_same': ['files_enc', 'unchanged'],
            'files_encrypted_deleted': ['files_enc', 'deleted'],
            'files_encrypted_scanned': ['files_enc', 'scanned'],
            'files_encrypted_total': ['files_enc', 'total'],
            'directories': ['dir', 'new'],
            'directories_changed': ['dir', 'changed'],
            'directories_same': ['dir', 'unchanged'],
            'directories_deleted': ['dir', 'deleted'],
            'directories_scanned': ['dir', 'scanned'],
            'directories_total': ['dir', 'total'],
            'soft_links': ['softlink', 'new'],
            'soft_links_changed': ['softlink', 'changed'],
            'soft_links_same': ['softlink', 'unchanged'],
            'soft_links_deleted': ['softlink', 'deleted'],
            'soft_links_scanned': ['softlink', 'scanned'],
            'soft_links_total': ['softlink', 'total'],
            'hard_links': ['hardlink', 'new'],
            'hard_links_changed': ['hardlink', 'changed'],
            'hard_links_same': ['hardlink', 'unchanged'],
            'hard_links_deleted': ['hardlink', 'deleted'],
            'hard_links_scanned': ['hardlink', 'scanned'],
            'hard_links_total': ['hardlink', 'total'],
            'meta_data': ['meta', 'new'],
            'meta_data_changed': ['meta', 'changed'],
            'meta_data_same': ['meta', 'unchanged'],
            'meta_data_deleted': ['meta', 'deleted'],
            'meta_data_scanned': ['meta', 'scanned'],
            'meta_data_total': ['meta', 'total'],
            'meta_data_encrypted': ['meta_enc', 'new'],
            'meta_data_encrypted_changed': ['meta_enc', 'changed'],
            'meta_data_encrypted_same': ['meta_enc', 'unchanged'],
            'meta_data_encrypted_deleted': ['meta_enc', 'deleted'],
            'meta_data_encrypted_scanned': ['meta_enc', 'scanned'],
            'meta_data_encrypted_total': ['meta_enc', 'total'],
            'special_files': ['special', 'new'],
            'special_files_changed': ['special', 'changed'],
            'special_files_same': ['special', 'unchanged'],
            'special_files_deleted': ['special', 'deleted'],
            'special_files_scanned': ['special', 'scanned'],
            'special_files_total': ['special', 'total'],
            'efs_files': ['efs', 'new'],
            'efs_files_changed': ['efs', 'changed'],
            'efs_files_same': ['efs', 'unchanged'],
            'efs_files_deleted': ['efs', 'deleted'],
            'efs_files_scanned': ['efs', 'scanned'],
            'efs_files_total': ['efs', 'total'],
            'vss_headers': ['vssheader', 'new'],
            'vss_headers_changed': ['vssheader', 'changed'],
            'vss_headers_same': ['vssheader', 'unchanged'],
            'vss_headers_deleted': ['vssheader', 'deleted'],
            'vss_headers_scanned': ['vssheader', 'scanned'],
            'vss_headers_total': ['vssheader', 'total'],
            'vss_headers_encrypted': ['vssheader_enc', 'new'],
            'vss_headers_encrypted_changed': ['vssheader_enc', 'changed'],
            'vss_headers_encrypted_same': ['vssheader_enc', 'unchanged'],
            'vss_headers_encrypted_deleted': ['vssheader_enc', 'deleted'],
            'vss_headers_encrypted_scanned': ['vssheader_enc', 'scanned'],
            'vss_headers_encrypted_total': ['vssheader_enc', 'total'],
            'vss_footers': ['vssfooter', 'new'],
            'vss_footers_changed': ['vssfooter', 'changed'],
            'vss_footers_same': ['vssfooter', 'unchanged'],
            'vss_footers_deleted': ['vssfooter', 'deleted'],
            'vss_footers_scanned': ['vssfooter', 'scanned'],
            'vss_footers_total': ['vssfooter', 'total'],
            'vss_footers_encrypted': ['vssfooter_enc', 'new'],
            'vss_footers_encrypted_changed': ['vssfooter_enc', 'changed'],
            'vss_footers_encrypted_same': ['vssfooter_enc', 'unchanged'],
            'vss_footers_encrypted_deleted': ['vssfooter_enc', 'deleted'],
            'vss_footers_encrypted_scanned': ['vssfooter_enc', 'scanned'],
            'vss_footers_encrypted_total': ['vssfooter_enc', 'total'],
            'total': ['total', 'new'],
            'total_changed': ['total', 'changed'],
            'total_same': ['total', 'unchanged'],
            'total_deleted': ['total', 'deleted'],
            'total_scanned': ['total', 'scanned'],
            'total_total': ['total', 'total']
        }
        f = self.status('c:{0}:b:{1}:f:backup_stats\n'.format(client, number), agent=agent)
        for line in f:
            if line == '-list begin-' or line == '-list end-':
                continue
            (key, val) = line.split(':')
            if backup['windows'] == 'unknown' and key == 'client_is_windows':
                if val == '1':
                    backup['windows'] = 'true'
                else:
                    backup['windows'] = 'false'
                continue
            if key not in keys:
                continue
            rk = keys[key]
            if isinstance(rk, list):
                if not rk[0] in backup:
                    backup[rk[0]] = {}
                backup[rk[0]][rk[1]] = int(val)
            else:
                backup[rk] = int(val)
        return backup

    def _parse_backup_log(self, fh, number, client=None, agent=None):
        """
        The :func:`burpui.misc.backend.Burp1._parse_backup_log` function is
        used to parse the log.gz of a given backup and returns a dict
        containing different stats used to render the charts in the reporting
        view.

        :param fh: List representing the content of the log file
        :type fh: list

        :param number: Backup number to work on
        :type number: int

        :param client: Client name to work on
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: Dict containing the backup log
        """
        lookup_easy = {
            'start': '^Start time: (.+)$',
            'end': '^\s*End time: (.+)$',
            'duration': '^Time taken: (.+)$',
            'totsize': '^\s*Bytes in backup:\s+(\d+)',
            'received': '^\s*Bytes received:\s+(\d+)'
        }
        lookup_complex = {
            'files': '^\s*Files:?\s+(.+)\s+\|\s+(\d+)$',
            'files_enc': '^\s*Files \(encrypted\):?\s+(.+)\s+\|\s+(\d+)$',
            'dir': '^\s*Directories:?\s+(.+)\s+\|\s+(\d+)$',
            'softlink': '^\s*Soft links:?\s+(.+)\s+\|\s+(\d+)$',
            'hardlink': '^\s*Hard links:?\s+(.+)\s+\|\s+(\d+)$',
            'meta': '^\s*Meta data:?\s+(.+)\s+\|\s+(\d+)$',
            'meta_enc': '^\s*Meta data\(enc\):?\s+(.+)\s+\|\s+(\d+)$',
            'special': '^\s*Special files:?\s+(.+)\s+\|\s+(\d+)$',
            'efs': '^\s*EFS files:?\s+(.+)\s+\|\s+(\d+)$',
            'vssheader': '^\s*VSS headers:?\s+(.+)\s+\|\s+(\d+)$',
            'vssheader_enc': '^\s*VSS headers \(enc\):?\s+(.+)\s+\|\s+(\d+)$',
            'vssfooter': '^\s*VSS footers:?\s+(.+)\s+\|\s+(\d+)$',
            'vssfooter_enc': '^\s*VSS footers \(enc\):?\s+(.+)\s+\|\s+(\d+)$',
            'total': '^\s*Grand total:?\s+(.+)\s+\|\s+(\d+)$'
        }
        backup = {'windows': 'false', 'number': int(number)}
        if client is not None:
            backup['name'] = client
        useful = False
        for line in fh:
            if re.match('^\d{4}-\d{2}-\d{2} (\d{2}:){3} \w+\[\d+\] Client is Windows$', line):
                backup['windows'] = 'true'
            elif not useful and not re.match('^-+$', line):
                continue
            elif useful and re.match('^-+$', line):
                useful = False
                continue
            elif re.match('^-+$', line):
                useful = True
                continue

            found = False
            # this method is not optimal, but it is easy to read and to maintain
            for key, regex in lookup_easy.iteritems():
                r = re.search(regex, line)
                if r:
                    found = True
                    if key in ['start', 'end']:
                        backup[key] = int(time.mktime(datetime.datetime.strptime(r.group(1), '%Y-%m-%d %H:%M:%S').timetuple()))
                    elif key == 'duration':
                        tmp = r.group(1).split(':')
                        tmp.reverse()
                        i = 0
                        fields = [0] * 4
                        for v in tmp:
                            fields[i] = int(v)
                            i += 1
                        seconds = 0
                        seconds += fields[0]
                        seconds += fields[1] * 60
                        seconds += fields[2] * (60 * 60)
                        seconds += fields[3] * (60 * 60 * 24)
                        backup[key] = seconds
                    else:
                        backup[key] = int(r.group(1))
                    # break the loop as soon as we find a match
                    break

            # if found is True, we already parsed the line so we can jump to the next one
            if found:
                continue

            for key, regex in lookup_complex.iteritems():
                r = re.search(regex, line)
                if r:
                    # self._logger('debug', "match[1]: '{0}'".format(r.group(1)))
                    sp = re.split('\s+', r.group(1))
                    if len(sp) < 5:
                        return {}
                    backup[key] = {
                        'new': int(sp[0]),
                        'changed': int(sp[1]),
                        'unchanged': int(sp[2]),
                        'deleted': int(sp[3]),
                        'total': int(sp[4]),
                        'scanned': int(r.group(2))
                    }
                    break
        return backup

    def get_clients_report(self, clients, agent=None):
        """
        get_clients_report returns the computed/compacted data to display clients
        report.
        It returns an array containing two dicts
        """
        ret = []
        cl = []
        ba = []
        for c in clients:
            client = self.get_client(c['name'])
            if not client:
                continue
            stats = self.get_backup_logs(client[-1]['number'], c['name'])
            cl.append({'name': c['name'], 'stats': {'windows': stats['windows'], 'totsize': stats['totsize'], 'total': stats['total']['total']}})
            ba.append({'name': c['name'], 'number': len(client)})
        ret.append({'clients': cl, 'backups': ba})
        return ret

    def get_counters(self, name=None, agent=None):
        """
        get_counters parses the stats of the live status for a given client and
        returns a dict
        """
        r = {}
        if agent:
            if not name or name not in self.running[agent]:
                return r
        else:
            if not name or name not in self.running:
                return r
        f = self.status('c:{0}\n'.format(name))
        if not f:
            return r
        for line in f:
            # self._logger('debug', 'line: {0}'.format(line))
            rs = re.search('^{0}\s+(\d)\s+(\S)\s+(.+)$'.format(name), line)
            if rs and rs.group(2) == 'r' and int(rs.group(1)) == 2:
                c = 0
                for v in rs.group(3).split('\t'):
                    # self._logger('debug', '{0}: {1}'.format(self.counters[c], v))
                    if c > 0 and c < 15:
                        val = map(int, v.split('/'))
                        if val[0] > 0 or val[1] > 0 or val[2] or val[3] > 0:
                            r[self.counters[c]] = val
                    else:
                        if 'path' == self.counters[c]:
                            r[self.counters[c]] = v
                        else:
                            try:
                                r[self.counters[c]] = int(v)
                            except ValueError:
                                continue
                    c += 1
        if r.viewkeys() & {'start', 'estimated_bytes', 'bytes_in'}:
            try:
                diff = time.time() - int(r['start'])
                byteswant = int(r['estimated_bytes'])
                bytesgot = int(r['bytes_in'])
                bytespersec = bytesgot / diff
                bytesleft = byteswant - bytesgot
                r['speed'] = bytespersec
                if (bytespersec > 0):
                    timeleft = int(bytesleft / bytespersec)
                    r['timeleft'] = timeleft
                else:
                    r['timeleft'] = -1
            except:
                r['timeleft'] = -1
        return r

    def is_backup_running(self, name=None, agent=None):
        """
        is_backup_running returns True if the given client is currently running a
        backup
        """
        if not name:
            return False
        try:
            f = self.status('c:{0}\n'.format(name))
        except BUIserverException:
            return False
        for line in f:
            r = re.search('^{0}\s+\d\s+(\w)'.format(name), line)
            if r and r.group(1) not in ['i', 'c', 'C']:
                return True
        return False

    def is_one_backup_running(self, agent=None):
        """
        is_one_backup_running returns a list of clients name that are currently
        running a backup
        """
        r = []
        try:
            cls = self.get_all_clients()
        except BUIserverException:
            return r
        for c in cls:
            if self.is_backup_running(c['name']):
                r.append(c['name'])
        self.running = r
        return r

    def get_all_clients(self, agent=None):
        """
        get_all_clients returns a list of dict representing each clients with their
        name, state and last backup date
        """
        j = []
        f = self.status()
        for line in f:
            regex = re.compile('\s*(\S+)\s+\d\s+(\S)\s+(.+)')
            m = regex.search(line)
            c = {}
            c['name'] = m.group(1)
            c['state'] = self.states[m.group(2)]
            infos = m.group(3)
            if c['state'] in ['running']:
                c['last'] = 'now'
            elif infos == "0":
                c['last'] = 'never'
            elif re.match('^\d+\s\d+\s\d+$', infos):
                sp = infos.split()
                c['last'] = datetime.datetime.fromtimestamp(int(sp[2])).strftime('%Y-%m-%d %H:%M:%S')
            else:
                sp = infos.split('\t')
                c['last'] = datetime.datetime.fromtimestamp(int(sp[len(sp) - 2])).strftime('%Y-%m-%d %H:%M:%S')
            j.append(c)
        return j

    def get_client(self, name=None, agent=None):
        """
        get_client returns a list of dict representing the backups (with its number
        and date) of a given client
        """
        r = []
        if not name:
            return r
        c = name
        f = self.status('c:{0}\n'.format(c))
        for line in f:
            if not re.match('^{0}\t'.format(c), line):
                continue
            # self._logger('debug', "line: '{0}'".format(line))
            regex = re.compile('\s*(\S+)\s+\d\s+(\S)\s+(.+)')
            m = regex.search(line)
            if m.group(3) == "0" or m.group(2) not in ['i', 'c', 'C']:
                continue
            backups = m.group(3).split('\t')
            for b in backups:
                ba = {}
                sp = b.split()
                ba['number'] = sp[0]
                ba['deletable'] = (sp[1] == '1')
                ba['date'] = datetime.datetime.fromtimestamp(int(sp[2])).strftime('%Y-%m-%d %H:%M:%S')
                log = self.get_backup_logs(sp[0], name)
                ba['encrypted'] = log['encrypted']
                r.append(ba)
        # Here we need to reverse the array so the backups are sorted by date ASC
        r.reverse()
        return r

    def get_tree(self, name=None, backup=None, root=None, agent=None):
        """
        get_tree returns a list of dict representing files/dir (with their attr)
        within a given path
        """
        r = []
        if not name or not backup:
            return r
        if not root:
            top = ''
        else:
            try:
                top = root.decode('utf-8', 'replace')
            except UnicodeDecodeError:
                top = root

        f = self.status('c:{0}:b:{1}:p:{2}\n'.format(name, backup, top))
        useful = False
        for line in f:
            if not useful and re.match('^-list begin-$', line):
                useful = True
                continue
            if useful and re.match('^-list end-$', line):
                useful = False
                continue
            if useful:
                t = {}
                m = re.search('^(.{10})\s', line)
                if m:
                    if re.match('^(d|l)', m.group(1)):
                        t['type'] = 'd'
                    else:
                        t['type'] = 'f'
                    sp = re.split('\s+', line, 7)
                    t['mode'] = sp[0]
                    t['inodes'] = sp[1]
                    t['uid'] = sp[2]
                    t['gid'] = sp[3]
                    t['size'] = '{0:.1eM}'.format(_hr(sp[4]))
                    t['date'] = '{0} {1}'.format(sp[5], sp[6])
                    t['name'] = sp[7]
                    t['parent'] = top
                    r.append(t)
        return r

    def restore_files(self, name=None, backup=None, files=None, strip=None, archive='zip', password=None, agent=None):
        if not name or not backup or not files:
            return None, 'At least one argument is missing'
        if not self.stripbin:
            return None, 'Missing \'strip\' binary'
        if not self.burpbin:
            return None, 'Missing \'burp\' binary'
        flist = json.loads(files)
        if password:
            fh, tmpfile = tempfile.mkstemp()
        tmpdir = tempfile.mkdtemp(prefix=self.tmpdir)
        if 'restore' not in flist:
            return None, 'Wrong call'
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)
        full_reg = u''
        for r in flist['restore']:
            reg = u''
            if r['folder'] and r['key'] != '/':
                reg += '^' + re.escape(r['key']) + '/|'
            else:
                reg += '^' + re.escape(r['key']) + '$|'
            full_reg += reg

        cmd = [self.burpbin, '-C', quote(name), '-a', 'r', '-b', quote(str(backup)), '-r', full_reg.rstrip('|'), '-d', tmpdir]
        if password:
            if not self.burpconfcli:
                return None, 'No client configuration file specified'
            content = []
            fdh = os.fdopen(fh, 'w+')
            with open(self.burpconfcli) as f:
                shutil.copyfileobj(f, fdh)

            fdh.write('encryption_password = {}\n'.format(password))
            fdh.close()
            cmd.append('-c')
            cmd.append(tmpfile)
        elif self.burpconfcli:
            cmd.append('-c')
            cmd.append(self.burpconfcli)
        if strip and strip.isdigit() and int(strip) > 0:
            cmd.append('-s')
            cmd.append(strip)
        self._logger('debug', cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        status = p.wait()
        out, err = p.communicate()
        if password:
            os.remove(tmpfile)
        self._logger('debug', out)
        self._logger('debug', 'command returned: %d', status)
        # hack to handle client-side encrypted backups
        # this is now handled client-side, but we should never trust user input
        # so we need to handle it server-side too
        if 'zstrm inflate error: -3' in out and 'transfer file returning: -1' in out:
            status = 1
            out = 'encrypted'
        # a return code of 2 means there were some warnings during restoration
        # so we can assume the restoration was successful anyway
        if status not in [0, 2]:
            # out, err = p.communicate()
            return None, out

        zip_dir = tmpdir.rstrip(os.sep)
        zip_file = zip_dir + '.zip'
        if os.path.isfile(zip_file):
            os.remove(zip_file)
        zip_len = len(zip_dir) + 1
        stripping = True
        test_strip = True
        with BUIcompress(zip_file, archive) as zf:
            for dirname, subdirs, files in os.walk(zip_dir):
                for filename in files:
                    path = os.path.join(dirname, filename)
                    # try to detect if the file contains vss headers
                    if test_strip:
                        test_strip = False
                        otp = None
                        try:
                            otp = subprocess.check_output([self.stripbin, '-p', '-i', path])
                        except subprocess.CalledProcessError as e:
                            self._logger('debug', "Stripping failed on '{}': {}".format(path, str(e)))
                        if not otp:
                            stripping = False

                    if stripping and os.path.isfile(path):
                        self._logger('debug', "stripping file: %s", path)
                        shutil.move(path, path + '.tmp')
                        status = subprocess.call([self.stripbin, '-i', path + '.tmp', '-o', path])
                        if status != 0:
                            os.remove(path)
                            shutil.move(path + '.tmp', path)
                            stripping = False
                            self._logger('debug', "Disable stripping since this file does not seem to embed VSS headers")
                        else:
                            os.remove(path + '.tmp')

                    entry = path[zip_len:]
                    zf.append(path, entry)

        shutil.rmtree(tmpdir)
        return zip_file, None

    def read_conf_cli(self, client=None, conf=None, agent=None):
        if not self.parser:
            return []
        return self.parser.read_client_conf(client, conf)

    def read_conf_srv(self, conf=None, agent=None):
        if not self.parser:
            return []
        return self.parser.read_server_conf(conf)

    def store_conf_cli(self, data, client=None, conf=None, agent=None):
        if not self.parser:
            return []
        try:
            conf = unquote(conf)
        except:
            pass
        return self.parser.store_client_conf(data, client, conf)

    def store_conf_srv(self, data, conf=None, agent=None):
        if not self.parser:
            return []
        try:
            conf = unquote(conf)
        except:
            pass
        return self.parser.store_conf(data, conf)

    def expand_path(self, path=None, client=None, agent=None):
        if not path:
            return []
        return self.parser.path_expander(path, client)

    def delete_client(self, client=None, agent=None):
        if not client:
            return [2, "No client provided"]
        return self.parser.remove_client(client)

    def get_parser_attr(self, attr=None, agent=None):
        """
        Using a method because of the bui-agent
        """
        if not attr or not self.parser:
            return []
        return self.parser.get_priv_attr(attr)
