# -*- coding: utf8 -*-
"""
.. module:: burpui._json
    :platform: Unix
    :synopsis: Burp-UI json compatibility module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import ujson
from six import viewkeys

__implements__ = ['dumps', 'loads']
ori_dumps = None
ori_loads = None

IMPLEMENTED_DUMPS_KWARGS = [
    'ensure_ascii',
    'double_precision',
    'encode_html_chars',
    'sort_keys',
]
IMPLEMENTED_LOADS_KWARGS = [
    'precise_float',
]


# ujson does not implement all the features of the original json parser
# the trick here is to catch such an exception to fallback to the original one
def dumps(*args, **kwargs):
    keys = []
    if kwargs:
        keys = viewkeys(kwargs)
    for key in keys:
        if key not in IMPLEMENTED_DUMPS_KWARGS:
            return ori_dumps(*args, **kwargs)
    try:
        return ujson.dumps(*args, **kwargs)
    except:
        return ori_dumps(*args, **kwargs)


def loads(*args, **kwargs):
    keys = []
    if kwargs:
        keys = viewkeys(kwargs)
    for key in keys:
        if key not in IMPLEMENTED_LOADS_KWARGS:
            return ori_loads(*args, **kwargs)
    try:
        return ujson.loads(*args, **kwargs)
    except:
        return ori_loads(*args, **kwargs)
