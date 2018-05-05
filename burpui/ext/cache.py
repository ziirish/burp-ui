# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.cache
    :platform: Unix
    :synopsis: Burp-UI external cache module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask_caching import Cache


cache = Cache(config={
    'CACHE_TYPE': 'simple',
    'CACHE_THRESHOLD': 50,
    'CACHE_DEFAULT_TIMEOUT': 7200
})
