# -*- coding: utf8 -*-
from .interface import BUIhandler, BUIuser, BUIloader
from ..._compat import ConfigParser


class BasicLoader(BUIloader):
    """The :class:`burpui.misc.auth.basic.BasicLoader` class loads the *Basic*
    users.
    """
    def __init__(self, app=None, handler=None):
        """:func:`burpui.misc.auth.basic.BasicLoader.__init__` loads users from
        the configuration file.

        :param app: Instance of the app we are running in
        :type app: :class:`burpui.server.BUIServer`
        """
        self.app = app
        self.users = {
            'admin': 'admin'
        }
        conf = self.app.config['CFG']
        c = ConfigParser.ConfigParser()
        c.optionxform = str
        with open(conf) as fp:
            c.readfp(fp)
            if c.has_section('BASIC'):
                self.users = {}
                for opt in c.options('BASIC'):
                    if opt == 'priority':
                        # Maybe the handler argument is None, maybe the 'priority'
                        # option is missing. We don't care.
                        try:
                            handler.priority = c.getint('BASIC', opt)
                        except:
                            pass
                        continue  # pragma: no cover
                    self.users[opt] = c.get('BASIC', opt)
                    self.logger.info('Loading user: {}'.format(opt))

    def fetch(self, uid=None):
        """:func:`burpui.misc.auth.basic.BasicLoader.fetch` searches for a user
        in the configuration.

        :param uid: User to search for
        :type uid: str

        :returns: The given UID if the user exists or None
        """
        if uid in self.users:
            return uid

        return None

    def check(self, uid=None, passwd=None):
        """:func:`burpui.misc.auth.basic.BasicLoader.check` verifies if the
        given password matches the given user settings.

        :param uid: User to authenticate
        :type uid: str

        :param passwd: Password
        :type passwd: str

        :returns: True if there is a match, otherwise False
        """
        return uid in self.users and self.users[uid] == passwd


class UserHandler(BUIhandler):
    """See :class:`burpui.misc.auth.interface.BUIhandler`"""
    def __init__(self, app=None, auth=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.__init__`"""
        self.basic = BasicLoader(app, self)
        self.users = {}

    def user(self, name=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.user`"""
        if name not in self.users:
            self.users[name] = BasicUser(self.basic, name)
        return self.users[name]


class BasicUser(BUIuser):
    """See :class:`burpui.misc.auth.interface.BUIuser`"""
    def __init__(self, basic=None, name=None):
        self.active = False
        self.authenticated = False
        self.basic = basic
        self.name = name
        self.id = None

        res = self.basic.fetch(self.name)

        if res:
            self.id = res
            self.active = True

    def login(self, name=None, passwd=None):
        """See :func:`burpui.misc.auth.interface.BUIuser.login`"""
        self.authenticated = self.basic.check(name, passwd)
        return self.authenticated

    @property
    def is_active(self):  # pragma: no cover
        return self.active

    @property
    def is_authenticated(self):  # pragma: no cover
        return self.authenticated

    def get_id(self):
        return self.id
