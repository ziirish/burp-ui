# -*- coding: utf8 -*-
from six import viewitems

from .interface import BUIhandler, BUIuser, BUIloader
from ..._compat import ConfigParser

import ssl

try:
    from ldap3 import Server, Connection, Tls, ALL, RESTARTABLE, AUTO_BIND_TLS_BEFORE_BIND, AUTO_BIND_NONE, SIMPLE
except ImportError:
    raise ImportError('Unable to load \'ldap3\' module')


class LdapLoader(BUIloader):
    """The :class:`burpui.misc.auth.ldap.LdapLoader` handles searching for and
    binding as a :class:`burpui.misc.auth.ldap.LdapUser` user.
    """
    def __init__(self, app=None, handler=None):
        """:func:`burpui.misc.auth.ldap.LdapLoader.__init__` establishes a
        connection to the LDAP server.

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
            # Maybe the handler argument is None, maybe the 'priority'
            # option is missing. We don't care.
            try:
                handler.priority = c.getint('LDAP', 'priority')
            except:
                pass
            for (opt, key) in viewitems(mapping):
                try:
                    setattr(self, opt, c.get('LDAP', key))
                except ConfigParser.NoOptionError as e:
                    self.logger.info(str(e))
                except ConfigParser.NoSectionError as e:
                    self.logger.error(str(e))

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
                self.logger.error('LDAP port must be a valid integer')
                self.port = None
        self.logger.info('LDAP host: {0}'.format(self.host))
        self.logger.info('LDAP port: {0}'.format(self.port))
        self.logger.info('LDAP encryption: {0}'.format(self.encryption))
        self.logger.info('LDAP filter: {0}'.format(self.filt))
        self.logger.info('LDAP base: {0}'.format(self.base))
        self.logger.info('LDAP search attr: {0}'.format(self.attr))
        self.logger.info('LDAP binddn: {0}'.format(self.binddn))
        self.logger.info('LDAP bindpw: {0}'.format('*****' if self.bindpw else 'None'))
        self.logger.info('TLS object: {0}'.format(self.tls))

        try:
            self.server = Server(host=self.host, port=self.port, use_ssl=self.ssl, get_info=ALL, tls=self.tls)
            self.logger.debug('LDAP Server = {0}'.format(str(self.server)))
            if self.binddn:
                self.ldap = Connection(self.server, user=self.binddn, password=self.bindpw, raise_exceptions=True, client_strategy=RESTARTABLE, auto_bind=self.auto_bind, authentication=SIMPLE)
            else:
                self.ldap = Connection(self.server, raise_exceptions=True, client_strategy=RESTARTABLE, auto_bind=self.auto_bind)
            with self.ldap:
                self.logger.debug('LDAP Connection = {0}'.format(str(self.ldap)))
                self.logger.info('OK, connected to LDAP')
                return

            raise Exception('Not connected')
        except Exception as e:
            self.logger.error('Could not connect to LDAP: {0}'.format(str(e)))
            self.server = None
            self.ldap = None

    def __exit__(self, exc_type, exc_value, traceback):
        """:func:`burpui.misc.auth.ldap.LdapLoader.__exit__` closes the
        connection to the LDAP server.
        """
        if self.ldap and self.ldap.bound:
            self.ldap.unbind()

    def fetch(self, searchval=None):
        """:func:`burpui.misc.auth.ldap.LdapLoader.fetch` searches for a user
        object in the LDAP server.

        :param searchval: attribute value to search for
        :type searchval: str

        :returns: dictionary of `distinguishedName` and `commonName` attributes for the
        user if found, otherwise None.
        """
        try:
            if self.filt:
                query = self.filt.format(self.attr, searchval)
            else:
                query = '({0}={1})'.format(self.attr, searchval)
            self.logger.info('filter: {0} | base: {1}'.format(query, self.base))
            r = None
            with self.ldap:
                self.logger.debug('LDAP Connection = {0}'.format(str(self.ldap)))
                self.ldap.search(self.base, query, attributes=['cn', self.attr])
                r = self.ldap.response
            if not r:
                raise Exception('no results')
        except Exception as e:
            self.logger.error('Ooops, LDAP lookup failed: {0}'.format(str(e)))
            return None

        for record in r:
            attrs = record['attributes']
            if self.attr in attrs and searchval in attrs[self.attr]:
                self.logger.info('Found DN: {0}'.format(record['dn']))
                return {'dn': record['dn'], 'cn': attrs['cn'][0]}

    def check(self, dn=None, passwd=None):
        """:func:`burpui.misc.auth.ldap.LdapLoader.check` authenticates a user
        against the LDAP server.

        :param dn: canonical `dn` of the user to authenticate as
        :type dn: str

        :param passwd: password of the user to authenticate as
        :type passwd: str

        :returns: True if bind was successful, otherwise False
        """
        try:
            with Connection(self.server, user='{0}'.format(dn), password=passwd, raise_exceptions=True, auto_bind=self.auto_bind, authentication=SIMPLE) as l:
                self.logger.debug('LDAP Connection = {0}'.format(str(l)))
                self.logger.info('Bound as user: {0}'.format(dn))
                return l.bind()
        except Exception as e:
            self.logger.error('Failed to authenticate user: {0}, {1}'.format(dn, str(e)))

        self.logger.error('Bind as \'{0}\' failed'.format(dn))
        return False


class UserHandler(BUIhandler):
    """The :class:`burpui.misc.auth.ldap.UserHandler` class maintains a list of
    ``Burp-UI`` users.
    """
    def __init__(self, app=None, auth=None):
        """:func:`burpui.misc.auth.ldap.UserHandler.__init__` creates the
        handler instance

        :param app: Instance of the app we are running in
        :type app: :class:`burpui.server.BUIServer`
        """
        self.ldap = LdapLoader(app, self)
        self.users = {}

    def user(self, name=None):
        """See :func:`burpui.misc.auth.interface.BUIhandler.user`"""
        if name not in self.users:
            self.users[name] = LdapUser(self.ldap, name)
        return self.users[name]


class LdapUser(BUIuser):
    """The :class:`burpui.misc.auth.ldap.LdapUser` class generates a ``Burp-UI``
    user from a user object found in the LDAP server.
    """
    def __init__(self, ldap=None, name=None):
        """:func:`burpui.misc.auth.ldap.LdapUser.__init__` function finds a user
        in the LDAP server and stores the DN of the user if found.

        :param ldap: an ``LdapLoader`` instance
        :type ldap: :class:`burpui.misc.auth.ldap.LdapLoader`

        :param name: login name of the user to find in the LDAP server
        :param type: str
        """
        self.active = False
        self.authenticated = False
        self.ldap = ldap
        self.name = name

        found = self.ldap.fetch(name)

        if found:
            self.id = found['dn']
            self.active = True

    def login(self, name=None, passwd=None):
        """:func:`burpui.misc.auth.ldap.LdapUser.login` function finds a user in
        the LDAP server and authenticates that user using an LDAP bind.

        :param name: login name of the user to authenticate as
        :type name: str

        :param passwd: password to bind to the LDAP server with
        :type passwd: str

        :returns: True if found and bind was successful;
                  False if found but bind failed;
                  otherwise de-activates the user and returns False
        """
        if self.ldap.fetch(name):
            self.authenticated = self.ldap.check(self.id, passwd)
            return self.authenticated
        else:
            self.authenticated = False
            self.active = False
            return False

    @property
    def is_active(self):
        """:func:`burpui.misc.auth.ldap.LdapUser.is_active` function

        :returns: True if user is active, otherwise False
        """
        return self.active

    @property
    def is_authenticated(self):
        """:func:`burpui.misc.auth.ldap.LdapUser.is_authenticated` function

        :returns: True if a user is authenticated, otherwise False
        """
        return self.authenticated

    def get_id(self):
        """:func:`burpui.misc.auth.ldap.LdapUser.get_id` function

        :returns: login name of the user
        """
        return self.name
