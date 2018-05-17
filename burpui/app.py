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
import time
import logging

from logging import Formatter

from .desc import __version__, __release__
from .extensions import create_celery, create_db, create_websocket, \
    parse_db_setting, get_redis_server


def create_app(conf=None, verbose=0, logfile=None, **kwargs):
    """Initialize the whole application.

    :param conf: Configuration file to use
    :type conf: str

    :param verbose: Set the verbosity level
    :type verbose: int

    :param logfile: Store the logs in the given file
    :type logfile: str

    :param kwargs: Extra options:
                   - gunicorn (bool): Enable gunicorn engine instead of flask's
                   default. Default is True.
                   - unittest (bool): Are we running tests (used for test only).
                   Default is False.
                   - debug (bool): Enable debug mode. Default is False.
                   - cli (bool): Are we running the CLI. Default is False.
                   - reverse_proxy (bool): Are we behind a reverse-proxy.
                   Default is True if gunicorn is True
                   - websocket_server (bool): Are we running the websocket
                   server. Default is False
    :type kwargs: dict

    :returns: A :class:`burpui.server.BUIServer` object
    """
    from flask import g, request, session, render_template
    from flask_login import LoginManager
    from flask_bower import Bower
    from flask_babel import gettext
    from .utils import ReverseProxied, lookup_file, is_uuid
    from .security import basic_login_from_request
    from .server import BUIServer as BurpUI
    from .sessions import session_manager
    from .ext.cache import cache
    from .ext.i18n import babel, get_locale
    from .misc.auth.handler import BUIanon

    logger = logging.getLogger('burp-ui')

    gunicorn = kwargs.get('gunicorn', True)
    unittest = kwargs.get('unittest', False)
    debug = kwargs.get('debug', False)
    cli = kwargs.get('cli', False)
    reverse_proxy = kwargs.get('reverse_proxy', gunicorn)
    celery_worker = kwargs.get('celery_worker', False)
    websocket_server = kwargs.get('websocket_server', False)

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
            '-' * 27 +
            '[%(asctime)s]' +
            '-' * 28 + '\n' +
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
        'unittest: {}\n'.format(unittest) +
        'cli: {}\n'.format(cli) +
        'reverse_proxy: {}'.format(reverse_proxy)
    )

    if not unittest:  # pragma: no cover
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

    SENTRY_AVAILABLE = False
    if app.demo:
        try:
            from .ext.sentry import sentry
            sentry.init_app(app, dsn=app.config['BUI_DSN'])
            SENTRY_AVAILABLE = True
        except ImportError:
            pass

    # manage application secret key
    if app.secret_key and \
            (app.secret_key.lower() == 'none' or
             (app.secret_key.lower() == 'random' and
              gunicorn)):  # pragma: no cover
        logger.critical('Your setup is not secure! Please consider setting a'
                        ' secret key in your configuration file')
        app.secret_key = 'Burp-UI'
    if not app.secret_key or app.secret_key.lower() == 'random':
        from base64 import b64encode
        app.secret_key = b64encode(os.urandom(256))

    app.wsgi_app = ReverseProxied(app.wsgi_app, app)

    # Manage reverse_proxy special tricks & improvements
    if reverse_proxy:  # pragma: no cover
        from werkzeug.contrib.fixers import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app)

    if app.storage and app.storage.lower() == 'redis':
        try:
            # Session setup
            if not app.session_db or \
                    str(app.session_db).lower() not in ['none', 'false']:
                from redis import Redis
                from .ext.session import sess
                host, port, pwd = get_redis_server(app)
                db = 0
                if app.session_db and \
                        str(app.session_db).lower() not \
                        in ['redis', 'default', 'true']:
                    try:  # pragma: no cover
                        (_, _, pwd, host, port, db) = \
                            parse_db_setting(app.session_db)
                    except ValueError as exp:
                        logger.warning(str(exp))
                try:
                    db = int(db)
                except ValueError:
                    db = 0
                logger.debug(
                    'SESSION: Using redis://guest:****@{}:{}/{}'.format(
                        host,
                        port,
                        db)
                )
                red = Redis(host=host, port=port, db=db, password=pwd)
                app.config['WITH_SRV_SESSION'] = True
                app.config['SESSION_TYPE'] = 'redis'
                app.config['SESSION_REDIS'] = red
                app.config['SESSION_USE_SIGNER'] = app.secret_key is not None
                app.config['SESSION_PERMANENT'] = False
                sess.init_app(app)
                session_manager.backend = red
        except Exception as exp:  # pragma: no cover
            logger.warning('Unable to initialize session: {}'.format(str(exp)))
            app.config['WITH_SRV_SESSION'] = False
        try:
            # Cache setup
            if not app.cache_db or \
                    str(app.cache_db).lower() not in ['none', 'false']:
                host, port, pwd = get_redis_server(app)
                db = 1
                if app.cache_db and \
                        str(app.cache_db).lower() not \
                        in ['redis', 'default', 'true']:
                    try:  # pragma: no cover
                        (_, _, pwd, host, port, db) = \
                            parse_db_setting(app.cache_db)
                    except ValueError as exp:
                        logger.warning(str(exp))
                try:
                    db = int(db)
                except ValueError:
                    db = 1
                logger.debug('CACHE: Using redis://guest:****@{}:{}/{}'.format(
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
            else:  # pragma: no cover
                cache.init_app(app)
        except Exception as exp:  # pragma: no cover
            logger.warning('Unable to initialize cache: {}'.format(str(exp)))
            cache.init_app(app)
        try:
            # Limiter setup
            if app.limiter and str(app.limiter).lower() not \
                    in ['none', 'false']:  # pragma: no cover
                from .ext.limit import limiter
                app.config['RATELIMIT_HEADERS_ENABLED'] = True
                if app.limiter and str(app.limiter).lower() not \
                        in ['default', 'redis', 'true']:
                    app.config['RATELIMIT_STORAGE_URL'] = app.limiter
                else:
                    db = 3
                    host, port, pwd = get_redis_server(app)
                    if pwd:
                        conn = 'redis://guest:{}@{}:{}/{}'.format(
                            pwd,
                            host,
                            port,
                            db
                        )
                    else:
                        conn = 'redis://{}:{}/{}'.format(host, port, db)
                    app.config['RATELIMIT_STORAGE_URL'] = conn

                (_, _, pwd, host, port, db) = parse_db_setting(
                    app.config['RATELIMIT_STORAGE_URL']
                )

                logger.debug(
                    'LIMITER: Using redis://guest:****@{}:{}/{}'.format(
                        host,
                        port,
                        db
                    )
                )
                limiter.init_app(app)
                app.config['WITH_LIMIT'] = True
        except ImportError:  # pragma: no cover
            logger.warning('Unable to load limiter. Did you run \'pip install '
                           'flask-limiter\'?')
        except Exception as exp:  # pragma: no cover
            logger.warning('Unable to initialize limiter: {}'.format(str(exp)))
    else:
        cache.init_app(app)

    # Initialize i18n
    babel.init_app(app)

    # Create SQLAlchemy if enabled
    create_db(app, cli, unittest, celery_worker=celery_worker)

    if not celery_worker:
        from .api import api, apibp
        from .routes import view, mypad

        app.jinja_env.globals.update(
            isinstance=isinstance,
            list=list,
            mypad=mypad,
            version_id='{}-{}'.format(__version__, __release__),
        )

        # We initialize the API
        api.load_all()
        app.register_blueprint(apibp)

        # Then we load our routes
        app.register_blueprint(view)

        # Initialize Bower ext
        app.config.setdefault(
            'BOWER_COMPONENTS_ROOT',
            os.path.join('static', 'vendor')
        )
        app.config.setdefault('BOWER_REPLACE_URL_FOR', True)
        bower = Bower()
        bower.init_app(app)

    # Order of the initialization matters!
    # The websocket must be configured prior to the celery worker for instance

    # Initialize Session Manager
    session_manager.init_app(app)

    # And the login_manager
    app.login_manager = LoginManager()
    app.login_manager.anonymous_user = BUIanon
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

    # Create WebSocket server
    if create_websocket(app, websocket_server, celery_worker, gunicorn, cli):
        return app

    # Create celery app if enabled
    create_celery(app, warn=False)

    def _check_session(user, request, api=False):
        """Check if the session is in the db"""
        if user and not session_manager.session_in_db():  # pragma: no cover
            login = getattr(user, 'name', None)
            if login and not is_uuid(login):
                remember = session.get('persistent', False)
                if not remember:
                    from flask_login import decode_cookie
                    remember_cookie = request.cookies.get(
                        app.config.get('REMEMBER_COOKIE_NAME'),
                        False
                    )
                    # check if the remember_cookie is legit
                    if remember_cookie and decode_cookie(remember_cookie):
                        remember = True
                session_manager.store_session(
                    login,
                    request.remote_addr,
                    request.headers.get('User-Agent'),
                    remember,
                    api
                )
            elif login:
                app.uhandler.remove(login)

    @app.before_request
    def setup_request():
        g.version = '{}-{}'.format(__version__, __release__)
        g.locale = get_locale()
        g.now = round(time.time())
        g.date_format = session.get('dateFormat', 'llll')
        # make sure to store secure cookie if required
        if app.scookie:
            criteria = [
                request.is_secure,
                request.headers.get('X-Forwarded-Proto', 'http') == 'https'
            ]
            app.config['SESSION_COOKIE_SECURE'] = \
                app.config['REMEMBER_COOKIE_SECURE'] = any(criteria)
        if '_extra' in request.args:
            session['_extra'] = request.args.get('_extra')
        g._extra = session.get('_extra', '')

    @app.login_manager.user_loader
    def load_user(userid):
        """User loader callback"""
        if app.auth != 'none':
            user = app.uhandler.user(userid)
            if not user:
                return None
            if 'X-Language' in request.headers:
                language = request.headers.get('X-Language')
                user.language = language
                session['language'] = language
            if '_id' not in session:
                from flask_login import login_user
                # if _id is not in session, it means we loaded the user from
                # cache/db using the remember cookie so we need to login it
                login_user(user, remember=user.is_authenticated, fresh=False)
            _check_session(user, request)
            return user
        return None

    @app.login_manager.request_loader
    def load_user_from_request(request):
        """User loader from request callback"""
        if app.auth != 'none':
            user = basic_login_from_request(request, app)
            _check_session(user, request, True)
            return user

    @app.after_request
    def after_request(response):
        if getattr(g, 'basic_session', False):
            if session_manager.invalidate_current_session():
                session_manager.delete_session()
        return response

    if app.demo and SENTRY_AVAILABLE:
        @app.errorhandler(500)
        def internal_server_error(error):
            from .ext.sentry import sentry
            return render_template(
                '500_sentry.html',
                event_id=g.sentry_event_id,
                public_dsn=sentry.client.get_public_dsn('https')
            )

    return app


init = create_app
