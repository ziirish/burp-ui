#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui.celery_worker
    :platform: Unix
    :synopsis: Burp-UI celery worker module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import os
import sys

# Try to load modules from our current env first
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))


def init_app(conf):
    from burpui import create_app
    app = create_app(conf)
    return app

config = os.getenv('BUI_CONFIG')
app = init_app()
app.app_context().push()

celery = app.celery
if not celery:
    message = 'Something went wrong while initializing celery worker.\n' \
              'Maybe it is not enabled in your conf ({}).'.format(config)
    raise Exception(message)
