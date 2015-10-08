# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.acl.interface
    :platform: Unix
    :synopsis: Burp-UI ACL interface.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""


class BUIaclLoader:
    """The :class:`burpui.misc.acl.interface.BUIaclLoader` class is used to
    load the actual ACL backend"""
    def __init__(self, app=None, standalone=False):
        """:func:`burpui.misc.acl.interface.BUIaclLoader.__init__` instanciate
        the loader.

        :param app: Application context
        :type app: :class:`burpui.server.BUIServer`

        :param standalone: Multi-agent or standalone mode
        :type standalone: bool
        """
        pass

    @property
    def acl(self):
        """Property to retrieve the backend"""
        return None


class BUIacl:
    """The :class:`burpui.misc.acl.interface.BUIacl` class represents the ACL
    engine.
    """
    def is_admin(self, username=None):
        """:func:`burpui.misc.acl.interface.BUIacl.is_admin` is used to know if
        a user has administrator rights.

        :param username: Username to check
        :type username: str

        :returns: True if the user has admin rights, otherwise False
        """
        return False

    def clients(self, username=None, server=None):
        """:func:`burpui.misc.acl.interface.BUIacl.clients` returns a list of
        allowed clients for a given user.

        :param username: Username to check
        :type username: str

        :param server: Server name. Used in multi-agent mode
        :type server: str

        :returns: A list of clients
        """
        return []

    def servers(self, username=None):
        """:func:`burpui.misc.acl.interface.BUIacl.servers` returns a list of
        allowed servers for a given user.

        :param username: Username to check
        :type username: str

        :returns: A list of servers
        """
        return []

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
        return False
