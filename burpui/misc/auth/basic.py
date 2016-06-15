# -*- coding: utf8 -*-
import re

from .interface import BUIhandler, BUIuser, BUIloader
from werkzeug.security import check_password_hash, generate_password_hash


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
        conf = self.app.conf
        if 'BASIC' in conf.options:
            # check passwords are salted
            salted = False
            if len(conf.options.comments['BASIC']) > 0:
                if re.match(
                        r'^\s*#+\s*@salted@',
                        conf.options.comments['BASIC'][-1]):
                    salted = True
            self.users = {}
            for opt in conf.options.get('BASIC').keys():
                if opt == 'priority':
                    # Maybe the handler argument is None, maybe the 'priority'
                    # option is missing. We don't care.
                    try:
                        handler.priority = conf.safe_get(opt, section='BASIC')
                    except:
                        pass
                    continue  # pragma: no cover
                pwd = conf.safe_get(opt, section='BASIC')
                if not salted:
                    pwd = generate_password_hash(pwd)
                    conf.options['BASIC'][opt] = pwd
                self.users[opt] = pwd
                self.logger.info('Loading user: {}'.format(opt))

            if not salted:
                conf.options.comments['BASIC'].append(
                    '# Please DO NOT touch the following line'
                )
                conf.options.comments['BASIC'].append('# @salted@')
                conf.options.write()

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
        return uid in self.users and \
            check_password_hash(self.users[uid], passwd)


class UserHandler(BUIhandler):
    """See :class:`burpui.misc.auth.interface.BUIhandler`"""
    def __init__(self, app=None):
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

    def get_id(self):
        return self.id
