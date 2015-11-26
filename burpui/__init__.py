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
try:  # pragma: no cover
    __release__ = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'RELEASE')).read().rstrip()
except:  # pragma: no cover
    __release__ = 'unknown'


def lookup_config(conf=None):
    ret = None
    if conf:
        if os.path.isfile(conf):
            ret = conf
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
            if os.path.isfile(p):
                ret = p
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

    :returns: A :class:`flask.Flask` object
    """
    from flask.ext.login import LoginManager, login_user
    from flask.ext.bower import Bower
    from .server import BUIServer as BurpUI
    from .routes import view
    from .api import api, apibp

    # We initialize the core
    app = BurpUI()

    app.config['CFG'] = None

    app.secret_key = 'VpgOXNXAgcO81xFPyWj07ppN6kExNZeCDRShseNzFKV7ZCgmW2/eLn6xSlt7pYAVBj12zx2Vv9Kw3Q3jd1266A=='
    app.jinja_env.globals.update(isinstance=isinstance, list=list)

    # Then we load our routes
    view.init_bui(app)
    app.register_blueprint(view)

    # We initialize the API
    api.init_bui(app)
    api.version = __version__
    api.release = __release__
    app.register_blueprint(apibp)

    # And the login_manager
    app.login_manager = LoginManager()
    app.login_manager.init_app(app)
    app.login_manager.login_view = 'view.login'
    app.login_manager.login_message_category = 'info'

    app.config.setdefault('BOWER_COMPONENTS_ROOT', os.path.join('static', 'vendor'))
    app.config.setdefault('BOWER_REPLACE_URL_FOR', True)
    bower = Bower()
    bower.init_app(app)

    @app.login_manager.user_loader
    def load_user(userid):
        """User loader callback"""
        if app.auth != 'none':
            return app.uhandler.user(userid)
        return None  # pragma: no cover

    @app.login_manager.request_loader
    def load_user_from_request(request):
        """User loader from request callback"""
        if app.auth != 'none':
            creds = request.headers.get('Authorization')
            if creds:
                creds = creds.replace('Basic ', '', 1)
                try:
                    import base64
                    login, password = base64.b64decode(creds.encode('utf-8')).decode('utf-8').split(':')
                except:  # pragma: no cover
                    pass
                if login:
                    user = app.uhandler.user(login)
                    if user.active and user.login(login, password):
                        login_user(user)
                        return user

        return None

    # The debug argument used to be a boolean so we keep supporting this format
    if isinstance(debug, bool):
        if debug:
            debug = logging.DEBUG
        else:
            debug = logging.NOTSET
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
        if debug < logging.INFO:
            LOG_FORMAT = (
                '-' * 80 + '\n' +
                '%(levelname)s in %(module)s.%(funcName)s [%(pathname)s:%(lineno)d]:\n' +
                '%(message)s\n' +
                '-' * 80
            )
        else:
            LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s'
        file_handler.setLevel(debug)
        file_handler.setFormatter(Formatter(LOG_FORMAT))
        app.logger.addHandler(file_handler)

    # Still need to test conf file here because the init function can be called
    # by gunicorn directly
    app.config['CFG'] = lookup_config(conf)

    app.setup(app.config['CFG'])

    if gunicorn:  # pragma: no cover
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

    return app
