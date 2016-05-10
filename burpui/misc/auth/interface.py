# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.auth.interface
    :platform: Unix
    :synopsis: Burp-UI authentication interface.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask_login import UserMixin
from abc import ABCMeta, abstractmethod
import logging


class BUIloader:
    logger = logging.getLogger('burp-ui')


class BUIhandler:
    """The :class:`burpui.misc.auth.interface.BUIhandler` class maintains a list
    of ``Burp-UI`` users.
    """
    __metaclass__ = ABCMeta

    priority = 0

    def __init__(self, app=None):
        """:func:`burpui.misc.auth.interface.BUIhandler.__init__`

        :param app: Instance of the app we are running in
        :type app: :class:`burpui.server.BUIServer`
        """
        pass  # pragma: no cover

    @abstractmethod
    def user(self, name=None):
        """The :func:`burpui.misc.auth.interface.BUIhandler.user` function
        returns the :class:`flask_login.UserMixin` object corresponding to
        the given user name.

        :param name: Name of the user
        :type name: str

        :returns: The corresponding user object
        """
        return None  # pragma: no cover


class BUIuser(UserMixin):
    """The :class:`burpui.misc.auth.interface.BUIuser` class extends the
    :class:`flask_login.UserMixin` class.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def login(self, name=None, passwd=None):
        """The :func:`burpui.misc.auth.interface.BUIuser.login` function
        checks if the profided username and password match.

        :param name: Username
        :type name: str

        :param passwd: Password
        :type passwd: str

        :returns: True if the name and password match, otherwise False
        """
        return False  # pragma: no cover
