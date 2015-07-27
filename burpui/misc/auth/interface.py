# -*- coding: utf8 -*-


class BUIhandler:
    def __init__(self, app=None):
        pass

    def user(self, name=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")


class BUIuser:
    def login(self, name=None, passwd=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")
