# -*- coding: utf8 -*-
import re
import os
import socket
import time
import json
import datetime
import ConfigParser
import shutil
import subprocess
import zipfile

from burpui.misc.utils import human_readable as _hr
from burpui.misc.backend.interface import BUIbackend, BUIserverException

g_burpport = 4972
g_burphost = '127.0.0.1'
g_tmpdir   = '/tmp/buirestore'
g_burpbin  = '/usr/sbin/burp'
g_stripbin = '/usr/sbin/vss_strip'

class Burp(BUIbackend):
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

    def __init__(self, app=None, conf=None):
        global g_burpport, g_burphost, g_tmpdir, g_burpbin, g_stripbin
        self.app = app
        self.host = g_burphost
        self.port = g_burpport
        self.burpbin = g_burpbin
        self.stripbin = g_stripbin
        self.tmpdir = g_tmpdir
        self.running = []
        if conf:
            config = ConfigParser.ConfigParser({'bport': g_burpport, 'bhost': g_burphost, 'tmpdir': g_tmpdir, 'burpbin': g_burpbin, 'stripbin': g_stripbin})
            with open(conf) as fp:
                config.readfp(fp)
                try:
                    self.port = config.getint('Burp1', 'bport')
                    self.host = config.get('Burp1', 'bhost')
                    tdir = config.get('Burp1', 'tmpdir')
                    bbin = config.get('Burp1', 'burpbin')
                    strip = config.get('Burp1', 'stripbin')

                    if self.host not in ['127.0.0.1', '::1']:
                        self.logger('warning', "Invalid value for 'bhost'. Must be '127.0.0.1' or '::1'. Falling back to '%s'", g_burphost)
                        self.host = g_burphost

                    if not strip.startswith('/'):
                        self.logger('warning', "Please provide an absolute path for the 'stripbin' option. Fallback to '%s'", g_stripbin)
                        strip = g_stripbin
                    elif not re.match('^\S+$', strip):
                        self.logger('warning', "Incorrect value for the 'stripbin' option. Fallback to '%s'", g_stripbin)
                        strip = g_stripbin
                    elif not os.path.isfile(strip) or not os.access(strip, os.X_OK):
                        self.logger('warning', "'%s' does not exist or is not executable. Fallback to '%s'", strip, g_stripbin)
                        strip = g_stripbin
                        
                    if not bbin.startswith('/'):
                        self.logger('warning', "Please provide an absolute path for the 'burpbin' option. Fallback to '%s'", g_burpbin)
                        bbin = g_burpbin
                    elif not re.match('^\S+$', bbin):
                        self.logger('warning', "Incorrect value for the 'burpbin' option. Fallback to '%s'", g_burpbin)
                        bbin = g_burpbin
                    elif not os.path.isfile(bbin) or not os.access(bbin, os.X_OK):
                        self.logger('warning', "'%s' does not exist or is not executable. Fallback to '%s'", bbin, g_burpbin)
                        bbin = g_burpbin

                    if not tdir.startswith('/'):
                        self.logger('warning', "Please provide an absolute path for the 'tmpdir' option. Fallback to '%s'", g_tmpdir)
                        tdir = g_tmpdir
                    elif not re.match('^\S+$', tdir):
                        self.logger('warning', "Incorrect value for the 'tmpdir' option. Fallback to '%s'", g_tmpdir)
                        tdir = g_tmpdir
                    elif os.path.isdir(tdir) and os.listdir(tdir) and not self.app.config.get('TESTING'):
                        raise Exception("'{0}' is not empty!".format(tdir))
                    elif os.path.isdir(tdir) and not os.access(tdir, os.W_OK|os.X_OK):
                        self.logger('warning', "'%s' is not writable. Fallback to '%s'", tdir, g_tmpdir)
                        tdir = g_tmpdir

                    self.burpbin = bbin
                    self.tmpdir = tdir
                    self.stripbin = strip
                except ConfigParser.NoOptionError, e:
                    self.logger('error', str(e))
                except ConfigParser.NoSectionError, e:
                    self.logger('error', str(e))

        self.logger('info', 'burp port: %d', self.port)
        self.logger('info', 'burp host: %s', self.host)
        self.logger('info', 'burp binary: %s', self.burpbin)
        self.logger('info', 'strip binary: %s', self.stripbin)
        self.logger('info', 'temporary dir: %s', self.tmpdir)

    def logger(self, level, *args):
        if self.app:
            logs = {
                'info': self.app.logger.info,
                'error': self.app.logger.error,
                'debug': self.app.logger.debug,
                'warning': self.app.logger.warning
            }
            if level in logs:
                logs[level](*args)
    """
    Utilities functions
    """

    def status(self, query='\n'):
        """
        status connects to the burp status port, ask the given 'question' and
        parses the output in an array
        """
        r = []
        try:
            socket.inet_aton(self.host)
            form = socket.AF_INET
        except socket.error:
            form = socket.AF_INET6
        try:
            if not query.endswith('\n'):
                q = '{0}\n'.format(query)
            else:
                q = query
            s = socket.socket(form, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.send(q)
            s.shutdown(socket.SHUT_WR)
            f = s.makefile()
            s.close()
            for l in f.readlines():
                line = l.rstrip('\n')
                if not line:
                    continue
                r.append(line)
            f.close()
            return r
        except socket.error:
            self.logger('error', 'Cannot contact burp server at %s:%s', self.host, self.port)
            raise BUIserverException('Cannot contact burp server at {0}:{1}'.format(self.host, self.port))

    def parse_backup_log(self, f, n, c=None):
        """
        parse_backup_log parses the log.gz of a given backup and returns a dict
        containing different stats used to render the charts in the reporting view
        """
        lookup_easy = {
                'start':    '^Start time: (.+)$',
                'end':      '^\s*End time: (.+)$',
                'duration': '^Time taken: (.+)$',
                'totsize':  '^\s*Bytes in backup:\s+(\d+)',
                'received': '^\s*Bytes received:\s+(\d+)'
                }
        lookup_complex = {
                'files':         '^\s*Files:\s+(.+)\s+\|\s+(\d+)$',
                'files_enc':     '^\s*Files \(encrypted\):\s+(.+)\s+\|\s+(\d+)$',
                'dir':           '^\s*Directories:\s+(.+)\s+\|\s+(\d+)$',
                'softlink':      '^\s*Soft links:\s+(.+)\s+\|\s+(\d+)$',
                'hardlink':      '^\s*Hard links:\s+(.+)\s+\|\s+(\d+)$',
                'meta':          '^\s*Meta data:\s+(.+)\s+\|\s+(\d+)$',
                'meta_enc':      '^\s*Meta data\(enc\):\s+(.+)\s+\|\s+(\d+)$',
                'special':       '^\s*Special files:\s+(.+)\s+\|\s+(\d+)$',
                'efs':           '^\s*EFS files:\s+(.+)\s+\|\s+(\d+)$',
                'vssheader':     '^\s*VSS headers:\s+(.+)\s+\|\s+(\d+)$',
                'vssheader_enc': '^\s*VSS headers \(enc\):\s+(.+)\s+\|\s+(\d+)$',
                'vssfooter':     '^\s*VSS footers:\s+(.+)\s+\|\s+(\d+)$',
                'vssfooter_enc': '^\s*VSS footers \(enc\):\s+(.+)\s+\|\s+(\d+)$',
                'total':         '^\s*Grand total:\s+(.+)\s+\|\s+(\d+)$'
                }
        backup = { 'windows': False, 'number': int(n) }
        if c is not None:
            backup['name'] = c 
        useful = False
        for line in f:
            if re.match('^\d{4}-\d{2}-\d{2} (\d{2}:){3} \w+\[\d+\] Client is Windows$', line):
                backup['windows'] = True
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
                    self.logger('debug', "match[1]: '{0}'".format(r.group(1)))
                    sp = re.split('\s+', r.group(1))
                    backup[key] = {
                            'new':       int(sp[0]),
                            'changed':   int(sp[1]),
                            'unchanged': int(sp[2]),
                            'deleted':   int(sp[3]),
                            'total':     int(sp[4]),
                            'scanned':   int(r.group(2))
                            }
                    break
        return backup

    def get_counters(self, name=None):
        """
        get_counters parses the stats of the live status for a given client and
        returns a dict
        """
        r = {}
        if not name or name not in self.running:
            return r
        f = self.status('c:{0}\n'.format(name))
        if not f:
            return r
        for line in f:
            self.logger('debug', 'line: {0}'.format(line))
            rs = re.search('^{0}\s+(\d)\s+(\S)\s+(.+)$'.format(name), line)
            if rs and rs.group(2) == 'r' and int(rs.group(1)) == 2:
                c = 0
                for v in rs.group(3).split('\t'):
                    self.logger('debug', '{0}: {1}'.format(self.counters[c], v))
                    if c > 0 and c < 15:
                        val = map(int, v.split('/'))
                        if val[0] > 0 or val[1] > 0 or val[2] or val[3] > 0:
                            r[self.counters[c]] = val
                    else:
                        if 'path' == self.counters[c]:
                            r[self.counters[c]] = v.encode('utf-8')
                        else:
                            r[self.counters[c]] = int(v)
                    c += 1
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
        return r

    def is_backup_running(self, name=None):
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
            if r and r.group(1) not in [ 'i', 'c', 'C' ]:
                return True
        return False

    def is_one_backup_running(self):
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

    def get_all_clients(self):
        """
        get_all_clients returns a list of dict representing each clients with their
        name, state and last backup date
        """
        j = []
        f = self.status()
        for line in f:
            self.logger('debug', "line: '{0}'".format(line))
            regex = re.compile('\s*(\S+)\s+\d\s+(\S)\s+(.+)')
            m = regex.search(line)
            c = {}
            c['name'] = m.group(1)
            c['state'] = self.states[m.group(2)]
            infos = m.group(3)
            self.logger('debug', "infos: '{0}'".format(infos))
            if infos == "0":
                c['last'] = 'never'
            elif re.match('^\d+\s\d+\s\d+$', infos):
                sp = infos.split()
                c['last'] = datetime.datetime.fromtimestamp(int(sp[2])).strftime('%Y-%m-%d %H:%M:%S')
            else:
                sp = infos.split('\t')
                c['last'] = datetime.datetime.fromtimestamp(int(sp[len(sp)-2])).strftime('%Y-%m-%d %H:%M:%S')
            j.append(c)
        return j

    def get_client(self, name=None):
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
            self.logger('debug', "line: '{0}'".format(line))
            regex = re.compile('\s*(\S+)\s+\d\s+(\S)\s+(.+)')
            m = regex.search(line)
            if m.group(3) == "0" or m.group(2) not in [ 'i', 'c', 'C' ]:
                continue
            backups = m.group(3).split('\t')
            for b in backups:
                ba = {}
                sp = b.split()
                ba['number'] = sp[0]
                ba['date'] = datetime.datetime.fromtimestamp(int(sp[2])).strftime('%Y-%m-%d %H:%M:%S')
                r.append(ba)
        # Here we need to reverse the array so the backups are sorted by date ASC
        r.reverse()
        return r

    def get_tree(self, name=None, backup=None, root=None):
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
            top = root.encode('utf-8')

        f = self.status('c:{0}:b:{1}:p:{2}\n'.format(name, backup, top))
        useful = False
        for line in f:
            self.logger('debug', "line: '{0}'".format(line))
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
                    if re.match('^d', m.group(1)):
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

    def restore_files(self, name=None, backup=None, files=None):
        if not name or not backup or not files:
            return None
        flist = json.loads(files)
        if 'restore' not in flist:
            return None
        if os.path.isdir(self.tmpdir):
            shutil.rmtree(self.tmpdir)
        for r in flist['restore']:
            reg = ''
            if r['folder'] and r['key'] != '/':
                reg = r['key']+'/'
            else:
                reg = r['key']
            status = subprocess.call([self.burpbin, '-C', name, '-a', 'r', '-b', str(backup), '-r', reg, '-d', self.tmpdir])
            if status != 0:
                return None

        zip_dir = self.tmpdir.rstrip(os.sep)
        zip_file = zip_dir+'.zip'
        if os.path.isfile(zip_file):
            os.remove(zip_file)
        zip_len = len(zip_dir) + 1
        stripping = True
        with zipfile.ZipFile(zip_file, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            for dirname, subdirs, files in os.walk(zip_dir):
                for filename in files:
                    path = os.path.join(dirname, filename)
                    if stripping and os.path.isfile(path):
                        self.logger('debug', "stripping file: %s", path)
                        shutil.move(path, path+'.tmp')
                        status = subprocess.call([self.stripbin, '-i', path+'.tmp', '-o', path])
                        if status != 0:
                            os.remove(path)
                            shutil.move(path+'.tmp', path)
                            stripping = False
                            self.logger('debug', "Disable stripping since this file does not seem to embed VSS headers")
                        else:
                            os.remove(path+'.tmp')

                    entry = path[zip_len:]
                    zf.write(path, entry)

        shutil.rmtree(self.tmpdir)
        return zip_file

