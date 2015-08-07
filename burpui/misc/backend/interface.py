# -*- coding: utf8 -*-


class BUIbackend:
    def __init__(self, app=None, host='127.0.0.1', port=4972):
        self.app = app
        self.host = host
        self.port = port

    def status(self, query='\n', agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_backup_logs(self, number, client, forward=False, agent=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def get_clients_report(self, clients, agent=None):
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
