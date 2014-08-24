# -*- coding: utf8 -*-
from flask.ext.login import UserMixin
from burpui.misc.auth.interface import BUIhandler, BUIuser

import simpleldap
import ConfigParser

class LdapLoader:
    def __init__(self, app=None):
        self.app = app
        conf = self.app.config['CFG']
        c = ConfigParser.ConfigParser({'host': 'localhost', 'binddn': '', 'bindpw': '', 'filter': '', 'base': ''})
        with open(conf) as fp:
            c.readfp(fp)
            try:
                self.host = c.get('LDAP', 'host')
                self.filt = c.get('LDAP', 'filter')
                self.base = c.get('LDAP', 'base')
                self.binddn = c.get('LDAP', 'binddn')
                self.bindpw = c.get('LDAP', 'bindpw')
            except ConfigParser.NoOptionError:
                self.app.logger.error("Missing option")

        self.app.logger.info('LDAP host: %s', self.host)
        self.app.logger.info('LDAP filter: %s', self.filt)
        self.app.logger.info('LDAP base: %s', self.base)
        self.app.logger.info('LDAP binddn: %s', self.binddn)
        self.app.logger.info('LDAP bindpw: %s', '*****' if self.bindpw else 'None')

        try:
            self.ldap = simpleldap.Connection(self.host, dn=self.binddn, password=self.bindpw)
            self.app.logger.info('OK, connected to LDAP')
        except:
            self.app.logger.error('Could not connect to LDAP')
            self.ldap = None

    def __exit__(self, exc_type, exc_value, traceback):
        if self.ldap:
            self.ldap.close()

    def fetch(self, uid=None):
        try:
            if self.filt:
                self.app.logger.info('filter: %s | base: %s', self.filt, self.base)
                r = self.ldap.search(self.filt, base_dn=self.base)
                for record in r:
                    if record['uid'][0] == uid:
                        return record['uid'][0]
                return None
            else:
                query = 'uid={0}'.format(uid)
                self.app.logger.info('query: %s | base: %s', query, self.base)
                r = self.ldap.search(query, base_dn=self.base)
        except:
            self.app.logger.info('Ooops, LDAP lookup failed')
            return None

        return r[0]['uid'][0]

    def check(self, uid=None, passwd=None):
        try:
            l = simpleldap.Connection(self.host, dn='uid={0},{1}'.format(uid, self.base), password=passwd)
        except:
            return False

        l.close()
        return True



class UserHandler(BUIhandler):
    def __init__(self, app=None):
        self.ldap = LdapLoader(app)
        self.users = {}

    def user(self, name=None):
        if name not in self.users:
            self.users[name] = LdapUser(self.ldap, name)
        return self.users[name]



class LdapUser(UserMixin, BUIuser):
    def __init__(self, ldap=None, name=None):
        self.active = False
        self.ldap = ldap
        self.name = name

        ldapres = self.ldap.fetch(self.name)

        if ldapres:
            self.id = ldapres
            self.active = True

    def login(self, name=None, passwd=None):
        return self.ldap.check(name, passwd)

    def is_active(self):
        return self.active

    def get_id(self):
        return self.id

