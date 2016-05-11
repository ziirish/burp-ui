# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.parser.interface
    :platform: Unix
    :synopsis: Burp-UI parser interface.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from abc import ABCMeta, abstractmethod

import logging


class BUIparser(object):
    """:class:`burpui.misc.parser.interface.BUIparser` defines a generic
    interface for ``burp`` configuration files parser.
    """
    __metaclass__ = ABCMeta

    logger = logging.getLogger('burp-ui')

    def __init__(self, backend=None):
        """:func:`burpui.misc.parser.interface.BUIparser.__init__` instanciate
        the parser.

        :param backend: The application backend
        :type backend: :class:`burpui.misc.backend.BUIbackend`
        """
        self.backend = backend
        self.conf = backend.burpconfsrv

    @abstractmethod
    def read_server_conf(self, conf=None):
        """:func:`burpui.misc.parser.interface.BUIparser.read_server_conf` is
        called by :func:`burpui.misc.backend.interface.BUIbackend.read_conf_srv`
        in order to parse the burp-server configuration file.

        :param conf: Complementary configuration file (for instance, file
                     inclusions)
        :type conf: str

        :returns: Dict of options

        Example::

            {
                "boolean": [
                    {
                        "name": "hardlinked_archive",
                        "value": false
                    },
                    {
                        "name": "syslog",
                        "value": true
                    },
                ],
                "clients": [
                    {
                        "name": "client1",
                        "value": "/etc/burp/clientconfdir/client1"
                    },
                    {
                        "name": "client2",
                        "value": "/etc/burp/clientconfdir/client2"
                    },
                ],
                "common": [
                    {
                        "name": "mode",
                        "value": "server"
                    },
                    {
                        "name": "directory",
                        "value": "/srv/burp"
                    },
                ],
                "includes": [],
                "includes_ext": [],
                "integer": [
                    {
                        "name": "port",
                        "value": 4971
                    },
                    {
                        "name": "status_port",
                        "value": 4972
                    },
                    {
                        "name": "max_children",
                        "value": 5
                    },
                    {
                        "name": "max_status_children",
                        "value": 5
                    }
                ],
                "multi": [
                    {
                        "name": "keep",
                        "value": [
                            "7",
                            "4",
                            "4"
                        ]
                    },
                    {
                        "name": "timer_arg",
                        "value": [
                            "12h",
                            "Mon,Tue,Thu,Fri,17,18,19,20,21,22,23",
                            "Wed,Sat,Sun,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23"
                        ]
                    },
                ],
            }
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def store_client_conf(self, data, client=None, conf=None):
        """:func:`burpui.misc.parser.interface.BUIparser.store_client_conf` is
        used by :func:`burpui.misc.backend.BUIbackend.store_conf_cli`.

        It works the same way as
        :func:`burpui.misc.parser.interface.BUIparser.store_conf`
        with an extra parameter:

        :param client: Name of the client for which to apply this config
        :type client: str
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def store_conf(self, data, conf=None, mode='srv'):
        """:func:`burpui.misc.parser.interface.BUIparser.store_conf` is used to
        store the configuration from the web-ui into the actual configuration
        files.
        It is used by :func:`burpui.misc.backend.BUIbackend.store_conf_srv`.

        :param data: Data sent by the web-form
        :type data: dict

        :param conf: Force the file path (for file inclusions for instance)
        :type conf: str

        :param mode: We actually use the same method for clients and server
                     files
        :type mode: str

        :returns: A list of notifications to return to the UI (success or
                  failure)

        Example::

            [[0, "Success"]]
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def path_expander(self, pattern=None, client=None):
        """:func:`burpui.misc.parser.interface.BUIparser.path_expander` is used
        to expand path of file inclusions glob the user can set in the setting
        panel.

        :param pattern: The glob/path to expand
        :type pattern: str

        :param client: The client name when working on client files
        :type client: str

        :returns: A list of files or an empty list
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def list_clients(self):
        """:func:`burpui.misc.parser.interface.BUIparser.list_clients` is used
        to retrieve a list of clients with their configuration file.

        :returns: A list of clients with their configuration file
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def remove_client(self, client=None):
        """:func:`burpui.misc.parser.interface.BUIparser.remove_client` is used
        to delete a client from burp's configuration.

        :param client: The name of the client to remove
        :type client: str
        :returns: A list of notifications to return to the UI (success or
                  failure)
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def read_client_conf(self, client=None, conf=None):
        """:func:`burpui.misc.parser.interface.BUIparser.read_client_conf` is
        called by :func:`burpui.misc.backend.interface.BUIbackend.read_conf_cli`
        in order to parse the burp-clients configuration files.

        It works the same way as
        :func:`burpui.misc.parser.interface.BUIparser.read_server_conf`
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def cancel_restore(self, name=None):
        """:func:`burpui.misc.parser.interface.BUIparser.cancel_restore` called
        by
        :func:`burpui.misc.backend.interface.BUIbackend.cancel_server_restore`
        in order to cancel a server-initiated restoration.

        :param name: Client name
        :type name: str

        :returns: A list of notifications to return to the UI (success or
                  failure)
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def read_restore(self, name=None):
        """:func:`burpui.misc.parser.interface.BUIparser.read_restore` called
        by :func:`burpui.misc.backend.interface.BUIbackend.is_server_restore`
        in order to read a server-initiated restoration file.

        :param name: Client name
        :type name: str

        :returns: A dict describing the content of the file
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def server_initiated_restoration(
            self,
            name=None,
            backup=None,
            files=None,
            strip=None,
            force=None,
            prefix=None,
            restoreto=None):
        """
        :func:`burpui.misc.parser.interface.BUIparser.server_initiated_restoration`
        called by :func:`burpui.misc.backend.interface.BUIbackend.server_restore`
        in order to create server-initiated restoration file.

        :param name: Client name
        :type name: str

        :param backup: Backup number
        :type backup: int

        :param files: List of files to restore
        :type files: str

        :param strip: Number of leading path to strip
        :type strip: int

        :param force: Whether to force overriding files or not
        :type force: bool

        :param prefix: Where to restore files
        :type prefix: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of notifications to return to the UI (success or
                  failure)
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def cancel_backup(self, name=None):
        """:func:`burpui.misc.parser.interface.BUIparser.cancel_backup` called
        by :func:`burpui.misc.backend.interface.BUIbackend.cancel_server_backup`
        in order to cancel a server-initiated backup.

        :param name: Client name
        :type name: str

        :returns: A list of notifications to return to the UI (success or
                  failure)
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def read_backup(self, name=None):
        """:func:`burpui.misc.parser.interface.BUIparser.read_backup` called
        by :func:`burpui.misc.backend.interface.BUIbackend.is_server_backup`
        in order to test the existence of a server-initiated backup file.

        :param name: Client name
        :type name: str

        :returns: A True if the file is found, else False.
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def server_initiated_backup(self, name=None):
        """:func:`burpui.misc.parser.interface.BUIparser.server_initiated_backup`
        called by :func:`burpui.misc.backend.interface.BUIbackend.server_backup`
        in order to create a server-initiated backup file.

        :param name: Client name
        :type name: str

        :returns: A list of notifications to return to the UI (success or
                  failure)
        """
        raise NotImplementedError(
            "Sorry, the current Parser does not implement this method!"
        )  # pragma: no cover
