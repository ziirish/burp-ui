# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.async
    :platform: Unix
    :synopsis: Burp-UI external Async module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from celery import current_app

celery = current_app
