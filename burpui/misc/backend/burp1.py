# -*- coding: utf8 -*-
import re
import socket
import time
import datetime

from burpui.misc.utils import human_readable as _hr
from burpui.misc.backend.interface import BUIbackend

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

    def __init__(self, app=None, host='127.0.0.1', port=4972):
        self.app = app
        self.host = host
        self.port = port
        self.running = []

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
            self.app.logger.error('Cannot contact burp server at %s:%s', self.host, self.port)
            return r

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
                    self.app.logger.debug("match[1]: '{0}'".format(r.group(1)))
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
        if not name or name not in running:
            return r
        f = self.status('c:{0}\n'.format(name))
        if not f:
            return r
        for line in f:
            self.app.logger.debug('line: {0}'.format(line))
            rs = re.search('^{0}\s+(\d)\s+(\S)\s+(.+)$'.format(name), line)
            if rs and rs.group(2) == 'r' and int(rs.group(1)) == 2:
                c = 0
                for v in rs.group(3).split('\t'):
                    self.app.logger.debug('{0}: {1}'.format(self.counters[c], v))
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
        f = self.status('c:{0}\n'.format(name))
        for line in f:
            r = re.search('^{0}\s+\d\s+(\S)'.format(name), line)
            if r and r.group(1) not in [ 'i', 'c', 'C' ]:
                return True
        return False

    def is_one_backup_running(self):
        """
        is_one_backup_running returns a list of clients name that are currently
        running a backup
        """
        r = []
        for c in self.get_all_clients():
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
            self.app.logger.debug("line: '{0}'".format(line))
            regex = re.compile('\s*(\S+)\s+\d\s+(\S)\s+(.+)')
            m = regex.search(line)
            c = {}
            c['name'] = m.group(1)
            c['state'] = self.states[m.group(2)]
            infos = m.group(3)
            self.app.logger.debug("infos: '{0}'".format(infos))
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
            self.app.logger.debug("line: '{0}'".format(line))
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
            self.app.logger.debug("line: '{0}'".format(line))
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
                    sp = re.split('\s+', line)
                    t['mode'] = sp[0]
                    t['inodes'] = sp[1]
                    t['uid'] = sp[2]
                    t['gid'] = sp[3]
                    t['size'] = '{0:.1eM}'.format(_hr(sp[4]))
                    t['date'] = '{0} {1}'.format(sp[5], sp[6])
                    t['name'] = sp[len(sp)-1]
                    t['parent'] = top
                    r.append(t)
        return r
