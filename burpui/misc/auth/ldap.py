# -*- coding: utf8 -*-
from flask.ext.login import UserMixin

import simpleldap
import ConfigParser

class LdapLoader:
    def __init__(self, app=None):
        self.app = app
        conf = self.app.config['CFG']
        c = ConfigParser.ConfigParser({'host': 'localhost', 'binddn': '', 'bindpw': '', 'filter': None, 'base': ''})
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
        except:
            self.ldap = None

    def __exit__(self, exc_type, exc_value, traceback):
        if self.ldap:
            self.ldap.close()

    def fetch(self, uid=None):
        try:
            if self.filter:
                r = self.ldap.search('uid={0}'.format(uid), self.filt, base_dn=self.base)
            else:
                r = self.ldap.search('uid={0}'.format(uid), base_dn=self.base)
        except:
            return None

        return r[0]['uid'][0]

    def check(self, uid=None, passwd=None):
        try:
            l = simpleldap.Connection(self.host, dn='uid={0},{1}'.format(uid, self.base), password=passwd)
        except:
            return False

        l.close()
        return True





class LdapUser(UserMixin):
    def __init__(self, app=None):
        self.active = False
        self.ldap = LdapLoader(app)

    def exists(self, uid=None):
        return self.ldap.fetch(uid)

    def login(self, uid=None, passwd=None):
        return self.ldap.check(uid, passwd)


