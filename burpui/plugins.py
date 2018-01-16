# -*- coding: utf8 -*-
"""
.. module:: burpui.plugins
    :platform: Unix
    :synopsis: Burp-UI plugins module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from pluginbase import PluginBase
from six import iteritems


class PluginManager(object):
    """The :class:`burpui.plugins.PluginManager` class is a plugin manager.

    :param app: Instance of the app we are running in
    :type app: :class:`burpui.server.BUIServer`

    :param searchpath: The places to look for plugins
    :type searchpath: list
    """

    def __init__(self, app, searchpath):
        self.app = app
        self.searchpath = searchpath
        self.init = False
        self.loaded = False
        self.plugins = {}

    def _init_manager(self):
        if self.init:
            return
        self.plugin_base = PluginBase(package='burpui.plugins.ext')
        self.plugin_source = self.plugin_base.make_plugin_source(
            searchpath=self.searchpath
        )
        self.init = True

    def load_all(self, force=False):
        if self.loaded and not force:
            return
        self._init_manager()
        for plugin_name in self.plugin_source.list_plugins():
            if plugin_name not in self.plugins:
                try:
                    plugin = self.plugin_source.load_plugin(plugin_name)
                    current_type = getattr(plugin, '__type__', None)
                    if not current_type:
                        self.app.logger.warning(
                            'No __type__ for {}. Ignoring it'.format(
                                repr(plugin_name)
                            )
                        )
                        continue
                    self.app.logger.info(
                        'Loading plugin {} ({})'.format(
                            repr(plugin_name),
                            current_type
                        )
                    )
                    self.plugins[plugin_name] = plugin
                except Exception as exp:
                    self.app.logger.error(
                        'Unable to load plugin {}: {}'.format(
                            repr(plugin_name),
                            str(exp)
                        )
                    )
        self.loaded = True

    def get_plugins_by_type(self, plugin_type):
        ret = {}
        for name, plugin in iteritems(self.plugins):
            current_type = getattr(plugin, '__type__', None)
            if not current_type:
                self.app.logger.warning(
                    'No __type__ for {}. Ignoring it'.format(repr(name))
                )
                continue
            if current_type == plugin_type:
                ret[name] = plugin

        return ret

    def get_plugin_by_name(self, name):
        return self.plugins.get(name, None)
