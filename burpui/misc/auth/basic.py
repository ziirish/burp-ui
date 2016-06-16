# -*- coding: utf8 -*-
import re
import codecs

from .interface import BUIhandler, BUIuser, BUIloader
from werkzeug.security import check_password_hash, generate_password_hash


class BasicLoader(BUIloader):
    """The :class:`burpui.misc.auth.basic.BasicLoader` class loads the *Basic*
    users.
    """
    section = name = 'BASIC'

    def __init__(self, app=None, handler=None):
        """:func:`burpui.misc.auth.basic.BasicLoader.__init__` loads users from
        the configuration file.

        :param app: Instance of the app we are running in
        :type app: :class:`burpui.server.BUIServer`

        :param handler: Instance of handler
        :type handler: :class:`burpui.misc.auth.interface.BUIhandler`
        """
        self.app = app
        self.conf = self.app.conf
        self.handler = handler
        self.handler.add_user = self.add_user
        self.handler.del_user = self.del_user
        self.handler.change_password = self.change_password
        self._load_users()

    def _load_users(self):
        self.users = {
            'admin': generate_password_hash('admin')
        }
        if self.section in self.conf.options:
            # check passwords are salted
            salted = False
            if len(self.conf.options.comments[self.section]) > 0:
                if re.match(
                        r'^\s*#+\s*@salted@',
                        self.conf.options.comments[self.section][-1]):
                    salted = True
            self.users = {}
            for opt in self.conf.options.get(self.section).keys():
                if opt == 'priority':
                    # Maybe the handler argument is None, maybe the 'priority'
                    # option is missing. We don't care.
                    try:
                        self.handler.priority = self.conf.safe_get(
                            opt,
                            section=self.section
                        ) or 0
                    except:
                        pass
                    continue  # pragma: no cover
                pwd = self.conf.safe_get(opt, section=self.section)
                if not salted:
                    pwd = generate_password_hash(pwd)
                    self.conf.options[self.section][opt] = pwd
                self.users[opt] = pwd
                self.logger.info('Loading user: {}'.format(opt))

            if not salted:
                self.conf.options.comments[self.section].append(
                    '# Please DO NOT touch the following line'
                )
                self.conf.options.comments[self.section].append('# @salted@')
                self.conf.options.write()

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

    def _setup_users(self):
        """Setup user management"""
        if self.section not in self.conf.options:
            # look for the section in the comments
            conffile = self.conf.options.filename
            last = ''
            ori = []
            with codecs.open(conffile, 'r', 'utf-8') as config:
                ori = [x.rstrip('\n') for x in config.readlines()]
            if ori:
                with codecs.open(conffile, 'w', 'utf-8') as config:
                    found = False
                    for line in ori:
                        if re.match(r'^\s*#+\s*\[{}\]'.format(self.section),
                                    line):
                            if not last or \
                                    not re.match(r'^\s*#+\s*@salted@', last):
                                config.write(
                                    '# Please DO NOT touch the following line\n'
                                )
                                config.write('# @salted@\n')

                            config.write('[{}]\n'.format(self.section))
                            found = True
                        else:
                            config.write('{}\n'.format(line))
                            last = line

                    if not found:
                        config.write(
                            '# Please DO NOT touch the following line\n'
                        )
                        config.write('# @salted@\n')
                        config.write('[{}]\n'.format(self.section))

            self.conf.options.reload()

    def add_user(self, user, passwd):
        """Add a user"""
        self._setup_users()
        if user in self.users:
            self.logger.warning("user '{}' already exists".format(user))
            return False
        pwd = generate_password_hash(passwd)
        self.conf.options[self.section][user] = pwd
        self.conf.options.write()
        self._load_users()
        return True

    def del_user(self, user):
        """Delete a user"""
        self._setup_users()
        if user not in self.users:
            self.logger.error("user '{}' does not exist".format(user))
            return False
        if user == 'admin' and len(self.users.keys()) == 1:
            self.logger.warning('trying to delete the admin account!')
            return False
        del self.conf.options[self.section][user]
        self.conf.options.write()
        self._load_users()
        return True

    def change_password(self, user, passwd):
        """Change a user password"""
        self._setup_users()
        if user not in self.users:
            self.logger.error("user '{}' does not exist".format(user))
            return False
        if check_password_hash(self.users[user], passwd):
            self.logger.warning('password is the same')
            return False
        pwd = generate_password_hash(passwd)
        self.conf.options[self.section][user] = pwd
        self.conf.options.write()
        self._load_users()
        return True


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

    def login(self, passwd=None):
        """See :func:`burpui.misc.auth.interface.BUIuser.login`"""
        self.authenticated = self.basic.check(self.name, passwd)
        return self.authenticated

    def get_id(self):
        return self.id
