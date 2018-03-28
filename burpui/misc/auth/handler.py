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

ACL_METHODS = BUIacl.__abstractmethods__


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
        backends.sort(key=lambda x: getattr(x, 'priority', -1), reverse=True)
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

    @property
    def loader(self):
        return None


class ProxyACLCall(object):
    """Class that actually calls the ACL method"""
    def __init__(self, acl, username, method):
        """
        :param acl: ACL to use
        :type acl: :class:`burpui.misc.acl.interface.BUIacl`

        :param username: username to check ACL for
        :type username: str

        :param method: Name of the method to proxify
        :type method: str
        """
        self.acl = acl
        self.username = username
        self.method = method

    def __call__(self, *args, **kwargs):
        """This is where the proxy call (and the magic) occurs"""
        # retrieve the original function prototype
        proto = getattr(BUIacl, self.method)
        args_name = list(proto.__code__.co_varnames)
        # skip self
        args_name.pop(0)
        # skip username
        args_name.pop(0)
        # we transform unnamed arguments to named ones
        # example:
        #     def my_function(toto, tata=None, titi=None):
        #
        #     x = my_function('blah', titi='blih')
        #
        # => {'toto': 'blah', 'titi': 'blih'}
        encoded_args = {
            'username': self.username
        }
        for idx, opt in enumerate(args):
            encoded_args[args_name[idx]] = opt
        encoded_args.update(kwargs)

        func = getattr(self.acl, self.method)
        return func(**encoded_args)


class ACLproxy(BUIacl):
    foreign = ACL_METHODS
    BUIacl.__abstractmethods__ = frozenset()

    def __init__(self, acl, username):
        self.acl = acl
        self.username = username

    def __getattribute__(self, name):
        # always return this value because we need it and if we don't do that
        # we'll end up with an infinite loop
        if name in ['foreign', 'acl', 'username']:
            return object.__getattribute__(self, name)
        # now we can retrieve the 'foreign' list and know if the object called
        # needs to be "proxyfied"
        if name in self.foreign:
            if self.acl:
                return ProxyACLCall(self.acl, self.username, name)
            # no ACL, assume true
            return ProxyTrue()
        return object.__getattribute__(self, name)


class ProxyTrue(object):
    def __call__(self, *args, **kwargs):
        return True


class ProxyFalse(object):
    def __call__(self, *args, **kwargs):
        return False


class ACLanon(BUIacl):
    foreign = ACL_METHODS
    BUIacl.__abstractmethods__ = frozenset()

    def __getattribute__(self, name):
        # always return this value because we need it and if we don't do that
        # we'll end up with an infinite loop
        if name == 'foreign':
            return object.__getattribute__(self, name)
        # now we can retrieve the 'foreign' list and know if the object called
        # needs to be "proxyfied"
        if name in self.foreign:
            return ProxyFalse()
        return object.__getattribute__(self, name)


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

    @property
    def is_moderator(self):
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
                self.real = user
                self.active = True
                self.name = res
                self.back = back
                break

        self._acl = ACLproxy(self.app.acl, self.name)
        # now load the available prefs
        self._load_prefs()

    @property
    def acl(self):
        return self._acl

    @property
    def is_admin(self):
        return self.acl.is_admin()

    @property
    def is_moderator(self):
        return self.acl.is_moderator()

    def _load_prefs(self):
        session['login'] = self.name
        if self.app.config['WITH_SQL']:
            from ...models import Pref
            prefs = Pref.query.filter_by(user=self.name).all()
            for pref in prefs:
                if pref.key == 'language':
                    continue
                if hasattr(self, pref.key):
                    setattr(self, pref.key, pref.value)
                session[pref.key] = pref.value

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
