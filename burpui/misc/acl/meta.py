# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.acl.meta
    :platform: Unix
    :synopsis: Burp-UI ACL meta definitions.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from .interface import BUIacl
from ...utils import make_list
from ...config import config
from ...ext.cache import cache

from six import iteritems, itervalues

import re
import json
import fnmatch


class BUImetaGrant(object):

    def _merge_data(self, d1, d2):
        """Merge data as list or dict recursively avoiding duplicates"""
        if not d1 and not d2:
            if isinstance(d1, dict) or isinstance(d2, dict):
                return {}
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

    def _parse_clients(self, data, mode=None, parent=None):
        agents = clients = []
        advanced = {}
        if isinstance(data, list):
            if mode:
                if parent and parent not in ['agents', 'clients', 'ro', 'rw']:
                    advanced[mode] = {parent: data}
                else:
                    advanced[mode] = {'clients': data}
            return data, agents, advanced
        if not isinstance(data, dict):
            if mode:
                if parent and parent not in ['agents', 'clients', 'ro', 'rw']:
                    advanced[mode] = {parent: make_list(data)}
                else:
                    advanced[mode] = {'clients': make_list(data)}
            return make_list(data), agents, advanced
        for key, val in iteritems(data):
            if key in ['agents', 'clients', 'ro', 'rw']:
                continue
            cl1, ag1, ad1 = self._parse_clients(val, parent=key)
            agents = self._merge_data(agents, ag1)
            clients = self._merge_data(clients, cl1)
            agents = self._merge_data(agents, key)
            advanced = self._merge_data(advanced, ad1)
            advanced = self._merge_data(advanced, {key: cl1})
            if mode:
                if parent and parent not in ['agents', 'clients', 'ro', 'rw']:
                    advanced = self._merge_data(advanced, {mode: {parent: cl1}})
                else:
                    advanced = self._merge_data(advanced, {mode: {key: cl1}})

        for key in ['clients', 'ro', 'rw']:
            md = None
            if key in data:
                if key in ['ro', 'rw']:
                    md = key
                cl2, ag2, ad2 = self._parse_clients(data[key], md, parent=key)
                agents = self._merge_data(agents, ag2)
                clients = self._merge_data(clients, cl2)
                if parent and parent not in ['agents', 'clients', 'ro', 'rw']:
                    ro = ad2.get('ro')
                    rw = ad2.get('rw')
                    if ro and 'clients' in ro:
                        ro[parent] = ro['clients']
                        del ro['clients']
                        ad2['ro'] = ro
                    if rw and 'clients' in rw:
                        rw[parent] = rw['clients']
                        del rw['clients']
                        ad2['rw'] = rw
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
            if mode:
                advanced = self._merge_data(advanced, {mode: ad1})
            # FIXME: why did I do that?
            # advanced = self._merge_data(advanced, {key: cl1})
            # if mode:
            #     advanced = self._merge_data(advanced, {mode: {key: cl1}})

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

    _options = {}
    _backends = {}

    _name = 'meta_grant'

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
        self._reset_cached()
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
            (ret, inh) = group.is_member(member)
            if ret and group.name not in self._gp_hidden:
                groups.append((group.name, inh))
        return groups

    def _gen_key(self, username):
        return '{}-{}'.format(self._name, username)

    def _set_cached(self, username, value):
        key = self._gen_key(username)
        return cache.cache.set(key, value)

    def _get_cached(self, username):
        key = self._gen_key(username)
        return cache.cache.get(key)

    def _reset_cached(self):
        cache.clear()

    def _is_cached(self, username):
        key = self._gen_key(username)
        return cache.cache.has(key)

    def _extract_grants(self, username, parent=None):
        if not self._is_cached(username):
            data = {}

            if username in self.grants:
                grants = self.grants[username].grants
            else:
                grants = []

            clients, agents, advanced = self._parse_clients(grants)
            data['clients'] = clients
            data['agents'] = agents
            data['advanced'] = [advanced] if advanced else []

            def __merge_grants_with(grp, prt):
                data2 = self._extract_grants(grp, prt)
                data['clients'] = self._merge_data(
                    data['clients'],
                    data2['clients']
                )
                data['agents'] = self._merge_data(
                    data['agents'],
                    data2['agents']
                )
                tmp = data2['advanced']
                if tmp:
                    data['advanced'] += tmp

            # moderator is also a group
            for gname, group in iteritems(self.groups):
                # no grants need to be parsed for admins
                if gname == self._gp_admin_name:
                    continue
                (ret, _) = group.is_member(username)
                if not parent:
                    parent = set([username])
                elif isinstance(parent, set):
                    parent.add(username)
                if ret and gname != username and parent and gname not in parent:
                    __merge_grants_with(gname, parent)

            self._set_cached(username, data)
            return data
        return self._get_cached(username)

    def _extract_clients(self, username):
        ret = self._extract_grants(username)
        return ret.get('clients', [])

    def _extract_agents(self, username):
        ret = self._extract_grants(username)
        return ret.get('agents', [])

    def _extract_advanced(self, username, idx=None):
        ret = self._extract_grants(username).get('advanced', [])
        if idx is not None:
            return ret[idx]
        if self.opt('inverse_inheritance'):
            return reversed(ret)
        return ret

    def _extract_advanced_mode(self, username, mode, kind, idx):
        return self._extract_advanced(username, idx).get(mode, {}).get(kind, [])

    def _client_match(self, username, client):
        clients = self._extract_clients(username)
        if not clients:
            return None

        if self.opt('extended'):
            matches = []
            for exp in clients:
                regex = fnmatch.translate(exp)
                if re.match(regex, client):
                    matches.append(exp)
            return matches if matches else False
        else:
            return [client] if client in clients else False

    def _server_match(self, username, server):
        servers = self._extract_agents(username)
        if not servers:
            return None

        if self.opt('extended'):
            matches = []
            for exp in servers:
                regex = fnmatch.translate(exp)
                if re.match(regex, server):
                    matches.append(exp)
            return matches if matches else False
        else:
            return [server] if server in servers else False

    # implement BUIacl methods

    def is_admin(self, username):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_admin`"""
        if self._gp_admin_name in self._groups:
            return self._groups[self._gp_admin_name].is_member(username)
        return False, None

    def is_moderator(self, username):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_moderator`"""
        if self._gp_moderator_name in self._groups:
            return self._groups[self._gp_moderator_name].is_member(username)
        return False, None

    def is_client_rw(self, username=None, client=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_client_rw`"""
        if not username or not client:  # pragma: no cover
            return False

        (is_admin, _) = self.is_admin(username)

        ret = is_admin or self.opt('assume_rw', True) or self.opt('legacy')

        if self.is_client_allowed(username, client, server):
            # legacy mode: assume rw for everyone
            if self.opt('legacy'):
                return True
            client_match = self._client_match(username, client)
            advanced = self._extract_advanced(username)

            if client_match is None and username == client:
                client_match = [username]

            if server:
                server_match = self._server_match(username, server)

                if not server_match and not client_match:
                    return is_admin or self.opt('assume_rw', True)

                for adv in advanced:
                    for adv2 in advanced:
                        # the whole agent is rw and we did not find explicit entry for
                        # client_match
                        if client_match is False:
                            if server_match and \
                                    any([x in adv.get('rw', {}) or
                                         x in adv.get('rw', {}).get('agents', [])
                                         for x in server_match]):
                                return True
                            if server in adv.get('rw', {}) or \
                                    server in adv.get('rw', {}).get('agents', []):
                                return True

                        if server_match and \
                                any([x in adv.get('rw', {}) or
                                     x in adv.get('rw', {}).get('agents', [])
                                     for x in server_match]):
                            # both agent and client are defined as rw
                            if client_match and \
                                any([x in adv2.get('rw', []) or
                                     x in adv2.get('rw', {}).get('clients', []) or
                                     any([x in adv2.get('rw', {}).get(y, [])
                                          for y in server_match])
                                     for x in client_match
                                     ]):
                                return True

                            # the agent is rw but the client is explicitly defined as ro
                            if client_match and \
                                any([x in adv2.get('ro', []) or
                                     x in adv2.get('ro', {}).get('clients', []) or
                                     any([x in adv2.get('ro', {}).get(y, [])
                                          for y in server_match])
                                     for x in client_match
                                     ]):
                                return False

                        if server_match and \
                                any([x in adv.get('ro', {}) or
                                     x in adv.get('ro', {}).get('agents', [])
                                     for x in server_match]):
                            # the agent is ro, but the client is explicitly defined as rw
                            if client_match and \
                                any([x in adv2.get('rw', {}).get('clients', []) or
                                     x in adv2.get('rw', []) or
                                     any([x in adv2.get('rw', {}).get(y, [])
                                          for y in server_match])
                                     for x in client_match
                                     ]):
                                return True

                            # both server and client are explicitly defined as ro
                            if client_match and \
                                any([x in adv2.get('ro', {}).get('clients', []) or
                                     x in adv2.get('ro', []) or
                                     any([x in adv2.get('ro', {}).get(y, [])
                                         for y in server_match])
                                     for x in client_match
                                     ]):
                                return False

            for adv in advanced:
                # client is explicitly defined as rw
                rw_clients = adv.get('rw', {}).get('clients', [])
                if client_match and \
                        any([x in rw_clients for x in client_match]):
                    return True

                if client and \
                        client in rw_clients:
                    return True

                # client is explicitly defined as ro
                ro_clients = adv.get('ro', {}).get('clients', [])
                if client_match and \
                        any([x in ro_clients for x in client_match]):
                    return False

                if client and \
                        client in ro_clients:
                    return False

        return ret

    def is_client_allowed(self, username=None, client=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_client_allowed`"""
        if not username or not client:  # pragma: no cover
            return False

        (is_admin, _) = self.is_admin(username)
        client_match = self._client_match(username, client)

        if client_match is None and username == client:
            client_match = [username]
        elif not client_match:
            client_match = False

        if server:
            server_match = self._server_match(username, server)
            if server_match is not None or self.opt('legacy'):
                if not server_match:
                    return is_admin

                advanced = self._extract_advanced(username)
                if self.opt('implicit_link', True) and not advanced:
                    advanced = False

                if advanced is not False:
                    for idx, adv in enumerate(advanced):
                        if all([x not in adv for x in server_match]) and \
                                any([x in y
                                     for x in server_match
                                     for y in self._extract_advanced_mode(username, 'ro', 'agents', idx)
                                     ]) or \
                                any([x in y
                                     for x in server_match
                                     for y in self._extract_advanced_mode(username, 'rw', 'agents', idx)
                                     ]):
                            return True

                        tmp = set(adv.get(server, []))
                        for srv in server_match:
                            tmp |= set(adv.get(srv, []))
                        adv2 = list(tmp)
                        if client_match is not False and \
                                (any([x in adv2 for x in client_match]) or
                                 client in adv2):
                            return True

                    return False

        return client_match is not False or is_admin

    def is_server_rw(self, username=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_server_rw`"""
        if not username:  # pragma: no cover
            return False

        # special case single-agent mode
        if not server and config.get('STANDALONE'):
            server = 'local'

        (is_admin, _) = self.is_admin(username)

        ret = is_admin or self.opt('assume_rw', True) or self.opt('legacy')

        if self.is_server_allowed(username, server):
            server_match = self._server_match(username, server)
            if not server_match:
                return is_admin or self.opt('assume_rw', True)

            advanced = self._extract_advanced(username)

            for adv in advanced:
                # server is explicitly defined as ro
                if any([x in adv.get('ro', {}).get('agents', []) for x in server_match]):
                    return False

                # server is explicitly defined as rw
                if any([x in adv.get('rw', {}).get('agents', []) for x in server_match]):
                    return True

        return ret

    def is_server_allowed(self, username=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_server_allowed`"""
        if not username or not server:
            return False

        server_match = self._server_match(username, server)
        (is_admin, _) = self.is_admin(username)

        if server_match is None and self.opt('legacy'):
            server_match = False

        return server_match is not False or is_admin


class BUIaclGroup(object):
    """The :class:`burpui.misc.acl.interface.BUIaclGroup` class is used to
    represent a Group"""

    def __init__(self, name, members=None):
        self._name = name
        self._set_members(members)
        self.has_subgroups = -1

    def _parse_members(self, members):
        # we support only lists
        if members and ',' in members and not isinstance(members, list):
            parsed = [x.strip() for x in members.split(',')]
        else:
            parsed = make_list(members)
        return parsed

    def _set_members(self, members):
        self._members = set(self._parse_members(members))

    def add_members(self, new_members):
        new_members = self._parse_members(new_members)
        self._members = self._members | set(new_members)
        # reset the flag
        self.has_subgroups = -1
        return new_members

    def del_members(self, members_remove):
        members_remove = self._parse_members(members_remove)
        self._members = self._members - set(members_remove)
        # reset the flag
        self.has_subgroups = -1

    def is_member(self, member, parent=None):
        inherit = set()
        ret = member in self._members
        if not ret and (self.has_subgroups > 0 or self.has_subgroups == -1):
            self.has_subgroups = 0
            for mem in self.members:
                # avoid infinite loop with mutual inheritance
                if parent and mem in parent:
                    continue
                if mem.startswith('@'):
                    self.has_subgroups += 1
                    if mem in meta_grants._groups:
                        if parent:
                            parent.append(mem)
                        else:
                            parent = [mem]
                        (ret, inh2) = meta_grants._groups[mem].is_member(member, parent=parent)
                        if ret:
                            for subinh in inh2:
                                inherit.add(subinh)
                            inherit.add(mem)
                            # no break, we may have other inheritance at the level
        return ret, list(inherit)

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
            # handle empty/missing grants
            if not grants:
                return []
            # ignore mal-formatted json
            if any([x in grants for x in ['{', '}', '[', ']']]):
                ret = None
            elif grants and ',' in grants:
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
