# -*- coding: utf8 -*-
"""
.. module:: burpui._rtfd
    :platform: Unix
    :synopsis: Burp-UI wrapper documentation module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""

# THIS IS ONLY USED FOR DOC GENERATION

from . import create_app

app = create_app(conf='/dev/null', gunicorn=False)
