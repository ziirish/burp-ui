# -*- coding: utf8 -*-


class BUIparser(object):
    def __init__(self, app=None, conf=None):
        self.app = app
        self.conf = conf

    def read_server_conf(self):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def store_client_conf(self, data, client=None, conf=None):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def store_conf(self, data, conf=None, mode='srv'):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def get_priv_attr(self, key):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def path_expander(self, pattern=None):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def read_client_conf(self, client=None, conf=None):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")
