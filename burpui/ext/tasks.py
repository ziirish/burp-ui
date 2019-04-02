# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.tasks
    :platform: Unix
    :synopsis: Burp-UI external Tasks module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from celery import current_app

celery = current_app
