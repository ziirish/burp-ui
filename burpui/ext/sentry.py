# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.sentry
    :platform: Unix
    :synopsis: Burp-UI external Sentry module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from raven.contrib.flask import Sentry

sentry = Sentry()
