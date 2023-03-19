# -*- coding: utf8 -*-
"""
.. module:: burpui._compat
    :platform: Unix
    :synopsis: Burp-UI compatibility module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import pickle  # noqa
from urllib.parse import quote, unquote, urljoin, urlparse  # noqa

text_type = str
string_types = (str,)


def to_bytes(text):
    """Transform string to bytes."""
    if isinstance(text, text_type):
        text = text.encode("utf-8")
    return text or b""


def to_unicode(input_bytes, encoding="utf-8"):
    """Decodes input_bytes to text if needed."""
    if not isinstance(input_bytes, string_types):
        input_bytes = input_bytes.decode(encoding)
    return input_bytes or ""


# maps module name -> attribute name -> original item
# e.g. "time" -> "sleep" -> built-in function sleep
saved = {}


# Borrowed from gevent in order to patch json
def patch_item(module, attr, newitem, newmodule=None):
    NONE = object()
    olditem = getattr(module, attr, NONE)
    if olditem is not NONE:
        saved.setdefault(module.__name__, {}).setdefault(attr, olditem)
        if newmodule and not getattr(newmodule, "ori_" + attr, None):
            setattr(newmodule, "ori_" + attr, olditem)
    if not getattr(newmodule, "ori_" + attr, None):
        setattr(module, attr, newitem)


def patch_module(name, items=None):
    toimport = items or []
    mod = __name__
    if "." in mod:
        mod = mod.split(".")[0]
    replace_module = __import__("{}._{}".format(mod, name), fromlist=toimport)
    module_name = name
    module = __import__(module_name)
    if items is None:
        items = getattr(replace_module, "__implements__", None)
        if items is None:
            raise AttributeError("%r does not have __implements__" % replace_module)
    for attr in items:
        patch_item(module, attr, getattr(replace_module, attr), replace_module)


def patch_json():
    try:
        import ujson  # noqa
    except ImportError:
        # ujson is not available, we won't patch anything
        return
    patch_module("json", ["dumps", "loads"])
