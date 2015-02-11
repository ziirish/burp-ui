# -*- coding: utf8 -*-
from burpui.misc.acl.interface import BUIacl, BUIaclLoader

import ConfigParser
import json

class ACLloader(BUIaclLoader):
    def __init__(self, app=None):
        self.app = app
        self.admins = [
                'admin'
                ]
        self.clients = {}
        conf = self.app.config['CFG']
        c = ConfigParser.ConfigParser()
        adms = []
        with open(conf) as fp:
            c.readfp(fp)
            if c.has_section('BASIC:ACL'):
                temp = c.get('BASIC:ACL', 'admin')
                try:
                    adms = json.loads(temp)
                except Exception, e:
                    self.app.logger.error(str(e))
                    adms = [temp]
                for opt in c.options('BASIC:ACL'):
                    if opt == 'admin':
                        continue
                    lit = c.get('BASIC:ACL', opt)
                    rec = []
                    try:
                        rec = json.loads(lit)
                    except Exception, e:
                        self.app.logger.error(str(e))
                        rec = [lit]
                    self.clients[opt] = rec

        if adms:
            self.admins = adms
        self.acl = BasicACL(self.admins, self.clients)
        self.app.logger.debug(self.admins)
        self.app.logger.debug(self.clients)

    def get_acl(self):
        return self.acl

class BasicACL(BUIacl):
    def __init__(self, admins=[], clients={}):
        self.admins = admins
        self.cls = clients

    def is_admin(self, username=None):
        if not username:
            return False
        return username in self.admins

    def clients(self, username=None):
        if not username:
            return []
        if username in self.cls:
            return self.cls[username]
        return [username]

    def is_client_allowed(self, username=None, client=None):
        if not username or not client:
            return False
        cls = self.clients(username)
        return (cls and client in cls) or self.is_admin(username)
