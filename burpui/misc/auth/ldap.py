# -*- coding: utf8 -*-
from flask.ext.login import UserMixin
from burpui.misc.auth.interface import BUIhandler, BUIuser

import ssl

try:
    from ldap3 import Server, Connection, Tls, ALL, RESTARTABLE, AUTO_BIND_TLS_BEFORE_BIND, AUTO_BIND_NONE
except ImportError:
    raise ImportError('Unable to load \'ldap3\' module')

# python 3 compatibility
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser


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
        defaults = {
            'host': 'localhost',
            'port': None,
            'encryption': None,
            'binddn': None,
            'bindpw': None,
            'filter': None,
            'base': None,
            'searchattr': 'uid',
            'validate': 'none',
            'version': None,
            'cafile': None
        }
        mapping = {
            'host': 'host',
            'port': 'port',
            'encryption': 'encryption',
            'filt': 'filter',
            'base': 'base',
            'attr': 'searchattr',
            'binddn': 'binddn',
            'bindpw': 'bindpw',
            'validate': 'validate',
            'version': 'version',
            'cafile': 'cafile'
        }
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

        if self.validate and self.validate.lower() in ['none', 'optional', 'required']:
            self.validate = getattr(ssl, 'CERT_{}'.format(self.validate.upper()))
        else:
            self.validate = None
        if self.version and self.version in ['SSLv2', 'SSLv3', 'SSLv23', 'TLSv1', 'TLSv1_1']:
            self.version = getattr(ssl, 'PROTOCOL_{}'.format(self.version))
        else:
            self.version = None
        self.tls = None
        self.ssl = False
        self.auto_bind = AUTO_BIND_NONE
        if self.encryption == 'ssl':
            self.ssl = True
        elif self.encryption == 'tls':
            self.tls = Tls(local_certificate_file=self.cafile, validate=self.validate, version=self.version)
            self.auto_bind = AUTO_BIND_TLS_BEFORE_BIND
        if self.port:
            try:
                self.port = int(self.port)
            except ValueError:
                self.app.logger.error('LDAP port must be a valid integer')
                self.port = None
        self.app.logger.info('LDAP host: {0}'.format(self.host))
        self.app.logger.info('LDAP port: {0}'.format(self.port))
        self.app.logger.info('LDAP encryption: {0}'.format(self.encryption))
        self.app.logger.info('LDAP filter: {0}'.format(self.filt))
        self.app.logger.info('LDAP base: {0}'.format(self.base))
        self.app.logger.info('LDAP search attr: {0}'.format(self.attr))
        self.app.logger.info('LDAP binddn: {0}'.format(self.binddn))
        self.app.logger.info('LDAP bindpw: {0}'.format('*****' if self.bindpw else 'None'))
        self.app.logger.info('TLS object: {0}'.format(self.tls))

        try:
            self.server = Server(host=self.host, port=self.port, use_ssl=self.ssl, get_info=ALL, tls=self.tls)
            self.app.logger.debug('LDAP Server = {0}'.format(str(self.server)))
            self.ldap = Connection(self.server, user=self.binddn, password=self.bindpw, raise_exceptions=True, client_strategy=RESTARTABLE, auto_bind=self.auto_bind)
            with self.ldap:
                self.app.logger.debug('LDAP Connection = {0}'.format(str(self.ldap)))
                self.app.logger.info('OK, connected to LDAP')
                return

            raise Exception('Not connected')
        except Exception as e:
            self.app.logger.error('Could not connect to LDAP: {0}'.format(str(e)))
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
            self.app.logger.info('filter: {0} | base: {1}'.format(query, self.base))
            r = None
            with self.ldap:
                self.app.logger.debug('LDAP Connection = {0}'.format(str(self.ldap)))
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
            with Connection(self.server, user='{0}'.format(dn), password=passwd, raise_exceptions=True, auto_bind=self.auto_bind) as l:
                self.app.logger.debug('LDAP Connection = {0}'.format(str(l)))
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
