# -*- coding: utf8 -*-
import re

from .interface import BUIhandler, BUIuser, BUIloader
from ...utils import NOTIF_ERROR, NOTIF_OK, NOTIF_WARN
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
        self.conf_id = None
        self.users = {}
        self.handler = handler
        self.handler.name = self.name
        self.handler.add_user = self.add_user
        self.handler.del_user = self.del_user
        self.handler.change_password = self.change_password
        self.load_users(True)

    def load_users(self, force=False):
        if not force and self.conf_id:
            if not self.conf.changed(self.conf_id):
                return False

        self.users = {
            'admin': {'pwd': generate_password_hash('admin'), 'salted': True}
        }

        if self.section in self.conf.options:
            # check passwords are salted
            salted = False
            changed = False
            # This is not necessary for now. Maybe will use this some day
            # TODO: clean this?
            # if len(self.conf.options.comments[self.section]) > 0:
            #     if re.match(
            #             r'^\s*#+\s*@salted@',
            #             self.conf.options.comments[self.section][-1]):
            #         salted = True
            # allow mixed logins (plain and hashed)
            mixed = self.conf.safe_get(
                'mixed',
                cast='boolean',
                section=self.section,
                defaults=False
            )
            self.users = {}
            for opt in self.conf.options.get(self.section).keys():
                salt = True
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
                # list of reserved options
                if opt in ['mixed']:
                    continue
                pwd = self.conf.safe_get(opt, section=self.section)
                if not salted or mixed:
                    if not re.match(r'^pbkdf2:.+\$.+\$.+', pwd):
                        if mixed:
                            salt = False
                        else:
                            # mixed not allowed so we convert plain passwords
                            # TODO: in further versions we should not convert
                            # the passwords anymore but we should skip the user
                            pwd = generate_password_hash(pwd)
                            self.conf.options[self.section][opt] = pwd
                            changed = True
                self.users[opt] = {'pwd': pwd, 'salted': salt}
                self.logger.info('Loading user: {} ({})'.format(
                    opt,
                    'hashed' if salt else 'plain')
                )

            if changed:
                self.conf.options.write()
            # if not salted:
            #     self.conf.options.comments[self.section].append(
            #         '# Please DO NOT touch the following line'
            #     )
            #     self.conf.options.comments[self.section].append('# @salted@')
            #     self.conf.options.write()
            self.conf_id = self.conf.id
        return True

    def fetch(self, uid=None):
        """:func:`burpui.misc.auth.basic.BasicLoader.fetch` searches for a user
        in the configuration.

        :param uid: User to search for
        :type uid: str

        :returns: The given UID if the user exists or None
        """
        self.load_users()
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
        self.load_users()
        if uid in self.users:
            if self.users[uid]['salted']:
                return check_password_hash(self.users[uid]['pwd'], passwd)
            else:
                return self.users[uid]['pwd'] == passwd
        return False

    def _setup_users(self):
        """Setup user management"""
        if not self.conf.lookup_section(self.section):
            self.conf._refresh()

    def add_user(self, user, passwd):
        """Add a user"""
        self._setup_users()
        if user in self.users:
            message = "user '{}' already exists".format(user)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        pwd = generate_password_hash(passwd)
        self.conf.options[self.section][user] = pwd
        self.conf.options.write()
        self.load_users(True)
        message = "user '{}' successfully added".format(user)
        return True, message, NOTIF_OK

    def del_user(self, user):
        """Delete a user"""
        self._setup_users()
        self.load_users(True)
        if user not in self.users:
            message = "user '{}' does not exist".format(user)
            self.logger.error(message)
            return False, message, NOTIF_ERROR
        if user == 'admin' and len(self.users.keys()) == 1:
            message = 'trying to delete the admin account!'
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        del self.conf.options[self.section][user]
        del self.users[user]
        self.conf.options.write()
        self.load_users(True)
        message = "user '{}' successfully removed".format(user)
        return True, message, NOTIF_OK

    def change_password(self, user, passwd, old_passwd=None):
        """Change a user password"""
        self._setup_users()
        self.load_users(True)
        if user not in self.users:
            message = "user '{}' does not exist".format(user)
            self.logger.error(message)
            return False, message, NOTIF_ERROR
        current = self.users[user]
        if current['salted']:
            func = check_password_hash
        else:
            def func(x, y):
                return x == y
        curr = current['pwd']
        if old_passwd and not func(curr, old_passwd):
            message = "unable to authenticate user '{}'".format(user)
            self.logger.error(message)
            return False, message, NOTIF_ERROR
        if func(curr, passwd):
            message = 'password is the same'
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        pwd = generate_password_hash(passwd)
        self.conf.options[self.section][user] = pwd
        self.conf.options.write()
        self.load_users(True)
        message = "user '{}' successfully updated".format(user)
        return True, message, NOTIF_OK


class UserHandler(BUIhandler):
    """See :class:`burpui.misc.auth.interface.BUIhandler`"""
    def __init__(self, app=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.__init__`"""
        self.basic = BasicLoader(app, self)
        self.change = False
        self.users = {}

    def user(self, name=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.user`"""
        if name not in self.users:
            self.change = self.basic.load_users()
            self.users[name] = BasicUser(self.basic, name)
        return self.users[name]

    @property
    def changed(self):
        ret = self.change or self.basic.load_users()
        self.change = False
        return ret

    @property
    def loader(self):
        return self.basic


class BasicUser(BUIuser):
    """See :class:`burpui.misc.auth.interface.BUIuser`"""
    def __init__(self, basic=None, name=None):
        self.active = False
        self.authenticated = False
        self.basic = basic
        self.name = name
        self.id = None
        self.backend = self.basic.name

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
