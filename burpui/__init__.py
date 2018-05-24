# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui
    :platform: Unix
    :synopsis: Burp-UI main module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import warnings

from .app import init

warnings.simplefilter('always', RuntimeWarning)


# backward compatibility
create_app = init
