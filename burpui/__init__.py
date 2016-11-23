# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui
    :platform: Unix
    :synopsis: Burp-UI main module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import sys
import warnings

from .app import init

warnings.simplefilter('always', RuntimeWarning)

if sys.version_info < (3, 0):  # pragma: no cover
    reload(sys)
    sys.setdefaultencoding('utf-8')


# backward compatibility
create_app = init
