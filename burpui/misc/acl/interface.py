# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.acl.interface
    :platform: Unix
    :synopsis: Burp-UI ACL interface.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import logging
from abc import ABCMeta, abstractmethod, abstractproperty


class BUIaclLoader(object, metaclass=ABCMeta):
    """The :class:`burpui.misc.acl.interface.BUIaclLoader` class is used to
    load the actual ACL backend"""

    logger = logging.getLogger("burp-ui")
    priority = 0

    add_grant = False
    del_grant = False
    mod_grant = False

    add_group = False
    del_group = False
    mod_group = False

    add_group_member = False
    del_group_member = False

    add_moderator = False
    del_moderator = False
    mod_moderator = False

    add_admin = False
    del_admin = False

    moderator = None
    moderators = []

    admins = []

    def __init__(self, app=None):
        """:func:`burpui.misc.acl.interface.BUIaclLoader.__init__` instanciate
        the loader.

        :param app: Application context
        :type app: :class:`burpui.engines.server.BUIServer`
        """
        self.app = None
        if app:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        """Register the given app"""
        self.app = app

    @abstractmethod
    def reload(self):
        """Reload the backend"""
        return None  # pragma: no cover

    @abstractproperty
    @property
    def acl(self):
        """Property to retrieve the backend"""
        return None  # pragma: no cover

    @abstractproperty
    @property
    def grants(self):
        """Property to retrieve the list of grants"""
        return None  # pragma: no cover

    @abstractproperty
    @property
    def groups(self):
        """Property to retrieve the list of groups with their members"""
        return None  # pragma: no cover


class BUIacl(object, metaclass=ABCMeta):
    """The :class:`burpui.misc.acl.interface.BUIacl` class represents the ACL
    engine.
    """

    def __init__(self, app=None):
        """:func:`burpui.misc.acl.interface.BUIacl.__init__` instanciate
        the ACL.

        :param app: Application context
        :type app: :class:`burpui.engines.server.BUIServer`
        """
        self.app = None
        if app:  # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        """Register the given app"""
        self.app = app

    @abstractmethod
    def is_admin(self, username=None):
        """:func:`burpui.misc.acl.interface.BUIacl.is_admin` is used to know if
        a user has administrator rights.

        :param username: Username to check
        :type username: str

        :returns: True if the user has admin rights, otherwise False
        :rtype: bool
        """
        return False  # pragma: no cover

    @abstractmethod
    def is_moderator(self, username=None):
        """:func:`burpui.misc.acl.interface.BUIacl.is_moderator` is used to
        know if a user has moderator rights.

        :param username: Username to check
        :type username: str

        :returns: True if the user has moderator rights, otherwise False
        :rtype: bool
        """
        return False  # pragma: no cover

    @abstractmethod
    def is_client_rw(self, username=None, client=None, server=None):
        """:func:`burpui.misc.acl.interface.BUIacl.is_client_rw` tells us
        if a given user has access to a given client on a given server in RW
        mode.

        :param username: Username to check
        :type username: str

        :param client: Client to check
        :type client: str

        :param server: Server to check
        :type server: str

        :returns: True if username is granted, otherwise False
        :rtype: bool
        """
        return False  # pragma: no cover

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
        :rtype: bool
        """
        return False  # pragma: no cover

    @abstractmethod
    def is_server_rw(self, username=None, server=None):
        """:func:`burpui.misc.acl.interface.BUIacl.is_server_rw` tells us
        if a given user has access to a given server in RW mode.

        :param username: Username to check
        :type username: str

        :param server: Server to check
        :type server: str

        :returns: True if username is granted, otherwise False
        :rtype: bool
        """
        return False  # pragma: no cover

    @abstractmethod
    def is_server_allowed(self, username=None, server=None):
        """:func:`burpui.misc.acl.interface.BUIacl.is_server_allowed` tells us
        if a given user has access to a given server.

        :param username: Username to check
        :type username: str

        :param server: Server to check
        :type server: str

        :returns: True if username is granted, otherwise False
        :rtype: bool
        """
        return False  # pragma: no cover
