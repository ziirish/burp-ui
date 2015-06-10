# -*- coding: utf8 -*-
from flask.ext.login import UserMixin
from burpui.misc.auth.interface import BUIhandler, BUIuser

try:
    import simpleldap
except ImportError:
    raise ImportError('Unable to load \'simpleldap\' module')

import ConfigParser

class LdapLoader:
    """
    The :class:`burpui.misc.auth.ldap.LdapLoader` handles searching for and binding as
    a :class:`burpui.misc.auth.ldap.LdapUser` user.
    """
    def __init__(self, app=None):
        """
        :func:`burpui.misc.auth.ldap.LdapLoader.__init__` establishes a connection to the
        LDAP server.

        :param app: Instance of the app we are running in
        :type app: :class:`burpui.server.BUIServer`
        """
        self.app = app
        self.attr = 'uid' # default search attr
        conf = self.app.config['CFG']
        c = ConfigParser.ConfigParser({'host': 'localhost', 'port': None, 'encryption': None, 'binddn': '', 'bindpw': '', 'filter': '', 'base': ''})
        with open(conf) as fp:
            c.readfp(fp)
            try:
                self.host = c.get('LDAP', 'host')
                self.port = c.get('LDAP', 'port')
                self.encryption = c.get('LDAP', 'encryption')
                self.filt = c.get('LDAP', 'filter')
                self.base = c.get('LDAP', 'base')
                self.attr = c.get('LDAP', 'searchattr')
                self.binddn = c.get('LDAP', 'binddn')
                self.bindpw = c.get('LDAP', 'bindpw')
            except ConfigParser.NoOptionError, e:
                self.app.logger.info(str(e))
            except ConfigParser.NoSectionError, e:
                self.app.logger.error(str(e))

        self.app.logger.info('LDAP host: %s', self.host)
        self.app.logger.info('LDAP port: %s', self.port)
        self.app.logger.info('LDAP encryption: %s', self.encryption)
        self.app.logger.info('LDAP filter: %s', self.filt)
        self.app.logger.info('LDAP base: %s', self.base)
        self.app.logger.info('LDAP search attr: %s', self.attr)
        self.app.logger.info('LDAP binddn: %s', self.binddn)
        self.app.logger.info('LDAP bindpw: %s', '*****' if self.bindpw else 'None')

        try:
            self.ldap = simpleldap.Connection(hostname=self.host, port=self.port, dn=self.binddn, password=self.bindpw, encryption=self.encryption)
            self.app.logger.info('OK, connected to LDAP')
        except:
            self.app.logger.error('Could not connect to LDAP')
            self.ldap = None

    def __exit__(self, exc_type, exc_value, traceback):
        """
        :func:`burpui.misc.auth.ldap.LdapLoader.__exit__` closes the connection to the
        LDAP server.
        """
        if self.ldap:
            self.ldap.close()

    def fetch(self, searchval=None):
        """
        :func:`burpui.misc.auth.ldap.LdapLoader.fetch` searches for a user object in the
        LDAP server.

        :param searchval: attribute value to search for
        :type searchval: str

        :returns: dictionary of `distinguishedName` and `commonName` attributes for the
        user if found, otherwise None.
        """
        try:
            if self.filt:
                query = self.filt.format(self.attr, searchval)
            else:
                query = '{0}={1}'.format(self.attr, searchval)
            self.app.logger.info('filter: %s | base: %s', query, self.base)
            r = self.ldap.search(query, base_dn=self.base, attrs=['distinguishedname', 'cn', self.attr])
        except Exception, e:
            self.app.logger.error('Ooops, LDAP lookup failed: {0}'.format(str(e)))
            return None

        for record in r:
            if record[self.attr][0] == searchval:
                dn = record['distinguishedname'][0]
                self.app.logger.info('Found DN: {0}'.format(dn))
                return {'dn': dn, 'cn': record['cn'][0]}

    def check(self, dn=None, passwd=None):
        """
        :func:`burpui.misc.auth.ldap.LdapLoader.check` authenticates a user against the
        LDAP server.

        :param dn: `distinguishedName` attribute of the user to authenticate as
        :type dn: str

        :param passwd: password of the user to authenticate as
        :type passwd: str

        :returns: True if bind was successful, otherwise False
        """
        try:
            l = simpleldap.Connection(self.host, dn='{0}'.format(dn), password=passwd)
            self.app.logger.info('Bound as user: {0}'.format(dn))
        except Exception, e:
            self.app.logger.error('Failed to authenticate user: {0}, {1}'.format(dn, str(e)))
            return False

        l.close()
        return True



class UserHandler(BUIhandler):
    """
    The :class:`burpui.misc.auth.ldap.UserHandler` class maintains a list of ``Burp-UI`` users.
    """
    def __init__(self, app=None):
        self.ldap = LdapLoader(app)
        self.users = {}

    def user(self, name=None):
        if name not in self.users:
            self.users[name] = LdapUser(self.ldap, name)
        return self.users[name]



class LdapUser(UserMixin, BUIuser):
    """
    The :class:`burpui.misc.auth.ldap.LdapUser` class generates a ``Burp-UI`` user from
    a user object found in the LDAP server.
    """
    def __init__(self, ldap=None, name=None):
        """
        :func:`burpui.misc.auth.ldap.LdapUser.__init__` function finds a user in the
        LDAP server and stores the DN of the user if found.

        :param ldap: an ``LdapLoader`` instance
        :type ldap: :class:`burpui.misc.auth.ldap.LdapLoader`

        :param name: login name of the user to find in the LDAP server
        :param type: str
        """
        self.active = False
        self.ldap = ldap
        self.name = name

        found = self.ldap.fetch(name)

        if found:
            self.id = found['dn']
            self.active = True

    def login(self, name=None, passwd=None):
        """
        :func:`burpui.misc.auth.ldap.LdapUser.login` function finds a user in the
        LDAP server and authenticates that user using an LDAP bind.

        :param name: login name of the user to authenticate as
        :type name: str

        :param passwd: password to bind to the LDAP server with
        :type passwd: str

        :returns: True if found and bind was successful;
                  False if found but bind failed;
                  otherwise de-activates the user and returns False
        """
        if self.ldap.fetch(name):
            return self.ldap.check(self.id, passwd)
        else:
            self.active = False
            return False

    def is_active(self):
        """
        :func:`burpui.misc.auth.ldap.LdapUser.is_active` function

        :returns: True if user is active, otherwise False
        """
        return self.active

    def get_id(self):
        """
        :func:`burpui.misc.auth.ldap.LdapUser.get_id` function

        :returns: login name of the user
        """
        return self.name

