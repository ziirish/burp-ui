# -*- coding: utf8 -*-
"""
.. module:: api
   :platform: Unix
   :synopsis: Burp-UI api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>


"""
import os
import re

from burpui import app
from flask.ext.restful import Api

api = Api(app)

app.jinja_env.globals.update(api=api)

# hack to automatically import api modules
for f in os.listdir(__path__[0]):
    if (os.path.isfile(os.path.join(__path__[0], f)) and
            re.search('\.py$', f) and not
            re.match('__init__', f)):
        mod = 'burpui.api.'+f[:-3]
        __import__(mod)
