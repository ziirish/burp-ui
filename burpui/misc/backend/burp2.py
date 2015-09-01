# -*- coding: utf8 -*-
import re
import os
import socket
import time
try:
    import ujson as json
except ImportError:
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
import signal
import sys

from pipes import quote
from select import select

from burpui.misc.utils import human_readable as _hr
from burpui.misc.backend.interface import BUIserverException
from burpui.misc.backend.burp1 import Burp as Burp1
from burpui.misc.parser.burp1 import Parser

if sys.version_info < (3, 3):
    TimeoutError = OSError

BURP_MINIMAL_VERSION = 'burp-2.0.18'

g_burpbin = u'/usr/sbin/burp'
g_stripbin = u'/usr/sbin/vss_strip'
g_burpconfcli = u'/etc/burp/burp.conf'
g_burpconfsrv = u'/etc/burp/burp-server.conf'
g_tmpdir = u'/tmp/bui'


# Some functions are the same as in Burp1 backend
class Burp(Burp1):

    def __init__(self, server=None, conf=None):
        global g_burpbin, g_stripbin, g_burpconfcli, g_burpconfsrv, g_tmpdir, BURP_MINIMAL_VERSION
        self.proc = None
        self.app = None
        self.acl_handler = False
        if server:
            if hasattr(server, 'app'):
                self.app = server.app
            self.acl_handler = server.acl_handler
        self.burpbin = g_burpbin
        self.stripbin = g_stripbin
        self.burpconfcli = g_burpconfcli
        self.burpconfsrv = g_burpconfsrv
        self.defaults = {'burpbin': g_burpbin, 'stripbin': g_stripbin, 'bconfcli': g_burpconfcli, 'bconfsrv': g_burpconfsrv, 'tmpdir': g_tmpdir}
        self.running = []
        if conf:
            config = ConfigParser.ConfigParser(self.defaults)
            version = ''
            with codecs.open(conf, 'r', 'utf-8') as fp:
                config.readfp(fp)
                try:
                    bbin = self._safe_config_get(config.get, 'burpbin', sect='Burp2')
                    strip = self._safe_config_get(config.get, 'stripbin', sect='Burp2')
                    confcli = self._safe_config_get(config.get, 'bconfcli', sect='Burp2')
                    confsrv = self._safe_config_get(config.get, 'bconfsrv', sect='Burp2')
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
                        self._logger('error', "Ooops, '%s' not found or is not executable", bbin)
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
            version = subprocess.check_output(cmd, universal_newlines=True).rstrip('\n')
            if version < BURP_MINIMAL_VERSION:
                raise Exception('Your burp version ({}) does not fit the minimal requirements: {}'.format(version, BURP_MINIMAL_VERSION))
        except subprocess.CalledProcessError as e:
            raise Exception('Unable to determine your burp version: {}'.format(str(e)))

        self.parser = Parser(self.app, self.burpconfsrv)
        signal.signal(signal.SIGALRM, self._sighandler)

        self._logger('info', 'burp binary: %s', self.burpbin)
        self._logger('info', 'strip binary: %s', self.stripbin)
        self._logger('info', 'burp conf cli: %s', self.burpconfcli)
        self._logger('info', 'burp conf srv: %s', self.burpconfsrv)
        self._logger('info', 'burp version: %s', version)

    def _sighandler(self, signum, frame):
        raise TimeoutError('Operation timed out')

    # try not to leave child process server side
    def __exit__(self, type, value, traceback):
        if self._proc_is_alive():
            self.proc.stdin.close()
            self.proc.communicate()
            self.proc.wait()

    def _spawn_burp(self):
        cmd = [self.burpbin, '-c', self.burpconfcli, '-a', 'm']
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False, universal_newlines=True)
        # wait a little bit in case the process dies on a network timeout
        time.sleep(0.5)
        if not self._proc_is_alive():
            raise Exception('Unable to spawn burp process')
        self.proc.stdin.write('j:pretty-print-off\n')
        js = self._read_proc_stdout()
        if self._is_warning(js):
            self._logger('info', js['warning'])

    def _proc_is_alive(self):
        if self.proc:
            return self.proc.poll() == None
        return False

    def _is_ignored(self, js):
        """
        We ignore the 'logline' lines
        """
        if not js:
            return True
        return 'logline' in js

    def _is_warning(self, js):
        """
        Returns True if the document is a warning
        """
        if not js:
            return False
        return 'warning' in js

    def _is_valid_json(self, doc):
        """
        Determine if the retrieved string is a valid json document or not
        """
        try:
            js = json.loads(doc)
            return js
        except ValueError:
            return None

    def _human_st_mode(self, mode):
        """
        Convert the st_mode returned by stat in human readable (ls-like) format
        """
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
        """
        reads the burp process stdout and returns a document or None
        """
        doc = u''
        js = None
        while True:
            try:
                signal.alarm(5)
                if not self._proc_is_alive():
                    raise Exception('process died while reading its output')
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
                break
            finally:
                signal.alarm(0)
        return js

    def status(self, query='c:\n', agent=None):
        """
        status spawns a burp process in monitor mode, ask the given 'question'
        and parses the output in an array
        """
        try:
            if not query.endswith('\n'):
                q = '{0}\n'.format(query)
            else:
                q = query
            if not self._proc_is_alive():
                self._spawn_burp()

            self.proc.stdin.write(q)
            js = self._read_proc_stdout()
            if self._is_warning(js):
                self._logger('warning', js['warning'])
                return None

            return js
        except (OSError, Exception) as e:
            msg = 'Cannot launch burp process: {}'.format(str(e))
            self._logger('error', msg)
            raise BUIserverException(msg)

    def get_backup_logs(self, number, client, forward=False, agent=None):
        if not client or not number:
            return {}

        query = self.status('c:{0}:b:{1}\n'.format(client, number))
        if not query:
            return {}
        clients = query['clients']
        if not clients:
            return {}
        if 'backups' not in clients[0]:
            return {}
        backups = clients[0]['backups']
        if not backups:
            return {}
        if 'logs' not in backups[0] and 'list' not in backups[0]['logs']:
            return {}
        logs = backups[0]['logs']['list']
        if 'backup_stats' in logs:
            ret = self._parse_backup_stats(number, client, forward)
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

    def _parse_backup_stats(self, number, client, forward=False, agent=None):
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
            return {}
        clients = query['clients']
        if not clients:
            return {}
        client = clients[0]
        backups = client['backups']
        if not backups:
            return {}
        back = backups[0]
        if 'backup_stats' not in back['logs']:
            return {}
        try:
            stats = json.loads(''.join(back['logs']['backup_stats']))
        except:
            pass
        if not stats:
            return {}
        counters = stats['counters']
        for counter in counters:
            name = counter['name']
            if name in translate:
                name = translate[name]
            if counter['name'] in single:
                backup[name] = counter['count']
            else:
                backup[name] = {}
                for k, v in counts.iteritems():
                    if v in counter:
                        backup[name][k] = counter[v]
                    else:
                        backup[name][k] = 0
        if 'start' in backup and 'end' in backup:
            backup['duration'] = backup['end'] - backup['start']

        return backup

    def _parse_backup_log(self, fh, number, client=None, agent=None):
        """
        parse_backup_log parses the log.gz of a given backup and returns a dict
        containing different stats used to render the charts in the reporting view
        """
        return {}

    # def get_clients_report(self, clients, agent=None):

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
        clients = self.status('c:{0}\n'.format(name))
        # check the status returned something
        if not clients:
            return r

        clients = clients['clients']
        # check there are at least one client
        if not clients:
            return r

        client = clients[0]
        # check the client is currently backing-up
        if client['run_status'] != 'running':
            return r

        backup = None
        for b in client['backups']:
            if 'flags' in b and 'working' in b['flags']:
                backup = b
                break
        # check we found a working backup
        if not backup:
            return r

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
                r[name] = [counter['count'], counter['changed'], counter['same'], counter['deleted'], counter['scanned']]
            else:
                r[name] = counter['count']

        if 'bytes' not in r:
            r['bytes'] = 0
        if r.viewkeys() & {'time_start', 'estimated_bytes', 'bytes'}:
            diff = time.time() - int(r['time_start'])
            byteswant = int(r['estimated_bytes'])
            bytesgot = int(r['bytes'])
            bytespersec = bytesgot / diff
            bytesleft = byteswant - bytesgot
            r['speed'] = bytespersec
            if (bytespersec > 0):
                timeleft = int(bytesleft / bytespersec)
                r['timeleft'] = timeleft
            else:
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
            query = self.status('c:{0}\n'.format(name))
        except BUIserverException:
            return False
        if not query:
            return False
        clients = query['clients']
        if not clients:
            return False
        client = clients[0]
        if client['run_status'] in ['running']:
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
            if c['state'] in ['running']:
                r.append(c['name'])
        self.running = r
        return r

    def _status_human_readable(self, status):
        if not status:
            return None
        if status == 'c crashed':
            return 'client crashed'
        if status == 's crashed':
            return 'server crashed'
        return status

    def get_all_clients(self, agent=None):
        """
        get_all_clients returns a list of dict representing each clients with their
        name, state and last backup date
        """
        j = []
        query = self.status()
        if not query or 'clients' not in query:
            return j
        clients = query['clients']
        for cl in clients:
            c = {}
            c['name'] = cl['name']
            c['state'] = self._status_human_readable(cl['run_status'])
            infos = cl['backups']
            if c['state'] in ['running']:
                c['last'] = 'now'
            elif not infos:
                c['last'] = 'never'
            else:
                infos = infos[0]
                c['last'] = datetime.datetime.fromtimestamp(infos['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
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
        query = self.status('c:{0}\n'.format(c))
        if not query:
            return r
        clients = query['clients']
        if not clients:
            return r
        client = clients[0]
        backups = client['backups']
        for backup in backups:
            ba = {}
            if 'flags' in backup and 'working' in backup['flags']:
                continue
            ba['number'] = backup['number']
            if 'flags' in backup and 'deletable' in backup['flags']:
                ba['deletable'] = True
            else:
                ba['deletable'] = False
            ba['date'] = datetime.datetime.fromtimestamp(backup['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            log = self.get_backup_logs(backup['number'], name)
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

        result = self.status('c:{0}:b:{1}:p:{2}\n'.format(name, backup, top))
        if not result:
            return r
        clients = result['clients']
        if not clients:
            return r
        client = clients[0]
        if 'backups' not in client:
            return r
        backups = client['backups']
        if not backups:
            return r
        backup = backups[0]
        for entry in backup['browse']['entries']:
            t = {}
            if entry['name'] == '.':
                continue
            else:
                t['name'] = entry['name']
            t['mode'] = self._human_st_mode(entry['mode'])
            if re.match('^(d|l)', t['mode']):
                t['type'] = 'd'
            else:
                t['type'] = 'f'
            t['inodes'] = entry['nlink']
            t['uid'] = entry['uid']
            t['gid'] = entry['gid']
            t['parent'] = top
            t['size'] = '{0:.1eM}'.format(_hr(entry['size']))
            t['date'] = datetime.datetime.fromtimestamp(entry['mtime']).strftime('%Y-%m-%d %H:%M:%S')
            r.append(t)
        return r

    # Same as in Burp1 backend
    # def restore_files(self, name=None, backup=None, files=None, strip=None, archive='zip', password=None, agent=None):

    # def read_conf_cli(self, agent=None):

    # def read_conf_srv(self, agent=None):

    # def store_conf_cli(self, data, agent=None):

    # def store_conf_srv(self, data, agent=None):

    # def get_parser_attr(self, attr=None, agent=None):
