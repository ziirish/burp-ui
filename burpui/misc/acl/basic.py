# -*- coding: utf8 -*-
from six import iteritems

from .meta import meta_grants, BUIaclGrant
from .interface import BUIaclLoader
from ...utils import NOTIF_OK, NOTIF_WARN, NOTIF_ERROR, __


class ACLloader(BUIaclLoader):
    __doc__ = __("Uses the Burp-UI configuration file to load its rules.")
    section = name = 'BASIC:ACL'
    priority = 100

    def __init__(self, app=None):
        """See :func:`burpui.misc.acl.interface.BUIaclLoader.__init__`

        :param app: Application context
        :type app: :class:`burpui.server.BUIServer`
        """
        self.app = app
        self.conf = self.app.conf
        self.admins = [
            'admin'
        ]
        self.moderators = []
        self._groups = {}
        self._grants = {}
        self.first_setup = True
        self.moderator = {}
        self._acl = meta_grants
        self.conf_id = None
        self.meta_id = meta_grants.id
        meta_grants.register_backend(self.name, self)
        self.load_acl(True)

    def reload(self):
        self.load_acl(True)

    def load_acl(self, force=False):
        if not force and self.conf_id:
            if not self.conf.changed(self.conf_id):
                return False

        # our config changed or we were forced to reload our rules.
        # if the meta_grants didn't change, we reset them
        # if they changed, it means something else triggered a reset
        if not meta_grants.changed(self.meta_id) and not self.first_setup:
            meta_grants.reset(self.name)

        self.first_setup = False

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
            self.priority = self.conf.safe_get(
                'priority',
                'integer',
                section=self.section,
                defaults=self.priority
            )
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
            default_moderator = None
            if self.conf.get('STANDALONE'):
                default_moderator = '{"agents": {"rw": "local"}}'
            self.moderator = self.conf.safe_get(
                '@moderator',
                'force_string',
                section=self.section,
                defaults=default_moderator
            ) or {}
            meta_grants.set_moderator_grants(self.moderator)
            for opt in self.conf.options.get(self.section).keys():
                if opt in ['admin', '+moderator', 'priority', '@moderator']:
                    continue
                record = self.conf.safe_get(
                    opt,
                    'force_string',
                    section=self.section
                )

                self.logger.debug('record: {} -> {}'.format(opt, record))

                def _record(key):
                    if gname not in self.groups_def:
                        self.groups_def[gname] = {}
                    self.groups_def[gname][key] = parsed

                    return parsed

                if opt[0] == '+':
                    short = opt.lstrip('+')
                    gname = '@{}'.format(short)
                    parsed = meta_grants.set_group(gname, record)
                    self._groups[short] = parsed
                    _record('members')
                elif opt[0] == '@':
                    short = opt.lstrip('@')
                    if short not in self._groups:
                        self._groups[short] = []
                    gname = opt
                    parsed = record
                    _record('grants')
                    meta_grants.set_grant(gname, parsed)
                else:
                    self._grants[opt] = BUIaclGrant(opt, record).grants
                    meta_grants.set_grant(opt, record)

        if not is_empty(adms):
            self.admins = adms
        if not is_empty(mods):
            self.moderators = mods

        meta_grants.set_admin(self.admins)
        meta_grants.set_moderator(self.moderators)

        self.logger.debug('admins: {}'.format(self.admins))
        self.logger.debug('moderators: {}'.format(self.moderators))
        self.logger.debug('moderator grants: {}'.format(self.moderator))
        self.logger.debug('groups: {}'.format(self.groups_def))

        self.conf_id = self.conf.id
        self.meta_id = meta_grants.id

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
        if name in self.admins:
            self.del_admin(name)
        if name in self.moderators:
            self.del_moderator(name)
        for group, members in iteritems(self._groups):
            if name in members:
                self.del_group_member(group, name)
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
        if name == 'moderator':
            message = "'moderator' is a reserved name"
            self.logger.error(message)
            return False, message, NOTIF_ERROR
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
        if name == 'moderator':
            message = "'moderator' is a reserved name"
            self.logger.error(message)
            return False, message, NOTIF_ERROR
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
        if gname in self.admins:
            self.del_admin(gname)
        if gname in self.moderators:
            self.del_moderator(gname)
        for group, members in iteritems(self._groups):
            if gname in members:
                self.del_group_member(group, gname)
        message = "grant '{}' successfully removed".format(name)
        return True, message, NOTIF_OK

    def mod_group(self, name, content):
        """Update a group"""
        self._setup_acl()
        name = '@{}'.format(name)
        if name == 'moderator':
            message = "'moderator' is a reserved name"
            self.logger.error(message)
            return False, message, NOTIF_ERROR
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
        self.conf.options[self.section][gmembers] = self._groups[group]
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
        self.conf.options[self.section][gmembers] = self._groups[group] or ''
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
        self.conf.options[self.section]['+moderator'] = self.moderators
        self.conf.options.write()
        self.load_acl(True)
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
        self.conf.options[self.section]['+moderator'] = self.moderators or ''
        self.conf.options.write()
        self.load_acl(True)
        message = "'{}' successfully removed from moderators".format(member)
        return True, message, NOTIF_OK

    def mod_moderator(self, grants):
        """Update moderator grants"""
        self._setup_acl()
        self.moderator = grants
        self.conf.options[self.section]['@moderator'] = grants
        self.conf.options.write()
        self.load_acl(True)
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
        self.conf.options[self.section]['admin'] = self.admins
        self.conf.options.write()
        self.load_acl(True)
        message = "'{}' successfully added as admin".format(member)
        return True, message, NOTIF_OK

    def del_admin(self, member):
        """Delete an admin"""
        if member not in self.admins:
            message = "'{}' is not an admin".format(member)
            self.logger.warning(message)
            return False, message, NOTIF_WARN
        self._setup_acl()
        self.admins.remove(member)
        self.conf.options[self.section]['admin'] = self.admins or ''
        self.conf.options.write()
        self.load_acl(True)
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
        return self._grants

    @property
    def groups(self):
        """Property to retrieve the list of groups with their members"""
        return self.groups_def
