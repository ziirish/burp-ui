# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui_agent
    :platform: Unix
    :synopsis: Burp-UI agent module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import sys

__title__ = 'burp-ui-agent'

if sys.version_info < (3, 0):  # pragma: no cover
    reload(sys)
    sys.setdefaultencoding('utf-8')
