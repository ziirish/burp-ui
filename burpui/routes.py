# -*- coding: utf8 -*-
import math
import select
from zlib import adler32
from time import gmtime, strftime, time

from flask import Flask, Response, request, render_template, jsonify, redirect, url_for, abort, flash, send_file
from flask.ext.login import login_user, login_required, logout_user 
from werkzeug.datastructures import Headers

from burpui import app, bui, login_manager
from burpui.forms import LoginForm
from burpui.misc.utils import human_readable as _hr
from burpui.misc.backend.interface import BUIserverException

@login_manager.user_loader
def load_user(userid):
    if bui.auth != 'none':
        return bui.uhandler.user(userid)
    return None

@app.route('/settings', methods=['GET', 'POST'])
@app.route('/<server>/settings', methods=['GET', 'POST'])
@login_required
def settings(server=None):
    if request.method == 'POST':
        noti = bui.cli.store_conf(request.form)
        return jsonify(notif=noti)
    return render_template('settings.html', settings=True, server=server)

@app.route('/api/server-config')
@app.route('/api/<server>/server-config')
@login_required
def read_conf_srv(server=None):
    r = bui.cli.read_conf(server)
    return jsonify(results=r,
                   boolean=bui.cli.get_parser_attr('boolean'),
                   string=bui.cli.get_parser_attr('string'),
                   integer=bui.cli.get_parser_attr('integer'),
                   multi=bui.cli.get_parser_attr('multi'),
                   server_doc=bui.cli.get_parser_attr('server_doc'),
                   suggest=bui.cli.get_parser_attr('values_server'),
                   placeholders=bui.cli.get_parser_attr('placeholders'),
                   defaults=bui.cli.get_parser_attr('defaults_server'))


"""
Here is the API

The whole API returns JSON-formated data
"""

@app.route('/api/restore/<name>/<int:backup>', methods=['POST'])
@app.route('/api/<server>/restore/<name>/<int:backup>', methods=['POST'])
@login_required
def restore(server=None, name=None, backup=None):
    l = request.form.get('list')
    s = request.form.get('strip')
    resp = None
    if not l or not name or not backup:
        abort(500)
    if server:
        filename = 'restoration_%d_%s_on_%s_at_%s.zip' % (backup, name, server, strftime("%Y-%m-%d_%H_%M_%S", gmtime()))
    else:
        filename = 'restoration_%d_%s_at_%s.zip' % (backup, name, strftime("%Y-%m-%d_%H_%M_%S", gmtime()))
    if not server:
        archive = bui.cli.restore_files(name, backup, l, s)
        if not archive:
            abort(500)
        try:
            resp = send_file(archive, as_attachment=True, attachment_filename=filename, mimetype='application/zip')
            resp.set_cookie('fileDownload', 'true')
        except Exception, e:
            app.logger.error(str(e))
            abort(500)
    else:
        socket = None
        try:
            socket, length = bui.cli.restore_files(name, backup, l, s, server)
            app.logger.debug('Need to get %d Bytes : %s', length, socket)
            def stream_file(sock, l):
                bsize = 1024
                received = 0
                if l < bsize:
                    bsize = l
                while received < l:
                    buf = b''
                    r, _, _ = select.select([sock], [], [], 5)
                    if not r:
                        raise Exception ('Socket timed-out')
                    buf += sock.recv(bsize)
                    if not buf:
                        continue
                    received += len(buf)
                    app.logger.debug('%d/%d', received, l)
                    yield buf
                sock.close()

            headers = Headers()
            headers.add('Content-Disposition', 'attachment', filename=filename)
            headers['Content-Length'] = length

            resp = Response(stream_file(socket, length), mimetype='application/zip',
                            headers=headers, direct_passthrough=True)
            resp.set_cookie('fileDownload', 'true')
            resp.set_etag('flask-%s-%s-%s' % (
                    time(),
                    length,
                    adler32(filename.encode('utf-8')) & 0xffffffff))
        except Exception, e:
            app.logger.error(str(e))
            abort(500)
    return resp

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
    if not name:
        abort(500)
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
        for serv in bui.cli.servers:
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
    r = False
    if isinstance(j, dict):
        for k, v in j.iteritems():
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
        clients = bui.cli.get_all_clients(agent=server)
    except BUIserverException, e:
        err = [[2, str(e)]]
        return jsonify(notif=err)
    cl = []
    ba = []
    for c in clients:
        client = bui.cli.get_client(c['name'], agent=server)
        if not client:
            continue
        cl.append( { 'name': c['name'], 'stats': bui.cli.get_backup_logs(client[-1]['number'], c['name'], agent=server) } )
        for b in client:
            ba.append(bui.cli.get_backup_logs(b['number'], c['name'], True, agent=server))
    j.append( { 'clients': cl, 'backups': sorted(ba, key=lambda k: k['end']) } )
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
        j = bui.cli.get_all_clients(agent=server)
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
@login_required
def client_browse(server=None, name=None, backup=None):
    """
    Browse a specific backup of a specific client
    """
    if not server:
        server = request.args.get('server')
    bkp = request.args.get('backup')
    if bkp and not backup:
        return redirect(url_for('client_browse', name=name, backup=bkp, server=server))
    return render_template('client-browse.html', tree=True, backup=True, overview=True, cname=name, nbackup=backup, server=server)

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
