# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.backend.interface
    :platform: Unix
    :synopsis: Burp-UI backend interface.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import logging

from abc import ABCMeta, abstractmethod

from ..._compat import ConfigParser


class BUIbackend(object):
    """The :class:`burpui.misc.backend.interface.BUIbackend` class provides
    a consistent interface backend for any ``burp`` server.

    :param server: ``Flask`` server instance in order to access logger
                   and/or some global settings
    :type server: :class:`burpui.server.BUIServer`

    :param conf: Configuration file to use
    :type conf: str
    """
    __metaclass__ = ABCMeta

    # cache the running clients
    running = []
    # do we need to refresh the cache?
    refresh = None
    # Defaults config parameters
    defaults = {}

    logger = logging.getLogger('burp-ui')

    def __init__(self, server=None, conf=None):  # pragma: no cover
        """
        :param server: Application context
        :type server: :class:`burpui.server.BUIServer`
        """
        self.app = server

    """
    Utilities functions
    """

    def _safe_config_get(self, callback, key, sect='Burp1', cast=None):
        """
        :func:`burpui.misc.backend.interface.BUIbackend._safe_config_get` is a
        wrapper to handle Exceptions thrown by :mod:`ConfigParser`.

        :param callback: Function to wrap
        :type callback: callable

        :param key: Key to retrieve
        :type key: str

        :param sect: Section of the config file to read
        :type sect: str

        :param cast: Cast the returned value if provided
        :type case: callable

        :returns: The value returned by the `callback`
        """
        try:
            return callback(sect, key)
        except ConfigParser.NoOptionError as e:
            self.logger.error(str(e))
        except ConfigParser.NoSectionError as e:
            self.logger.warning(str(e))
            if key in self.defaults:
                if cast:
                    return cast(self.defaults[key])
                return self.defaults[key]
        return None

    @abstractmethod
    def status(self, query='\n', agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.status` method is
        used to send queries to the Burp server

        :param query: Query to send to the server
        :type query: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: The output returned by the server parsed as an array

        Example::

            [
                "client1\t2\ti\t576 0 1443766803",
                "client2\t2\ti\t1 0 1422189120",
            ]
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def get_backup_logs(self, number, client, forward=False, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_backup_logs`
        function is used to retrieve the burp logs depending the burp-server
        version.

        :param number: Backup number to work on
        :type number: int

        :param client: Client name to work on
        :type client: str

        :param forward: Is the client name needed in later process
        :type forward: bool

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: Dict containing the backup log

        Example::

            {
                "dir": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 17,
                    "scanned": 30246,
                    "total": 30246,
                    "unchanged": 30229
                },
                "duration": 436,
                "efs": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 0,
                    "total": 0,
                    "unchanged": 0
                },
                "encrypted": false,
                "end": 1443767237,
                "files": {
                    "changed": 47,
                    "deleted": 2,
                    "new": 2,
                    "scanned": 227377,
                    "total": 227377,
                    "unchanged": 227328
                },
                "files_enc": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 0,
                    "total": 0,
                    "unchanged": 0
                },
                "hardlink": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 28,
                    "total": 28,
                    "unchanged": 28
                },
                "meta": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 58,
                    "total": 58,
                    "unchanged": 58
                },
                "meta_enc": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 0,
                    "total": 0,
                    "unchanged": 0
                },
                "number": 576,
                "received": 11691704,
                "softlink": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 9909,
                    "total": 9909,
                    "unchanged": 9909
                },
                "special": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 1,
                    "total": 1,
                    "unchanged": 1
                },
                "start": 1443766801,
                "total": {
                    "changed": 47,
                    "deleted": 2,
                    "new": 19,
                    "scanned": 267619,
                    "total": 267619,
                    "unchanged": 267553
                },
                "totsize": 52047768383,
                "vssfooter": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 0,
                    "total": 0,
                    "unchanged": 0
                },
                "vssfooter_enc": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 0,
                    "total": 0,
                    "unchanged": 0
                },
                "vssheader": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 0,
                    "total": 0,
                    "unchanged": 0
                },
                "vssheader_enc": {
                    "changed": 0,
                    "deleted": 0,
                    "new": 0,
                    "scanned": 0,
                    "total": 0,
                    "unchanged": 0
                },
                "windows": "false"
            }
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def get_clients_report(self, clients, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_clients_report`
        function returns the computed/compacted data to display clients report.

        :param clients: List of clients as returned by
                        :func:`burpui.misc.backend.interface.BUIbackend.get_all_clients`
        :type clients: list

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A dict with the computed data
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def get_counters(self, name=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_counters`
        function returns a dict of counters for a given client while it performs
        a backup.

        :param name: Name of the client for which you'd like stats
        :type name: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A dict of counters
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def is_backup_running(self, name=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.is_backup_running`
        functions tells you if a given client is currently performing a backup.

        :param name: Name of the client
        :type name: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: True or False
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def is_one_backup_running(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.is_one_backup_running`
        function tells you if at least one backup is running.

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of running clients
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def get_all_clients(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_all_clients`
        function returns a list containing all the clients with their states.

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of clients

        Example::

            [
                {
                    "last": "2015-10-02 08:20:03",
                    "name": "client1",
                    "state": "idle",
                    "percent": null,
                    "phase": null,
                },
                {
                    "last": "2015-01-25 13:32:00",
                    "name": "client2",
                    "state": "idle"
                    "percent": null,
                    "phase": null,
                },
            ]
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def get_client(self, name=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_client`
        function returns a list of dict representing the backups of a given
        client.

        :param name: Client name
        :type name: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of backups

        Example::

            [
                {
                    "date": "2015-01-25 13:32:00",
                    "deletable": true,
                    "encrypted": true,
                    "number": "1",
                    "received": 889818873,
                    "size": 35612321050,
                }
            ]
        """

        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def get_tree(self, name=None, backup=None, root=None, level=-1, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_tree`
        function returns a list of dict representing files/dir (with their
        attr) within a given path

        :param name: Client name
        :type name: str

        :param backup: Backup number
        :type backup: int

        :param root: Root path to look into
        :type root: str

        :param level: Level of the tree relative to its root
        :type level: int

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of files/dir within the given path with their attr

        Example::

            [
                {
                    "date": "2015-01-23 20:00:07",
                    "gid": "0",
                    "inodes": "168",
                    "mode": "drwxr-xr-x",
                    "name": "/",
                    "parent": "",
                    "fullname": "/",
                    "level": -1,
                    "size": "12.0KiB",
                    "type": "d",
                    "uid": "0",
                    "folder": True,
                    "children": []
                }
            ]
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def restore_files(self, name=None, backup=None, files=None, strip=None, archive='zip', password=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.restore_files`
        function performs a restoration and returns a tuple containing the path
        of the generated archive and/or a message if an error happened.

        :param name: Client name
        :type name: str

        :param backup: Backup number
        :type backup: int

        :param files: A string representing a list of files to restore
        :type files: str

        Example::

            ['/etc/passwd', '/etc/shadow']

        :param strip: Number of parent directories to strip while restoring
                      files
        :type strip: int

        :param archive: Format of the generated archive (may be zip, tar.gz or
                        tar.bz2)
        :type archive: str

        :param password: Password for encrypted backups
        :type password: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A tuple with the generated archive path and/or an error message
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def read_conf_srv(self, conf=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.read_conf_srv`
        function returns a dict of options present in the server config file.

        :param conf: Complementary configuration file (for instance, file
                     inclusions)
        :type conf: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

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
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def read_conf_cli(self, client=None, conf=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.read_conf_cli`
        function works the same way as the
        :func:`burpui.misc.backend.interface.BUIbackend.read_conf_srv` function
        but for the client config file.
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def store_conf_srv(self, data, conf=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.store_conf_srv`
        functions is used to save the new settings in the configuration file.

        :param data: Data as sent by the web-form
        :type data: dict

        :param conf: Force the file path (for file inclusions for instance)
        :type conf: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of notifications to return to the UI (success or
                  failure)

        Example::

            [[0, "Success"]]
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def store_conf_cli(self, data, client=None, conf=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.store_conf_cli`
        function works the same way as the
        :func:`burpui.misc.backend.interface.BUIbackend.store_conf_srv` function
        but for the client config file.
        It takes an extra parameter:

        :param client: Name of the client for which to apply this config
        :type client: str
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def get_parser_attr(self, attr=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_parser_attr`
        function is used to retrieve some attributes from the Parser.
        This function is useful in multi-agent mode because the front-end needs
        to access the backend attributes through the agents.

        :param attr: Name of the attribute to retrieve
        :type attr: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: The requested attribute or an empty list
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def expand_path(self, path=None, client=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.expand_path`
        function is used to expand path of file inclusions glob the user can
        set in the setting panel.
        This function is also a *proxy* for multi-agent setup.

        :param path: The glob/path to expand
        :type path: str

        :param client: The client name when working on client files
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of files or an empty list
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def clients_list(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.clients_list`
        function is used to retrieve a list of clients with their configuration
        file.

        :returns: A list of clients with their configuration file
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def delete_client(self, client=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.delete_client`
        function is used to delete a client from burp's configuration.

        :param client: The name of the client to remove
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of notifications to return to the UI (success or
                  failure)
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def is_server_restore(self, client=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.is_server_restore`
        function is used to know if there is a server-initiated restoration file
        in place and retrieve its content in order to edit it.

        :param client: The name of the client to look for
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A dict representing the content of the server-initiated
                  restoration file
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def cancel_server_restore(self, client=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.cancel_server_restore`
        function is used to delete the server-initiated restoration file of a
        given client.

        :param client: The name of the client to look for
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of notifications to return to the UI (success or
                  failure)

        Example::

            [[0, "Success"]]
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def server_restore(self, client=None, backup=None, files=None, strip=None, force=None, prefix=None, restoreto=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.server_restore`
        function is used to schedule a server-side initiated restoration.

        :param client: Client name
        :type client: str

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

        :param retoreto: Restore on an other client
        :type restoreto: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of notifications to return to the UI (success or
                  failure)
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def is_server_backup(self, client=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.is_server_backup`
        function is used to know if there is a server-initiated backup file
        in place.

        :param client: The name of the client to look for
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A dict like: {'is_server_backup': True}
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def cancel_server_backup(self, client=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.cancel_server_backup`
        function is used to delete the server-initiated backup file of a given
        client.

        :param client: The name of the client to look for
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of notifications to return to the UI (success or
                  failure)

        Example::

            [[0, "Success"]]
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def server_backup(self, client=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.server_backup`
        function is used to schedule a server-side initiated backup.

        :param client: Client name
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of notifications to return to the UI (success or
                  failure)
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def get_client_version(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_client_version`
        function returns the client version used to connect to the server.

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: Burp client version
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def get_server_version(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_server_version`
        function returns the server version (if any).

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: Burp server version
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover

    @abstractmethod
    def get_client_labels(self, client=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_client_labels`
        function returns a list of labels (if any) for a given client.

        .. note:: Labels are only available since Burp 2.0.34

        :param client: The client for which you want the labels
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of labels or an empty list
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")  # pragma: no cover
