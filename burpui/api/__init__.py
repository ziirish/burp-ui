# -*- coding: utf8 -*-
"""
.. module:: api
   :platform: Unix
   :synopsis: Burp-UI api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>


"""

from burpui import app
from flask.ext.restful import Api

api = Api(app)

app.jinja_env.globals.update(api=api)
