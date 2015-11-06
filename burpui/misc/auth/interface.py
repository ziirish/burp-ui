# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.auth.interface
    :platform: Unix
    :synopsis: Burp-UI authentication interface.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
from flask.ext.login import UserMixin, AnonymousUserMixin


class BUIhandler:
    """The :class:`burpui.misc.auth.interface.BUIhandler` class maintains a list
    of ``Burp-UI`` users.
    """

    priority = 0

    def __init__(self, app=None, auth=None):
        """:func:`burpui.misc.auth.interface.BUIhandler.__init__`

        :param app: Instance of the app we are running in
        :type app: :class:`burpui.server.BUIServer`

        :param auth: List au authentication backends to load
        :type auth: str
        """
        pass  # pragma: no cover

    def user(self, name=None):
        """The :func:`burpui.misc.auth.interface.BUIhandler.user` function
        returns the :class:`flask.ext.login.UserMixin` object corresponding to
        the given user name.

        :param name: Name of the user
        :type name: str

        :returns: The corresponding user object
        """
        return None


class BUIuser(UserMixin):
    """The :class:`burpui.misc.auth.interface.BUIuser` class extends the
    :class:`flask.ext.login.UserMixin` class.
    """
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
