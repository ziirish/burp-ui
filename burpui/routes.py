# -*- coding: utf8 -*-
import math

from flask import Flask, request, render_template, jsonify, redirect, url_for, abort, flash, g, session
from flask.ext.login import login_user, login_required, logout_user, current_user

from burpui import app, bui, login_manager
from burpui.forms import LoginForm
from burpui.misc.utils import human_readable as _hr

@login_manager.user_loader
def load_user(userid):
    return bui.uhandler.user(userid)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = bui.uhandler.user(form.username.data)
        app.logger.info('%s active: %s', form.username.data, user.active)
        if user.active and user.login(form.username.data, passwd=form.password.data):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('test_login'))
    return render_template('login.html', form=form, login=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/test_login')
@login_required
def test_login():
    return render_template('test-login.html', login=True, user=current_user.name)

"""
Here is the API
"""

@app.route('/api/running-clients.json')
def running_clients():
    """
    WebServer: return a list of running clients
    """
    r = bui.cli.is_one_backup_running()
    return jsonify(results=r)

@app.route('/api/render-live-template', methods=['GET'])
@app.route('/api/render-live-template/<name>')
def render_live_tpl(name=None):
    c = request.args.get('name')
    if not name and not c:
        abort(500)
    if not name:
        name = c
    if name not in bui.cli.running:
        abort(404)
    counters = bui.cli.get_counters(name)
    return render_template('live-monitor-template.html', cname=name, counters=counters)

@app.route('/api/live.json')
def live():
    """
    WebServer: return the live status of the server
    """
    r = []
    for c in bui.cli.is_one_backup_running():
        s = {}
        s['client'] = c
        s['status'] = bui.cli.get_counters(c)
        r.append(s)
    return jsonify(results=r)

@app.route('/api/running.json')
def backup_running():
    """
    WebService: return true if at least one backup is running
    """
    j = bui.cli.is_one_backup_running()
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
    j = bui.cli.get_tree(name, backup, root)
    return jsonify(results=j)

@app.route('/api/clients-report.json')
def clients_report_json():
    """
    WebService: return a JSON with global stats
    """
    j = []
    clients = bui.cli.get_all_clients()
    cl = []
    ba = []
    for c in clients:
        client = bui.cli.get_client(c['name'])
        if not client:
            continue
        f = bui.cli.status('c:{0}:b:{1}:f:log.gz\n'.format(c['name'], client[-1]['number']))
        cl.append( { 'name': c['name'], 'stats': bui.cli.parse_backup_log(f, client[-1]['number']) } )
        for b in client:
            f = bui.cli.status('c:{0}:b:{1}:f:log.gz\n'.format(c['name'], b['number']))
            ba.append(bui.cli.parse_backup_log(f, b['number'], c['name']))
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
        f = bui.cli.status('c:{0}:b:{1}:f:log.gz\n'.format(name, backup))
        j = bui.cli.parse_backup_log(f, backup)
    else:
        for c in bui.cli.get_client(name):
            f =  bui.cli.status('c:{0}:b:{1}:f:log.gz\n'.format(name, c['number']))
            j.append(bui.cli.parse_backup_log(f, c['number']))
    return jsonify(results=j)

@app.route('/api/client.json/<name>')
def client_json(name=None):
    """
    WebService: return a specific client backups overview
    """
    j = bui.cli.get_client(name)
    return jsonify(results=j)

@app.route('/api/clients.json')
def clients():
    """
    WebService: return a JSON listing all clients
    """
    j = bui.cli.get_all_clients()
    return jsonify(results=j)

"""
Here are some custom filters
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
    return '{0:.1eM}'.format(_hr(b))

"""
And here is the main site
"""

@app.route('/live-monitor')
@app.route('/live-monitor/<name>')
def live_monitor(name=None):
    """
    Live status monitor view
    """
    if not bui.cli.running:
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
    l = bui.cli.get_client(name)
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
    if bui.cli.is_backup_running(c):
        return redirect(url_for('live_monitor', name=name))
    return render_template('client.html', client=True, overview=True, cname=c)

@app.route('/')
def home():
    """
    Home page
    """
    return render_template('clients.html', clients=True, overview=True)
