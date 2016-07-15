# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui
    :platform: Unix
    :synopsis: Burp-UI main module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""

import os
import sys
import logging
import warnings
from logging import Formatter

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf-8')

__title__ = 'burp-ui'
__author__ = 'Benjamin SANS (Ziirish)'
__author_email__ = 'hi+burpui@ziirish.me'
__url__ = 'https://git.ziirish.me/ziirish/burp-ui'
__doc__ = 'https://burp-ui.readthedocs.io/en/latest/'
__description__ = ('Burp-UI is a web-ui for burp backup written in python with '
                   'Flask and jQuery/Bootstrap')
__license__ = 'BSD 3-clause'
__version__ = open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'VERSION')
).read().rstrip()
try:  # pragma: no cover
    __release__ = open(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'RELEASE')
    ).read().rstrip()
except:  # pragma: no cover
    __release__ = 'unknown'

warnings.simplefilter('always', RuntimeWarning)


def get_redis_server(myapp):
    if myapp.redis and myapp.redis.lower() != 'none':
        parts = myapp.redis.split(':')
        host = parts[0]
        try:
            port = int(parts[1])
        except (ValueError, IndexError):
            port = 6379
    else:
        host = 'localhost'
        port = 6379
    return host, port


def create_db(myapp):
    """Create the SQLAlchemy instance if possible

    :param myapp: Application context
    :type myapp: :class:`burpui.server.BUIServer`
    """
    # singleton
    if myapp.db:
        return myapp.db

    if myapp.config['WITH_SQL']:
        from .models import db
        db.init_app(myapp)
        myapp.db = db
        return db

    return None


def create_celery(myapp, warn=True):
    """Create the Celery app if possible

    :param myapp: Application context
    :type myapp: :class:`burpui.server.BUIServer`
    """
    # singleton
    if myapp.celery:
        return myapp.celery

    if myapp.config['WITH_CELERY']:
        from celery import Celery
        host, port = get_redis_server(myapp)
        redis_url = 'redis://{}:{}/2'.format(host, port)
        myapp.config['CELERY_BROKER_URL'] = redis_url
        myapp.config['CELERY_RESULT_BACKEND'] = redis_url
        celery = Celery(myapp.name, broker=myapp.config['CELERY_BROKER_URL'])
        celery.conf.update(myapp.config)
        myapp.celery = celery
        return celery

    if warn:
        message = 'Something went wrong while initializing celery worker.\n' \
                  'Maybe it is not enabled in your conf ' \
                  '({}).'.format(myapp.config['CFG'])
        warnings.warn(
            message,
            RuntimeWarning
        )

    return None


def create_app(*args, **kwargs):
    """Alias for init"""
    return init(*args, **kwargs)


def init(conf=None, verbose=0, logfile=None, gunicorn=True, unittest=False, debug=False):
    """Initialize the whole application.

    :param conf: Configuration file to use
    :type conf: str

    :param verbose: Set the verbosity level
    :type verbose: int

    :param logfile: Store the logs in the given file
    :type logfile: str

    :param gunicorn: Enable gunicorn engine instead of flask's default
    :type gunicorn: bool

    :param unittest: Are we running tests (used for test only)
    :type unittest: bool

    :param debug: Enable debug mode
    :type debug: bool

    :returns: A :class:`burpui.server.BUIServer` object
    """
    from flask_login import LoginManager
    from flask_bower import Bower
    from .utils import basic_login_from_request, ReverseProxied, lookup_file
    from .server import BUIServer as BurpUI
    from .routes import view
    from .api import api, apibp

    logger = logging.getLogger('burp-ui')

    # The debug argument used to be a boolean so we keep supporting this format
    if isinstance(verbose, bool):
        if verbose:
            verbose = logging.DEBUG
        else:
            verbose = logging.CRITICAL
    else:
        levels = [
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            logging.DEBUG
        ]
        if verbose >= len(levels):
            verbose = len(levels) - 1
        if not verbose:
            verbose = 0
        verbose = levels[verbose]

    if logfile:
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            logfile,
            maxBytes=1024 * 1024 * 100,
            backupCount=5
        )
    else:
        from logging import StreamHandler
        handler = StreamHandler()

    if verbose > logging.DEBUG:
        LOG_FORMAT = (
            '[%(asctime)s] %(levelname)s in '
            '%(module)s.%(funcName)s: %(message)s'
        )
    else:
        LOG_FORMAT = (
            '-' * 80 + '\n' +
            '%(levelname)s in %(module)s.%(funcName)s ' +
            '[%(pathname)s:%(lineno)d]:\n' +
            '%(message)s\n' +
            '-' * 80
        )

    handler.setLevel(verbose)
    handler.setFormatter(Formatter(LOG_FORMAT))

    logger.setLevel(verbose)

    logger.addHandler(handler)

    logger.debug(
        'conf: {}\n'.format(conf) +
        'verbose: {}\n'.format(logging.getLevelName(verbose)) +
        'logfile: {}\n'.format(logfile) +
        'gunicorn: {}\n'.format(gunicorn) +
        'debug: {}\n'.format(debug) +
        'unittest: {}'.format(unittest)
    )

    if not unittest:
        from ._compat import patch_json
        patch_json()

    # We initialize the core
    app = BurpUI()
    if verbose:
        app.enable_logger()
    app.gunicorn = gunicorn

    app.config['CFG'] = None
    # FIXME: strange behavior when bundling errors
    # app.config['BUNDLE_ERRORS'] = True

    app.config['REMEMBER_COOKIE_HTTPONLY'] = True

    app.jinja_env.globals.update(
        isinstance=isinstance,
        list=list,
        version_id='{}-{}'.format(__version__, __release__)
    )

    if debug and not gunicorn:  # pragma: no cover
        app.config['DEBUG'] = True and not unittest
        app.config['TESTING'] = True and not unittest

    # Still need to test conf file here because the init function can be called
    # by gunicorn directly
    app.config['CFG'] = lookup_file(conf, guess=False)

    logger.info('Using configuration: {}'.format(app.config['CFG']))

    app.setup(app.config['CFG'])

    if debug:
        app.config.setdefault('TEMPLATES_AUTO_RELOAD', True)
        app.config['TEMPLATES_AUTO_RELOAD'] = True

    # manage application secret key
    if app.secret_key and (app.secret_key.lower() == 'none' or
                           (app.secret_key.lower() == 'random' and gunicorn)):
        logger.warning('Your setup is not secure! Please consider setting a'
                       ' secret key in your configuration file')
        app.secret_key = 'Burp-UI'
    if not app.secret_key or app.secret_key.lower() == 'random':
        from base64 import b64encode
        app.secret_key = b64encode(os.urandom(256))

    app.wsgi_app = ReverseProxied(app.wsgi_app, app)

    # Manage gunicorn special tricks & improvements
    if gunicorn:  # pragma: no cover
        logger.info('Using gunicorn')
        from werkzeug.contrib.fixers import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app)

    if app.storage and app.storage.lower() == 'redis':
        host, port = get_redis_server(app)
        logger.debug('Using redis {}:{}'.format(host, port))
        try:
            from redis import Redis
            from flask_session import Session
            red = Redis(host=host, port=port)
            app.config['SESSION_TYPE'] = 'redis'
            app.config['SESSION_REDIS'] = red
            app.config['SESSION_USE_SIGNER'] = app.secret_key is not None
            app.config['SESSION_PERMANENT'] = False
            ses = Session()
            ses.init_app(app)
            app.cache.init_app(
                app,
                config={
                    'CACHE_TYPE': 'redis',
                    'CACHE_REDIS_HOST': host,
                    'CACHE_REDIS_PORT': port,
                    'CACHE_REDIS_DB': 1
                }
            )
            # clear cache at startup in case we removed or added servers
            with app.app_context():
                app.cache.clear()
        except Exception as e:
            logger.warning('Unable to initialize redis: {}'.format(str(e)))
            app.cache.init_app(app)
    else:
        app.cache.init_app(app)

    # Create celery app if enabled
    create_celery(app, warn=False)
    # Create SQLAlchemy if enabled
    create_db(app)

    # We initialize the API
    api.version = __version__
    api.release = __release__
    api.__url__ = __url__
    api.__doc__ = __doc__
    api.db = app.db
    api.gapp = app
    api.celery = app.celery
    api.app_cli = app.cli
    api.cache = app.cache
    api.load_all()
    app.register_blueprint(apibp)

    # Then we load our routes
    view.__url__ = __url__
    view.__doc__ = __doc__
    app.register_blueprint(view)

    # And the login_manager
    app.login_manager = LoginManager()
    app.login_manager.login_view = 'view.login'
    app.login_manager.login_message_category = 'info'
    app.login_manager.session_protection = 'strong'
    app.login_manager.init_app(app)

    app.config.setdefault(
        'BOWER_COMPONENTS_ROOT',
        os.path.join('static', 'vendor')
    )
    app.config.setdefault('BOWER_REPLACE_URL_FOR', True)
    bower = Bower()
    bower.init_app(app)

    @app.before_request
    def setup_request():
        if app.scookie:
            from flask import request
            criteria = [
                request.is_secure,
                request.headers.get('X-Forwarded-Proto', 'http') == 'https'
            ]
            app.config['SESSION_COOKIE_SECURE'] = \
                app.config['REMEMBER_COOKIE_SECURE'] = any(criteria)

    @app.login_manager.user_loader
    def load_user(userid):
        """User loader callback"""
        if app.auth != 'none':
            return app.uhandler.user(userid)
        return None

    @app.login_manager.request_loader
    def load_user_from_request(request):
        """User loader from request callback"""
        if app.auth != 'none':
            return basic_login_from_request(request, app)

    return app
