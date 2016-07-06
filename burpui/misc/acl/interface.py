# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.acl.interface
    :platform: Unix
    :synopsis: Burp-UI ACL interface.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from abc import ABCMeta, abstractmethod, abstractproperty
from six import with_metaclass

import logging


class BUIaclLoader(with_metaclass(ABCMeta, object)):
    """The :class:`burpui.misc.acl.interface.BUIaclLoader` class is used to
    load the actual ACL backend"""

    logger = logging.getLogger('burp-ui')

    def __init__(self, app=None):
        """:func:`burpui.misc.acl.interface.BUIaclLoader.__init__` instanciate
        the loader.

        :param app: Application context
        :type app: :class:`burpui.server.BUIServer`
        """
        pass  # pragma: no cover

    @abstractproperty
    @property
    def acl(self):
        """Property to retrieve the backend"""
        return None  # pragma: no cover


class BUIacl(with_metaclass(ABCMeta, object)):
    """The :class:`burpui.misc.acl.interface.BUIacl` class represents the ACL
    engine.
    """

    @abstractmethod
    def is_admin(self, username=None):
        """:func:`burpui.misc.acl.interface.BUIacl.is_admin` is used to know if
        a user has administrator rights.

        :param username: Username to check
        :type username: str

        :returns: True if the user has admin rights, otherwise False
        """
        return False  # pragma: no cover

    @abstractmethod
    def clients(self, username=None, server=None):
        """:func:`burpui.misc.acl.interface.BUIacl.clients` returns a list of
        allowed clients for a given user.

        :param username: Username to check
        :type username: str

        :param server: Server name. Used in multi-agent mode
        :type server: str

        :returns: A list of clients
        """
        return []  # pragma: no cover

    @abstractmethod
    def servers(self, username=None):
        """:func:`burpui.misc.acl.interface.BUIacl.servers` returns a list of
        allowed servers for a given user.

        :param username: Username to check
        :type username: str

        :returns: A list of servers
        """
        return []  # pragma: no cover

    @abstractmethod
    def is_client_allowed(self, username=None, client=None, server=None):
        """:func:`burpui.misc.acl.interface.BUIacl.is_client_allowed` tells us
        if a given user has access to a given client on a given server.

        :param username: Username to check
        :type username: str

        :param client: Client to check
        :type client: str

        :param server: Server to check
        :type server: str

        :returns: True if username is granted, otherwise False
        """
        return False  # pragma: no cover
