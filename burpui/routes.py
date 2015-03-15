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
"""


api.add_resource(Restore, '/api/restore/<name>/<int:backup>', '/api/<server>/restore/<name>/<int:backup>')
app.jinja_env.globals.update(Restore=Restore)

api.add_resource(ServerSettings, '/api/server-config', '/api/<server>/server-config')
app.jinja_env.globals.update(ServerSettings=ServerSettings)

api.add_resource(ClientSettings, '/api/client-config/<client>', '/api/<server>/client-config/<client>')
app.jinja_env.globals.update(ClientSettings=ClientSettings)

@app.route('/api/running-clients.json')
@app.route('/api/<server>/running-clients.json')
@login_required
def running_clients(server=None):
    """
    API: running_clients
    :returns: a list of running clients
    """
    if not server:
        server = request.args.get('server')
    r = bui.cli.is_one_backup_running(server)
    # Manage ACL
    if bui.acl_handler and not bui.acl_handler.get_acl().is_admin(current_user.name):
        if isinstance(r, dict):
            new = {}
            for serv in bui.acl_handler.get_acl().servers(current_user.name):
                allowed = bui.acl_handler.get_acl().clients(current_user.name, serv)
                new[serv] = [x for x in r[serv] if x in allowed]
            r = new
        else:
            allowed = bui.acl_handler.get_acl().clients(current_user.name, server)
            r = [x for x in r if x in allowed]
    return jsonify(results=r)

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

@app.route('/api/servers.json')
@login_required
def servers_json():
    r = []
    if hasattr(bui.cli, 'servers'):
        check = False
        allowed = []
        if bui.acl_handler and not bui.acl_handler.get_acl().is_admin(current_user.name):
            check = True
            allowed = bui.acl_handler.get_acl().servers(current_user.name)
        for serv in bui.cli.servers:
            if check:
                if serv in allowed:
                    r.append({'name': serv, 'clients': len(bui.cli.servers[serv].get_all_clients(serv)), 'alive': bui.cli.servers[serv].ping()})
            else:
                r.append({'name': serv, 'clients': len(bui.cli.servers[serv].get_all_clients(serv)), 'alive': bui.cli.servers[serv].ping()})
    return jsonify(results=r)

@app.route('/api/live.json')
@app.route('/api/<server>/live.json')
@login_required
def live(server=None):
    """
    API: live
    :returns: the live status of the server
    """
    if not server:
        server = request.args.get('server')
    r = []
    if server:
        l = (bui.cli.is_one_backup_running(server))[server]
    else:
        l = bui.cli.is_one_backup_running()
    if isinstance(l, dict):
        for k, a in l.iteritems():
            for c in a:
                s = {}
                s['client'] = c
                s['agent'] = k
                try:
                    s['status'] = bui.cli.get_counters(c, agent=k)
                except BUIserverException:
                    s['status'] = []
                r.append(s)
    else:
        for c in l:
            s = {}
            s['client'] = c
            try:
                s['status'] = bui.cli.get_counters(c, agent=server)
            except BUIserverException:
                s['status'] = []
            r.append(s)
    return jsonify(results=r)

@app.route('/api/running.json')
@app.route('/api/<server>/running.json')
@login_required
def backup_running(server=None):
    """
    API: backup_running
    :returns: true if at least one backup is running
    """
    j = bui.cli.is_one_backup_running(server)
    # Manage ACL
    if bui.acl_handler and not bui.acl_handler.get_acl().is_admin(current_user.name):
        if isinstance(j, dict):
            new = {}
            for serv in bui.acl_handler.get_acl().servers(current_user.name):
                allowed = bui.acl_handler.get_acl().clients(current_user.name, serv)
                new[serv] = [x for x in j[serv] if x in allowed]
            j = new
        else:
            allowed = bui.acl_handler.get_acl().clients(current_user.name, server)
            j = [x for x in j if x in allowed]
    r = False
    if isinstance(j, dict):
        for k, v in j.iteritems():
            if r:
                break
            r = r or (len(v) > 0)
    else:
        r = len(j) > 0
    return jsonify(results=r)

@app.route('/api/client-tree.json/<name>/<int:backup>', methods=['GET'])
@app.route('/api/<server>/client-tree.json/<name>/<int:backup>', methods=['GET'])
@login_required
def client_tree(server=None, name=None, backup=None):
    """
    WebService: return a specific client files tree
    :param name: the client name (mandatory)
    :param backup: the backup number (mandatory)

    """
    if not server:
        server = request.args.get('server')
    j = []
    if not name or not backup:
        return jsonify(results=j)
    root = request.args.get('root')
    try:
        if bui.acl_handler and\
                (not bui.acl_handler.get_acl().is_admin(current_user.name)\
                and not bui.acl_handler.get_acl().is_client_allowed(current_user.name, name, server)):
            raise BUIserverException('Sorry, you are not allowed to view this client')
        j = bui.cli.get_tree(name, backup, root, agent=server)
    except BUIserverException, e:
        err = [[2, str(e)]]
        return jsonify(notif=err)
    return jsonify(results=j)

@app.route('/api/clients-report.json')
@app.route('/api/<server>/clients-report.json')
@login_required
def clients_report_json(server=None):
    """
    WebService: return a JSON with global stats
    """
    if not server:
        server = request.args.get('server')
    j = []
    try:
        # Manage ACL
        if not bui.standalone and bui.acl_handler and \
                (not bui.acl_handler.get_acl().is_admin(current_user.name) \
                and server not in bui.acl_handler.get_acl().servers(current_user.name)):
            raise BUIserverException('Sorry, you don\'t have rights on this server')
        clients = bui.cli.get_all_clients(agent=server)
    except BUIserverException, e:
        err = [[2, str(e)]]
        return jsonify(notif=err)
    cl = []
    ba = []
    # Filter only allowed clients
    allowed = []
    check = False
    if bui.acl_handler and not bui.acl_handler.get_acl().is_admin(current_user.name):
        check = True
        allowed = bui.acl_handler.get_acl().clients(current_user.name, server)
    for c in clients:
        if check and c['name'] not in allowed:
            continue
        client = bui.cli.get_client(c['name'], agent=server)
        if not client:
            continue
        cl.append( { 'name': c['name'], 'stats': bui.cli.get_backup_logs(client[-1]['number'], c['name'], agent=server) } )
        for b in client:
            ba.append(bui.cli.get_backup_logs(b['number'], c['name'], True, agent=server))
    app.logger.debug(json.dumps(ba))
    if 'end' in ba:
        j.append( { 'clients': cl, 'backups': sorted(ba, key=lambda k: k['end']) } )
    else:
        j.append( { 'clients': cl, 'backups': ba } )
    return jsonify(results=j)

@app.route('/api/client-stat.json/<name>')
@app.route('/api/<server>/client-stat.json/<name>')
@app.route('/api/client-stat.json/<name>/<int:backup>')
@app.route('/api/<server>/client-stat.json/<name>/<int:backup>')
@login_required
def client_stat_json(server=None, name=None, backup=None):
    """
    WebService: return a specific client detailed report
    """
    if not server:
        server = request.args.get('server')
    j = []
    if not name:
        err = [[1, 'No client defined']]
        return jsonify(notif=err)
    if bui.acl_handler and not bui.acl_handler.get_acl().is_client_allowed(current_user.name, name, server):
        err = [[2, 'You don\'t have rights to view this client stats']]
        return jsonify(notif=err)
    if backup:
        try:
            j = bui.cli.get_backup_logs(backup, name, agent=server)
        except BUIserverException, e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
    else:
        try:
            cl = bui.cli.get_client(name, agent=server)
        except BUIserverException, e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        for c in cl:
            j.append(bui.cli.get_backup_logs(c['number'], name, agent=server))
    return jsonify(results=j)

@app.route('/api/client.json/<name>')
@app.route('/api/<server>/client.json/<name>')
@login_required
def client_json(server=None, name=None):
    """
    WebService: return a specific client backups overview
    """
    if not server:
        server = request.args.get('server')
    try:
        if bui.acl_handler and ( \
                not bui.acl_handler.get_acl().is_admin(current_user.name) \
                and not bui.acl_handler.get_acl().is_client_allowed(current_user.name, name, server)):
            raise BUIserverException('Sorry, you cannot access this client')
        j = bui.cli.get_client(name, agent=server)
    except BUIserverException, e:
        err = [[2, str(e)]]
        return jsonify(notif=err)
    return jsonify(results=j)

@app.route('/api/clients.json')
@app.route('/api/<server>/clients.json')
@login_required
def clients_json(server=None):
    """
    WebService: return a JSON listing all clients
    """
    if not server:
        server = request.args.get('server')
    try:
        if not bui.standalone and bui.acl_handler and \
                (not bui.acl_handler.get_acl().is_admin(current_user.name) \
                and server not in bui.acl_handler.get_acl().servers(current_user.name)):
            raise BUIserverException('Sorry, you don\'t have any rights on this server')
        j = bui.cli.get_all_clients(agent=server)
        if bui.acl_handler and not bui.acl_handler.get_acl().is_admin(current_user.name):
            j = [x for x in j if x['name'] in bui.acl_handler.get_acl().clients(current_user.name, server)]
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
