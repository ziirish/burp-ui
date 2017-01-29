# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.limit
    :platform: Unix
    :synopsis: Burp-UI external Limit module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
