# -*- coding: utf8 -*-

class BUIparser:
    def __init__(self, app=None, conf=None):
        self.app = app
        self.conf = conf

    def readfile(self):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")

    def getkey(self, key):
        raise NotImplementedError("Sorry, the current Parser does not implement this method!")
