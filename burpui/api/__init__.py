# -*- coding: utf8 -*-
"""
.. module:: burpui.api
    :platform: Unix
    :synopsis: Burp-UI api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>


"""
import os
import sys

from flask import Blueprint, Response
from flask.ext.restplus import Api
from flask.ext.login import current_user, current_app
from importlib import import_module
from functools import wraps


def api_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if api.bui.auth != 'none' and not current_app.config.get('LOGIN_DISABLED', False):
            if not current_user.is_authenticated:
                return Response(
                    'Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return func(*args, **kwargs)
    return decorated_view


class ApiWrapper(Api):
    loaded = False

    def init_bui(self, bui):
        """Loads the right context.
        :param bui: application context
        :type bui: :class:`burpui.server.BUIServer`
        """
        self.bui = bui
        self.load_all()

    def load_all(self):
        # hack to automatically import api modules
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
api = ApiWrapper(apibp, title='Burp-UI API', description='Documented API to interact with burp')
