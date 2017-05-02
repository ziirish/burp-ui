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

from ._compat import PY3, to_unicode
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
    if not parts:  # pragma: no cover
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
        except ValueError:  # pragma: no cover
            pass
    return host, port, pwd


def create_db(myapp, cli=False, unittest=False, create=True):
    """Create the SQLAlchemy instance if possible

    :param myapp: Application context
    :type myapp: :class:`burpui.server.BUIServer`
    """
    if myapp.config['WITH_SQL']:
        try:
            from .ext.sql import db
            from sqlalchemy.exc import OperationalError
            from sqlalchemy_utils.functions import database_exists
            myapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            if not database_exists(myapp.config['SQLALCHEMY_DATABASE_URI']) and \
                    not cli and not unittest:
                if create:  # pragma: no cover
                    import subprocess
                    local = os.path.join(os.getcwd(), '..', 'tools', 'bui-manage')
                    buimanage = local if os.path.exists(local) else 'bui-manage'
                    cmd = [
                        buimanage,
                        '-c',
                        myapp.config['CFG'],
                        '-l',
                        os.devnull,
                        'db',
                        'upgrade'
                    ]
                    upgd = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT
                    )
                    (out, _) = upgd.communicate()
                    if upgd.returncode != 0:
                        myapp.logger.error(
                            'Disabling SQL support because '
                            'something went wrong while setting up the '
                            'database:\n{}'.format(out)
                        )
                        myapp.config['WITH_SQL'] = False
                        return None
                    return create_db(myapp, cli, unittest, False)
                else:  # pragma: no cover
                    myapp.logger.error(
                        'Database not found, disabling SQL support'
                    )
                    myapp.config['WITH_SQL'] = False
                    return None

            back = parse_db_setting(myapp.config['SQLALCHEMY_DATABASE_URI'])[0]

            if 'mysql' in back:  # pragma: no cover
                # optimize SQL pools for MySQL driver
                myapp.config['SQLALCHEMY_POOL_SIZE'] = 20
                myapp.config['SQLALCHEMY_POOL_RECYCLE'] = 600

            db.init_app(myapp)
            if not cli and not unittest:  # pragma: no cover
                with myapp.app_context():
                    try:
                        import subprocess

                        # get the current revision from alembic_version
                        res = db.engine.execute(
                            'select version_num from alembic_version'
                        )
                        if not res:
                            raise Exception(
                                'Alembic does not seem to be setup'
                            )
                        current = None
                        for row in res:
                            current = to_unicode(row['version_num'])
                            break

                        # get current head using alembic/FLask-Migrate
                        local = os.path.join(
                            os.getcwd(),
                            'tools',
                            'bui-manage'
                        )
                        buimanage = local if os.path.exists(local) \
                            else 'bui-manage'
                        cmd = [
                            buimanage,
                            '-c',
                            myapp.config['CFG'],
                            '-l',
                            os.devnull,
                            'db',
                            'heads'
                        ]
                        rev = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT
                        )
                        (out, _) = rev.communicate()
                        if rev.returncode != 0:
                            raise Exception(
                                'something went wrong while setting up the '
                                'database:\n{}'.format(out)
                            )

                        latest = to_unicode(out).split()[0]

                        # now we compare the revision numbers
                        if latest != current:
                            myapp.logger.critical(
                                'Your database seems out of sync ({} != {}), '
                                'you may want to run \'bui-manage db '
                                'upgrade\'.'.format(latest, current)
                            )
                            myapp.logger.critical(
                                'Disabling SQL support for now.'
                            )
                            myapp.config['WITH_SQL'] = False
                            return None

                    except (OperationalError, Exception) as exp:
                        err = str(exp)
                        if 'no such table' in err:
                            myapp.logger.critical(
                                'Your database seems out of sync, you may want '
                                'to run \'bui-manage db upgrade\'.'
                            )
                        else:
                            myapp.logger.critical(
                                'Something seems to be wrong with your setup: '
                                '{}'.format(err)
                            )

                        myapp.logger.critical('Disabling SQL support for now.')
                        myapp.config['WITH_SQL'] = False
                        return None

            # If we are here, it means everything is alright
            return db

        except ImportError:  # pragma: no cover
            myapp.logger.critical(
                'Unable to load requirements, you may want to run \'pip '
                'install "burp-ui[sql]"\'.\nDisabling SQL support for now.'
            )
            myapp.config['WITH_SQL'] = False
        except OperationalError as exp:  # pragma: no cover
            myapp.logger.critical(
                'unable to contact database: {}\nDisabling SQL '
                'support.'.format(exp)
            )
            myapp.config['WITH_SQL'] = False

    return None


def create_celery(myapp, warn=True):
    """Create the Celery app if possible

    :param myapp: Application context
    :type myapp: :class:`burpui.server.BUIServer`
    """
    if myapp.config['WITH_CELERY']:  # pragma: no cover
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

    if warn:  # pragma: no cover
        message = 'Something went wrong while initializing celery worker.\n' \
                  'Maybe it is not enabled in your conf ' \
                  '({}).'.format(myapp.config['CFG'])
        warnings.warn(
            message,
            RuntimeWarning
        )

    return None


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
    :type kwargs: dict

    :returns: A :class:`burpui.server.BUIServer` object
    """
    from flask import g, request, session
    from flask_login import LoginManager
    from flask_bower import Bower
    from flask_babel import gettext
    from .utils import basic_login_from_request, ReverseProxied, lookup_file, \
        is_uuid
    from .server import BUIServer as BurpUI
    from .sessions import session_manager
    from .routes import view, mypad
    from .api import api, apibp
    from .ext.cache import cache
    from .ext.i18n import babel, get_locale

    logger = logging.getLogger('burp-ui')

    gunicorn = kwargs.get('gunicorn', True)
    unittest = kwargs.get('unittest', False)
    debug = kwargs.get('debug', False)
    cli = kwargs.get('cli', False)
    reverse_proxy = kwargs.get('reverse_proxy', gunicorn)

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

    app.jinja_env.globals.update(
        isinstance=isinstance,
        list=list,
        mypad=mypad,
        version_id='{}-{}'.format(__version__, __release__),
    )

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
                app.config['SESSION_TYPE'] = 'redis'
                app.config['SESSION_REDIS'] = red
                app.config['SESSION_USE_SIGNER'] = app.secret_key is not None
                app.config['SESSION_PERMANENT'] = False
                sess.init_app(app)
                session_manager.backend = red
        except Exception as exp:  # pragma: no cover
            logger.warning('Unable to initialize session: {}'.format(str(exp)))
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
    create_db(app, cli, unittest)

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

    # Create celery app if enabled
    create_celery(app, warn=False)
    if app.config['WITH_CELERY']:
        # may fail in case redis is not running (this can happen while running
        # the bui-manage script)
        try:
            from .api.async import force_scheduling_now
            force_scheduling_now()
        except:  # pragma: no cover
            pass

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
        g.locale = get_locale()
        g.date_format = session.get('dateFormat', 'llll')
        # make sure to store secure cookie if required
        if app.scookie:
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
            user = app.uhandler.user(userid)
            if 'X-Language' in request.headers:
                language = request.headers.get('X-Language')
                user.language = language
                session['language'] = language
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

    return app


init = create_app
