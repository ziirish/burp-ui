# -*- coding: utf8 -*-
"""
.. module:: burpui._compat
    :platform: Unix
    :synopsis: Burp-UI compatibility module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import re
import sys

try:
    import cPickle as pickle  # noqa
except ImportError:
    import pickle  # noqa

if sys.version_info[0] >= 3:
    PY3 = True
    from urllib.parse import unquote, quote, urlparse, urljoin  # noqa
    text_type = str
    string_types = (str,)

    def iterkeys(d, *args, **kwargs):
        return iter(d.keys(*args, **kwargs))

    def itervalues(d, *args, **kwargs):
        return iter(d.values(*args, **kwargs))

    def iteritems(d, *args, **kwargs):
        return iter(d.items(*args, **kwargs))

    def iterlists(d, *args, **kwargs):
        return iter(d.lists(*args, **kwargs))

    def iterlistvalues(d, *args, **kwargs):
        return iter(d.listvalues(*args, **kwargs))

else:
    PY3 = False
    from urllib import unquote, quote  # noqa
    from urlparse import urlparse, urljoin  # noqa
    text_type = unicode
    string_types = (str, unicode)

    def iterkeys(d, *args, **kwargs):
        return d.iterkeys(*args, **kwargs)

    def itervalues(d, *args, **kwargs):
        return d.itervalues(*args, **kwargs)

    def iteritems(d, *args, **kwargs):
        return d.iteritems(*args, **kwargs)

    def iterlists(d, *args, **kwargs):
        return d.iterlists(*args, **kwargs)

    def iterlistvalues(d, *args, **kwargs):
        return d.iterlistvalues(*args, **kwargs)


def to_bytes(text):
    """Transform string to bytes."""
    if isinstance(text, text_type):
        text = text.encode('utf-8')
    return text


def to_unicode(input_bytes, encoding='utf-8'):
    """Decodes input_bytes to text if needed."""
    if not isinstance(input_bytes, string_types):
        input_bytes = input_bytes.decode(encoding)
    elif re.match(r'\\u[0-9a-f]{4}', input_bytes):
        input_bytes = input_bytes.decode('unicode-escape')
    return input_bytes


try:
    from pluginbase import PluginBase as PluginBaseOrig, \
        PluginSource as PluginSourceOrig, _internalspace, _shutdown_module

    class PluginSource(PluginSourceOrig):
        def __cleanup(self, _sys=sys, _shutdown_module=_shutdown_module):
            # The default parameters are necessary because this can be fired
            # from the destructor and so late when the interpreter shuts down
            # that these functions and modules might be gone.
            if self.mod is None or self.mod.__name__ is None:
                return
            modname = self.mod.__name__
            self.mod.__pluginbase_state__ = None
            self.mod = None
            try:
                delattr(_internalspace, self.spaceid)
            except AttributeError:
                pass
            prefix = modname + '.'
            # avoid the bug described in issue #6
            if modname in _sys.modules:
                del _sys.modules[modname]
            for key, value in list(_sys.modules.copy().items()):
                if not key.startswith(prefix):
                    continue
                mod = _sys.modules.pop(key, None)
                if mod is None:
                    continue
                _shutdown_module(mod)

    class PluginBase(PluginBaseOrig):
        def make_plugin_source(self, *args, **kwargs):
            """Creates a plugin source for this plugin base and returns it.
            All parameters are forwarded to :class:`PluginSource`.
            """
            return PluginSource(self, *args, **kwargs)

except ImportError:
    PluginBase = object


# maps module name -> attribute name -> original item
# e.g. "time" -> "sleep" -> built-in function sleep
saved = {}


# Borrowed from gevent in order to patch json
def patch_item(module, attr, newitem, newmodule=None):
    NONE = object()
    olditem = getattr(module, attr, NONE)
    if olditem is not NONE:
        saved.setdefault(module.__name__, {}).setdefault(attr, olditem)
        if newmodule and not getattr(newmodule, 'ori_' + attr, None):
            setattr(newmodule, 'ori_' + attr, olditem)
    if not getattr(newmodule, 'ori_' + attr, None):
        setattr(module, attr, newitem)


def patch_module(name, items=None):
    toimport = items or []
    mod = __name__
    if '.' in mod:
        mod = mod.split('.')[0]
    replace_module = __import__('{}._{}'.format(mod, name), fromlist=toimport)
    module_name = name
    module = __import__(module_name)
    if items is None:
        items = getattr(replace_module, '__implements__', None)
        if items is None:
            raise AttributeError('%r does not have __implements__' % replace_module)
    for attr in items:
        patch_item(module, attr, getattr(replace_module, attr), replace_module)


def patch_json():
    try:
        import ujson  # noqa
    except ImportError:
        # ujson is not available, we won't patch anything
        return
    patch_module('json', ['dumps', 'loads'])
