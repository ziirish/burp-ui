# -*- coding: utf8 -*-
import os

from ...sessions import session_manager
from .interface import BUIhandler, BUIuser
from importlib import import_module
from flask import session
from six import iteritems
from collections import OrderedDict


class UserAuthHandler(BUIhandler):
    """See :class:`burpui.misc.auth.interface.BUIhandler`"""
    def __init__(self, app=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.__init__`"""
        self.app = app
        self.users = {}
        backends = []
        if self.app.auth:
            me, _ = os.path.splitext(os.path.basename(__file__))
            back = self.app.auth
            for au in back:
                if au == me:
                    self.app.logger.error('Recursive import not permited!')
                    continue
                try:
                    (modpath, _) = __name__.rsplit('.', 1)
                    mod = import_module('.' + au, modpath)
                    obj = mod.UserHandler(self.app)
                    backends.append(obj)
                except:
                    pass
        backends.sort(key=lambda x: x.priority, reverse=True)
        if not backends:
            raise ImportError('No backend found for \'{}\''.format(self.app.auth))
        self.backends = OrderedDict()
        for obj in backends:
            self.backends[obj.name] = obj

    def user(self, name=None, refresh=False):
        """See :func:`burpui.misc.auth.interface.BUIhandler.user`"""
        key = session_manager.get_session_id() or name
        if refresh and key in self.users:
            del self.users[key]
        if session_manager.session_managed():
            session_manager.session_expired()
        if key not in self.users:
            ret = UserHandler(self.app, self.backends, name, key)
            self.users[key] = ret
            return ret
        ret = self.users[key]
        ret.refresh_session()
        self.users[key] = ret
        return ret


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
        self.name = session_manager.get_session_username() or \
            session.get('login') or name
        self.real = None
        self.admin = not self.app.acl

        for name, back in iteritems(self.backends):
            u = back.user(self.name)
            res = u.get_id()
            if res:
                self.active = True
                self.name = res
                self.back = back
                if self.app.acl:
                    self.admin = self.app.acl.is_admin(self.name)
                break

    def refresh_session(self):
        self.authenticated = session.get('authenticated', False)
        self.language = session.get('language', None)

    def login(self, passwd=None):
        """See :func:`burpui.misc.auth.interface.BUIuser.login`"""
        if not self.real:
            self.authenticated = False
            for name, back in iteritems(self.backends):
                u = back.user(self.name)
                res = u.get_id()
                if u.login(passwd):
                    self.authenticated = True
                    self.real = u
                    self.back = back
                    self.name = res
                    if self.app.acl:
                        self.admin = self.app.acl.is_admin(self.name)
                    break
        elif self.real:  # pragma: no cover
            if self.back and getattr(self.back, 'changed', False):
                self.real = None
                self.back = None
                self.admin = not self.app.acl
                return self.login(passwd)
            self.authenticated = self.real.login(passwd)
        session['authenticated'] = self.authenticated
        session['language'] = self.language
        session['login'] = self.name
        return self.authenticated
