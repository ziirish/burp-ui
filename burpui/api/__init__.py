# -*- coding: utf8 -*-
"""
.. module:: burpui.api
    :platform: Unix
    :synopsis: Burp-UI api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
import os
import sys
import uuid
import hashlib
import logging

from flask import Blueprint, Response, request, current_app, session, abort
from flask_restplus import Api as ApiPlus
from flask_login import current_user
from importlib import import_module
from functools import wraps

from .custom.namespace import Namespace
from .._compat import to_bytes
from ..desc import __version__, __release__, __url__, __doc__
from ..server import BUIServer  # noqa
from ..exceptions import BUIserverException
from ..config import config

bui = current_app  # type: BUIServer
EXEMPT_METHODS = set(['OPTIONS'])


def force_refresh():
    return request.headers.get('X-No-Cache', False) is not False


def cache_key():
    key = '{}-{}-{}-{}-{}-{}'.format(
        session.get('login', uuid.uuid4()),
        request.path,
        request.values,
        request.headers.get('X-Session-Tag', ''),
        request.cookies,
        session.get('language', '')
    )
    key = hashlib.sha256(to_bytes(key)).hexdigest()
    return key


def api_login_required(func):
    """Custom login decorator that is able to parse Basic credentials as well as
    Cookies set with the traditional login.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        """decorator"""
        if request.method in EXEMPT_METHODS:  # pragma: no cover
            return func(*args, **kwargs)
        # 'func' is a Flask.view.MethodView so we have access to some special
        # params
        cls = func.view_class
        login_required = getattr(cls, 'login_required', True)
        if (bui.auth != 'none' and
                login_required and
                not bui.config.get('LOGIN_DISABLED', False)):
            if not current_user.is_authenticated:
                if request.headers.get('X-From-UI', False):
                    abort(403)
                return Response(
                    'Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return func(*args, **kwargs)
    return decorated_view


def check_acl(func):
    """Custom decorator to check if the ACL are in use or not"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in EXEMPT_METHODS:  # pragma: no cover
            return func(*args, **kwargs)
        # 'func' is a Flask.view.MethodView so we have access to some special
        # params
        cls = func.view_class
        login_required = getattr(cls, 'login_required', True)
        if (bui.auth != 'none' and
                login_required and
                not bui.config.get('LOGIN_DISABLED', False)):
            if current_user.is_anonymous:
                abort(403)
        return func(*args, **kwargs)
    return decorated_view


class Api(ApiPlus):
    """Wrapper class around :class:`flask_restplus.Api`"""
    logger = logging.getLogger('burp-ui')
    # TODO: should use global object instead of reference
    loaded = False
    release = __release__
    __doc__ = __doc__
    __url__ = __url__
    CELERY_REQUIRED = ['async']

    def load_all(self):
        if config['WITH_LIMIT']:
            try:
                from ..ext.limit import limiter
                self.decorators.append(limiter.limit(config['BUI_RATIO']))
            except ImportError:
                self.logger.warning('Unable to import limiter module')
        """hack to automatically import api modules"""
        if not self.loaded:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            self.loaded = True
            for f in os.listdir(__path__[0]):
                name, ext = os.path.splitext(f)
                if (os.path.isfile(os.path.join(__path__[0], f)) and
                        ext == '.py' and
                        name not in ['__init__', '.', '..']):
                    mod = '.' + name
                    if name not in self.CELERY_REQUIRED or \
                            config['WITH_CELERY']:
                        self.logger.debug('Loading API module: {}'.format(mod))
                        try:
                            import_module(mod, __name__)
                        except:  # pragma: no cover
                            import traceback
                            self.logger.critical(
                                'Unable to load {}:\n{}'.format(
                                    mod,
                                    traceback.format_exc()
                                )
                            )
                    else:
                        self.logger.warning(
                            'Skipping API module: {}'.format(mod)
                        )

    def acl_admin_required(self, message='Access denied', code=403):
        def decorator(func):
            @wraps(func)
            def decorated(resource, *args, **kwargs):
                if not current_user.is_anonymous and \
                        not current_user.acl.is_admin():
                    resource.abort(code, message)
                return func(resource, *args, **kwargs)
            return decorated
        return decorator

    def acl_admin_or_moderator_required(self, message='Access denied', code=403):
        def decorator(func):
            @wraps(func)
            def decorated(resource, *args, **kwargs):
                if not current_user.is_anonymous and \
                        not current_user.acl.is_admin() and \
                        not current_user.acl.is_moderator():
                    resource.abort(code, message)
                return func(resource, *args, **kwargs)
            return decorated
        return decorator

    def acl_own_or_admin(self, key='name', message='Access denied', code=403):
        def decorator(func):
            @wraps(func)
            def decorated(resource, *args, **kwargs):
                if key not in kwargs:  # pragma: no cover
                    resource.abort(500, "key '{}' not found".format(key))
                if kwargs[key] != current_user.name and \
                        not current_user.is_anonymous and \
                        not current_user.acl.is_admin():
                    resource.abort(code, message)
                return func(resource, *args, **kwargs)
            return decorated
        return decorator

    def disabled_on_demo(self):
        def decorator(func):
            @wraps(func)
            def decorated(resource, *args, **kwargs):
                if config['BUI_DEMO']:
                    resource.abort(
                        405,
                        'Sorry, this feature is not available on the demo'
                    )
                return func(resource, *args, **kwargs)
            return decorated
        return decorator

    def namespace(self, *args, **kwargs):
        """A namespace factory

        :returns Namespace: a new namespace instance
        """
        ns = Namespace(*args, **kwargs)
        self.add_namespace(ns)
        return ns


apibp = Blueprint('api', __name__, url_prefix='/api')
api = Api(
    apibp,
    title='Burp-UI API',
    description='Burp-UI API to interact with burp',
    version=__version__,
    doc='/doc',
    decorators=[api_login_required]
)


@api.errorhandler(BUIserverException)
def handle_bui_server_exception(error):
    """Forward a BUIserverException to the final user

    :param error: Custom exception
    :type error: :class:`burpui.exceptions.BUIserverException`
    """
    return {'message': error.description}, error.code
