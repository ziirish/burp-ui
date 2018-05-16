# -*- coding: utf8 -*-
"""
.. module:: burpui.routes
    :platform: Unix
    :synopsis: Burp-UI routes module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import re
import math
import uuid

from six import iteritems
from flask import request, render_template, redirect, url_for, abort, \
    flash, Blueprint, session, current_app, g
from flask_login import login_user, login_required, logout_user, current_user
from flask_babel import gettext as _, refresh as refresh_babel

from .desc import __url__, __doc__
from .server import BUIServer  # noqa
from .sessions import session_manager
from ._compat import quote
from .forms import LoginForm
from .exceptions import BUIserverException
from .utils import human_readable as _hr
from .security import sanitize_string, is_safe_url


bui = current_app  # type: BUIServer
view = Blueprint('view', 'burpui', template_folder='templates')


"""
Here are some custom filters
"""


@view.app_template_filter()
def mypad(value):
    """
    Filter: used to pad 0's to backup numbers as in the burp's status monitor
    """
    if not value:
        return '0000000'
    return '{0:07d}'.format(int(value))


@view.app_template_filter()
def time_human(value):
    """Convert the input value to human readable time"""
    string = ''
    seconds = (((value % 31536000) % 86400) % 3600) % 60
    minutes = math.floor((((value % 31536000) % 86400) % 3600) / 60)
    hours = math.floor(((value % 31536000) % 86400) / 3600)
    if hours > 0:
        string = '%02dH' % hours
    return '%s %02dm %02ds' % (string, minutes, seconds)


@view.app_template_filter()
def bytes_human(value):
    """Convert the input value to human readable bytes"""
    return '{0:.1eM}'.format(_hr(value))


@view.app_template_filter()
def regex_replace(value, regex, replace):
    """Replace every string matching the given regex with the replacement"""
    return re.sub(regex, replace, value, flags=re.IGNORECASE)


"""
And here is the main site
"""


@view.route('/calendar')
@view.route('/calendar/<client>')
@view.route('/<server>/calendar')
@view.route('/<server>/calendar/<client>')
@login_required
def calendar(server=None, client=None):
    server = server or request.args.get('serverName')
    client = client or request.args.get('clientName')
    if not bui.standalone:
        servers = not server and not client
        clients = bool(server)
        cli = bool(client)
    else:
        servers = False
        cli = bool(client)
        clients = not cli
    return render_template(
        'calendar.html',
        calendar=True,
        server=server,
        cname=client,
        client=cli,
        servers=servers,
        clients=clients
    )


@view.route('/settings')
@view.route('/settings/<path:conf>')
@view.route('/<server>/settings')
@view.route('/<server>/settings/<path:conf>')
@login_required
def settings(server=None, conf=None):
    # Only the admin can edit the configuration
    if not current_user.is_anonymous and not current_user.acl.is_admin() and \
            not current_user.acl.is_moderator():
        abort(403)
    if not conf:
        try:
            conf = quote(request.args.get('conf'), safe='')
            if conf:
                return redirect(url_for('.settings', server=server, conf=conf))
        except:
            pass
    server = server or request.args.get('serverName')
    return render_template(
        'settings.html',
        settings=True,
        is_admin=current_user.acl.is_admin(),
        is_moderator=current_user.acl.is_moderator(),
        server=server,
        conf=conf,
        ng_controller='ConfigCtrl'
    )


@view.route('/admin/sessions/<user>')
@login_required
def admin_sessions(user):
    # Only the admin can access this page
    if not current_user.is_anonymous and not current_user.acl.is_admin() and \
            not current_user.acl.is_moderator():
        abort(403)
    return render_template('admin/sessions.html', admin=True, sessions=True, user=user, ng_controller='AdminCtrl')


@view.route('/admin/authentication/<user>')
@login_required
def admin_authentication(user):
    # Only the admin can access this page
    if not current_user.is_anonymous and not current_user.acl.is_admin() and \
            not current_user.acl.is_moderator():
        abort(403)
    backend = request.args.get('backend')
    if not backend:
        abort(400)
    return render_template('admin/authentication.html', admin=True, authentication=True, user=user, backend=backend, ng_controller='AdminCtrl')


@view.route('/admin/authorization/grant/<grant>')
@login_required
def admin_grant_authorization(grant):
    # Only the admin can access this page
    if not current_user.is_anonymous and not current_user.acl.is_admin() and \
            not current_user.acl.is_moderator():
        abort(403)
    backend = request.args.get('backend')
    if not backend:
        abort(400)
    return render_template('admin/grant-authorization.html', admin=True, authorization=True, grant=grant, backend=backend, ng_controller='AdminCtrl')


@view.route('/admin/authorization/group/<group>')
@login_required
def admin_group_authorization(group):
    # Only the admin can access this page
    if not current_user.is_anonymous and not current_user.acl.is_admin() and \
            not current_user.acl.is_moderator():
        abort(403)
    backend = request.args.get('backend')
    if not backend:
        abort(400)
    return render_template('admin/group-authorization.html', admin=True, authorization=True, group=group, backend=backend, ng_controller='AdminCtrl')


@view.route('/admin/backend/<backend>')
@login_required
def admin_backend(backend):
    # Only the admin can access this page
    if not current_user.is_anonymous and not current_user.acl.is_admin() and \
            not current_user.acl.is_moderator():
        abort(403)
    return render_template('admin/backend.html', admin=True, onebackend=True, backend=backend, ng_controller='AdminCtrl')


@view.route('/admin/backends')
@login_required
def admin_backends():
    # Only the admin can access this page
    if not current_user.is_anonymous and not current_user.acl.is_admin() and \
            not current_user.acl.is_moderator():
        abort(403)
    return render_template('admin-backends.html', admin=True, backends=True, ng_controller='AdminCtrl')


@view.route('/admin/authorizations')
@login_required
def admin_authorizations():
    # Only the admin can access this page
    if not current_user.is_anonymous and not current_user.acl.is_admin() and \
            not current_user.acl.is_moderator():
        abort(403)
    return render_template('admin-authorizations.html', admin=True, authorizations=True, ng_controller='AdminCtrl')


@view.route('/admin/authentications')
@login_required
def admin_authentications():
    # Only the admin can access this page
    if not current_user.is_anonymous and not current_user.acl.is_admin() and \
            not current_user.acl.is_moderator():
        abort(403)
    return render_template('admin-authentications.html', admin=True, authentications=True, ng_controller='AdminCtrl')


@view.route('/me')
@login_required
def me():
    return render_template('user.html', me=True, ng_controller='UserCtrl')


@view.route('/client/client-settings')
@view.route('/<client>/client-settings')
@view.route('/<client>/client-settings/<path:conf>')
@view.route('/<server>/client/client-settings')
@view.route('/<server>/<client>/client-settings')
@view.route('/<server>/<client>/client-settings/<path:conf>')
@login_required
def cli_settings(server=None, client=None, conf=None):
    # Only the admin can edit the configuration
    if not current_user.is_anonymous and not current_user.acl.is_admin() and \
            not current_user.acl.is_moderator():
        abort(403)
    if not conf:
        try:
            conf = quote(request.args.get('conf'), safe='')
            if conf:
                return redirect(
                    url_for(
                        '.cli_settings',
                        server=server,
                        client=client,
                        conf=conf
                    )
                )
        except:
            pass
    client = client or request.args.get('client')
    server = server or request.args.get('serverName')
    template = request.args.get('template') or False
    return render_template(
        'settings.html',
        settings=True,
        client_mode=True,
        template=template,
        client=client,
        server=server,
        conf=conf,
        ng_controller='ConfigCtrl'
    )


@view.route('/live-monitor')
@view.route('/<server>/live-monitor')
@view.route('/live-monitor/<name>')
@view.route('/<server>/live-monitor/<name>')
@login_required
def live_monitor(server=None, name=None):
    """Live status monitor view"""
    server = server or request.args.get('serverName')
    running = bui.client.is_one_backup_running()
    if bui.standalone:
        if not running:
            flash(_('Sorry, there are no running backups'), 'warning')
            return redirect(url_for('.home'))
    else:
        if not any([x for y, x in iteritems(running)]):
            flash(_('Sorry, there are no running backups'), 'warning')
            return redirect(url_for('.home'))

    return render_template(
        'live-monitor.html',
        live=True,
        cname=name,
        server=server,
        ng_controller='LiveCtrl'
    )


@view.route('/edit-server-initiated-restore/<name>', methods=['GET'])
@view.route('/<server>/edit-server-initiated-restore/<name>', methods=['GET'])
@login_required
def edit_server_initiated_restore(server=None, name=None):
    data = bui.client.is_server_restore(name, server)
    to = None
    if not data or not data['found']:
        flash(
            _(
                'Sorry, there are no restore file found for this client'
            ),
            'warning'
        )
        return redirect(url_for('.home'))
    if data.get('orig_client'):
        to = name
        name = data['orig_client']
    return redirect(
        url_for(
            '.client_browse',
            server=server,
            name=name,
            backup=data['backup'],
            edit=1,
            to=to
        )
    )


@view.route('/client-browse/<name>', methods=['GET'])
@view.route('/<server>/client-browse/<name>', methods=['GET'])
@view.route('/client-browse/<name>/<int:backup>')
@view.route('/<server>/client-browse/<name>/<int:backup>')
@view.route('/client-browse/<name>/<int:backup>/<int:encrypted>')
@view.route('/<server>/client-browse/<name>/<int:backup>/<int:encrypted>')
@login_required
def client_browse(server=None, name=None, backup=None, encrypted=None,
                  edit=None):
    """Browse a specific backup of a specific client"""
    if request.args.get('encrypted') == '1':
        encrypted = 1
    if request.args.get('edit') == '1':
        to = request.args.get('to') or name
        edit = bui.client.is_server_restore(to, server)
        if not edit or not edit['found']:
            flash(
                _(
                    'Sorry, there are no restore file found for this client'
                ),
                'warning'

            )
            edit = None
        else:
            edit['roots'] = [x['key'] for x in edit['list']]
    server = server or request.args.get('serverName')
    bkp = request.args.get('backup')
    if bkp and not backup:
        return redirect(
            url_for(
                '.client_browse',
                name=name,
                backup=bkp,
                encrypted=encrypted,
                server=server
            )
        )
    return render_template(
        'client-browse.html',
        tree=True,
        backup=True,
        overview=True,
        cname=name,
        nbackup=backup,
        encrypted=encrypted,
        server=server,
        edit=edit,
        ng_controller='BrowseCtrl'
    )


@view.route('/client-report/<name>')
@view.route('/<server>/client-report/<name>')
@login_required
def client_report(server=None, name=None):
    """Specific client report"""
    server = server or request.args.get('serverName')
    try:
        res = bui.client.get_client(name, agent=server)
    except BUIserverException:
        res = []
    if len(res) == 1:
        return redirect(
            url_for(
                '.backup_report',
                name=name,
                backup=res[0]['number'],
                server=server
            )
        )
    return render_template(
        'client-report.html',
        client=True,
        report=True,
        cname=name,
        server=server
    )


@view.route('/clients-report')
@view.route('/<server>/clients-report')
@login_required
def clients_report(server=None):
    """Global report"""
    server = server or request.args.get('serverName')
    return render_template(
        'clients-report.html',
        clients=True,
        report=True,
        server=server
    )


@view.route('/backup-report/<name>', methods=['GET'])
@view.route('/<server>/backup-report/<name>', methods=['GET'])
@view.route('/backup-report/<name>/<int:backup>', methods=['GET'])
@view.route('/<server>/backup-report/<name>/<int:backup>', methods=['GET'])
@login_required
def backup_report(server=None, name=None, backup=None):
    """Backup specific report"""
    backup = backup or request.args.get('backup')
    server = server or request.args.get('serverName')
    return render_template(
        'backup-report.html',
        client=True,
        backup=True,
        report=True,
        cname=name,
        nbackup=backup,
        server=server
    )


@view.route('/client', methods=['GET'])
@view.route('/<server>/client', methods=['GET'])
@view.route('/client/<name>')
@view.route('/<server>/client/<name>')
@login_required
def client(server=None, name=None):
    """Specific client overview"""
    c = name or request.args.get('name')
    server = server or request.args.get('serverName')
    # burp 2 allows to browse backups will backing up whereas burp 1 does not
    if bui.client.version(server) == 1 and \
            bui.client.is_backup_running(c, agent=server):
        return redirect(url_for('.live_monitor', name=c, server=server))
    return render_template(
        'client.html',
        client=True,
        overview=True,
        cname=c,
        server=server
    )


@view.route('/clients', methods=['GET'])
@view.route('/<server>/clients', methods=['GET'])
@login_required
def clients(server=None):
    server = server or request.args.get('serverName')
    return render_template(
        'clients.html',
        clients=True,
        overview=True,
        server=server
    )


@view.route('/servers', methods=['GET'])
@login_required
def servers():
    return render_template('servers.html', servers=True, overview=True)


@view.route('/servers-report', methods=['GET'])
@login_required
def servers_report():
    return render_template('servers-report.html', servers=True, report=True)


@view.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm(request.form)

    if form.validate_on_submit():
        # allow to switch to another backend
        refresh = True
        session['tag_id'] = uuid.uuid4()
        session['language'] = form.language.data
        session['_extra'] = g.now
        user = bui.uhandler.user(form.username.data, refresh)
        # at the time the context is loaded, the locale is not set
        refresh_babel()
        if user and user.is_active and user.login(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(_('Logged in successfully'), 'success')
            session_manager.store_session(
                form.username.data,
                request.remote_addr,
                request.headers.get('User-Agent'),
                form.remember.data
            )
            next_hop = request.args.get("next") or url_for('.home')
            if is_safe_url(next_hop):
                return redirect(next_hop)
            return abort(400)
        else:
            flash(_('Wrong username or password'), 'danger')
            bui.logger.critical(
                'Wrong username or password attempted by {} at {}'.format(
                    repr(sanitize_string(form.username.data, paranoid=True)),
                    request.remote_addr
                )
            )
    elif form.is_submitted():
        flash(_('Wrong CSRF token, please try again'), 'warning')
    return render_template('login.html', form=form, login=True)


@view.route('/logout')
@login_required
def logout():
    session_manager.delete_session()
    # cleanup the session at logout to avoid further reuse by another user
    session.clear()
    logout_user()
    return redirect(url_for('.home'))


@view.route('/about')
def about():
    """about view"""
    return render_template(
        'about.html',
        about=True,
        login=(not current_user.is_authenticated),
        doc=__doc__,
        url=__url__
    )


@view.route('/')
@login_required
def home():
    """Home page"""
    if bui.standalone:
        return redirect(url_for('.clients'))
    else:
        server = request.args.get('serverName')
        if server:
            return redirect(url_for('.clients', server=server))
        return redirect(url_for('.servers'))
