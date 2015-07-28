# -*- coding: utf8 -*-
from flask.ext.login import UserMixin
from burpui.misc.auth.interface import BUIhandler, BUIuser

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser


class BasicLoader:
    def __init__(self, app=None):
        self.app = app
        self.users = {
            'admin': 'admin'
        }
        conf = self.app.config['CFG']
        c = ConfigParser.ConfigParser()
        c.optionxform = str
        with open(conf) as fp:
            c.readfp(fp)
            if c.has_section('BASIC'):
                self.users = {}
                for opt in c.options('BASIC'):
                    self.users[opt] = c.get('BASIC', opt)
                    self.app.logger.info('Loading user: %s', opt)

    def fetch(self, uid=None):
        if uid in self.users:
            return uid

        return None

    def check(self, uid=None, passwd=None):
        return uid in self.users and self.users[uid] == passwd


class UserHandler(BUIhandler):
    def __init__(self, app=None):
        self.basic = BasicLoader(app)
        self.users = {}

    def user(self, name=None):
        if name not in self.users:
            self.users[name] = BasicUser(self.basic, name)
        return self.users[name]


class BasicUser(UserMixin, BUIuser):
    def __init__(self, basic=None, name=None):
        self.active = False
        self.basic = basic
        self.name = name

        res = self.basic.fetch(self.name)

        if res:
            self.id = res
            self.active = True

    def login(self, name=None, passwd=None):
        return self.basic.check(name, passwd)

    def is_active(self):
        return self.active

    def get_id(self):
        return self.id
