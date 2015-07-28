# -*- coding: utf8 -*-
from burpui.misc.acl.interface import BUIacl, BUIaclLoader

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import json


class ACLloader(BUIaclLoader):
    def __init__(self, app=None, standalone=False):
        self.app = app
        self.admins = [
            'admin'
        ]
        self.clients = {}
        self.servers = {}
        self.standalone = standalone
        conf = self.app.config['CFG']
        c = ConfigParser.ConfigParser()
        adms = []
        with open(conf) as fp:
            c.readfp(fp)
            if c.has_section('BASIC:ACL'):
                try:
                    temp = c.get('BASIC:ACL', 'admin')
                    try:
                        adms = json.loads(temp)
                    except Exception as e:
                        self.app.logger.error(str(e))
                        adms = [temp]
                except Exception as e:
                    self.app.logger.warning(str(e))
                for opt in c.options('BASIC:ACL'):
                    if opt == 'admin':
                        continue
                    lit = c.get('BASIC:ACL', opt)
                    rec = []
                    try:
                        rec = json.loads(lit)
                        if isinstance(rec, dict):
                            self.servers[opt] = rec.keys()
                    except Exception as e:
                        self.app.logger.error(str(e))
                        rec = [lit]
                    self.clients[opt] = rec

        if adms:
            self.admins = adms
        self._acl = BasicACL(self)
        self.app.logger.debug('admins: ' + str(self.admins))
        self.app.logger.debug('clients: ' + str(self.clients))
        self.app.logger.debug('servers: ' + str(self.servers))

    @property
    def acl(self):
        if self._acl:
            return self._acl
        return None


class BasicACL(BUIacl):
    def __init__(self, handler=None):
        if not handler:
            return
        self.handler = handler
        self.standalone = handler.standalone
        self.admins = handler.admins
        self.cls = handler.clients
        self.srv = handler.servers

    def is_admin(self, username=None):
        if not username:
            return False
        return username in self.admins

    def clients(self, username=None, server=None):
        if not username:
            return []
        if username in self.cls:
            cls = self.cls[username]
            if server and isinstance(cls, dict):
                if server in cls:
                    return cls[server]
                return []
            # No server defined whereas we have an extended ACL
            if not server and self.servers(username):
                return []
            return cls
        return [username]

    def servers(self, username=None):
        if username and username in self.srv:
            return self.srv[username]
        return []

    def is_client_allowed(self, username=None, client=None, server=None):
        if not username or not client:
            return False
        # No server defined whereas we have an extended ACL
        if not server and self.servers(username):
            return False
        cls = self.clients(username, server)
        return (cls and client in cls) or self.is_admin(username)
