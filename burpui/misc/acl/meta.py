# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.acl.meta
    :platform: Unix
    :synopsis: Burp-UI ACL meta definitions.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from .interface import BUIacl
from ...utils import make_list

from six import iteritems, itervalues

import re
import json
import fnmatch


class BUImetaGrant(object):

    def _merge_data(self, d1, d2):
        """Merge data as list or dict recursively avoiding duplicates"""
        if not d1 and not d2:
            return []
        if not d2:
            return d1
        if not d1:
            return d2
        if isinstance(d1, list) and isinstance(d2, list):
            return list(set(d1 + d2))
        if isinstance(d1, list) and not isinstance(d2, dict):
            if d2 in d1:
                return d1
            return d1 + make_list(d2)
        if isinstance(d2, list) and not isinstance(d1, dict):
            if d1 in d2:
                return d2
            return d2 + make_list(d1)
        if not isinstance(d1, dict) and not isinstance(d2, dict):
            if d1 == d2:
                return make_list(d1)
            else:
                return [d1, d2]

        res = d1
        for key2, val2 in iteritems(d2):
            if key2 in res:
                res[key2] = self._merge_data(val2, res[key2])
            else:
                res[key2] = val2
        return res

    def _parse_clients(self, data, mode=None):
        agents = clients = []
        advanced = {}
        if isinstance(data, list):
            if mode:
                advanced[mode] = {'clients': data}
            return data, agents, advanced
        if not isinstance(data, dict):
            if mode:
                advanced[mode] = {'clients': make_list(data)}
            return make_list(data), agents, advanced
        for key, val in iteritems(data):
            if key in ['agents', 'clients', 'ro', 'rw']:
                continue
            cl1, ag1, ad1 = self._parse_clients(val)
            agents = self._merge_data(agents, ag1)
            clients = self._merge_data(clients, cl1)
            agents = self._merge_data(agents, key)
            advanced = self._merge_data(advanced, ad1)
            advanced = self._merge_data(advanced, {key: cl1})
            if mode:
                advanced = self._merge_data(advanced, {mode: {key: cl1}})

        for key in ['clients', 'ro', 'rw']:
            md = None
            if key in data:
                if key in ['ro', 'rw']:
                    md = key
                cl2, ag2, ad2 = self._parse_clients(data[key], md)
                agents = self._merge_data(agents, ag2)
                clients = self._merge_data(clients, cl2)
                advanced = self._merge_data(advanced, ad2)

        if 'agents' in data:
            ag3, cl3, ad3 = self._parse_agents(data['agents'])
            agents = self._merge_data(agents, ag3)
            clients = self._merge_data(clients, cl3)
            advanced = self._merge_data(advanced, ad3)

        return make_list(clients), make_list(agents), advanced

    def _parse_agents(self, data, mode=None):
        agents = clients = []
        advanced = {}
        if isinstance(data, list):
            if mode:
                advanced[mode] = {'agents': data}
            return data, clients, advanced
        if not isinstance(data, dict):
            if mode:
                advanced[mode] = {'agents': make_list(data)}
            return make_list(data), clients, advanced
        for key, val in iteritems(data):
            if key in ['agents', 'clients', 'ro', 'rw']:
                continue
            cl1, ag1, ad1 = self._parse_clients(data)
            agents = self._merge_data(agents, ag1)
            clients = self._merge_data(clients, cl1)
            agents = self._merge_data(agents, key)
            advanced = self._merge_data(advanced, ad1)
            advanced = self._merge_data(advanced, {key: cl1})
            if mode:
                advanced = self._merge_data(advanced, {mode: {key: cl1}})

        for key in ['agents', 'ro', 'rw']:
            md = None
            if key in data:
                if key in ['ro', 'rw']:
                    md = key
                ag2, cl2, ad2 = self._parse_agents(data[key], md)
                agents = self._merge_data(agents, ag2)
                clients = self._merge_data(clients, cl2)
                advanced = self._merge_data(advanced, ad2)

        if 'clients' in data:
            cl3, ag3, ad3 = self._parse_clients(data['clients'])
            agents = self._merge_data(agents, ag3)
            clients = self._merge_data(clients, cl3)
            advanced = self._merge_data(advanced, ad3)

        return make_list(agents), make_list(clients), advanced


class BUIgrantHandler(BUImetaGrant, BUIacl):
    """This class is here to handle grants in a generic way.
    It will automatically merge grants from various backends that register to it
    """
    _id = 1
    _gp_admin_name = '@BUIADMINRESERVED'
    _gp_moderator_name = '@moderator'
    _gp_hidden = set([str(_gp_admin_name[1:]), str(_gp_moderator_name[1:])])

    _grants = {}
    _groups = {}

    _parsed_grants = []

    _clients_cache = {}
    _agents_cache = {}
    _advanced_cache = {}

    _options = {}
    _backends = {}

    @property
    def id(self):
        """current handler id, used to detect configuration changes"""
        return self._id

    @property
    def grants(self):
        """grants managed by our handler"""
        return self._grants

    @property
    def groups(self):
        """groups managed by our handler"""
        return self._groups

    @property
    def options(self):
        """options of our ACL engine"""
        return self._options

    @options.setter
    def options(self, value):
        """set the options of our engine"""
        self._options = value
        if self._options.get('legacy'):
            self._options['extended'] = False

    def changed(self, sid):
        """detect a configuration change"""
        return sid != self._id

    def reset(self, reset_from):
        """a configuration change occurred, we reload our grants and groups"""
        self._grants.clear()
        self._groups.clear()
        self._parsed_grants = []
        self._clients_cache.clear()
        self._agents_cache.clear()
        self._advanced_cache.clear()
        self._id += 1
        for name, backend in iteritems(self._backends):
            if name == reset_from:
                continue
            backend.reload()

    def opt(self, key, default=False):
        """access a given option"""
        if key not in self.options:
            return default
        return self.options.get(key)

    def register_backend(self, name, backend):
        """register a new ACL backend

        :param name: Backend name
        :type name: str

        :param backend: ACL Backend
        :type backend: :class:`burpui.misc.acl.interface.BUIaclLoader`
        """
        self._backends[name] = backend

    def set_grant(self, name, grant):
        """parse and set the given grants"""
        if name in self._grants:
            return self._grants[name].add_grants(grant)
        self._grants[name] = BUIaclGrant(name, grant)
        return self._grants[name].grants

    def set_group(self, name, members):
        """parse and set the given group"""
        if name in self._groups:
            return self._groups[name].add_members(members)
        self._groups[name] = BUIaclGroup(name, members)
        return self._groups[name].members

    def set_admin(self, admins):
        """parse and set the admins"""
        self.set_group(self._gp_admin_name, admins)

    def set_moderator(self, moderators):
        """parse and set the moderators"""
        self.set_group(self._gp_moderator_name, moderators)

    def set_moderator_grants(self, grants):
        """parse and set the moderators grants"""
        self.set_grant(self._gp_moderator_name, grants)

    def get_member_groups(self, member):
        groups = []
        for group in itervalues(self._groups):
            if group.is_member(member) and group.name not in self._gp_hidden:
                groups.append(group.name)
        return groups

    def _extract_grants(self, username):
        if username not in self._parsed_grants:

            if username in self.grants:
                grants = self.grants[username].grants
            else:
                grants = []

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

            # moderator is also a group
            for gname, group in iteritems(self.groups):
                # no grants need to be parsed for admins
                if gname == self._gp_admin_name:
                    continue
                if group.is_member(username) and gname != username:
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

        if self.opt('extended'):
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

        if self.opt('extended'):
            for exp in servers:
                regex = fnmatch.translate(exp)
                if re.match(regex, server):
                    return exp
            return False
        else:
            return server if server in servers else False

    # implement BUIacl methods

    def is_admin(self, username):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_admin`"""
        return self._gp_admin_name in self._groups and \
            self._groups[self._gp_admin_name].is_member(username)

    def is_moderator(self, username):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_moderator`"""
        return self._gp_moderator_name in self._groups and \
            self._groups[self._gp_moderator_name].is_member(username)

    def is_client_rw(self, username=None, client=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_client_rw`"""
        if not username or not client:  # pragma: no cover
            return False

        is_admin = self.is_admin(username)

        if self.is_client_allowed(username, client, server):
            # legacy mode: assume rw for everyone
            if self.opt('legacy'):
                return True
            client_match = self._client_match(username, client)
            advanced = self._extract_advanced(username)

            if not client_match and username == client:
                client_match = username

            if server:
                server_match = self._server_match(username, server)

                if not server_match and not client_match:
                    return is_admin or self.opt('assume_granted')

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

        if self.opt('legacy'):
            return True
        return is_admin or self.opt('assume_granted')

    def is_client_allowed(self, username=None, client=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_client_allowed`"""
        if not username or not client:  # pragma: no cover
            return False

        is_admin = self.is_admin(username)
        client_match = self._client_match(username, client)

        if not client_match and username == client:
            client_match = username
        elif not client_match:
            client_match = False

        if server:
            server_match = self._server_match(username, server)
            if server_match is not None or self.opt('legacy'):
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
                return self.is_admin or self.opt('assume_granted')

            advanced = self._extract_advanced(username)

            if server_match in advanced.get('rw', {}).get('agents', []):
                return True

        if self.opt('legacy'):
            return True
        return is_admin or self.opt('assume_granted')

    def is_server_allowed(self, username=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_server_allowed`"""
        if not username or not server:
            return False

        server_match = self._server_match(username, server)
        is_admin = self.is_admin(username)

        if server_match is None and self.opt('legacy'):
            server_match = False

        return server_match is not False or is_admin


class BUIaclGroup(object):
    """The :class:`burpui.misc.acl.interface.BUIaclGroup` class is used to
    represent a Group"""

    def __init__(self, name, members=None):
        self._name = name
        self._set_members(members)

    def _parse_members(self, members):
        # we support only lists
        if ',' in members and not isinstance(members, list):
            parsed = [x.strip() for x in members.split(',')]
        else:
            parsed = make_list(members)
        return parsed

    def _set_members(self, members):
        self._members = set(self._parse_members(members))

    def add_members(self, new_members):
        new_members = self._parse_members(new_members)
        self._members = self._members | set(new_members)
        return new_members

    def del_members(self, members_remove):
        members_remove = self._parse_members(members_remove)
        self._members = self._members - set(members_remove)

    def is_member(self, member):
        return member in self._members

    @property
    def name(self):
        if self._name and any(self._name.startswith(x) for x in ['@', '+']):
            return str(self._name[1:])
        return self._name

    @property
    def members(self):
        return list(self._members)


class BUIaclGrant(BUImetaGrant):
    """The :class:`burpui.misc.acl.interface.BUIaclGrant` class is used to
    represent a Grant"""

    def __init__(self, name, grants):
        self._name = name
        self._grants = self._parse_grants(grants)

    def _parse_grants(self, grants):
        try:
            ret = json.loads(grants)
        except (ValueError, TypeError):
            # ignore mal-formatted json
            if any([x in grants for x in ['{', '}', '[', ']']]):
                ret = None
            elif ',' in grants:
                ret = [x.rstrip() for x in grants.split(',')]
            else:
                ret = make_list(grants)
        return ret

    @property
    def name(self):
        if self._name and any(self._name.startswith(x) for x in ['@', '+']):
            return str(self._name[1:])
        return self._name

    @property
    def grants(self):
        return self._grants

    @property
    def grants_raw(self):
        return json.dumps(self._grants)

    def add_grants(self, grants):
        parsed = self._parse_grants(grants)
        self._grants = self._merge_data(self._grants, parsed)
        return parsed


meta_grants = BUIgrantHandler()
