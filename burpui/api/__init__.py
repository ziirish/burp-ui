# -*- coding: utf8 -*-

from burpui import app
from flask.ext.restful import Api

api = Api(app)

app.jinja_env.globals.update(api=api)
