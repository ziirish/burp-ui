# -*- coding: utf8 -*-

class BUIparser:
    def __init__(self, app=None, conf=None):
        self.app = app
        self.conf = conf

    def readfile(self):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")
