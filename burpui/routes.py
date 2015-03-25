# -*- coding: utf8 -*-
import math
import select
import json

from flask import Flask, Response, request, render_template, jsonify, redirect, url_for, abort, flash
from flask.ext.login import login_user, login_required, logout_user, current_user
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException

from burpui import app, bui, login_manager
from burpui.forms import LoginForm
from burpui.misc.utils import human_readable as _hr
from burpui.misc.backend.interface import BUIserverException

from burpui.api import api
from burpui.api.restore import Restore
from burpui.api.settings import ServerSettings, ClientSettings
from burpui.api.clients import RunningClients, BackupRunning, ClientsReport, ClientsStats
from burpui.api.client import ClientTree, ClientStats, ClientReport
from burpui.api.servers import ServersStats, Live

@login_manager.user_loader
def load_user(userid):
    if bui.auth != 'none':
        return bui.uhandler.user(userid)
    return None

@app.route('/settings', methods=['GET', 'POST'])
@app.route('/<server>/settings', methods=['GET', 'POST'])
@app.route('/settings/<client>', methods=['GET', 'POST'])
@app.route('/<server>/settings/<client>', methods=['GET', 'POST'])
@login_required
def settings(server=None, client=None):
    # Only the admin can edit the configuration
    if bui.acl_handler and not bui.acl_handler.get_acl().is_admin(current_user.name):
        abort(403)
    if not client:
        client = request.args.get('client')
    if request.method == 'POST':
        if not client:
            noti = bui.cli.store_conf_srv(request.form, server)
        else:
            noti = bui.cli.store_conf_cli(request.form, server)
        return jsonify(notif=noti)
    return render_template('settings.html', settings=True, server=server, client=client)


"""
Here is the API

The whole API returns JSON-formated data

The API has been split-out into several files and now uses Flask-Restful
"""

app.jinja_env.globals.update(Restore=Restore)
app.jinja_env.globals.update(ServerSettings=ServerSettings)
app.jinja_env.globals.update(ClientSettings=ClientSettings)
app.jinja_env.globals.update(RunningClients=RunningClients)
app.jinja_env.globals.update(BackupRunning=BackupRunning)
app.jinja_env.globals.update(ClientsReport=ClientsReport)
app.jinja_env.globals.update(ClientsStats=ClientsStats)
app.jinja_env.globals.update(ClientTree=ClientTree)
app.jinja_env.globals.update(ClientStats=ClientStats)
app.jinja_env.globals.update(ClientReport=ClientReport)
app.jinja_env.globals.update(ServersStats=ServersStats)
app.jinja_env.globals.update(Live=Live)

@app.route('/api/render-live-template', methods=['GET'])
@app.route('/api/<server>/render-live-template', methods=['GET'])
@app.route('/api/render-live-template/<name>')
@app.route('/api/<server>/render-live-template/<name>')
@login_required
def render_live_tpl(server=None, name=None):
    """
    API: render_live_tpl
    :param name: the client name if any. You can also use the GET parameter
    'name' to achieve the same thing
    :returns: HTML that should be included directly into the page
    """
    if not server:
        server = request.args.get('server')
    if not name:
        name = request.args.get('name')
    # Check params
    if not name:
        abort(500)
    # Manage ACL
    if bui.acl_handler \
        and (not bui.acl_handler.get_acl().is_client_allowed(current_user.name, name, server) \
        or not bui.acl_handler.get_acl().is_admin(current_user.name)):
        abort(403)
    if isinstance(bui.cli.running, dict):
        if server and name not in bui.cli.running[server]:
            abort(404)
        else:
            found = False
            for k, a in bui.cli.running.iteritems():
                found = found or (name in a)
            if not found:
                abort(404)
    else:
        if name not in bui.cli.running:
            abort(404)
    try:
        counters = bui.cli.get_counters(name, agent=server)
    except BUIserverException:
        counters = []
    return render_template('live-monitor-template.html', cname=name, counters=counters, server=server)

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
@app.route('/<server>/live-monitor')
@app.route('/live-monitor/<name>')
@app.route('/<server>/live-monitor/<name>')
@login_required
def live_monitor(server=None, name=None):
    """
    Live status monitor view
    """
    if not server:
        server = request.args.get('server')
    if bui.standalone:
        if not bui.cli.running:
            flash('Sorry, there are no running backups', 'warning')
            return redirect(url_for('home'))
    else:
        run = False
        for a in bui.cli.servers:
            run = run or (a in bui.cli.running and bui.cli.running[a])
        if not run:
            flash('Sorry, there are no running backups', 'warning')
            return redirect(url_for('home'))
            
    return render_template('live-monitor.html', live=True, cname=name, server=server)

@app.route('/client-browse/<name>', methods=['GET'])
@app.route('/<server>/client-browse/<name>', methods=['GET'])
@app.route('/client-browse/<name>/<int:backup>')
@app.route('/<server>/client-browse/<name>/<int:backup>')
@app.route('/client-browse/<name>/<int:backup>/<int:encrypted>')
@app.route('/<server>/client-browse/<name>/<int:backup>/<int:encrypted>')
@login_required
def client_browse(server=None, name=None, backup=None, encrypted=None):
    """
    Browse a specific backup of a specific client
    """
    if request.args.get('encrypted') == '1':
        encrypted = 1
    if not server:
        server = request.args.get('server')
    bkp = request.args.get('backup')
    if bkp and not backup:
        return redirect(url_for('client_browse', name=name, backup=bkp, encrypted=encrypted, server=server))
    return render_template('client-browse.html', tree=True, backup=True, overview=True, cname=name, nbackup=backup, encrypted=encrypted, server=server)

@app.route('/client-report/<name>')
@app.route('/<server>/client-report/<name>')
@login_required
def client_report(server=None, name=None):
    """
    Specific client report
    """
    if not server:
        server = request.args.get('server')
    l = bui.cli.get_client(name, agent=server)
    if len(l) == 1:
        return redirect(url_for('backup_report', name=name, backup=l[0]['number'], server=server))
    return render_template('client-report.html', client=True, report=True, cname=name, server=server)

@app.route('/clients-report')
@app.route('/<server>/clients-report')
@login_required
def clients_report(server=None):
    """
    Global report
    """
    if not server:
        server = request.args.get('server')
    return render_template('clients-report.html', clients=True, report=True, server=server)

@app.route('/backup-report/<name>', methods=['GET'])
@app.route('/<server>/backup-report/<name>', methods=['GET'])
@app.route('/backup-report/<name>/<int:backup>', methods=['GET'])
@app.route('/<server>/backup-report/<name>/<int:backup>', methods=['GET'])
@login_required
def backup_report(server=None, name=None, backup=None):
    """
    Backup specific report
    """
    if not backup:
        backup = request.args.get('backup')
    if not server:
        server = request.args.get('server')
    return render_template('backup-report.html', client=True, backup=True, report=True, cname=name, nbackup=backup, server=server)

@app.route('/client', methods=['GET'])
@app.route('/<server>/client', methods=['GET'])
@app.route('/client/<name>')
@app.route('/<server>/client/<name>')
@login_required
def client(server=None, name=None):
    """
    Specific client overview
    """
    if name:
        c = name
    else:
        c = request.args.get('name')
    if not server:
        server = request.args.get('server')
    if bui.cli.is_backup_running(c, agent=server):
        return redirect(url_for('live_monitor', name=name, server=server))
    return render_template('client.html', client=True, overview=True, cname=c, server=server)

@app.route('/clients', methods=['GET'])
@app.route('/<server>/clients', methods=['GET'])
@login_required
def clients(server=None):
    if not server:
        server = request.args.get('server')
    return render_template('clients.html', clients=True, overview=True, server=server)

@app.route('/servers', methods=['GET'])
@login_required
def servers():
    return render_template('servers.html', servers=True, overview=True)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = bui.uhandler.user(form.username.data)
        if user.active and user.login(form.username.data, passwd=form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully', 'success')
            return redirect(request.args.get("next") or url_for('home'))
        else:
            flash('Wrong username or password', 'danger')
    return render_template('login.html', form=form, login=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
@login_required
def home():
    """
    Home page
    """
    if bui.standalone:
        return redirect(url_for('clients'))
    else:
        return redirect(url_for('servers'))
