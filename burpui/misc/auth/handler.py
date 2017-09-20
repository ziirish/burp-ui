# -*- coding: utf8 -*-
import os

from ...sessions import session_manager
from ...utils import is_uuid
from .interface import BUIhandler, BUIuser
from ..acl.interface import BUIacl

from importlib import import_module
from flask import session
from six import iteritems
from collections import OrderedDict
from flask_login import AnonymousUserMixin


class UserAuthHandler(BUIhandler):
    """See :class:`burpui.misc.auth.interface.BUIhandler`"""
    def __init__(self, app=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.__init__`

        :param app: Instance of the app we are running in
        :type app: :class:`burpui.server.BUIServer`
        """
        self.app = app
        self.users = {}
        backends = []
        self.errors = {}
        if self.app.auth and 'none' not in self.app.auth:
            me, _ = os.path.splitext(os.path.basename(__file__))
            back = self.app.auth
            for au in back:
                if au == me:
                    self.app.logger.critical('Recursive import not permitted!')
                    continue
                try:
                    (modpath, _) = __name__.rsplit('.', 1)
                    mod = import_module('.' + au, modpath)
                    obj = mod.UserHandler(self.app)
                    backends.append(obj)
                except:
                    import traceback
                    self.errors[au] = traceback.format_exc()
        for name, plugin in iteritems(self.app.plugin_manager.get_plugins_by_type('auth')):
            try:
                obj = plugin.UserHandler(self.app)
                backends.append(obj)
            except:
                import traceback
                self.errors[name] = traceback.format_exc()
        backends.sort(key=lambda x: x.priority, reverse=True)
        if not backends:
            raise ImportError(
                'No backend found for \'{}\':\n{}'.format(self.app.auth,
                                                          self.errors)
            )
        for name, err in iteritems(self.errors):
            self.app.logger.error(
                'Unable to load module {}:\n{}'.format(repr(name), err)
            )
        self.backends = OrderedDict()
        for obj in backends:
            self.backends[obj.name] = obj

    def user(self, name=None, refresh=False):
        """See :func:`burpui.misc.auth.interface.BUIhandler.user`"""
        key = session_manager.get_session_id() or name
        if key != name and is_uuid(name) and name in self.users and \
                not session_manager.session_expired_by_id(name):
            usr = self.users[name]
            usr.id = key
            self.users[key] = usr
            del self.users[name]
            session_manager.session_import_from(name)
            session['authenticated'] = True
        if not key:
            return None
        if refresh and key in self.users:
            del self.users[key]
        if session_manager.session_managed():
            session_manager.session_expired()
        if key not in self.users:
            ret = UserHandler(self.app, self.backends, name, key)
            if not ret.name or not ret.active:
                return None
            self.users[key] = ret
            return ret
        ret = self.users[key]
        ret.refresh_session()
        self.users[key] = ret
        return ret

    def remove(self, name):
        """See :func:`burpui.misc.auth.interface.BUIhandler.remove`"""
        if name in self.users:
            del self.users[name]


class ACLproxy(BUIacl):
    def __init__(self, acl, username):
        self.acl = acl
        self.username = username

    def is_admin(self):
        if not self.acl:
            return True
        return self.acl.is_admin(self.username)

    def is_moderator(self):
        if not self.acl:
            return True
        return self.acl.is_moderator(self.username)

    def is_client_allowed(self, client, server=None):
        if not self.acl:
            return True
        return self.acl.is_client_allowed(self.username, client, server)

    def is_server_allowed(self, server):
        if not self.acl:
            return True
        return self.acl.is_server_allowed(self.username, server)


class ACLanon(BUIacl):
    def is_admin(self):
        return False

    def is_moderator(self):
        return False

    def is_client_allowed(self, client, server=None):
        return False

    def is_server_allowed(self, server):
        return False


class BUIanon(AnonymousUserMixin):
    _acl = ACLanon()
    name = 'Unknown'

    def login(self, passwd=None):
        return False

    @property
    def acl(self):
        return self._acl

    @property
    def is_admin(self):
        return False


class UserHandler(BUIuser):
    """See :class:`burpui.misc.auth.interface.BUIuser`"""
    def __init__(self, app, backends=None, name=None, id=None):
        """
        :param app: Application context
        :type app: :class:`burpui.server.BUIServer`
        """
        self.id = id
        self.app = app
        self.active = False
        self.authenticated = session.get('authenticated', False)
        self.language = session.get('language', None)
        self.backends = backends
        self.back = None
        if not is_uuid(name):
            self.name = name
        else:
            self.name = session_manager.get_session_username() or \
                session.get('login')
        self.real = None
        if not self.name:
            return

        for _, back in iteritems(self.backends):
            user = back.user(self.name)
            if not user:
                continue
            res = user.get_id()
            if res:
                self.active = True
                self.name = res
                self.back = back
                break

        self._acl = ACLproxy(self.app.acl, self.name)
        # language may change upon login
        self._store_lang()
        # now load the available prefs
        self._load_prefs()

    @property
    def acl(self):
        return self._acl

    def _load_prefs(self):
        session['login'] = self.name
        if self.app.config['WITH_SQL']:
            from ...models import Pref
            prefs = Pref.query.filter_by(user=self.name).all()
            for pref in prefs:
                if hasattr(self, pref.key):
                    setattr(self, pref.key, pref.value)
                session[pref.key] = pref.value

    def _store_lang(self):
        if self.app.config['WITH_SQL'] and self.language:
            from ...ext.sql import db
            from ...models import Pref
            pref = Pref.query.filter_by(user=self.name, key='language').first()
            if pref:
                pref.value = self.language
            else:
                pref = Pref(self.name, 'language', self.language)
                db.session.add(pref)
            try:
                db.session.commit()
            except:
                db.session.rollback()

    def refresh_session(self):
        self.authenticated = session.get('authenticated', False)
        self.language = session.get('language', None)
        self._load_prefs()

    def login(self, passwd=None):
        """See :func:`burpui.misc.auth.interface.BUIuser.login`"""
        if not self.real:
            self.authenticated = False
            for name, back in iteritems(self.backends):
                u = back.user(self.name)
                if not u:
                    continue
                res = u.get_id()
                if u.login(passwd):
                    self.authenticated = True
                    self.real = u
                    self.back = back
                    self.name = res
                    self._acl.username = res
                    break
        elif self.real:  # pragma: no cover
            if self.back and getattr(self.back, 'changed', False):
                self.real = None
                self.back = None
                return self.login(passwd)
            self.authenticated = self.real.login(passwd)
        session['authenticated'] = self.authenticated
        session['language'] = self.language
        session['login'] = self.name
        return self.authenticated
