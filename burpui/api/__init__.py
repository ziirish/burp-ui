# -*- coding: utf8 -*-
"""
.. module:: burpui.api
    :platform: Unix
    :synopsis: Burp-UI api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>


"""
import os
import sys
import json

from flask import Blueprint, Response, request, make_response
from flask.ext.restplus import Api
from flask.ext.login import current_user, current_app, login_user
from importlib import import_module
from functools import wraps

from ..misc.utils import BUIserverException, BUIhttpException


def api_login_user(request):
    """Utility function to login the user using Basic HTTP credentials."""
    creds = request.headers.get('Authorization')
    if creds:
        creds = creds.replace('Basic ', '', 1)
        try:
            import base64
            login, password = base64.b64decode(creds).split(':')
        except:
            pass
        if login:
            user = api.bui.uhandler.user(login)
            if user and user.active and user.login(login, password):
                login_user(user)
                return user
    return None


def api_login_required(func):
    """Custom login decorator that is able to parse Basic credentials as well as
    Cookies set with the traditional login.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        """decorator"""
        if api.bui.auth != 'none' and not current_app.config.get('LOGIN_DISABLED', False):
            if not current_user.is_authenticated and not api_login_user(request):
                return Response(
                    'Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return func(*args, **kwargs)
    return decorated_view


class ApiWrapper(Api):
    """Wrapper class around :class:`flask.ext.restplus.Api`"""
    loaded = False

    def init_bui(self, bui):
        """Loads the right context.
        :param bui: application context
        :type bui: :class:`burpui.server.BUIServer`
        """
        self.bui = bui
        self.load_all()

    def abort(self, code=500, message=None, **kwargs):
        """Override :func:`flask.ext.restplus.Api.abort` in order to raise
        custom exceptions
        """
        if message and (isinstance(message, basestring) or isinstance(message, str)):
            # raise a custom error that is caught by 'errorhandler'
            raise BUIhttpException(code, message)
        message = json.dumps(message)
        super(ApiWrapper, self).abort(code, message, **kwargs)

    def load_all(self):
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
                    import_module(mod, 'burpui.api')

apibp = Blueprint('api', __name__, url_prefix='/api', template_folder='../templates')
api = ApiWrapper(apibp, title='Burp-UI API', description='Burp-UI API to interact with burp', decorators=[api_login_required])


# Just in case the exception was not caught earlier
@apibp.errorhandler(BUIserverException)
def handle_bui_server_exception(error):
    response = make_response(str(error), 500)
    response.headers['content-type'] = 'text/plain'
    return response


@apibp.errorhandler(BUIhttpException)
def handle_bui_http_exception(error):
    response = make_response(error.message, error.status)
    response.headers['content-type'] = 'text/plain'
    return response
