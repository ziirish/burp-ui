# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui.app
    :platform: Unix
    :synopsis: Burp-UI app module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import os
import re
import logging
import warnings

from logging import Formatter

from ._compat import PY3
from .desc import __url__, __doc__, __version__, __release__

if PY3:  # pragma: no cover
    basestring = str


def parse_db_setting(string):
    parts = re.search(
        '(?:(?P<backend>\w+)(?:\+(?P<driver>\w+))?://)?'
        '(?:(?P<user>\w+)(?::?(?P<pass>.+))?@)?'
        '(?P<host>[\w_.-]+):?(?P<port>\d+)?(?:/(?P<db>\w+))?',
        string
    )
    if not parts:
        raise ValueError('Unable to parse the db: "{}"'.format(string))
    back = parts.group('backend') or ''
    user = parts.group('user') or None
    pwd = parts.group('pass') or None
    host = parts.group('host') or ''
    port = parts.group('port') or ''
    db = parts.group('db') or ''
    return (back, user, pwd, host, port, db)


def get_redis_server(myapp):
    host = 'localhost'
    port = 6379
    if myapp.redis and myapp.redis.lower() != 'none':
        try:
            back, user, pwd, host, port, db = parse_db_setting(myapp.redis)
            host = host or 'localhost'
            try:
                port = int(port)
            except (ValueError, IndexError):
                port = 6379
        except ValueError:
            pass
    return host, port, pwd


def create_db(myapp, cli=False):
    """Create the SQLAlchemy instance if possible

    :param myapp: Application context
    :type myapp: :class:`burpui.server.BUIServer`
    """
    if myapp.config['WITH_SQL']:
        try:
            from .ext.sql import db
            from .models import test_database
            from sqlalchemy.exc import OperationalError
            from sqlalchemy_utils.functions import database_exists, \
                create_database
            myapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            if not database_exists(myapp.config['SQLALCHEMY_DATABASE_URI']) and \
                    not cli:
                try:
                    create_database(
                        myapp.config['SQLALCHEMY_DATABASE_URI']
                    )
                    db.init_app(myapp)
                    with myapp.app_context():
                        db.create_all()
                        db.session.commit()
                    return db
                except OperationalError as exp:
                    myapp.logger.error(
                        'An error occured, disabling SQL support: '
                        '{}'.format(str(exp))
                    )
                    myapp.config['WITH_SQL'] = False
                    return None
            db.init_app(myapp)
            if not cli:
                with myapp.app_context():
                    try:
                        test_database()
                    except OperationalError as exp:
                        if 'no such table' in str(exp):
                            myapp.logger.critical(
                                'Your database seem out of sync, you may want '
                                'to run \'bui-manage db upgrade\'. Disabling '
                                'SQL support for now.'
                            )
                            myapp.config['WITH_SQL'] = False
                            return None
            return db
        except ImportError:
            myapp.logger.critical(
                'Unable to load requirements, you may want to run \'pip '
                'install "burp-ui[sql]"\'. Disabling SQL support for now.'
            )
            myapp.config['WITH_SQL'] = False

    return None


def create_celery(myapp, warn=True):
    """Create the Celery app if possible

    :param myapp: Application context
    :type myapp: :class:`burpui.server.BUIServer`
    """
    if myapp.config['WITH_CELERY']:
        from .ext.async import celery
        from .exceptions import BUIserverException
        host, oport, pwd = get_redis_server(myapp)
        odb = 2
        if isinstance(myapp.use_celery, basestring):
            try:
                (_, _, pwd, host, port, db) = parse_db_setting(myapp.use_celery)
                if not port:
                    port = oport
                if not db:
                    db = odb
                else:
                    try:
                        db = int(db)
                    except ValueError:
                        db = odb
            except ValueError:
                pass
        else:
            db = odb
            port = oport
        if pwd:
            redis_url = 'redis://:{}@{}:{}/{}'.format(pwd, host, port, db)
        else:
            redis_url = 'redis://{}:{}/{}'.format(host, port, db)
        myapp.config['CELERY_BROKER_URL'] = myapp.config['BROKER_URL'] = \
            redis_url
        myapp.config['CELERY_RESULT_BACKEND'] = redis_url
        celery.conf.update(myapp.config)

        if not hasattr(celery, 'flask_app'):
            celery.flask_app = myapp

        TaskBase = celery.Task

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args, **kwargs):
                with myapp.app_context():
                    try:
                        return TaskBase.__call__(self, *args, **kwargs)
                    except BUIserverException:
                        # ignore unhandled exceptions in the celery worker
                        pass

        celery.Task = ContextTask

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


def create_app(conf=None, verbose=0, logfile=None, gunicorn=True,
               unittest=False, debug=False, cli=False):
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

    :param cli: Are we running the CLI
    :type cli: bool

    :returns: A :class:`burpui.server.BUIServer` object
    """
    from flask import g
    from flask_login import LoginManager
    from flask_bower import Bower
    from flask_babel import gettext
    from .utils import basic_login_from_request, ReverseProxied, lookup_file
    from .server import BUIServer as BurpUI
    from .sessions import session_manager
    from .routes import view, mypad
    from .api import api, apibp
    from .ext.cache import cache
    from .ext.i18n import babel, get_locale

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

    # Some config
    app.config['BUI_CLI'] = cli

    # FIXME: strange behavior when bundling errors
    # app.config['BUNDLE_ERRORS'] = True

    app.config['REMEMBER_COOKIE_HTTPONLY'] = True

    if debug and not gunicorn:  # pragma: no cover
        app.config['DEBUG'] = True and not unittest
        app.config['TESTING'] = True and not unittest

    # Still need to test conf file here because the init function can be called
    # by gunicorn directly
    if conf:
        app.config['CFG'] = lookup_file(conf, guess=False)
    else:
        app.config['CFG'] = lookup_file()

    logger.info('Using configuration: {}'.format(app.config['CFG']))

    app.setup(app.config['CFG'], unittest, cli)

    if debug:
        app.config.setdefault('TEMPLATES_AUTO_RELOAD', True)
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['DEBUG'] = True

    app.jinja_env.globals.update(
        isinstance=isinstance,
        list=list,
        mypad=mypad,
        version_id='{}-{}'.format(__version__, __release__),
        config=app.config
    )

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

    if app.storage and app.storage.lower() != 'default':
        try:
            # Session setup
            if not app.session_db or \
                    app.session_db.lower() not in ['none']:
                from redis import Redis
                from .ext.session import sess
                host, port, pwd = get_redis_server(app)
                db = 0
                if app.session_db and \
                        app.session_db.lower() not in ['redis', 'default']:
                    try:
                        (_, _, pwd, host, port, db) = \
                            parse_db_setting(app.session_db)
                    except ValueError as exp:
                        logger.warning(str(exp))
                try:
                    db = int(db)
                except ValueError:
                    db = 0
                logger.debug('Using redis://guest:****@{}:{}/{}'.format(
                    host,
                    port,
                    db)
                )
                red = Redis(host=host, port=port, db=db, password=pwd)
                app.config['SESSION_TYPE'] = 'redis'
                app.config['SESSION_REDIS'] = red
                app.config['SESSION_USE_SIGNER'] = app.secret_key is not None
                app.config['SESSION_PERMANENT'] = False
                sess.init_app(app)
                session_manager.backend = red
            # Cache setup
            if not app.cache_db or \
                    app.cache_db.lower() not in ['none']:
                host, port, pwd = get_redis_server(app)
                db = 1
                if app.cache_db and \
                        app.cache_db.lower() not in ['redis', 'default']:
                    try:
                        (_, _, pwd, host, port, db) = \
                            parse_db_setting(app.cache_db)
                    except ValueError as exp:
                        logger.warning(str(exp))
                try:
                    db = int(db)
                except ValueError:
                    db = 1
                logger.debug('Using redis://guest:****@{}:{}/{}'.format(
                    host,
                    port,
                    db)
                )
                cache.init_app(
                    app,
                    config={
                        'CACHE_TYPE': 'redis',
                        'CACHE_REDIS_HOST': host,
                        'CACHE_REDIS_PORT': port,
                        'CACHE_REDIS_PASSWORD': pwd,
                        'CACHE_REDIS_DB': db
                    }
                )
                # clear cache at startup in case we removed or added servers
                with app.app_context():
                    cache.clear()
            else:
                cache.init_app(app)
        except Exception as e:
            logger.warning('Unable to initialize redis: {}'.format(str(e)))
            cache.init_app(app)
    else:
        cache.init_app(app)

    # Create celery app if enabled
    create_celery(app, warn=False)
    if app.config['WITH_CELERY']:
        # may fail in case redis is not running (this can happen while running
        # the bui-manage script)
        try:
            from .api.async import force_scheduling_now
            force_scheduling_now()
        except:
            pass

    # Initialize i18n
    babel.init_app(app)

    # Create SQLAlchemy if enabled
    create_db(app, cli)

    # We initialize the API
    api.version = __version__
    api.release = __release__
    api.__url__ = __url__
    api.__doc__ = __doc__
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
    # This is just to have the strings in the .po files
    app.login_manager.login_message = gettext(
        'Please log in to access this page.'
    )
    app.login_manager.needs_refresh_message = gettext(
        'Please reauthenticate to access this page.'
    )
    # This will be called at runtime and will then translate the strings
    app.login_manager.localize_callback = gettext
    app.login_manager.init_app(app)

    # Initialize Session Manager
    session_manager.init_app(app)

    # Initialize Bower ext
    app.config.setdefault(
        'BOWER_COMPONENTS_ROOT',
        os.path.join('static', 'vendor')
    )
    app.config.setdefault('BOWER_REPLACE_URL_FOR', True)
    bower = Bower()
    bower.init_app(app)

    @app.before_request
    def setup_request():
        g.locale = get_locale()
        # make sure to store secure cookie if required
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

    @app.after_request
    def after_request(response):
        if getattr(g, 'basic_session', False):
            session_manager.invalidate_current_session()
        return response

    return app


init = create_app
