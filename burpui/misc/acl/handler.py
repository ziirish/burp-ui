# -*- coding: utf8 -*-
import os

from .interface import BUIacl, BUIaclLoader
from .meta import meta_grants

from importlib import import_module
from six import iteritems
from collections import OrderedDict


class ACLloader(BUIaclLoader):
    section = name = 'ACL'

    def __init__(self, app=None):
        """See :func:`burpui.misc.acl.interface.BUIaclLoader.__init__`

        :param app: Application context
        :type app: :class:`burpui.server.BUIServer`
        """
        self.app = app
        self.conf = self.app.conf
        self._acl = ACLhandler(self)
        backends = []
        self.errors = {}
        if self.section in self.conf.options:
            opts = {}
            opts['extended'] = self.conf.safe_get(
                'extended',
                'boolean',
                section=self.section,
                defaults=True
            )
            opts['assume_rw'] = self.conf.safe_get(
                'assume_rw',
                'boolean',
                section=self.section,
                defaults=True
            )
            opts['legacy'] = self.conf.safe_get(
                'legacy',
                'boolean',
                section=self.section
            )
            opts['implicit_link'] = self.conf.safe_get(
                'implicit_link',
                'boolean',
                section=self.section,
                defaults=True
            )
            opts['inverse_inheritance'] = self.conf.safe_get(
                'inverse_inheritance',
                'boolean',
                section=self.section
            )
            meta_grants.options = opts
            meta_grants.init_app(app)
        if self.app.acl_engine and 'none' not in self.app.acl_engine:
            me, _ = os.path.splitext(os.path.basename(__file__))
            back = self.app.acl_engine
            for au in back:
                if au == me:
                    self.app.logger.critical('Recursive import not permitted!')
                    continue
                try:
                    (modpath, _) = __name__.rsplit('.', 1)
                    mod = import_module('.' + au, modpath)
                    obj = mod.ACLloader(self.app)
                    backends.append(obj)
                except:
                    import traceback
                    self.errors[au] = traceback.format_exc()
        for name, plugin in iteritems(self.app.plugin_manager.get_plugins_by_type('acl')):
            try:
                obj = plugin.ACLloader(self.app)
                backends.append(obj)
            except:
                import traceback
                self.errors[name] = traceback.format_exc()
        backends.sort(key=lambda x: getattr(x, 'priority', -1), reverse=True)
        if not backends:
            raise ImportError(
                'No backend found for \'{}\':\n{}'.format(self.app.acl_engine,
                                                          self.errors)
            )
        for name, err in iteritems(self.errors):
            self.app.logger.error(
                'Unable to load module {}:\n{}'.format(repr(name), err)
            )
        self.backends = OrderedDict()
        for obj in backends:
            self.backends[obj.name] = obj

    def reload(self):
        return None

    @property
    def acl(self):
        return self._acl

    @property
    def grants(self):
        return meta_grants.grants

    @property
    def groups(self):
        return meta_grants.groups


class ACLhandler(BUIacl):
    """See :class:`burpui.misc.acl.interface.BUIacl`"""
    def __init__(self, loader=None):
        """:func:`burpui.misc.acl.interface.BUIacl.__init__` instanciate ACL
        engine.

        :param loader: ACL loader
        :type loader: :class:`burpui.misc.acl.handler.ACLloader`
        """
        self.loader = loader

    def _iterate_through_loader(self, method, *args, **kwargs):
        ret = None
        for _, acl_engine in iteritems(self.loader.backends):
            func = getattr(acl_engine.acl, method)
            ret = func(*args, **kwargs)
            if isinstance(ret, tuple):
                (ret, _) = ret
            if ret:
                break
        if not ret:
            func = getattr(meta_grants, method)
            ret = func(*args, **kwargs)
            if isinstance(ret, tuple):
                (ret, _) = ret
        return ret

    def is_admin(self, username=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_admin`"""
        ret = self._iterate_through_loader('is_admin', username) or False
        return ret

    def is_moderator(self, username=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_moderator`"""
        ret = self._iterate_through_loader('is_moderator', username) or False
        return ret

    def is_client_rw(self, username=None, client=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_client_rw`"""
        ret = self._iterate_through_loader(
            'is_client_rw',
            username,
            client,
            server
        ) or False
        return ret

    def is_client_allowed(self, username=None, client=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_client_allowed`"""
        ret = self._iterate_through_loader(
            'is_client_allowed',
            username,
            client,
            server
        ) or False
        return ret

    def is_server_rw(self, username=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_server_rw`"""
        ret = self._iterate_through_loader(
            'is_server_rw',
            username,
            server
        ) or False
        return ret

    def is_server_allowed(self, username=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_server_allowed`"""
        ret = self._iterate_through_loader(
            'is_server_allowed',
            username,
            server
        ) or False
        return ret
