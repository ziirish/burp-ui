# -*- coding: utf8 -*-
import os

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

    def user(self, name=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.user`"""
        if name not in self.users:
            self.users[name] = UserHandler(self.backends, name)
        return self.users[name]


class UserHandler(BUIuser):
    """See :class:`burpui.misc.auth.interface.BUIuser`"""
    def __init__(self, backends=None, name=None):
        sess = session._get_current_object()
        self.active = False
        self.authenticated = sess.get('authenticated', False)
        self.backends = backends
        self.back = None
        self.name = name
        self.real = None

        for name, back in iteritems(self.backends):
            u = back.user(self.name)
            res = u.get_id()
            if res:
                self.id = res
                self.active = True
                break

    def login(self, passwd=None):
        """See :func:`burpui.misc.auth.interface.BUIuser.login`"""
        if not self.real:
            self.authenticated = False
            for name, back in iteritems(self.backends):
                u = back.user(self.name)
                res = u.get_id()
                if u.login(passwd):
                    self.authenticated = True
                    self.id = res
                    self.real = u
                    self.back = back
                    break
        elif self.real:  # pragma: no cover
            if self.back and getattr(self.back, 'changed', False):
                self.real = None
                self.back = None
                return self.login(passwd)
            self.authenticated = self.real.login(passwd)
        sess = session._get_current_object()
        sess['authenticated'] = self.authenticated
        return self.authenticated

    def get_id(self):
        try:
            return unicode(self.id)
        except NameError:
            return str(self.id)
