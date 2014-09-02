# -*- coding: utf8 -*-
import math

from flask import Flask, request, render_template, jsonify, redirect, url_for, abort, flash, g, session
from flask.ext.login import login_user, login_required, logout_user, current_user

from burpui import app, bui, login_manager
from burpui.forms import LoginForm
from burpui.misc.utils import human_readable as _hr
from burpui.misc.backend.interface import BUIserverException

@login_manager.user_loader
def load_user(userid):
    if bui.auth != 'none':
        return bui.uhandler.user(userid)
    return None

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = bui.uhandler.user(form.username.data)
        if user.active and user.login(form.username.data, passwd=form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully', 'success')
            return redirect(request.args.get("next") or url_for('home'))
    return render_template('login.html', form=form, login=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

"""
Here is the API

The whole API returns JSON-formated data
"""

@app.route('/api/running-clients.json')
@login_required
def running_clients():
    """
    API: running_clients
    :returns: a list of running clients
    """
    r = bui.cli.is_one_backup_running()
    return jsonify(results=r)

@app.route('/api/render-live-template', methods=['GET'])
@app.route('/api/render-live-template/<name>')
@login_required
def render_live_tpl(name=None):
    """
    API: render_live_tpl
    :param name: the client name if any. You can also use the GET parameter
    'name' to achieve the same thing
    :returns: HTML that should be included directly into the page
    """
    c = request.args.get('name')
    if not name and not c:
        abort(500)
    if not name:
        name = c
    if name not in bui.cli.running:
        abort(404)
    try:
        counters = bui.cli.get_counters(name)
    except BUIserverException:
        counters = []
    return render_template('live-monitor-template.html', cname=name, counters=counters)

@app.route('/api/live.json')
@login_required
def live():
    """
    API: live
    :returns: the live status of the server
    """
    r = []
    for c in bui.cli.is_one_backup_running():
        s = {}
        s['client'] = c
        try:
            s['status'] = bui.cli.get_counters(c)
        except BUIserverException:
            s['status'] = []
        r.append(s)
    return jsonify(results=r)

@app.route('/api/running.json')
@login_required
def backup_running():
    """
    API: backup_running
    :returns: true if at least one backup is running
    """
    j = bui.cli.is_one_backup_running()
    r = len(j) > 0
    return jsonify(results=r)

@app.route('/api/client-tree.json/<name>/<int:backup>', methods=['GET'])
@login_required
def client_tree(name=None, backup=None):
    """
    WebService: return a specific client files tree
    :param name: the client name (mandatory)
    :param backup: the backup number (mandatory)

    """
    j = []
    if not name or not backup:
        return jsonify(results=j)
    root = request.args.get('root')
    try:
        j = bui.cli.get_tree(name, backup, root)
    except BUIserverException, e:
        err = [[2, str(e)]]
        return jsonify(notif=err)
    return jsonify(results=j)

@app.route('/api/clients-report.json')
@login_required
def clients_report_json():
    """
    WebService: return a JSON with global stats
    """
    j = []
    try:
        clients = bui.cli.get_all_clients()
    except BUIserverException, e:
        err = [[2, str(e)]]
        return jsonify(notif=err)
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
@login_required
def client_stat_json(name=None, backup=None):
    """
    WebService: return a specific client detailed report
    """
    j = []
    if not name:
        err = [[1, 'No client defined']]
        return jsonify(notif=err)
    if backup:
        try:
            f = bui.cli.status('c:{0}:b:{1}:f:log.gz\n'.format(name, backup))
        except BUIserverException, e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        j = bui.cli.parse_backup_log(f, backup)
    else:
        try:
            cl = bui.cli.get_client(name)
        except BUIserverException, e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        for c in cl:
            f =  bui.cli.status('c:{0}:b:{1}:f:log.gz\n'.format(name, c['number']))
            j.append(bui.cli.parse_backup_log(f, c['number']))
    return jsonify(results=j)

@app.route('/api/client.json/<name>')
@login_required
def client_json(name=None):
    """
    WebService: return a specific client backups overview
    """
    try:
        j = bui.cli.get_client(name)
    except BUIserverException, e:
        err = [[2, str(e)]]
        return jsonify(notif=err)
    return jsonify(results=j)

@app.route('/api/clients.json')
@login_required
def clients():
    """
    WebService: return a JSON listing all clients
    """
    try:
        j = bui.cli.get_all_clients()
    except BUIserverException, e:
        err = [[2, str(e)]]
        return jsonify(notif=err)
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
@login_required
def live_monitor(name=None):
    """
    Live status monitor view
    """
    if not bui.cli.running:
        flash('Sorry, there are no running backups', 'warning')
        return redirect(url_for('home'))
    return render_template('live-monitor.html', live=True, cname=name)

@app.route('/client-browse/<name>', methods=['GET'])
@app.route('/client-browse/<name>/<int:backup>')
@login_required
def client_browse(name=None, backup=None):
    """
    Browse a specific backup of a specific client
    """
    bkp = request.args.get('backup')
    if bkp and not backup:
        return redirect(url_for('client_browse', name=name, backup=bkp))
    return render_template('client-browse.html', tree=True, backup=True, overview=True, cname=name, nbackup=backup)

@app.route('/client-report/<name>')
@login_required
def client_report(name=None):
    """
    Specific client report
    """
    l = bui.cli.get_client(name)
    if len(l) == 1:
        return redirect(url_for('backup_report', name=name, backup=l[0]['number']))
    return render_template('client-report.html', client=True, report=True, cname=name)

@app.route('/clients-report')
@login_required
def clients_report():
    """
    Global report
    """
    return render_template('clients-report.html', clients=True, report=True)

@app.route('/backup-report/<name>', methods=['GET'])
@app.route('/backup-report/<name>/<int:backup>', methods=['GET'])
@login_required
def backup_report(name=None, backup=None):
    """
    Backup specific report
    """
    if not backup:
        backup = request.args.get('backup')
    return render_template('backup-report.html', client=True, backup=True, report=True, cname=name, nbackup=backup)

@app.route('/client', methods=['GET'])
@app.route('/client/<name>')
@login_required
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
@login_required
def home():
    """
    Home page
    """
    return render_template('clients.html', clients=True, overview=True)
