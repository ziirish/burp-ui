# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.cache
    :platform: Unix
    :synopsis: Burp-UI external cache module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import warnings

from flask_caching import Cache


cache = Cache(config={'CACHE_TYPE': 'null', 'CACHE_NO_NULL_WARNING': True})
