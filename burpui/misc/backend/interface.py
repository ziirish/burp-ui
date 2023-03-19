# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.backend.interface
    :platform: Unix
    :synopsis: Burp-UI backend interface.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import os
import re
from abc import ABCMeta, abstractmethod

from ...tools.logging import logger

G_BURPPORT = 4972
G_BURPHOST = "::1"
G_BURPBIN = "/usr/sbin/burp"
G_STRIPBIN = "/usr/sbin/vss_strip"
G_STRIPBIN2 = "/usr/bin/vss_strip"
G_BURPCONFCLI = "/etc/burp/burp.conf"
G_BURPCONFSRV = "/etc/burp/burp-server.conf"
G_TMPDIR = "/tmp/bui"
G_TIMEOUT = 15
G_DEEP_INSPECTION = False
G_ZIP64 = True
G_INCLUDES = ["/etc/burp"]
G_ENFORCE = False
G_REVOKE = True


class BUIbackend(object, metaclass=ABCMeta):
    """The :class:`burpui.misc.backend.interface.BUIbackend` class provides
    a consistent interface backend for any ``burp`` server.

    :param server: ``Flask`` server instance in order to access logger
                   and/or some global settings
    :type server: :class:`burpui.engines.server.BUIServer`

    :param conf: Configuration file to use
    :type conf: str
    """

    # Defaults config parameters
    defaults = {}

    logger = logger

    def __init__(self, server=None, conf=None):  # pragma: no cover
        """
        :param server: Application context
        :type server: :class:`burpui.engines.server.BUIServer`
        """
        self.app = server
        self.zip64 = G_ZIP64
        self.timeout = G_TIMEOUT
        self.host = G_BURPHOST
        self.port = G_BURPPORT
        self.burpbin = G_BURPBIN
        self.stripbin = G_STRIPBIN2
        self.burpconfcli = G_BURPCONFCLI
        self.burpconfsrv = G_BURPCONFSRV
        self.includes = G_INCLUDES
        self.revoke = G_REVOKE
        self.enforce = G_ENFORCE
        self.deep_inspection = G_DEEP_INSPECTION
        self.running = []
        burp_opts = {
            "bport": G_BURPPORT,
            "bhost": G_BURPHOST,
            "burpbin": G_BURPBIN,
            "stripbin": G_STRIPBIN2,
            "bconfcli": G_BURPCONFCLI,
            "bconfsrv": G_BURPCONFSRV,
            "timeout": G_TIMEOUT,
            "tmpdir": G_TMPDIR,
            "deep_inspection": G_DEEP_INSPECTION,
        }
        self.defaults = {
            "Burp": burp_opts,
            # TODO: remove this when we drop the compatibility
            "Burp1": burp_opts,
            "Burp2": burp_opts,
            "Experimental": {
                "zip64": G_ZIP64,
            },
            "Security": {
                "includes": G_INCLUDES,
                "revoke": G_REVOKE,
                "enforce": G_ENFORCE,
            },
        }
        self.defaults["Burp1"]["stripbin"] = G_STRIPBIN
        tmpdir = G_TMPDIR
        if conf is not None:
            conf.update_defaults(self.defaults)
            section = "Burp"
            if section not in conf.options:
                section_old = "Burp{}".format(self._vers)
                if section_old in conf.options:
                    # TODO: remove the compatibility
                    self.logger.critical(
                        'The "[{}]" section is DEPRECATED and will be removed '
                        'in v0.7.0. Please use the "[Burp]" section '
                        "instead.".format(section_old)
                    )
                    section = section_old
            conf.default_section(section)
            self.with_celery = conf.get("WITH_CELERY", False)
            self.port = conf.safe_get("bport", "integer")
            self.host = conf.safe_get("bhost")
            self.burpbin = self._get_binary_path(
                conf, "burpbin", G_BURPBIN, sect=section
            )
            STRIPBIN_DEFAULT = G_STRIPBIN2
            if self._vers == 1:
                STRIPBIN_DEFAULT = G_STRIPBIN
            self.stripbin = self._get_binary_path(
                conf, "stripbin", STRIPBIN_DEFAULT, sect=section
            )
            confcli = conf.safe_get("bconfcli")
            confsrv = conf.safe_get("bconfsrv")
            tmpdir = conf.safe_get("tmpdir")
            self.timeout = conf.safe_get("timeout", "integer")

            self.deep_inspection = conf.safe_get("deep_inspection", "boolean")

            # Experimental options
            self.zip64 = conf.safe_get("zip64", "boolean", section="Experimental")

            # Security options
            self.includes = conf.safe_get("includes", "force_list", section="Security")
            self.enforce = conf.safe_get("enforce", "boolean", section="Security")
            self.revoke = conf.safe_get("revoke", "boolean", section="Security")

            if confcli and not os.path.isfile(confcli):
                self.logger.warning("The file '%s' does not exist", confcli)

            if confsrv and not os.path.isfile(confsrv):
                self.logger.warning("The file '%s' does not exist", confsrv)

            if (
                not self.burpbin
                and self._vers == 2
                and getattr(self.app, "strict", True)
            ):
                # The burp binary is mandatory for this backend
                self.logger.critical(
                    "This backend *CAN NOT* work without a burp binary"
                )

            if self.host not in ["127.0.0.1", "::1"] and self._vers == 1:
                self.logger.warning(
                    "Invalid value for 'bhost'. Must be '127.0.0.1' or '::1'. Falling back to '%s'",
                    G_BURPHOST,
                )
                self.host = G_BURPHOST

            self.burpconfcli = confcli
            self.burpconfsrv = confsrv

        if tmpdir and os.path.exists(tmpdir) and not os.path.isdir(tmpdir):
            self.logger.warning("'%s' is not a directory", tmpdir)
            if tmpdir == G_TMPDIR and getattr(self.app, "strict", True):
                self.logger.critical("Cannot use '{}' as tmpdir".format(tmpdir))
                self.tmpdir = None
                return
            tmpdir = G_TMPDIR
            if (
                os.path.exists(tmpdir)
                and not os.path.isdir(tmpdir)
                and getattr(self.app, "strict", True)
            ):
                self.logger.critical("Cannot use '{}' as tmpdir".format(tmpdir))
                self.tmpdir = None
                return
        if tmpdir and not os.path.exists(tmpdir):
            try:
                os.makedirs(tmpdir)
            except OSError as exp:
                self.logger.critical(str(exp))
                self.tmpdir = None
                return

        self.tmpdir = tmpdir

    # Utilities functions
    def _get_binary_path(self, config, field, default=None, sect="Burp"):
        """Helper function to retrieve a binary path from the configuration

        :param field: Field name to look for
        :type field: str

        :param default: Default value in case the retrieved value is not correct
        :type default: str
        """
        temp = config.safe_get(field, section=sect) or default

        if temp and not temp.startswith("/"):
            self.logger.warning(
                "Please provide an absolute path for the '{}' option. Fallback to '{}'".format(
                    field, default
                )
            )
            temp = default
        elif temp and not re.match(r"^\S+$", temp):
            self.logger.warning(
                "Incorrect value for the '{}' option. Fallback to '{}'".format(
                    field, default
                )
            )
            temp = default
        elif temp and (not os.path.isfile(temp) or not os.access(temp, os.X_OK)):
            self.logger.warning(
                "'{}' does not exist or is not executable. Fallback to '{}'".format(
                    temp, default
                )
            )
            temp = default

        if temp and (
            not os.path.isfile(temp) or not os.access(temp, os.X_OK)
        ):  # pragma: no cover
            self.logger.error("Ooops, '{}' not found or is not executable".format(temp))
            temp = None

        return temp

    """
    Utilities functions
    """

    @abstractmethod
    def statistics(agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.statistics` method should
        return statistics about the current backend.

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A dict containing statistics about the backend
        :rtype: dict

        Example::

            {
                "alive": true,
                "server_version": "2.1.12",
                "client_version": "2.1.12"
            }
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def status(self, query="\n", timeout=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.status` method is
        used to send queries to the Burp server

        :param query: Query to send to the server
        :type query: str

        :param timeout: Query timeout in seconds
        :type timeout: int

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: The output returned by the server parsed as an array

        Example::

            [
                "client1\t2\ti\t576 0 1443766803",
                "client2\t2\ti\t1 0 1422189120"
            ]
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def get_backup_logs(self, number, client, forward=False, deep=False, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_backup_logs`
        function is used to retrieve the burp logs depending the burp-server
        version.

        :param number: Backup number to work on
        :type number: int

        :param client: Client name to work on
        :type client: str

        :param forward: Is the client name needed in later process
        :type forward: bool

        :param deep: Enable deep log inspection
        :type deep: bool

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def is_one_backup_running(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.is_one_backup_running`
        function tells you if at least one backup is running.

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of running clients
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def get_all_clients(self, agent=None, last_attempt=True):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_all_clients`
        function returns a list containing all the clients with their states.

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :param last_attempt: Whether to return last backup attempt or not. This requires
                             one more query per client hence we can disable it.
        :type last_attempt: bool

        :returns: A list of clients

        Example::

            [
                {
                    "last": "2015-10-02 08:20:03",
                    "name": "client1",
                    "state": "idle",
                },
                {
                    "last": "2015-01-25 13:32:00",
                    "name": "client2",
                    "state": "idle"
                }
            ]
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def get_client_status(self, name=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_client_status`
        function returns the status of a given client with its last stats.

        :param name: What client status do we want
        :type name: str
        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: The last status of a given client

        Example::

            {
                "state": "idle",
                "percent": null,
                "phase": null,
                "last": "never"
            }

        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
                    "size": 35612321050
                }
            ]
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def get_client_filtered(
        self, name=None, limit=-1, page=None, start=None, end=None, agent=None
    ):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_client_filtered`
        function returns a list of dict representing the backups of a given
        client filtered by the given criteria.

        :param name: Client name
        :type name: str

        :param limit: Number of element to return, -1 for not limit
        :type limit: int

        :param page: What page to retrieve
        :type page: int

        :param start: Return elements after this date
        :type start: int

        :param end: Return elements until this date
        :type end: int

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
                    "size": 35612321050
                }
            ]
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def delete_backup(self, name=None, backup=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.delete_backup`
        function performs a backup deletion and returns an error message if
        the command failed.

        :param name: Client name
        :type name: str

        :param backup: Backup number
        :type backup: int

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: An error message if the command failed
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def restore_files(
        self,
        name=None,
        backup=None,
        files=None,
        strip=None,
        archive="zip",
        password=None,
        agent=None,
    ):
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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
                    }
                ]
            }
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def read_conf_cli(self, client=None, conf=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.read_conf_cli`
        function works the same way as the
        :func:`burpui.misc.backend.interface.BUIbackend.read_conf_srv` function
        but for the client config file.
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def store_conf_cli(
        self,
        data,
        client=None,
        conf=None,
        template=False,
        statictemplate=False,
        content="",
        agent=None,
    ):
        """The :func:`burpui.misc.backend.interface.BUIbackend.store_conf_cli`
        function works the same way as the
        :func:`burpui.misc.backend.interface.BUIbackend.store_conf_srv` function
        but for the client config file.
        It takes an extra parameter:

        :param client: Name of the client for which to apply this config
        :type client: str
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def expand_path(self, path=None, source=None, client=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.expand_path`
        function is used to expand path of file inclusions glob the user can
        set in the setting panel.
        This function is also a *proxy* for multi-agent setup.

        :param path: The glob/path to expand
        :type path: str

        :param source: In which file are we working
        :type source: str

        :param client: The client name when working on client files
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of files or an empty list
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def clients_list(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.clients_list`
        function is used to retrieve a list of clients with their configuration
        file.

        :returns: A list of clients with their configuration file
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def delete_client(
        self, client=None, keepconf=False, delcert=False, revoke=False, agent=None
    ):
        """The :func:`burpui.misc.backend.interface.BUIbackend.delete_client`
        function is used to delete a client from burp's configuration.

        :param client: The name of the client to remove
        :type client: str

        :param keepconf: Whether to keep the conf (in order to just revoke/delete the certs for instance)
        :type keepconf: bool

        :param delcert: Whether to delete the associated certificate
        :type delcert: bool

        :param revoke: Whether to revoke the associated certificate
        :type revoke: bool

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of notifications to return to the UI (success or
                  failure)
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def server_restore(
        self,
        client=None,
        backup=None,
        files=None,
        strip=None,
        force=None,
        prefix=None,
        restoreto=None,
        agent=None,
    ):
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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def is_server_backup(self, client=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.is_server_backup`
        function is used to know if there is a server-initiated backup file
        in place.

        :param client: The name of the client to look for
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: True or False
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def revocation_enabled(self, agent=None):
        """The
        :func:`burpui.misc.backend.interface.BUIbackend.revocation_enabled`
        function is used to know if the revocation feature is enabled or not.

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: True or False
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def get_client_version(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_client_version`
        function returns the client version used to connect to the server.

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: Burp client version
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def get_server_version(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_server_version`
        function returns the server version (if any).

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: Burp server version
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

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
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def get_attr(self, name, default=None, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_attr`
        function returns the given attribute or default.
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def get_parser(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_parser`
        function returns the parser of the current backend.
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def get_file(self, path, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.get_file`
        function is used to retrieve a file on a remote agent.
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def del_file(self, path, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.del_file`
        function is used to delete a file on a remote agent.
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover

    @abstractmethod
    def version(self, agent=None):
        """The :func:`burpui.misc.backend.interface.BUIbackend.version` function
        returns the version of the given agent.
        """
        raise NotImplementedError(
            "Sorry, the current Backend does not implement this method!"
        )  # pragma: no cover


BUIBACKEND_INTERFACE_METHODS = BUIbackend.__abstractmethods__.copy()
