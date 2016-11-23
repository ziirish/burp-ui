# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.cache
    :platform: Unix
    :synopsis: Burp-UI external cache module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import warnings

from flask_cache import Cache as CacheOrig
from flask.exthook import ExtDeprecationWarning


class Cache(CacheOrig):
    def init_app(self, app, config=None):
        # suppress warnings since upstream did not fix it yet
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', ExtDeprecationWarning)
            super(Cache, self).init_app(app, config)


cache = Cache(config={'CACHE_TYPE': 'null', 'CACHE_NO_NULL_WARNING': True})
