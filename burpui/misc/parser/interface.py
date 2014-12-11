# -*- coding: utf8 -*-

class BUIparser:
    def __init__(self, app=None, conf=None):
        self.app = app
        self.conf = conf

    def read_server_conf(self):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def store_server_conf(self, data):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def get_priv_attr(self, key):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")
