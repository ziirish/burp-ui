# -*- coding: utf8 -*-
from flask.ext.login import UserMixin
from burpui.misc.auth.interface import BUIhandler, BUIuser

try:
    from ldap3 import Server, Connection, ALL
except ImportError:
    raise ImportError('Unable to load \'ldap3\' module')

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
        conf = self.app.config['CFG']
        defaults = {'host': 'localhost', 'port': None, 'encryption': None, 'binddn': None, 'bindpw': None, 'filter': None, 'base': None, 'searchattr': 'uid'}
        mapping = {'host': 'host', 'port': 'port', 'encryption': 'encryption', 'filt': 'filter', 'base': 'base', 'attr': 'searchattr', 'binddn': 'binddn', 'bindpw': 'bindpw'}
        c = ConfigParser.ConfigParser(defaults)
        with open(conf) as fp:
            c.readfp(fp)
            for opt, key in mapping.viewitems():
                try:
                    setattr(self, opt, c.get('LDAP', key))
                except ConfigParser.NoOptionError, e:
                    self.app.logger.info(str(e))
                except ConfigParser.NoSectionError, e:
                    self.app.logger.error(str(e))

        self.tls = False
        self.ssl = False
        if self.encryption == 'ssl':
            self.ssl = True
        elif self.encryption == 'tls':
            selt.tls = True
        self.app.logger.info('LDAP host: %s', self.host)
        self.app.logger.info('LDAP port: %s', self.port)
        self.app.logger.info('LDAP encryption: %s', self.encryption)
        self.app.logger.info('LDAP filter: %s', self.filt)
        self.app.logger.info('LDAP base: %s', self.base)
        self.app.logger.info('LDAP search attr: %s', self.attr)
        self.app.logger.info('LDAP binddn: %s', self.binddn)
        self.app.logger.info('LDAP bindpw: %s', '*****' if self.bindpw else 'None')

        try:
            self.server = Server(host=self.host, port=self.port, use_ssl=self.ssl, get_info=ALL, tls=self.tls)
            self.ldap = Connection(self.server, user=self.binddn, password=self.bindpw, raise_exceptions=True)
            binded = False
            with self.ldap:
                binded = True
            if binded:
                self.app.logger.info('OK, connected to LDAP')
            else:
                raise Exception('Not connected')
        except:
            self.app.logger.error('Could not connect to LDAP')
            self.server = None
            self.ldap = None

    def __exit__(self, exc_type, exc_value, traceback):
        """
        :func:`burpui.misc.auth.ldap.LdapLoader.__exit__` closes the connection to the
        LDAP server.
        """
        if self.ldap and self.ldap.bound:
            self.ldap.unbind()

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
            r = None
            with self.ldap:
                self.ldap.search(self.base, query, attributes=['cn', self.attr])
                r = self.ldap.response
            if not r:
                raise Exception('no results')
        except Exception as e:
            self.app.logger.error('Ooops, LDAP lookup failed: {0}'.format(str(e)))
            return None

        for record in r:
            attrs = record['attributes']
            if self.attr in attrs and searchval in attrs[self.attr]:
                self.app.logger.info('Found DN: {0}'.format(record['dn']))
                return {'dn': record['dn'], 'cn': attrs['cn'][0]}

    def check(self, dn=None, passwd=None):
        """
        :func:`burpui.misc.auth.ldap.LdapLoader.check` authenticates a user against the
        LDAP server.

        :param dn: canonical `dn` of the user to authenticate as
        :type dn: str

        :param passwd: password of the user to authenticate as
        :type passwd: str

        :returns: True if bind was successful, otherwise False
        """
        try:
            with Connection(self.server, user='{0}'.format(dn), password=passwd, raise_exceptions=True) as l:
                self.app.logger.info('Bound as user: {0}'.format(dn))
                return True
        except Exception as e:
            self.app.logger.error('Failed to authenticate user: {0}, {1}'.format(dn, str(e)))

        self.app.logger.error('Bind as \'{0}\' failed'.format(dn))
        return False


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
