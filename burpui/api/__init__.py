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

from flask import Blueprint, Response, request
from flask.ext.restplus import Api
from flask.ext.login import current_user
from flask.ext.cache import Cache
from importlib import import_module
from functools import wraps

from .._compat import IS_GUNICORN

if sys.version_info >= (3, 0):  # pragma: no cover
    basestring = str


# Implement a "parallel loop" routine either with gipc or multiprocessing
# depending if we are under gunicorn or not
if IS_GUNICORN:
    def parallel_loop(func=None, elem=None):
        import gevent
        from gevent.queue import Queue
        ret = []
        api.bui.cli._logger('debug', 'Using gevent')

        if not callable(func):
            api.abort(500, 'The provided \'func\' is not callable!')
        if not elem:
            return []

        output = Queue()

        processes = [
            gevent.spawn(
                func,
                e,
                output
            ) for e in elem
        ]
        # wait for process termination
        gevent.joinall(processes)

        for p in processes:
            tmp = output.get()
            if isinstance(tmp, basestring):
                api.abort(500, tmp)
            elif tmp:
                ret.append(tmp)

        return ret

else:
    def parallel_loop(func=None, elem=None):
        import multiprocessing
        ret = []

        if not callable(func):
            api.abort(500, 'The provided \'func\' is not callable!')
        if not elem:
            return []

        # create our process pool/queue
        output = multiprocessing.Queue()
        processes = [
            multiprocessing.Process(
                target=func,
                args=(e, output)
            ) for e in elem
        ]
        # start the processes
        [p.start() for p in processes]
        # wait for process termination
        [p.join() for p in processes]

        for p in processes:
            tmp = output.get()
            if isinstance(tmp, basestring):
                api.abort(500, tmp)
            elif tmp:
                ret.append(tmp)

        return ret


def cache_key():
    return '{}-{}-{}'.format(current_user.get_id(), request.path, request.values)


def api_login_required(func):
    """Custom login decorator that is able to parse Basic credentials as well as
    Cookies set with the traditional login.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        """decorator"""
        try:
            name = func.func_name
        except:  # pragma: no cover
            name = func.__name__
        if (api.bui.auth != 'none' and
                name not in api.LOGIN_NOT_REQUIRED and
                not api.bui.config.get('LOGIN_DISABLED', False)):
            if not current_user.is_authenticated:
                return Response(
                    'Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return func(*args, **kwargs)
    return decorated_view


class ApiWrapper(Api):
    """Wrapper class around :class:`flask.ext.restplus.Api`"""
    cache = Cache(config={'CACHE_TYPE': 'null'})
    loaded = False
    release = None
    __doc__ = None
    __url__ = None
    LOGIN_NOT_REQUIRED = []

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
        if message and not isinstance(message, basestring):
            try:
                message = json.dumps(message)  # pragma: no cover
            except:
                message = None
        super(ApiWrapper, self).abort(code, message, **kwargs)  # pragma: no cover

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


apibp = Blueprint('api', __name__, url_prefix='/api')
api = ApiWrapper(apibp, title='Burp-UI API', description='Burp-UI API to interact with burp', doc='/doc', decorators=[api_login_required])
