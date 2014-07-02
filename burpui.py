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
from flask import Flask, request, render_template, jsonify, redirect, url_for, abort, flash
from optparse import OptionParser

burpport = 4972
burphost = '127.0.0.1'
port = 5000
bind = '::'
refresh = 15
ssl = False
sslcert = ''
sslkey = ''
sslcontext = None
conf = None

running = []

"""
Now this is Burp-UI
"""

app = Flask(__name__)
app.config['CFG'] = os.path.join(app.root_path, 'burpui.cfg')
app.secret_key = 'VpgOXNXAgcO81xFPyWj07ppN6kExNZeCDRShseNzFKV7ZCgmW2/eLn6xSlt7pYAVBj12zx2Vv9Kw3Q3jd1266A=='
app.jinja_env.globals.update(isinstance=isinstance,list=list)

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
Utilities functions
"""

def _burp_status(query='\n'):
    """
    _burp_status connects to the burp status port, ask the given 'question' and
    parses the output in an array
    """
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

def _parse_backup_log(f, n, c=None):
    """
    _parse_backup_log parses the log.gz of a given backup and returns a dict
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
                    while i < 3:
                        fields[i] = 0
                        i += 1
                    seconds = 0
                    seconds += fields[0]
                    seconds += fields[1] * 60
                    seconds += fields[2] * (60 * 60)
                    seconds += fields[3] * (60 * 60 * 24)
                    backup[key] = seconds
                else:
                    backup[key] = int(r.group(1))
                break

        if found:
            continue

        for key, regex in lookup_complex.iteritems():
            r = re.search(regex, line)
            if r:
                app.logger.debug("match[1]: '{0}'".format(r.group(1)))
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

def _get_counters(name=None):
    """
    _get_counters parses the stats of the live status for a given client and
    returns a dict
    """
    r = {}
    if not name or name not in running:
        return r
    f = _burp_status('c:{0}\n'.format(name))
    if not f:
        return r
    for line in f:
        app.logger.debug('line: {0}'.format(line))
        rs = re.search('^{0}\s+(\d)\s+(\S)\s+(.+)$'.format(name), line)
        if rs and rs.group(2) == 'r' and int(rs.group(1)) == 2:
            c = 0
            for v in rs.group(3).split('\t'):
                app.logger.debug('{0}: {1}'.format(counters[c], v))
                if c > 0 and c < 15:
                    val = map(int, v.split('/'))
                    if val[0] > 0 or val[1] > 0 or val[2] or val[3] > 0:
                        r[counters[c]] = val
                else:
                    if 'path' == counters[c]:
                        r[counters[c]] = v.encode('utf-8')
                    else:
                        r[counters[c]] = int(v)
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

def _is_backup_running(name=None):
    """
    _is_backup_running returns True if the given client is currently running a
    backup
    """
    if not name:
        return False
    f = _burp_status('c:{0}\n'.format(name))
    for line in f:
        r = re.search('^{0}\s+\d\s+(\S)'.format(name), line)
        if r and r.group(1) not in [ 'i', 'c', 'C' ]:
            return True
    return False

def _is_one_backup_running():
    """
    _is_one_backup_running returns a list of clients name that are currently
    running a backup
    """
    global running
    r = []
    for c in _get_all_clients():
        if _is_backup_running(c['name']):
            r.append(c['name'])
    running = r
    return r

def _get_all_clients():
    """
    _get_all_clients returns a list of dict representing each clients with their
    name, state and last backup date
    """
    j = []
    f = _burp_status()
    for line in f:
        app.logger.debug("line: '{0}'".format(line))
        regex = re.compile('\s*(\S+)\s+\d\s+(\S)\s+(.+)')
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

@app.route('/api/running-clients.json')
def running_clients():
    """
    WebServer: return a list of running clients
    """
    r = _is_one_backup_running()
    return jsonify(results=r)

@app.route('/api/render-live-template', methods=['GET'])
@app.route('/api/render-live-template/<name>')
def render_live_tpl(name=None):
    c = request.args.get('name')
    if not name and not c:
        abort(500)
    if not name:
        name = c
    if name not in running:
        abort(404)
    counters = _get_counters(name)
    return render_template('live-monitor-template.html', cname=name, counters=counters)

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

@app.route('/api/clients-report.json')
def clients_report_json():
    """
    WebService: return a JSON with global stats
    """
    j = []
    clients = _get_all_clients()
    cl = []
    ba = []
    for c in clients:
        client = _get_client(c['name'])
        if not client:
            continue
        f = _burp_status('c:{0}:b:{1}:f:log.gz\n'.format(c['name'], client[-1]['number']))
        cl.append( { 'name': c['name'], 'stats': _parse_backup_log(f, client[-1]['number']) } )
        for b in client:
            f = _burp_status('c:{0}:b:{1}:f:log.gz\n'.format(c['name'], b['number']))
            ba.append(_parse_backup_log(f, b['number'], c['name']))
    j.append( { 'clients': cl, 'backups': sorted(ba, key=lambda k: k['end']) } )
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
    if not s:
        return '0000000'
    return '{0:07d}'.format(int(s))

@app.template_filter()
def time_human(d):
    s = ''
    seconds = (((d % 31536000) % 86400) % 3600) % 60
    minutes = math.floor((((d % 31536000) % 86400) % 3600) / 60)
    hours   = math.floor(((d % 31536000) % 86400) / 3600)
    if hours > 0:
        s = '%02dH' % hours
    return '%s %02dm %02ds' % (s, minutes, seconds)

@app.template_filter()
def bytes_human(b):
    return '{0:.1eM}'.format(_human_readable(b))

"""
And here is the main site
"""

@app.route('/live-monitor')
@app.route('/live-monitor/<name>')
def live_monitor(name=None):
    """
    Live status monitor view
    """
    if not running:
        flash('Sorry, there are no running backups')
        return redirect(url_for('home'))
    return render_template('live-monitor.html', live=True, cname=name)

@app.route('/client-browse/<name>', methods=['GET'])
@app.route('/client-browse/<name>/<int:backup>')
def client_browse(name=None, backup=None):
    """
    Browse a specific backup of a specific client
    """
    bkp = request.args.get('backup')
    if bkp and not backup:
        return redirect(url_for('client_browse', name=name, backup=bkp))
    return render_template('client-browse.html', tree=True, backup=True, overview=True, cname=name, nbackup=backup)

@app.route('/client-report/<name>')
def client_report(name=None):
    """
    Specific client report
    """
    l = _get_client(name)
    if len(l) == 1:
        return redirect(url_for('backup_report', name=name, backup=l[0]['number']))
    return render_template('client-report.html', client=True, report=True, cname=name)

@app.route('/clients-report')
def clients_report():
    """
    Global report
    """
    return render_template('clients-report.html', clients=True, report=True)

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
    if _is_backup_running(c):
        return redirect(url_for('live_monitor', name=name))
    return render_template('client.html', client=True, overview=True, cname=c)

@app.route('/')
def home():
    """
    Home page
    """
    return render_template('clients.html', clients=True, overview=True)

def init(conf=None):
    global burpport, burphost, port, bind, refresh, ssl, sslcert, sslkey
    if not conf:
        conf = app.config['CFG']

    config = ConfigParser.ConfigParser({'bport': burpport, 'bhost': burphost, 'port': port, 'bind': bind, 'refresh': refresh, 'ssl': ssl, 'sslcert': sslcert, 'sslkey': sslkey})
    with open(conf) as fp:
        config.readfp(fp)
        burpport = config.getint('Global', 'bport')
        burphost = config.get('Global', 'bhost')
        port = config.getint('Global', 'port')
        bind = config.get('Global', 'bind')
        try:
            ssl = config.getboolean('Global', 'ssl')
        except ValueError:
            app.logger.error("Wrong value for 'ssl' key! Assuming 'false'")
            ssl = False
        sslcert = config.get('Global', 'sslcert')
        sslkey = config.get('Global', 'sslkey')

        app.config['REFRESH'] = config.getint('UI', 'refresh')

    app.logger.info('burp port: %d', burpport)
    app.logger.info('burp host: %s', burphost)
    app.logger.info('listen port: %d', port)
    app.logger.info('bind addr: %s', bind)
    app.logger.info('use ssl: %s', ssl)
    app.logger.info('sslcert: %s', sslcert)
    app.logger.info('sslkey: %s', sslkey)
    app.logger.info('refresh: %d', refresh)

if __name__ == '__main__':
    """
    Main function
    """
    parser = OptionParser()
    parser.add_option('-v', '--verbose', dest='log', help='verbose output', action='store_true')
    parser.add_option('-c', '--config', dest='config', help='configuration file', metavar='CONFIG')

    (options, args) = parser.parse_args()
    d = options.log
    app.config['DEBUG'] = d

    if options.config:
        conf = options.config
    else:
        conf = app.config['CFG']

    init(conf)

    if ssl:
        from OpenSSL import SSL
        sslcontext = SSL.Context(SSL.SSLv23_METHOD)
        sslcontext.use_privatekey_file(sslkey)
        sslcontext.use_certificate_file(sslcert)

    if sslcontext:
        app.run(host=bind, port=port, debug=d, ssl_context=sslcontext)
    else:
        app.run(host=bind, port=port, debug=d)
