# -*- coding: utf8 -*-
from flask.ext.login import UserMixin, AnonymousUserMixin


class BUIhandler:
    def __init__(self, app=None):
        pass

    def user(self, name=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")


class BUIuser(UserMixin):
    def login(self, name=None, passwd=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")
