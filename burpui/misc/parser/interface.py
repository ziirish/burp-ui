# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.parser.interface
    :platform: Unix
    :synopsis: Burp-UI parser interface.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
from burpui.misc.utils import BUIlogging


class BUIparser(BUIlogging):
    """:class:`burpui.misc.parser.interface.BUIparser` defines a generic
    interface for ``burp`` configuration files parser.
    """
    def __init__(self, app=None, conf=None):
        """:func:`burpui.misc.parser.interface.BUIparser.__init__` instanciate
        the parser.

        :param app: The application context
        :type app: :class:`burpui.server.BUIServer`

        :param conf: The main configuration file
        :type conf: str
        """
        self.app = app
        self.conf = conf
        self.logger = None
        if self.app:
            self.logger = self.app.logger

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
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def store_client_conf(self, data, client=None, conf=None):
        """:func:`burpui.misc.parser.interface.BUIparser.store_client_conf` is
        used by :func:`burpui.misc.backend.BUIbackend.store_conf_cli`.

        It works the same way as :func:`burpui.misc.parser.interface.BUIparser.store_conf`
        with an extra parameter:

        :param client: Name of the client for which to apply this config
        :type client: str
        """
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def store_conf(self, data, conf=None, mode='srv'):
        """:func:`burpui.misc.parser.interface.BUIparser.store_conf` is used to
        store the configuration from the web-ui into the actual configuration
        files.
        It is used by :func:`burpui.misc.backend.BUIbackend.store_conf_srv`.

        :param data: Data sent by the web-form
        :type data: dict

        :param conf: Force the file path (for file inclusions for instance)
        :type conf: str

        :param mode: We actually use the same method for clients and server files
        :type mode: str

        :returns: A list of notifications to return to the UI (success or
                  failure)

        Example::

            [[0, "Success"]]
        """
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def get_priv_attr(self, key):
        """:func:`burpui.misc.parser.interface.BUIparser.get_priv_attr` is used
        to retrieve some attributes from the Parser.
        It is used by :func:`burpui.misc.backend.interface.BUIbackend.get_parser_attr`

        :param key: Name of the attribute to retrieve
        :type key: str

        :returns: The requested attribute or an empty list
        """
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

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
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def remove_client(self, client=None):
        """:func:`burpui.misc.parser.interface.BUIparser.remove_client` is used
        to delete a client from burp's configuration.

        :param client: The name of the client to remove
        :type client: str
        :returns: A list of notifications to return to the UI (success or
                  failure)
        """
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def read_client_conf(self, client=None, conf=None):
        """:func:`burpui.misc.parser.interface.BUIparser.read_client_conf` is
        called by :func:`burpui.misc.backend.interface.BUIbackend.read_conf_cli`
        in order to parse the burp-clients configuration files.

        It works the same way as :func:`burpui.misc.parser.interface.BUIparser.read_server_conf`
        """
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")
