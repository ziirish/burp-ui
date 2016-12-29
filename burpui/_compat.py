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
    from urllib.parse import unquote, quote  # noqa
    text_type = str
    string_types = (str,)
else:
    PY3 = False
    from urllib import unquote, quote  # noqa
    text_type = unicode
    string_types = (str, unicode)


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
    replace_module = __import__('burpui._' + name, fromlist=toimport)
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
