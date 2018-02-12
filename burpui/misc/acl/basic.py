# -*- coding: utf8 -*-
from .interface import BUIacl, BUIaclLoader
from ...utils import make_list, NOTIF_OK, NOTIF_WARN, NOTIF_ERROR
from six import iteritems

import re
import json
import fnmatch


class ACLloader(BUIaclLoader):
    """See :class:`burpui.misc.acl.interface.BUIaclLoader`"""
    section = name = 'BASIC:ACL'
    priority = 100

    def __init__(self, app=None):
        """See :func:`burpui.misc.acl.interface.BUIaclLoader.__init__`

        :param app: Application context
        :type app: :class:`burpui.server.BUIServer`
        """
        self.app = app
        self.admins = [
            'admin'
        ]
        self.moderators = []
        self._groups = {}
        self._grants = {}
        self.standalone = self.app.standalone
        self.extended = False
        self.legacy = False
        self.assume_granted = True
        self.moderator = {}
        self._acl = None
        self.conf_id = None
        self.conf = self.app.conf
        self.load_acl(True)

    def load_acl(self, force=False):
        if not force and self.conf_id:
            if not self.conf.changed(self.conf_id):
                return False

        self.admins = [
            'admin'
        ]
        self.moderators = []
        self._grants = {}
        self.groups_def = {}

        adms = []
        mods = []

        def is_empty(data):
            return not data or data == [None]

        if self.section in self.conf.options:
            adms = self.conf.safe_get(
                'admin',
                'force_list',
                section=self.section
            )
            mods = self.conf.safe_get(
                '+moderator',
                'force_list',
                section=self.section
            )
            self.priority = self.conf.safe_get(
                'priority',
                'integer',
                section=self.section,
                defaults={self.section: {'priority': self.priority}}
            )
            self.extended = self.conf.safe_get(
                'extended',
                'boolean',
                section=self.section
            )
            self.assume_granted = self.conf.safe_get(
                'assume_granted',
                'boolean',
                section=self.section,
                defaults={self.section: {'assume_granted': True}}
            )
            self.legacy = self.conf.safe_get(
                'legacy',
                'boolean',
                section=self.section
            )
            self.moderator = self.conf.safe_get(
                '@moderator',
                'force_string',
                section=self.section
            ) or {}
            for opt in self.conf.options.get(self.section).keys():
                if opt in ['admin', '+moderator', 'extended', 'priority', '@moderator', 'legacy', 'assume_granted']:
                    continue
                record = self.conf.safe_get(
                    opt,
                    'force_string',
                    section=self.section
                )

                self.logger.debug('record: {} -> {}'.format(opt, record))

                def _parse_record(key, load=True):
                    if gname not in self.groups_def:
                        self.groups_def[gname] = {}
                    if load:
                        try:
                            parsed = json.loads(record)
                        except ValueError:
                            if ',' in record:
                                parsed = [x.strip() for x in record.split(',')]
                            else:
                                parsed = make_list(record)
                    else:
                        parsed = record
                    self.groups_def[gname][key] = parsed

                    return parsed

                if opt[0] == '+':
                    short = opt.lstrip('+')
                    gname = '@{}'.format(short)
                    members = _parse_record('members')
                    self._groups[short] = members
                elif opt[0] == '@':
                    short = opt.lstrip('@')
                    if short not in self._groups:
                        self._groups[short] = []
                    gname = opt
                    _parse_record('grants', load=False)
                else:
                    self._grants[opt] = record

        if not is_empty(adms):
            self.admins = adms
        if not is_empty(mods):
            self.moderators = mods

        if self.legacy:
            self.extended = False

        self.logger.debug('admins: {}'.format(self.admins))
        self.logger.debug('moderators: {}'.format(self.moderators))
        self.logger.debug('moderator grants: {}'.format(self.moderator))
        self.logger.debug('groups: {}'.format(self.groups_def))
        self.logger.debug('extended: {}'.format(self.extended))
        self.logger.debug('legacy: {}'.format(self.legacy))

        self.conf_id = self.conf.id
        self._acl = BasicACL(self)

        return True

    def _setup_acl(self):
        """Setup ACL management"""
        if not self.conf.lookup_section(self.section):
            self.conf._refresh()

    def add_grant(self, name, content):
        """Add a grant"""
        if name[0] in ['+', '@']:
            message = "'{}' is not a valid grant name".format(name)
            self.logger.error(message)
            return False, message, NOTIF_ERROR
        self._setup_acl()
        if name in self.conf.options[self.section]:
            message = "grant '{}' already exists".format(name)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        self.conf.options[self.section][name] = content
        self.conf.options.write()
        self.load_acl(True)
        message = "grant '{}' successfully added".format(name)
        return True, message, NOTIF_OK

    def del_grant(self, name):
        """Delete a grant"""
        if name[0] in ['+', '@']:
            message = "'{}' is not a valid grant name".format(name)
            self.logger.error(message)
            return False, message, NOTIF_ERROR
        self._setup_acl()
        self.load_acl(True)
        if name not in self.conf.options[self.section]:
            message = "grant '{}' does not exist".format(name)
            self.logger.error(message)
            return False, message, NOTIF_ERROR
        del self.conf.options[self.section][name]
        self.conf.options.write()
        self.load_acl(True)
        message = "grant '{}' successfully removed".format(name)
        return True, message, NOTIF_OK

    def mod_grant(self, name, content):
        """Update a grant"""
        if name[0] in ['+', '@']:
            message = "'{}' is not a valid grant name".format(name)
            self.logger.error(message)
            return False, message, NOTIF_ERROR
        self._setup_acl()
        self.load_acl(True)
        if name not in self.conf.options[self.section]:
            message = "grant '{}' does not exist".format(name)
            self.logger.error(message)
            return False, message, NOTIF_WARN
        self.conf.options[self.section][name] = content
        self.conf.options.write()
        self.load_acl(True)
        message = "grant '{}' successfully modified".format(name)
        return True, message, NOTIF_OK

    def add_group(self, name, content):
        """Create a group"""
        self._setup_acl()
        name = '@{}'.format(name)
        if name in self.conf.options[self.section]:
            message = "group '{}' already exists".format(name)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        self.conf.options[self.section][name] = content
        self.conf.options.write()
        self.load_acl(True)
        message = "group '{}' successfully added".format(name)
        return True, message, NOTIF_OK

    def del_group(self, name):
        """Delete a group"""
        self._setup_acl()
        self.load_acl(True)
        gname = '@{}'.format(name)
        if gname not in self.conf.options[self.section]:
            message = "group '{}' does not exist".format(name)
            self.logger.error(message)
            return False, message, NOTIF_ERROR
        del self.conf.options[self.section][gname]
        gmembers = '+{}'.format(name)
        if gmembers in self.conf.options[self.section]:
            del self.conf.options[self.section][gmembers]
        self.conf.options.write()
        self.load_acl(True)
        message = "grant '{}' successfully removed".format(name)
        return True, message, NOTIF_OK

    def mod_group(self, name, content):
        """Update a group"""
        self._setup_acl()
        name = '@{}'.format(name)
        if name not in self.conf.options[self.section]:
            message = "group '{}' does not exist".format(name)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        self.conf.options[self.section][name] = content
        self.conf.options.write()
        self.load_acl(True)
        message = "group '{}' successfully modified".format(name)
        return True, message, NOTIF_OK

    def add_group_member(self, group, member):
        """Add a user to a group"""
        if group not in self._groups:
            message = "group '{}' does not exist".format(group)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        if member in self._groups[group]:
            message = "'{}' already in group '{}'".format(member, group)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        self._setup_acl()
        self._groups[group].append(member)
        gmembers = '+{}'.format(group)
        self.conf.options[self.section][gmembers] = ','.join(self._groups[group])
        self.conf.options.write()
        self.load_acl(True)
        message = "'{}' added to group '{}'".format(member, group)
        return True, message, NOTIF_OK

    def del_group_member(self, group, member):
        """Remove a user from a group"""
        if group not in self._groups:
            message = "group '{}' does not exist".format(group)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        if member not in self._groups[group]:
            message = "'{}' not in group '{}'".format(member, group)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        self._setup_acl()
        self._groups[group].remove(member)
        gmembers = '+{}'.format(group)
        self.conf.options[self.section][gmembers] = ','.join(self._groups[group])
        self.conf.options.write()
        self.load_acl(True)
        message = "'{}' removed from group '{}'".format(member, group)
        return True, message, NOTIF_OK

    def add_moderator(self, member):
        """Add a moderator"""
        if member in self.moderators:
            message = "'{}' is already a moderator".format(member)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        self._setup_acl()
        self.moderators.append(member)
        self.conf.options[self.section]['+moderator'] = ','.format(self.moderators)
        self.conf.options.write()
        message = "'{}' successfully added as moderator".format(member)
        return True, message, NOTIF_OK

    def del_moderator(self, member):
        """Delete a moderator"""
        if member not in self.moderators:
            message = "'{}' is not a moderator".format(member)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        self._setup_acl()
        self.moderators.remove(member)
        self.conf.options[self.section]['+moderator'] = ','.format(self.moderators)
        self.conf.options.write()
        message = "'{}' successfully removed from moderators".format(member)
        return True, message, NOTIF_OK

    def mod_moderator(self, grants):
        """Update moderator grants"""
        self._setup_acl()
        self.moderator = grants
        self.conf.options[self.section]['@moderator'] = grants
        self.conf.options.write()
        message = "moderator grants updated"
        return True, message, NOTIF_OK

    def add_admin(self, member):
        """Add an admin"""
        if member in self.admins:
            message = "'{}' is already an admin".format(member)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        self._setup_acl()
        self.admins.append(member)
        self.conf.options[self.section]['admin'] = ','.format(self.admins)
        self.conf.options.write()
        message = "'{}' successfully added as admin".format(member)
        return True, message, NOTIF_OK

    def del_admin(self, member):
        """Delete an admin"""
        if member in self.admins:
            message = "'{}' is not an admin".format(member)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        self._setup_acl()
        self.admins.remove(member)
        self.conf.options[self.section]['admin'] = ','.format(self.admins)
        self.conf.options.write()
        message = "'{}' successfully removed from admins".format(member)
        return True, message, NOTIF_OK

    @property
    def acl(self):
        """Property to retrieve the backend"""
        if self._acl:
            self.load_acl()
            return self._acl
        return None  # pragma: no cover

    @property
    def grants(self):
        """Property to retrieve the list of grants"""
        if self._acl:
            self.load_acl()
            return self._grants
        return None  # pragma: no cover

    @property
    def groups(self):
        """Property to retrieve the list of groups with their members"""
        if self._acl:
            self.load_acl()
            return self.groups_def
        return None  # pragma: no cover


class BasicACL(BUIacl):
    """See :class:`burpui.misc.acl.interface.BUIacl`"""
    def __init__(self, loader=None):
        """:func:`burpui.misc.acl.interface.BUIacl.__init__` instanciate ACL
        engine.

        :param loader: ACL loader
        :type loader: :class:`burpui.misc.acl.interface.BUIaclLoader`
        """
        if not loader:  # pragma: no cover
            return
        self.loader = loader
        self.standalone = loader.standalone
        self.admins = loader.admins
        self.moderators = loader.moderators
        self.moderator = loader.moderator
        self.grants = loader.grants
        self.groups = loader.groups
        self.extended = loader.extended
        self.assume_granted = loader.assume_granted
        self.legacy = loader.legacy
        self._parsed_grants = []
        self._clients_cache = {}
        self._agents_cache = {}
        self._advanced_cache = {}

    def is_admin(self, username=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_admin`"""
        if not username:  # pragma: no cover
            return False
        return username in self.admins

    def is_moderator(self, username=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_moderator`"""
        if not username:
            return False
        return username in self.moderators

    def _extract_grants(self, username):
        if username not in self._parsed_grants:

            if username == '@moderator':
                grants = self.moderator
            elif username[0] == '@':
                grants = self.groups.get(username, {}).get('grants', '')
            else:
                grants = self.grants.get(username, '')
            try:
                grants = json.loads(grants)
            except ValueError:
                if ',' in grants:
                    grants = [x.strip() for x in grants.split(',')]
                else:
                    grants = make_list(grants)

            clients, agents, advanced = self._parse_clients(grants)
            self._clients_cache[username] = clients
            self._agents_cache[username] = agents
            self._advanced_cache[username] = advanced

            def __merge_grants_with(grp):
                if grp not in self._parsed_grants:
                    self._extract_grants(grp)
                self._clients_cache[username] = self._merge_data(
                    self._clients_cache[username],
                    self._clients_cache.get(grp, [])
                )
                self._agents_cache[username] = self._merge_data(
                    self._agents_cache[username],
                    self._agents_cache.get(grp, [])
                )
                self._advanced_cache[username] = self._merge_data(
                    self._advanced_cache[username],
                    self._advanced_cache.get(grp, [])
                )

            if self.is_moderator(username):
                __merge_grants_with('@moderator')

            for gname, group in iteritems(self.groups):
                if username in group.get('members', []) and gname != username:
                    __merge_grants_with(gname)

            self._parsed_grants.append(username)

    def _extract_clients(self, username):
        if username not in self._parsed_grants:
            self._extract_grants(username)
        return self._clients_cache.get(username, [])

    def _extract_agents(self, username):
        if username not in self._parsed_grants:
            self._extract_grants(username)
        return self._agents_cache.get(username, [])

    def _extract_advanced(self, username):
        if username not in self._parsed_grants:
            self._extract_grants(username)
        return self._advanced_cache.get(username, {})

    def _extract_advanced_mode(self, username, mode, kind):
        if username not in self._parsed_grants:
            self._extract_grants(username)
        return self._advanced_cache.get(username, {}).get(mode, {}).get(kind, [])

    def _client_match(self, username, client):
        clients = self._extract_clients(username)
        if not clients:
            return None

        if self.extended:
            for exp in clients:
                regex = fnmatch.translate(exp)
                if re.match(regex, client):
                    return exp
            return False
        else:
            return client if client in clients else False

    def _server_match(self, username, server):
        servers = self._extract_agents(username)
        if not servers:
            return None

        if self.extended:
            for exp in servers:
                regex = fnmatch.translate(exp)
                if re.match(regex, server):
                    return exp
            return False
        else:
            return server if server in servers else False

    def is_client_rw(self, username=None, client=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_client_rw`"""
        if not username or not client:  # pragma: no cover
            return False

        is_admin = self.is_admin(username)

        if self.is_client_allowed(username, client, server):
            # legacy mode: assume rw for everyone
            if self.legacy:
                return True
            client_match = self._client_match(username, client)
            advanced = self._extract_advanced(username)

            if not client_match and username == client:
                client_match = username

            if server:
                server_match = self._server_match(username, server)

                if not server_match and not client_match:
                    return is_admin or self.assume_granted

                # the whole agent is rw and we did not find explicit entry for
                # client_match
                if client_match is False:
                    if server_match in advanced.get('rw', {}) or \
                            server_match in advanced.get('rw', {}).get('agents', []):
                        return True
                    if server in advanced.get('rw', {}) or \
                            server in advanced.get('rw', {}).get('agents', []):
                        return True

                if server_match and \
                        (server_match in advanced.get('ro', {}) or
                         server_match in advanced.get('ro', {}).get('agents', [])):
                    # the agent is ro, but the client is explicitly defined as rw
                    if client_match and \
                        (client_match not in advanced.get('rw', {}).get(server_match, []) or
                         client_match not in advanced.get('rw', {}).get('clients', [])):
                        return True

            rw_clients = advanced.get('rw', {}).get('clients', [])
            if client_match and \
                    client_match in rw_clients:
                return True

            if client and \
                    client in rw_clients:
                return True

        if self.legacy:
            return True
        return is_admin or self.assume_granted

    def is_client_allowed(self, username=None, client=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_client_allowed`"""
        if not username or not client:  # pragma: no cover
            return False

        is_admin = self.is_admin(username)
        client_match = self._client_match(username, client)

        if not client_match and username == client:
            client_match = username

        if server:
            server_match = self._server_match(username, server)
            if server_match is not None or self.legacy:
                if not server_match:
                    return is_admin

                advanced = self._extract_advanced(username)

                if not client_match and server_match not in advanced and \
                        (server_match in self._extract_advanced_mode(username, 'ro', 'agents') or
                         server_match in self._extract_advanced_mode(username, 'rw', 'agents')):
                    return True

                advanced = advanced.get(server_match, advanced.get(server, []))
                if client_match not in advanced and client not in advanced:
                    return is_admin

        return client_match is not False or is_admin

    def is_server_rw(self, username=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_server_rw`"""
        if not username or not server:  # pragma: no cover
            return False

        is_admin = self.is_admin(username)
        if self.is_server_allowed(username, server):
            server_match = self._server_match(username, server)
            if not server_match:
                return self.is_admin or self.assume_granted

            advanced = self._extract_advanced(username)

            if server_match in advanced.get('rw', {}).get('agents', []):
                return True

        if self.legacy:
            return True
        return is_admin or self.assume_granted

    def is_server_allowed(self, username=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_server_allowed`"""
        if not username or not server:
            return False

        server_match = self._server_match(username, server)
        is_admin = self.is_admin(username)

        if server_match is None and self.legacy:
            server_match = False

        return server_match is not False or is_admin
