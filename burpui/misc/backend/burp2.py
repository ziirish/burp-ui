# -*- coding: utf8 -*-
import re
import os
import time
import subprocess
import codecs
import sys
import json
import logging

from six import iteritems
from select import select

from .burp1 import Burp as Burp1
from ..parser.burp2 import Parser
from ...utils import human_readable as _hr
from ...exceptions import BUIserverException
from ..._compat import ConfigParser

if sys.version_info < (3, 3):
    TimeoutError = OSError

BURP_MINIMAL_VERSION = 'burp-2.0.18'

g_burpbin = u'/usr/sbin/burp'
g_stripbin = u'/usr/sbin/vss_strip'
g_burpconfcli = u'/etc/burp/burp.conf'
g_burpconfsrv = u'/etc/burp/burp-server.conf'
g_tmpdir = u'/tmp/bui'
g_timeout = u'5'


# Some functions are the same as in Burp1 backend
class Burp(Burp1):
    """The :class:`burpui.misc.backend.burp2.Burp` class provides a consistent
    backend for ``burp-2`` servers.

    It extends the :class:`burpui.misc.backend.burp1.Burp` class because a few
    functions can be reused. The rest is just overrided.

    :param server: ``Burp-UI`` server instance in order to access logger
                   and/or some global settings
    :type server: :class:`burpui.server.BUIServer`

    :param conf: Configuration file to use
    :type conf: str
    """

    def __init__(self, server=None, conf=None):
        global g_burpbin, g_stripbin, g_burpconfcli, g_burpconfsrv, g_tmpdir, \
            g_timeout, BURP_MINIMAL_VERSION
        self.proc = None
        self.app = None
        self.client_version = None
        self.server_version = None
        self.zip64 = False
        self.logger = logging.getLogger('burp-ui')
        if server:
            if hasattr(server, 'zip64'):
                self.zip64 = server.zip64
        self.burpbin = g_burpbin
        self.stripbin = g_stripbin
        self.burpconfcli = g_burpconfcli
        self.burpconfsrv = g_burpconfsrv
        self.defaults = {
            'burpbin': g_burpbin,
            'stripbin': g_stripbin,
            'bconfcli': g_burpconfcli,
            'bconfsrv': g_burpconfsrv,
            'timeout': g_timeout,
            'tmpdir': g_tmpdir
        }
        self.running = []
        version = ''
        if conf:
            config = ConfigParser.ConfigParser(self.defaults)
            with codecs.open(conf, 'r', 'utf-8') as fp:
                config.readfp(fp)
                try:
                    bbin = self._safe_config_get(config.get, 'burpbin', sect='Burp2')
                    strip = self._safe_config_get(config.get, 'stripbin', sect='Burp2')
                    confcli = self._safe_config_get(config.get, 'bconfcli', sect='Burp2')
                    confsrv = self._safe_config_get(config.get, 'bconfsrv', sect='Burp2')
                    self.timeout = self._safe_config_get(config.getint, 'timeout', sect='Burp2', cast=int)
                    tmpdir = self._safe_config_get(config.get, 'tmpdir')

                    if tmpdir and os.path.exists(tmpdir) and not os.path.isdir(tmpdir):
                        self._logger('warning', "'%s' is not a directory", tmpdir)
                        tmpdir = g_tmpdir

                    if confcli and not os.path.isfile(confcli):
                        self._logger('warning', "The file '%s' does not exist", confcli)
                        confcli = g_burpconfcli

                    if confsrv and not os.path.isfile(confsrv):
                        self._logger('warning', "The file '%s' does not exist", confsrv)
                        confsrv = g_burpconfsrv

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
                        self._logger('critical', "Ooops, '%s' not found or is not executable", bbin)
                        # The burp binary is mandatory for this backend
                        raise Exception('This backend *CAN NOT* work without a burp binary')

                    self.tmpdir = tmpdir
                    self.burpbin = bbin
                    self.stripbin = strip
                    self.burpconfcli = confcli
                    self.burpconfsrv = confsrv
                except ConfigParser.NoOptionError as e:
                    self._logger('error', str(e))
                except ConfigParser.NoSectionError as e:
                    self._logger('warning', str(e))

        # check the burp version because this backend only supports clients newer than BURP_MINIMAL_VERSION
        try:
            cmd = [self.burpbin, '-v']
            version = subprocess.check_output(cmd, universal_newlines=True).rstrip()
            if version < BURP_MINIMAL_VERSION:
                raise Exception('Your burp version ({}) does not fit the minimal requirements: {}'.format(version, BURP_MINIMAL_VERSION))
        except subprocess.CalledProcessError as e:
            raise Exception('Unable to determine your burp version: {}'.format(str(e)))

        self.client_version = version.replace('burp-', '')

        self.parser = Parser(self.burpconfsrv)

        self._logger('info', 'burp binary: {}'.format(self.burpbin))
        self._logger('info', 'strip binary: {}'.format(self.stripbin))
        self._logger('info', 'burp conf cli: {}'.format(self.burpconfcli))
        self._logger('info', 'burp conf srv: {}'.format(self.burpconfsrv))
        self._logger('info', 'command timeout: {}'.format(self.timeout))
        self._logger('info', 'burp version: {}'.format(self.client_version))
        try:
            # make the connection
            self.status()
        except BUIserverException:
            pass

    def __exit__(self, type, value, traceback):
        """try not to leave child process server side"""
        self._terminate_burp()
        self._kill_burp()

    def _kill_burp(self):
        """Terminate the process"""
        if self._proc_is_alive():
            try:
                self.proc.terminate()
            except:
                pass
        if self._proc_is_alive():
            try:
                self.proc.kill()
            except:
                pass

    def _terminate_burp(self):
        """Terminate cleanly the process"""
        if self._proc_is_alive():
            self.proc.stdin.close()
            self.proc.communicate()
            self.proc.wait()

    def _spawn_burp(self):
        """Launch the burp client process"""
        cmd = [self.burpbin, '-c', self.burpconfcli, '-a', 'm']
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False, universal_newlines=True, bufsize=0)
        # wait a little bit in case the process dies on a network error
        time.sleep(0.5)
        if not self._proc_is_alive():
            raise Exception('Unable to spawn burp process')
        _, w, _ = select([], [self.proc.stdin], [], self.timeout)
        if self.proc.stdin not in w:
            self._kill_burp()
            raise OSError('Unable to setup burp client')
        self.proc.stdin.write('j:pretty-print-off\n')
        js = self._read_proc_stdout()
        if self._is_warning(js):
            self._logger('info', js['warning'])

    def _proc_is_alive(self):
        """Check if the burp client process is still alive"""
        if self.proc:
            return self.proc.poll() is None
        return False

    def _is_ignored(self, js):
        """We ignore the 'logline' lines"""
        if not js:
            return True
        if not self.server_version:
            if 'logline' in js:
                r = re.search('^Server version: (\d+\.\d+\.\d+)$', js['logline'])
                if r:
                    self.server_version = r.group(1)
        return 'logline' in js

    def _is_warning(self, js):
        """Returns True if the document is a warning"""
        if not js:
            return False
        return 'warning' in js

    def _is_valid_json(self, doc):
        """Determine if the retrieved string is a valid json document or not"""
        try:
            js = json.loads(doc)
            return js
        except ValueError:
            return None

    def _human_st_mode(self, mode):
        """Convert the st_mode returned by stat in human readable (ls-like) format"""
        hr = ''
        if os.path.stat.S_ISREG(mode):
            hr = '-'
        elif os.path.stat.S_ISLNK(mode):
            hr = 'l'
        elif os.path.stat.S_ISSOCK(mode):
            hr = 's'
        elif os.path.stat.S_ISDIR(mode):
            hr = 'd'
        elif os.path.stat.S_ISBLK(mode):
            hr = 'b'
        elif os.path.stat.S_ISFIFO(mode):
            hr = 'p'
        elif os.path.stat.S_ISCHR(mode):
            hr = 'c'
        else:
            hr = '-'

        for who in 'USR', 'GRP', 'OTH':
            for perm in 'R', 'W', 'X':
                if mode & getattr(os.path.stat, 'S_I' + perm + who):
                    hr += perm.lower()
                else:
                    hr += '-'

        return hr

    def _read_proc_stdout(self):
        """reads the burp process stdout and returns a document or None"""
        doc = u''
        js = None
        while True:
            try:
                if not self._proc_is_alive():
                    raise Exception('process died while reading its output')
                r, _, _ = select([self.proc.stdout], [], [], self.timeout)
                if self.proc.stdout not in r:
                    raise TimeoutError('Read operation timed out')
                doc += self.proc.stdout.readline().rstrip('\n')
                js = self._is_valid_json(doc)
                # if the string is a valid json and looks like a logline, we
                # simply ignore it
                if js and self._is_ignored(js):
                    doc = ''
                    continue
                elif js:
                    break
            except (TimeoutError, IOError, Exception) as e:
                # the os throws an exception if there is no data or timeout
                self._logger('warning', str(e))
                self._kill_burp()
                break
        return js

    def status(self, query='c:\n', agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.status`"""
        try:
            self._logger('info', "query: '{}'".format(query.rstrip()))
            if not query.endswith('\n'):
                query = '{0}\n'.format(query)
            if not self._proc_is_alive():
                self._spawn_burp()

            _, w, _ = select([], [self.proc.stdin], [], self.timeout)
            if self.proc.stdin not in w:
                raise TimeoutError('Write operation timed out')
            self.proc.stdin.write(query)
            js = self._read_proc_stdout()
            if self._is_warning(js):
                self._logger('warning', js['warning'])
                self._logger('debug', 'Nothing interesting to return')
                return None

            self._logger('debug', '=> {}'.format(js))
            return js
        except TimeoutError as e:
            msg = 'Cannot send command: {}'.format(str(e))
            self._logger('error', msg)
            self._kill_burp()
            raise BUIserverException(msg)
        except (OSError, Exception) as e:
            msg = 'Cannot launch burp process: {}'.format(str(e))
            self._logger('error', msg)
            raise BUIserverException(msg)

    def get_backup_logs(self, number, client, forward=False, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_backup_logs`"""
        ret = {}
        if not client or not number:
            return ret

        query = self.status('c:{0}:b:{1}\n'.format(client, number))
        if not query:
            return ret
        try:
            logs = query['clients'][0]['backups'][0]['logs']['list']
        except KeyError as e:
            self._logger('warning', 'No logs found')
            return ret
        if 'backup_stats' in logs:
            ret = self._parse_backup_stats(number, client, forward)
        # TODO: support clients that were upgraded to 2.x
        # else:
        #    cl = None
        #    if forward:
        #        cl = client

        #    f = self.status('c:{0}:b:{1}:f:log.gz\n'.format(client, number))
        #    ret = self._parse_backup_log(f, number, cl)

        ret['encrypted'] = False
        if 'files_enc' in ret and ret['files_enc']['total'] > 0:
            ret['encrypted'] = True
        return ret

    def _guess_backup_protocol(self, number, client):
        """The :func:`burpui.misc.backend.burp2.Burp._guess_backup_protocol`
        function helps you determine if the backup is protocol 2 or 1

        :param number: Backup number to work on
        :type number: int

        :param client: Client name to work on
        :type client: str

        :returns: 1 or 2
        """
        query = self.status('c:{0}:b:{1}:l:backup\n'.format(client, number))
        try:
            log = query['clients'][0]['backups'][0]['logs']['backup']
            for line in log:
                if re.search(r'Protocol: 2$', line):
                    return 2
        except KeyError as e:
            # Assume protocol 1 in all cases unless explicitly found Protocol 2
            return 1
        return 1

    def _parse_backup_stats(self, number, client, forward=False, agent=None):
        """The :func:`burpui.misc.backend.burp2.Burp._parse_backup_stats`
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
        ret = {}
        backup = {'windows': 'unknown', 'number': int(number)}
        if forward:
            backup['name'] = client
        translate = {
            'time_start': 'start',
            'time_end': 'end',
            'time_taken': 'duration',
            'bytes': 'totsize',
            'bytes_received': 'received',
            'bytes_estimated': 'estimated_bytes',
            'files': 'files',
            'files_encrypted': 'files_enc',
            'directories': 'dir',
            'soft_links': 'softlink',
            'hard_links': 'hardlink',
            'meta_data': 'meta',
            'meta_data_encrypted': 'meta_enc',
            'special_files': 'special',
            'efs_files': 'efs',
            'vss_headers': 'vssheader',
            'vss_headers_encrypted': 'vssheader_enc',
            'vss_footers': 'vssfooter',
            'vss_footers_encrypted': 'vssfooter_enc',
            'total': 'total',
            'grand_total': 'total',
        }
        counts = {
            'new': 'count',
            'changed': 'changed',
            'unchanged': 'same',
            'deleted': 'deleted',
            'total': 'scanned',
            'scanned': 'scanned',
        }
        single = ['time_start', 'time_end', 'time_taken', 'bytes_received', 'bytes_estimated', 'bytes']
        query = self.status('c:{0}:b:{1}:l:backup_stats\n'.format(client, number), agent=agent)
        if not query:
            return ret
        try:
            back = query['clients'][0]['backups'][0]
        except KeyError as e:
            self._logger('warning', 'No backup found')
            return ret
        if 'backup_stats' not in back['logs']:
            self._logger('warning', 'No stats found for backup')
            return ret
        stats = None
        try:
            stats = json.loads(''.join(back['logs']['backup_stats']))
        except:
            stats = back['logs']['backup_stats']
        if not stats:
            return ret
        # server was upgraded but backup comes from an older version
        if 'counters' not in stats:
            return super(Burp, self)._parse_backup_stats(number, client, forward, stats, agent)
        counters = stats['counters']
        for counter in counters:
            name = counter['name']
            if name in translate:
                name = translate[name]
            if counter['name'] in single:
                backup[name] = counter['count']
            else:
                backup[name] = {}
                for (k, v) in iteritems(counts):
                    if v in counter:
                        backup[name][k] = counter[v]
                    else:
                        backup[name][k] = 0
        if 'start' in backup and 'end' in backup:
            backup['duration'] = backup['end'] - backup['start']

        return backup

    # TODO: support old clients
    # def _parse_backup_log(self, fh, number, client=None, agent=None):
    #    """
    #    parse_backup_log parses the log.gz of a given backup and returns a dict
    #    containing different stats used to render the charts in the reporting view
    #    """
    #    return {}

    # def get_clients_report(self, clients, agent=None):

    def get_counters(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_counters`"""
        ret = {}
        if agent:
            if not name or name not in self.running[agent]:
                return ret
        else:
            if not name or name not in self.running:
                return ret
        query = self.status('c:{0}\n'.format(name))
        # check the status returned something
        if not query:
            return ret

        try:
            client = query['clients'][0]
        except KeyError as e:
            self._logger('warning', 'Client not found')
            return ret

        # check the client is currently backing-up
        if 'run_status' not in client or client['run_status'] != 'running':
            return ret

        backup = None
        for back in client['backups']:
            if 'flags' in back and 'working' in back['flags']:
                backup = back
                break
        # check we found a working backup
        if not backup:
            return ret

        # list of single counters (type CNTR_SINGLE_FIELD in cntr.c)
        single = [
            'bytes_estimated',
            'bytes',
            'bytes_received',
            'bytes_sent',
            'time_start',
            'time_end',
            'warnings',
            'errors'
        ]
        # translation table to be compatible with burp1
        translate = {'bytes_estimated': 'estimated_bytes'}
        for counter in backup['counters']:
            name = counter['name']
            if name in translate:
                name = translate[name]
            if counter['name'] not in single:
                ret[name] = [counter['count'], counter['changed'], counter['same'], counter['deleted'], counter['scanned']]
            else:
                ret[name] = counter['count']

        if 'bytes' not in ret:
            ret['bytes'] = 0
        if ret.viewkeys() & {'time_start', 'estimated_bytes', 'bytes'}:
            try:
                diff = time.time() - int(ret['time_start'])
                byteswant = int(ret['estimated_bytes'])
                bytesgot = int(ret['bytes'])
                bytespersec = bytesgot / diff
                bytesleft = byteswant - bytesgot
                ret['speed'] = bytespersec
                if (bytespersec > 0):
                    timeleft = int(bytesleft / bytespersec)
                    ret['timeleft'] = timeleft
                else:
                    ret['timeleft'] = -1
            except:
                ret['timeleft'] = -1
        try:
            ret['percent'] = round(float(ret['bytes']) / float(ret['estimated_bytes']) * 100)
        except:
            # You know... division by 0
            ret['percent'] = 0

        return ret

    def is_backup_running(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.is_backup_running`"""
        if not name:
            return False
        try:
            query = self.status('c:{0}\n'.format(name))
        except BUIserverException:
            return False
        if not query:
            return False
        try:
            return query['clients'][0]['run_status'] in ['running']
        except KeyError as e:
            self._logger('warning', 'Client not found')
            return False
        return False

    def is_one_backup_running(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.is_one_backup_running`"""
        ret = []
        try:
            clients = self.get_all_clients()
        except BUIserverException:
            return ret
        for client in clients:
            if client['state'] in ['running']:
                ret.append(client['name'])
        self.running = ret
        self.refresh = time.time()
        return ret

    def _status_human_readable(self, status):
        """The label has changed in burp2, we override it to be compatible with
        burp1's format

        :param status: The status returned by the burp2 server
        :type status: str

        :returns: burp1 status compatible
        """
        if not status:
            return None
        if status == 'c crashed':
            return 'client crashed'
        if status == 's crashed':
            return 'server crashed'
        return status

    def get_all_clients(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_all_clients`"""
        ret = []
        query = self.status()
        if not query or 'clients' not in query:
            return ret
        clients = query['clients']
        for client in clients:
            cli = {}
            cli['name'] = client['name']
            cli['state'] = self._status_human_readable(client['run_status'])
            infos = client['backups']
            if cli['state'] in ['running']:
                cli['phase'] = client['phase']
                cli['last'] = 'now'
                counters = self.get_counters(cli['name'])
                if 'percent' in counters:
                    cli['percent'] = counters['percent']
                else:
                    cli['percent'] = 0
            elif not infos:
                cli['last'] = 'never'
            else:
                infos = infos[0]
                cli['last'] = infos['timestamp']
            ret.append(cli)
        return ret

    def get_client(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client`"""
        ret = []
        if not name:
            return ret
        query = self.status('c:{0}\n'.format(name))
        if not query:
            return ret
        try:
            backups = query['clients'][0]['backups']
        except KeyError as e:
            self._logger('warning', 'Client not found')
            return ret
        for backup in backups:
            back = {}
            # skip running backups since data will be inconsistent
            if 'flags' in backup and 'working' in backup['flags']:
                continue
            back['number'] = backup['number']
            if 'flags' in backup and 'deletable' in backup['flags']:
                back['deletable'] = True
            else:
                back['deletable'] = False
            back['date'] = backup['timestamp']
            log = self.get_backup_logs(backup['number'], name)
            try:
                back['encrypted'] = log['encrypted']
                try:
                    back['received'] = log['received']
                except KeyError as e:
                    back['received'] = 0
                try:
                    back['size'] = log['totsize']
                except KeyError as e:
                    back['size'] = 0
                back['end'] = log['end']
                # override date since the timestamp is odd
                back['date'] = log['start']
                ret.append(back)
            except Exception as e:
                self._logger('warning', 'Unable to parse logs')
                pass

        # Here we need to reverse the array so the backups are sorted by date ASC
        ret.reverse()
        return ret

    def get_tree(self, name=None, backup=None, root=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_tree`"""
        ret = []
        if not name or not backup:
            return ret
        if not root:
            top = ''
        else:
            try:
                top = root.decode('utf-8', 'replace')
            except UnicodeDecodeError:
                top = root

        query = self.status('c:{0}:b:{1}:p:{2}\n'.format(name, backup, top))
        if not query:
            return ret
        try:
            backup = query['clients'][0]['backups'][0]
        except KeyError as e:
            return ret
        for entry in backup['browse']['entries']:
            data = {}
            if entry['name'] == '.':
                continue
            else:
                data['name'] = entry['name']
            data['mode'] = self._human_st_mode(entry['mode'])
            if re.match('^(d|l)', data['mode']):
                data['type'] = 'd'
            else:
                data['type'] = 'f'
            data['inodes'] = entry['nlink']
            data['uid'] = entry['uid']
            data['gid'] = entry['gid']
            data['parent'] = top
            data['size'] = '{0:.1eM}'.format(_hr(entry['size']))
            data['date'] = entry['mtime']
            ret.append(data)
        return ret

    def get_client_version(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_version`"""
        return self.client_version

    def get_server_version(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_server_version`"""
        if not self.server_version:
            self.status()
        return self.server_version

    def get_client_labels(self, client=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_labels`"""
        ret = []
        if not client:
            return ret
        query = self.status('c:{0}\n'.format(client))
        if not query:
            return ret
        try:
            return query['clients'][0]['labels']
        except KeyError as e:
            return ret

    # Same as in Burp1 backend
    # def restore_files(self, name=None, backup=None, files=None, strip=None, archive='zip', password=None, agent=None):

    # def read_conf_cli(self, agent=None):

    # def read_conf_srv(self, agent=None):

    # def store_conf_cli(self, data, agent=None):

    # def store_conf_srv(self, data, agent=None):

    # def get_parser_attr(self, attr=None, agent=None):
