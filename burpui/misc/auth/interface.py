# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.auth.interface
    :platform: Unix
    :synopsis: Burp-UI authentication interface.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask_login import UserMixin, AnonymousUserMixin
from abc import ABCMeta, abstractmethod, abstractproperty
from six import with_metaclass

import logging


class BUIloader:
    logger = logging.getLogger('burp-ui')


class BUIhandler(with_metaclass(ABCMeta, object)):
    """The :class:`burpui.misc.auth.interface.BUIhandler` class maintains a list
    of ``Burp-UI`` users.

    :param app: Instance of the app we are running in
    :type app: :class:`burpui.server.BUIServer`
    """

    priority = 0

    name = None

    add_user = False
    del_user = False
    change_password = False

    preload_users = True

    @abstractmethod
    def user(self, name=None, refresh=False):
        """The :func:`burpui.misc.auth.interface.BUIhandler.user` function
        returns the :class:`flask_login:flask_login.UserMixin` object
        corresponding to the given user name.

        :param name: Name of the user
        :type name: str

        :param refresh: Whether we need to re-create a fresh user or not
        :type refresh: bool

        :returns: :class:`burpui.misc.auth.interface.BUIuser`
        """
        return AnonymousUserMixin()

    def remove(self, name):
        """The :func:`burpui.misc.auth.interface.BUIhandler.remove` function
        allows to remove a user from the cache.

        :param name: Name of the user to remove
        :type name: str
        """
        pass

    @abstractproperty
    @property
    def loader(self):
        return None


class BUIuser(with_metaclass(ABCMeta, UserMixin)):
    """The :class:`burpui.misc.auth.interface.BUIuser` class extends the
    :class:`flask_login:flask_login.UserMixin` class.
    """
    backend = None
    admin = True
    moderator = True

    @abstractmethod
    def login(self, passwd=None):
        """The :func:`burpui.misc.auth.interface.BUIuser.login` function
        checks if the profided username and password match.

        :param passwd: Password
        :type passwd: str

        :returns: True if the name and password match, otherwise False
        """
        return False  # pragma: no cover

    @property
    def is_active(self):
        """
        :returns: True if user is active, otherwise False
        """
        return self.active

    @property
    def is_authenticated(self):
        """
        :returns: True if a user is authenticated, otherwise False
        """
        return self.authenticated

    @property
    def is_admin(self):
        """
        If no ACL engine is loaded, every logged-in user will be granted admin
        rights
        :returns: True if the user is admin, otherwise False
        """
        return self.admin

    @property
    def is_moderator(self):
        """
        If no ACL engine is loaded, every logged-in user will be granted
        moderator rights
        :returns: True if the user is moderator, otherwise False
        """
        return self.moderator

    def __str__(self):
        msg = UserMixin.__str__(self)
        return '{} (id: {}, admin: {}, authenticated: {}, active: {})'.format(
            msg,
            self.get_id(),
            self.is_admin,
            self.is_authenticated,
            self.is_active
        )
