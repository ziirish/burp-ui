# -*- coding: utf8 -*-


class BUIbackend:
    def __init__(self, server=None, conf=None):
        """
        The :class:`burpui.misc.backend.interface.BUIbackend` class provides a
        consistent interface backend for any ``burp`` server.

        :param server: ``Burp-UI`` server instance in order to access logger
                       and/or some global settings
        :type server: :class:`burpui.server.BUIServer`

        :param conf: Configuration file to use
        :type conf: str
        """
        self.app = None
        if server:
            if hasattr(server, 'app'):
                self.app = server.app

    def set_logger(self, logger):
        self.logger = logger

    def status(self, query='\n', agent=None):
        """
        The :func:`burpui.misc.backend.interface.BUIbackend.status` method is
        used to send queries to the Burp server

        :param query: Query to send to the server
        :type query: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: The output returned by the server parsed as an array
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_backup_logs(self, number, client, forward=False, agent=None):
        """
        The :func:`burpui.misc.backend.interface.BUIbackend.get_backup_logs`
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
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_clients_report(self, clients, agent=None):
        """
        The :func:`burpui.misc.backend.interface.BUIbackend.get_clients_report`
        function returns the computed/compacted data to display clients report.

        :param clients: List of clients as returned by
                        :func:`burpui.misc.backend.interface.BUIbackend.get_all_clients`
        :type clients: list

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: An array containing one dict with the computed data
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_counters(self, name=None, agent=None):
        """
        The :func:`burpui.misc.backend.interface.BUIbackend.get_counters`
        function returns a dict of counters for a given client while it performs
        a backup.

        :param name: Name of the client for which you'd like stats
        :type name: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A dict of counters
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def is_backup_running(self, name=None, agent=None):
        """
        The :func:`burpui.misc.backend.interface.BUIbackend.is_backup_running`
        functions tells you if a given client is currently performing a backup.

        :param name: Name of the client
        :type name: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: True or False
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def is_one_backup_running(self, agent=None):
        """
        The :func:`burpui.misc.backend.interface.BUIbackend.is_one_backup_running`
        function tells you if at least one backup is running.

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: A list of running clients
        """
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_all_clients(self, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_client(self, name=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_tree(self, name=None, backup=None, root=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def restore_files(self, name=None, backup=None, files=None, strip=None, archive='zip', password=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def read_conf_srv(self, conf=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def read_conf_cli(self, client=None, conf=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def store_conf_srv(self, data, conf=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def store_conf_cli(self, data, client=None, conf=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_parser_attr(self, attr=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def expand_path(self, path=None, client=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def delete_client(self, client=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")


class BUIserverException(Exception):
    pass
