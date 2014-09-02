# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap
"""
__title__ = 'burp-ui'
__author__ = 'Benjamin SANS (Ziirish)'
__license__ = 'BSD 3-clause'


from flask import Flask
from flask.ext.login import LoginManager
from burpui.server import Server as BurpUI

# First, we setup the app
app = Flask(__name__)

app.config['CFG'] = None

app.secret_key = 'VpgOXNXAgcO81xFPyWj07ppN6kExNZeCDRShseNzFKV7ZCgmW2/eLn6xSlt7pYAVBj12zx2Vv9Kw3Q3jd1266A=='
app.jinja_env.globals.update(isinstance=isinstance,list=list)

# We initialize the core
bui = BurpUI(app)

# And the login_manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Then we load our routes
import burpui.routes
