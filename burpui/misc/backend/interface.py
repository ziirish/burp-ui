# -*- coding: utf8 -*-

class BUIbackend:
    def __init__(self, app=None, host='127.0.0.1', port=4972):
        self.app = app
        self.host = host
        self.port = port

    def status(self, query='\n', agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_backup_logs(self, n, c, forward=False, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_counters(self, name=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def is_backup_running(self, name=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def is_one_backup_running(self, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_all_clients(self, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_client(self, name=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_tree(self, name=None, backup=None, root=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def restore_files(self, name=None, backup=None, files=None, strip=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def read_conf(self, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def store_conf(self, data, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_parser_attr(self, attr=None, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

class BUIserverException(Exception):
    pass

class BUIserverException(Exception):
    pass
