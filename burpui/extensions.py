# -*- coding: utf8 -*-
"""

.. module:: burpui.extensions
    :platform: Unix
    :synopsis: Burp-UI extensions module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import os
import re
import warnings

from ._compat import PY3, to_unicode

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
    pwd = None
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


def create_db(myapp, cli=False, unittest=False, create=True, celery_worker=False):
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
                    not cli and not unittest and not celery_worker:
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
            if not cli and not unittest and not celery_worker:  # pragma: no cover
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


def create_websocket(myapp, websocket_server=False, celery_worker=False,
                     gunicorn=False, cli=False):
    """Create the websocket server if possible

    :param myapp: Application context
    :type myapp: :class:`burpui.server.BUIServer`
    """
    if cli and not websocket_server:
        return False
    broker = myapp.ws_broker
    if broker is not False:
        if not broker or broker is True:
            broker = 'redis'
    if broker and broker.lower() != 'none':
        host, oport, pwd = get_redis_server(myapp)
        odb = 4
        if broker.lower() not in ['default', 'redis']:
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
            port = oport
            db = odb
        if pwd:
            redis_url = 'redis://:{}@{}:{}/{}'.format(pwd, host, port, db)
        else:
            redis_url = 'redis://{}:{}/{}'.format(host, port, db)
        myapp.config['WS_MESSAGE_QUEUE'] = redis_url
    myapp.config['WS_MANAGE_SESSION'] = not myapp.config.get('WITH_SRV_SESSION', False)
    if os.getenv('BUI_MODE') == 'celery':
        myapp.config['WS_ASYNC_MODE'] = 'threading'
    # myapp.config['WS_ASYNC_MODE'] = 'threading' if not gunicorn else None

    if celery_worker:
        return False

    # if you are not a celery worker, we can patch the flask server
    try:
        from .ext.ws import socketio
        socketio.init_app(
            myapp,
            message_queue=myapp.config.get('WS_MESSAGE_QUEUE'),
            manage_session=myapp.config.get('WS_MANAGE_SESSION', False)
        )
        myapp.config['WS_AVAILABLE'] = True
    except ImportError:
        myapp.config['WS_AVAILABLE'] = False

    # Now load the namespaces
    if myapp.config['WITH_WS'] or websocket_server:
        from .ws.namespace import BUINamespace
        socketio.on_namespace(BUINamespace('/ws'))
        return True

    return False


def create_celery(myapp, warn=True):
    """Create the Celery app if possible

    :param myapp: Application context
    :type myapp: :class:`burpui.server.BUIServer`
    """
    if myapp.config['WITH_CELERY']:  # pragma: no cover
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

        from .ext.tasks import celery
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

        # may fail in case redis is not running (this can happen while running
        # the bui-manage script)
        try:
            from .tasks import force_scheduling_now
            force_scheduling_now()
        except:  # pragma: no cover
            pass

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
