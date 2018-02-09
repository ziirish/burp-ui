# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.acl.interface
    :platform: Unix
    :synopsis: Burp-UI ACL interface.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from ...utils import make_list

from abc import ABCMeta, abstractmethod, abstractproperty
from six import with_metaclass, iteritems

import logging


class BUIaclLoader(with_metaclass(ABCMeta, object)):
    """The :class:`burpui.misc.acl.interface.BUIaclLoader` class is used to
    load the actual ACL backend"""

    logger = logging.getLogger('burp-ui')
    priority = 0

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

    def clients(self, username=None, server=None):
        """:func:`burpui.misc.acl.interface.BUIacl.clients` returns a list of
        allowed clients for a given user.

        :param username: Username to check
        :type username: str

        :param server: Server name. Used in multi-agent mode
        :type server: str

        :returns: A list of clients
        :rtype: list

        ..deprecated:: 0.6.0
        """
        return []  # pragma: no cover

    def servers(self, username=None):
        """:func:`burpui.misc.acl.interface.BUIacl.servers` returns a list of
        allowed servers for a given user.

        :param username: Username to check
        :type username: str

        :returns: A list of servers
        :rtype: list

        ..deprecated:: 0.6.0
        """
        return []  # pragma: no cover

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

    def _merge_data(self, d1, d2):
        """Merge data as list or dict recursively avoiding duplicates"""
        if not d2:
            return d1
        if not d1:
            return d2
        if isinstance(d1, list) and isinstance(d2, list):
            return list(set(d1 + d2))
        if isinstance(d1, list) and not isinstance(d2, dict):
            if d2 in d1:
                return d1
            return d1 + [d2]
        if isinstance(d2, list) and not isinstance(d1, dict):
            if d1 in d2:
                return d2
            return d2 + [d1]
        if not isinstance(d1, dict) and not isinstance(d2, dict):
            if d1 == d2:
                return [d1]
            else:
                return [d1, d2]

        res = d1
        for key2, val2 in iteritems(d2):
            if key2 in res:
                res[key2] = self._merge_data(val2, res[key2])
            else:
                res[key2] = val2
        return res

    def _parse_clients(self, data, mode=None):
        agents = clients = []
        advanced = {}
        if isinstance(data, list):
            if mode:
                advanced[mode] = {'clients': data}
            return data, agents, advanced
        if not isinstance(data, dict):
            if mode:
                advanced[mode] = {'clients': make_list(data)}
            return make_list(data), agents, advanced
        for key, val in iteritems(data):
            if key in ['agents', 'clients', 'ro', 'rw']:
                continue
            cl1, ag1, ad1 = self._parse_clients(val)
            agents = self._merge_data(agents, ag1)
            clients = self._merge_data(clients, cl1)
            agents = self._merge_data(agents, key)
            advanced = self._merge_data(advanced, ad1)
            advanced = self._merge_data(advanced, {key: cl1})
            if mode:
                advanced = self._merge_data(advanced, {mode: {key: cl1}})

        for key in ['clients', 'ro', 'rw']:
            md = None
            if key in data:
                if key in ['ro', 'rw']:
                    md = key
                cl2, ag2, ad2 = self._parse_clients(data[key], md)
                agents = self._merge_data(agents, ag2)
                clients = self._merge_data(clients, cl2)
                advanced = self._merge_data(advanced, ad2)

        if 'agents' in data:
            ag3, cl3, ad3 = self._parse_agents(data['agents'])
            agents = self._merge_data(agents, ag3)
            clients = self._merge_data(clients, cl3)
            advanced = self._merge_data(advanced, ad3)

        return make_list(clients), make_list(agents), advanced

    def _parse_agents(self, data, mode=None):
        agents = clients = []
        advanced = {}
        if isinstance(data, list):
            if mode:
                advanced[mode] = {'agents': data}
            return data, clients, advanced
        if not isinstance(data, dict):
            if mode:
                advanced[mode] = {'agents': make_list(data)}
            return make_list(data), clients, advanced
        for key, val in iteritems(data):
            if key in ['agents', 'clients', 'ro', 'rw']:
                continue
            cl1, ag1, ad1 = self._parse_clients(data)
            agents = self._merge_data(agents, ag1)
            clients = self._merge_data(clients, cl1)
            agents = self._merge_data(agents, key)
            advanced = self._merge_data(advanced, ad1)
            advanced = self._merge_data(advanced, {key: cl1})
            if mode:
                advanced = self._merge_data(advanced, {mode: {key: cl1}})

        for key in ['agents', 'ro', 'rw']:
            md = None
            if key in data:
                if key in ['ro', 'rw']:
                    md = key
                ag2, cl2, ad2 = self._parse_agents(data[key], md)
                agents = self._merge_data(agents, ag2)
                clients = self._merge_data(clients, cl2)
                advanced = self._merge_data(advanced, ad2)

        if 'clients' in data:
            cl3, ag3, ad3 = self._parse_clients(data['clients'])
            agents = self._merge_data(agents, ag3)
            clients = self._merge_data(clients, cl3)
            advanced = self._merge_data(advanced, ad3)

        return make_list(agents), make_list(clients), advanced
