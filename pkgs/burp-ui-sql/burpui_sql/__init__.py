# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui_sql
    :platform: Unix
    :synopsis: Burp-UI SQL dummy module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import os
import sys

__title__ = 'burp-ui-sql'
__author__ = 'Benjamin SANS (Ziirish)'
__author_email__ = 'hi+burpui@ziirish.me'
__url__ = 'https://git.ziirish.me/ziirish/burp-ui'
__description__ = ('Burp-UI is a web-ui for burp backup written in python with '
                   'Flask and jQuery/Bootstrap')
__license__ = 'BSD 3-clause'

ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)))
if os.path.exists(os.path.join(ROOT, 'VERSION')):
    __version__ = open(os.path.join(ROOT, 'VERSION')).read().rstrip()
else:
    __version__ = '0.4.4'
