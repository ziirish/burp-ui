#!/usr/bin/env python
# -*- coding: utf8 -*-
import ConfigParser
import logging
import sys
import os
import subprocess
import re
import socket
import time
import datetime
import collections
from flask import Flask, request, render_template, jsonify, redirect, url_for
from optparse import OptionParser

burpport = 4972
burphost = '127.0.0.1'
port = 5000
bind = '::'

"""
The following code is used to convert bytes to be human readable.
It was found on the Internet...
"""

import math
import string

# code from here: http://code.activestate.com/recipes/578323-human-readable-filememory-sizes-v2/
class _human_readable( long ):
    """ define a _human_readable class to allow custom formatting
        format specifiers supported : 
            em : formats the size as bits in IEC format i.e. 1024 bits (128 bytes) = 1Kib 
            eM : formats the size as Bytes in IEC format i.e. 1024 bytes = 1KiB
            sm : formats the size as bits in SI format i.e. 1000 bits = 1kb
            sM : formats the size as bytes in SI format i.e. 1000 bytes = 1KB
            cm : format the size as bit in the common format i.e. 1024 bits (128 bytes) = 1Kb
            cM : format the size as bytes in the common format i.e. 1024 bytes = 1KB
    """
    def __format__(self, fmt):
        # is it an empty format or not a special format for the size class
        if fmt == "" or fmt[-2:].lower() not in ["em","sm","cm"]:
            if fmt[-1].lower() in ['b','c','d','o','x','n','e','f','g','%']:
                # Numeric format.
                return long(self).__format__(fmt)
            else:
                return str(self).__format__(fmt)

        # work out the scale, suffix and base        
        factor, suffix = (8, "b") if fmt[-1] in string.lowercase else (1,"B")
        base = 1024 if fmt[-2] in ["e","c"] else 1000

        # Add the i for the IEC format
        suffix = "i"+ suffix if fmt[-2] == "e" else suffix

        mult = ["","K","M","G","T","P"]

        val = float(self) * factor
        i = 0 if val < 1 else int(math.log(val, base))+1
        v = val / math.pow(base,i)
        v,i = (v,i) if v > 0.5 else (v*base,i-1)

        # Identify if there is a width and extract it
        width = "" if fmt.find(".") == -1 else fmt[:fmt.index(".")]        
        precis = fmt[:-2] if width == "" else fmt[fmt.index("."):-2]

        # do the precision bit first, so width/alignment works with the suffix
        if float(self) == 0:
            return "{0:{1}f}".format(v, precis)
        t = ("{0:{1}f}"+mult[i]+suffix).format(v, precis) 

        return "{0:{1}}".format(t,width) if width != "" else t

"""
Now this is Burp-UI
"""

app = Flask(__name__)

status = {
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
        'files',
        'files_enc',
        'meta',
        'meta_enc',
        'dir',
        'softlink',
        'hardlink',
        'special',
        'efs',
        'vssheader',
        'vssheader_enc',
        'vssfooter',
        'vssfooter_enc',
        'total',
        'warning',
        'estimated_bytes',
        'bytes',
        'bytes_in',
        'bytes_out',
        'start',
        'path'
       ]

"""
Utilities functions
"""

def _burp_status(query='\n'):
    r = []
    try:
        socket.inet_aton(burphost)
        form = socket.AF_INET
    except socket.error:
        form = socket.AF_INET6
    try:
        if not query.endswith('\n'):
            q = '{0}\n'.format(query)
        else:
            q = query
        s = socket.socket(form, socket.SOCK_STREAM)
        s.connect((burphost, burpport))
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
        app.logger.error('Cannot contact burp server at %s:%s', burphost, burpport)
        return r

def _parse_backup_log(f, n):
    lookup_easy = {
            'start':    '^Start time: (.+)$',
            'end':      '^\s*End time: (.+)$',
            'duration': '^Time taken: (.+)$',
            'totsize':  '^\s*Bytes in backup: (\d+)',
            'received': '^\s*Bytes received: (\d+)'
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
    backup = { 'windows': False, 'number': n }
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
        for key, regex in lookup_easy.iteritems():
            r = re.search(regex, line)
            if r:
                found = True
                if key in ['start', 'end']:
                    backup[key] = int(time.mktime(datetime.datetime.strptime(r.group(1), '%Y-%m-%d %H:%M:%S').timetuple()))
                else:
                    backup[key] = r.group(1)
                break

        if found:
            continue

        for key, regex in lookup_complex.iteritems():
            r = re.search(regex, line)
            if r:
                app.logger.debug("match[1]: '{0}'".format(r.group(1)))
                sp = re.split('\s+', r.group(1))
                backup[key] = {
                        'new':       sp[0],
                        'changed':   sp[1],
                        'unchanged': sp[2],
                        'deleted':   sp[3],
                        'total':     sp[4],
                        'scanned':   r.group(2)
                        }
                break
    return backup

def _get_counters(name=None):
    r = {}
    if not name:
        return r
    f = _burp_status('c:{0}\n'.format(name))
    if not f:
        return r
    for line in f:
        app.logger.debug('line: {0}'.format(line))
        rs = re.search('^{0}\s+(\d)\s+(\w)\s+(.+)$'.format(name), line)
        if rs and rs.group(2) == 'r' and int(rs.group(1)) == 2:
            c = 0
            for v in rs.group(3).split('\t'):
                app.logger.debug('{0}: {1}'.format(counters[c], v))
                if c < 15:
                    r[counters[c]] = v.split('/')
                else:
                    r[counters[c]] = v
                c += 1
    diff = time.time() - int(r['start'])
    byteswant = int(r['estimated_bytes'])
    bytesgot = int(r['bytes_in'])
    bytespersec = bytesgot / diff
    bytesleft = byteswant - bytesgot
    if (bytespersec > 0):
        timeleft = int(bytesleft / bytespersec)
        r['timeleft'] = timeleft
    else:
        r['timeleft'] = -1
    return r

def _is_backup_running(name=None):
    if not name:
        return False
    f = _burp_status('c:{0}\n'.format(name))
    for line in f:
        r = re.search('^{0}\s+\d\s+(\w)'.format(name), line)
        if r and r.group(1) not in [ 'i', 'c', 'C' ]:
            return True
    return False

def _is_one_backup_running():
    r = []
    for c in _get_all_clients():
        if _is_backup_running(c['name']):
            r.append(c['name'])
    return r

def _get_all_clients():
    j = []
    f = _burp_status()
    for line in f:
        app.logger.debug("line: '{0}'".format(line))
        regex = re.compile("\s*(\w+)\s+\d\s+(\w)\s+(.+)")
        m = regex.search(line)
        c = {}
        c['name'] = m.group(1)
        c['state'] = status[m.group(2)]
        infos = m.group(3)
        app.logger.debug("infos: '{0}'".format(infos))
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

def _get_client(name=None):
    """
    _get_client returns a list of dict representing the backups (with its number
    and date) of a given client
    """
    r = []
    if not name:
        return r
    c = name
    f = _burp_status('c:{0}\n'.format(c))
    for line in f:
        if not re.match('^{0}\t'.format(c), line):
            continue
        app.logger.debug("line: '{0}'".format(line))
        regex = re.compile("\s*(\w+)\s+\d\s+(\w)\s+(.+)")
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

def _get_tree(name=None, backup=None, root=None):
    """
    _get_tree returns a list of dict representing files/dir (with their attr)
    within a given path
    """
    r = []
    if not name or not backup:
        return r
    if not root:
        top = ''
    else:
        top = root.encode('utf-8')

    f = _burp_status('c:{0}:b:{1}:p:{2}\n'.format(name, backup, top))
    useful = False
    for line in f:
        app.logger.debug("line: '{0}'".format(line))
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
                t['size'] = '{0:.1eM}'.format(_human_readable(sp[4]))
                t['date'] = '{0} {1}'.format(sp[5], sp[6])
                t['name'] = sp[len(sp)-1]
                t['parent'] = top
                r.append(t)
    return r

"""
Here is the API
"""

@app.route('/api/live.json')
def live():
    """
    WebServer: return the live status of the server
    """
    r = []
    for c in _is_one_backup_running():
        s = {}
        s['client'] = c
        s['status'] = _get_counters(c)
        r.append(s)
    return jsonify(results=r)

@app.route('/api/running.json')
def backup_running():
    """
    WebService: return true if at least one backup is running
    """
    j = _is_one_backup_running()
    r = len(j) > 0
    return jsonify(results=r)

@app.route('/api/client-tree.json/<name>/<int:backup>', methods=['GET'])
def client_tree(name=None, backup=None):
    """
    WebService: return a specific client files tree
    """
    j = []
    if not name or not backup:
        return jsonify(results=j)
    root = request.args.get('root')
    j = _get_tree(name, backup, root)
    return jsonify(results=j)

@app.route('/api/client-stat.json/<name>')
@app.route('/api/client-stat.json/<name>/<int:backup>')
def client_stat_json(name=None, backup=None):
    """
    WebService: return a specific client detailed report
    """
    j = []
    if not name:
        return jsonify(results=j)
    if backup:
        f = _burp_status('c:{0}:b:{1}:f:log.gz\n'.format(name, backup))
        j = _parse_backup_log(f, backup)
    else:
        for c in _get_client(name):
            f =  _burp_status('c:{0}:b:{1}:f:log.gz\n'.format(name, c['number']))
            j.append(_parse_backup_log(f, c['number']))
    return jsonify(results=j)

@app.route('/api/client.json/<name>')
def client_json(name=None):
    """
    WebService: return a specific client backups overview
    """
    j = _get_client(name)
    return jsonify(results=j)

@app.route('/api/clients.json')
def clients():
    """
    WebService: return a JSON listing all clients
    """
    j = _get_all_clients()
    return jsonify(results=j)

"""
Here is a custom filter
"""
@app.template_filter()
def mypad (s):
    """
    Filter: used to pad 0's to backup numbers as in the burp's status monitor
    """
    return '{0:07d}'.format(int(s))

"""
And here is the main site
"""

@app.route('/client-browse/<name>', methods=['GET'])
def client_browse(name=None):
    """
    Browse a specific backup of a specific client
    """
    return render_template('client-browse.html', tree=True, backup=True, overview=True, cname=name, nbackup=request.args.get('backup'))

@app.route('/client-report/<name>')
def client_report(name=None):
    """
    Specific client report
    """
    l = _get_client(name)
    if len(l) == 1:
        return redirect(url_for('backup_report', name=name, backup=l[0]['number']))
    return render_template('client-report.html', client=True, report=True, cname=name)

@app.route('/backup-report/<name>', methods=['GET'])
@app.route('/backup-report/<name>/<int:backup>', methods=['GET'])
def backup_report(name=None, backup=None):
    """
    Backup specific report
    """
    if not backup:
        backup = request.args.get('backup')
    return render_template('backup-report.html', client=True, backup=True, report=True, cname=name, nbackup=backup)

@app.route('/client', methods=['GET'])
@app.route('/client/<name>')
def client(name=None):
    """
    Specific client overview
    """
    if name:
        c = name
    else:
        c = request.args.get('name')
#    if _is_backup_running(c):
#        return redirect(url_for('live_status', name=name))
    return render_template('client.html', client=True, overview=True, cname=c)

@app.route("/")
def home():
    """
    Home page
    """
    return render_template('clients.html', clients=True, overview=True)

if __name__ == "__main__":
    """
    Main function
    """
    parser = OptionParser()
    parser.add_option('-v', '--verbose', dest='log', help='verbose output', action='store_true')
    parser.add_option('-c', '--config', dest='config', help='configuration file', metavar='CONFIG')

    (options, args) = parser.parse_args()
    d = options.log

    if options.config:
        conf = options.config
    else:
        conf = '{0}/burpui.cfg'.format(os.path.dirname(os.path.realpath(__file__)))

    config = ConfigParser.ConfigParser({'bport': burpport, 'bhost': burphost, 'port': port, 'bind': bind})
    with open(conf) as fp:
        config.readfp(fp)
        burpport = config.getint('Global', 'bport')
        burphost = config.get('Global', 'bhost')
        port = config.getint('Global', 'port')
        bind = config.get('Global', 'bind')

    app.logger.info('burp port: %s', burpport)
    app.logger.info('burp host: %s', burphost)
    app.logger.info('listen port: %s', port)
    app.logger.info('bind addr: %s', bind)

    app.run(host=bind, port=port, debug=d)
