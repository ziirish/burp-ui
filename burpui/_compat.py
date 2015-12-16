# -*- coding: utf8 -*-
"""
.. module:: burpui._compat
    :platform: Unix
    :synopsis: Burp-UI compatibility module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
import sys
import os

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

IS_GUNICORN = 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '')

if IS_GUNICORN:
    from gevent.local import local
else:
    local = object


if sys.version_info[0] >= 3:
    PY3 = True
else:
    PY3 = False

# maps module name -> attribute name -> original item
# e.g. "time" -> "sleep" -> built-in function sleep
saved = {}


# Borrowed from gevent in order to patch json
def patch_item(module, attr, newitem, newmodule=None):
    NONE = object()
    olditem = getattr(module, attr, NONE)
    if olditem is not NONE:
        saved.setdefault(module.__name__, {}).setdefault(attr, olditem)
        if newmodule:
            setattr(newmodule, 'ori_' + attr, olditem)
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
        import ujson
    except ImportError:
        # ujson is not available, we won't patch anything
        return
    patch_module('json', ['dumps', 'loads'])
