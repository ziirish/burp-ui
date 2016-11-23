# -*- coding: utf8 -*-
"""
.. module:: burpui._rtfd
    :platform: Unix
    :synopsis: Burp-UI wrapper documentation module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""

# THIS IS ONLY USED FOR DOC GENERATION

from . import create_app

# This is a lie we are not really unittesting, but we want to avoid the v2
# errors
app = create_app(conf='/dev/null', gunicorn=False, unittest=True)
