# -*- coding: utf8 -*-
import pam

from .interface import BUIhandler, BUIuser, BUIloader


class LocalLoader(BUIloader):
    """The :class:`burpui.misc.auth.local.LocalLoader` class loads the *Local*
    users.
    """
    section = name = 'LOCAL'

    def __init__(self, app=None, handler=None):
        """:func:`burpui.misc.auth.Local.localLoader.__init__` loads users from
        the configuration file.

        :param app: Instance of the app we are running in
        :type app: :class:`burpui.server.BUIServer`
        """
        self.app = app
        self.users = None
        handler.name = self.name
        conf = self.app.conf
        if self.section in conf.options:
            # Maybe the handler argument is None, maybe the 'priority'
            # option is missing. We don't care.
            try:
                handler.priority = conf.safe_get(
                    'priority',
                    'integer',
                    section=self.section
                ) or 0
            except:
                pass
            users = conf.safe_get(
                'users',
                cast='force_list',
                section=self.section
            )
            if users != [None]:
                self.users = users
        self.logger.debug('Local users: ' + str(self.users))

    def fetch(self, uid=None):
        """:func:`burpui.misc.auth.local.LocalLoader.fetch` searches for a user
        in the configuration.

        :param uid: User to search for
        :type uid: str

        :returns: The given UID if the user exists or None
        """
        if self.users is None or uid in self.users:
            return uid

        return None

    def check(self, uid=None, passwd=None):
        """:func:`burpui.misc.auth.local.LocalLoader.check` verifies if the
        given password matches the given user settings.

        :param uid: User to authenticate
        :type uid: str

        :param passwd: Password
        :type passwd: str

        :returns: True if there is a match, otherwise False
        """
        if self.users is None or uid in self.users:
            return pam.authenticate(uid, passwd, 'other')

        return False


class UserHandler(BUIhandler):
    """See :class:`burpui.misc.auth.interface.BUIhandler`"""
    def __init__(self, app=None, auth=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.__init__`"""
        self.local = LocalLoader(app, self)
        self.users = {}

    def user(self, name=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.user`"""
        if name not in self.users:
            self.users[name] = LocalUser(self.local, name)
        return self.users[name]

    @property
    def loader(self):
        return self.local


class LocalUser(BUIuser):
    """See :class:`burpui.misc.auth.interface.BUIuser`"""
    def __init__(self, local=None, name=None):
        self.active = False
        self.authenticated = False
        self.local = local
        self.name = name
        self.id = None
        self.backend = self.local.name

        res = self.local.fetch(self.name)

        if res:
            self.id = res
            self.active = True

    def login(self, passwd=None):
        """See :func:`burpui.misc.auth.interface.BUIuser.login`"""
        self.authenticated = self.local.check(self.name, passwd)
        return self.authenticated

    @property
    def is_active(self):  # pragma: no cover
        return self.active

    @property
    def is_authenticated(self):  # pragma: no cover
        return self.authenticated

    def get_id(self):
        return self.id
