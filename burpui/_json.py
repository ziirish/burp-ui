# -*- coding: utf8 -*-
"""
.. module:: burpui._json
    :platform: Unix
    :synopsis: Burp-UI json compatibility module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
import ujson as json

__implements__ = ['dumps', 'loads']
ori_dumps = None
ori_loads = None

# ujson does not implement all the features of the original json parser
# the trick here is to catch such an exception to fallback to the original one
def dumps(*args, **kwargs):
    try:
        return json.dumps(*args, **kwargs)
    except:
        return ori_dumps(*args, **kwargs)


def loads(*args, **kwargs):
    try:
        return json.loads(*args, **kwargs)
    except:
        return ori_loads(*args, **kwargs)
