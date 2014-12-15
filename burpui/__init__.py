# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap
"""
__title__        = 'burp-ui'
__author__       = 'Benjamin SANS (Ziirish)'
__author_email__ = 'ziirish+burpui@ziirish.info'
__url__          = 'https://git.ziirish.me/ziirish/burp-ui'
__description__  = 'Burp-UI is a web-ui for burp backup written in python with Flask and jQuery/Bootstrap'
__license__      = 'BSD 3-clause'
__version__      = '0.0.6'

import os

from flask import Flask
from flask.ext.login import LoginManager
from burpui.server import BUIServer as BurpUI

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

def init(conf=None, debug=False, gunicorn=True):
    app.config['DEBUG'] = debug
    if debug:
        app.config['TESTING'] = True

    if conf:
        if os.path.isfile(conf):
            app.config['CFG'] = conf
        else:
            raise IOError('File not found: \'{0}\''.format(conf))
    else:
        conf_files = ['/etc/burp/burpui.cfg', os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', 'share', 'burpui', 'etc', 'burpui.cfg')]
        for p in conf_files:
            app.logger.debug('Trying file \'%s\'', p)
            if os.path.isfile(p):
                app.config['CFG'] = p
                app.logger.debug('Using file \'%s\'', p)
                break

    bui.setup(app.config['CFG'])

    if gunicorn:
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

    return app
