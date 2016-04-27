# -*- coding: utf8 -*-
from .interface import BUIhandler, BUIuser
from importlib import import_module
from flask import session

import re
import os
import json


class UserAuthHandler(BUIhandler):
    """See :class:`burpui.misc.auth.interface.BUIhandler`"""
    def __init__(self, app=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.__init__`"""
        self.app = app
        self.users = {}
        self.backends = []
        if self.app.auth:
            me, _ = os.path.splitext(os.path.basename(__file__))
            try:
                back = json.loads(self.app.auth)
            except:
                back = re.split(' *,+ *', self.app.auth)
            for au in back:
                if au == me:
                    self.app.logger.error('Recursive import not permited!')
                    continue
                try:
                    (modpath, _) = __name__.rsplit('.', 1)
                    mod = import_module('.' + au, modpath)
                    obj = mod.UserHandler(self.app)
                    self.backends.append(obj)
                except:
                    pass
        self.backends.sort(key=lambda x: x.priority, reverse=True)
        if not self.backends:
            raise ImportError('No backend found for \'{}\''.format(self.app.auth))

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
        self.name = name
        self.real = None

        for back in self.backends:
            u = back.user(self.name)
            res = u.get_id()
            if res:
                self.id = res
                self.active = True
                break

    def login(self, name=None, passwd=None):
        """See :func:`burpui.misc.auth.interface.BUIuser.login`"""
        if not self.real:
            self.authenticated = False
            for back in self.backends:
                u = back.user(name)
                res = u.get_id()
                if u.login(name, passwd):
                    self.authenticated = True
                    self.id = res
                    self.real = u
                    break
        elif self.real:  # pragma: no cover
            self.authenticated = self.real.login(name, passwd)
        sess = session._get_current_object()
        sess['authenticated'] = self.authenticated
        return self.authenticated

    @property
    def is_active(self):
        return self.active

    @property
    def is_authenticated(self):
        return self.authenticated

    def get_id(self):
        try:
            return unicode(self.id)
        except NameError:
            return str(self.id)
