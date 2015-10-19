# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui
    :platform: Unix
    :synopsis: Burp-UI main module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>
"""

import os
import sys
import logging

from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.bower import Bower
from .server import BUIServer as BurpUI
from .routes import view
from .api import api

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf-8')

__title__ = 'burp-ui'
__author__ = 'Benjamin SANS (Ziirish)'
__author_email__ = 'ziirish+burpui@ziirish.info'
__url__ = 'https://git.ziirish.me/ziirish/burp-ui'
__description__ = 'Burp-UI is a web-ui for burp backup written in python with Flask and jQuery/Bootstrap'
__license__ = 'BSD 3-clause'
__version__ = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'VERSION')).read().rstrip()

# First, we setup the app
app = Flask(__name__)

app.config['CFG'] = None

app.secret_key = 'VpgOXNXAgcO81xFPyWj07ppN6kExNZeCDRShseNzFKV7ZCgmW2/eLn6xSlt7pYAVBj12zx2Vv9Kw3Q3jd1266A=='
app.jinja_env.globals.update(isinstance=isinstance, list=list)
app.jinja_env.globals.update(api=api)

# We initialize the core
bui = BurpUI(app)

# Then we load our routes
view.bui = bui
app.register_blueprint(view)

# We initialize the API
api.app = app
api.init_bui(bui)
api.init_app(app)

# And the login_manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'view.login'
login_manager.login_message_category = 'info'

app.config.setdefault('BOWER_COMPONENTS_ROOT', os.path.join('static', 'vendor'))
app.config.setdefault('BOWER_REPLACE_URL_FOR', True)
bower = Bower()
bower.init_app(app)


@login_manager.user_loader
def load_user(userid):
    """User loader callback"""
    if bui.auth != 'none':
        return bui.uhandler.user(userid)
    return None  # pragma: no cover


def lookup_config(conf=None):
    ret = None
    if conf:
        if os.path.isfile(conf):
            ret = conf
            app.config['CFG'] = conf
        else:
            raise IOError('File not found: \'{0}\''.format(conf))
    else:
        root = os.path.join(
            sys.prefix,
            'share',
            'burpui',
            'etc'
        )
        conf_files = [
            '/etc/burp/burpui.cfg',
            os.path.join(root, 'burpui.cfg'),
            os.path.join(root, 'burpui.sample.cfg')
        ]
        for p in conf_files:
            app.logger.debug('Trying file \'{}\''.format(p))
            if os.path.isfile(p):
                app.config['CFG'] = p
                ret = p
                app.logger.debug('Using file \'{}\''.format(p))
                break

    return ret


def init(conf=None, debug=0, logfile=None, gunicorn=True):
    """Initialize the whole application.

    :param conf: Configuration file to use
    :type conf: str

    :param debug: Enable verbose output
    :type debug: int

    :param logfile: Store the logs in the given file
    :type logfile: str

    :param gunicorn: Enable gunicorn engine instead of flask's default
    :type gunicorn: bool

    :returns: A :class:`Flask` object
    """
    # The debug argument used to be a boolean so we keep supporting this format
    if isinstance(debug, bool):
        debug = logging.DEBUG
    else:
        levels = [logging.NOTSET, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
        if debug >= len(levels):
            debug = len(levels) - 1
        if not debug:
            debug = 0
        debug = levels[debug]

    if debug != logging.NOTSET and not gunicorn:  # pragma: no cover
        app.config['DEBUG'] = True
        app.config['TESTING'] = True

    if logfile:
        from logging import Formatter
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(logfile, maxBytes=1024 * 1024 * 100, backupCount=20)
        if debug > logging.INFO:
            LOG_FORMAT = (
                '-' * 80 + '\n' +
                '%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
                '%(message)s\n' +
                '-' * 80
            )
            file_handler.setLevel(debug)
        else:
            LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
            file_handler.setLevel(debug)
        file_handler.setFormatter(Formatter(LOG_FORMAT))
        app.logger.addHandler(file_handler)

    # Still need to test conf file here because the init function can be called
    # by gunicorn directly
    lookup_config(conf)

    bui.setup(app.config['CFG'])

    if gunicorn:  # pragma: no cover
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

    return app
