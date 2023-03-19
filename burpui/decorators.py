# -*- coding: utf8 -*-
"""
.. module:: burpui.decorators
    :platform: Unix
    :synopsis: Burp-UI decorators module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import datetime
import time
from functools import wraps


def browser_cache(expires=None):
    """Add Flask cache response headers based on expires in seconds.

    If expires is None, caching will be disabled.
    Otherwise, caching headers are set to expire in now + expires seconds

    Example usage:

    ::

        @app.route('/map')
        @browser_cache(expires=60)
        def index():
            return render_template('index.html')

    """
    from wsgiref.handlers import format_date_time

    from flask import g
    from flask_restx.utils import unpack

    def cache_decorator(view):
        @wraps(view)
        def cache_func(*args, **kwargs):
            resp, code, headers = unpack(view(*args, **kwargs))
            now = datetime.datetime.now()

            headers["Last-Modified"] = format_date_time(time.mktime(now.timetuple()))

            failure = code - 200 >= 100  # this is not a successful answer
            do_not_cache = getattr(g, "DONOTCACHE", False)

            if expires is None or failure or do_not_cache:
                headers[
                    "Cache-Control"
                ] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
            else:
                headers["Cache-Control"] = "private, max-age={}".format(expires)

            return resp, code, headers

        return cache_func

    return cache_decorator


def implement(func):
    """A decorator indicating the method is implemented.

    For the agent and the 'multi' backend, we inherit the backend interface but
    we don't really implement it because we just act as a proxy.
    But maintaining the exhaustive list of methods in several places to always
    implement the same "proxy" thing was painful so I ended up cheating to
    dynamically implement those methods thanks to the __getattribute__ magic
    function.

    But sometimes we want to implement specific things, hence this decorator
    to indicate we don't want the default "magic" implementation and use the
    custom implementation instead.
    """
    try:
        func.__ismethodimplemented__ = True
    except AttributeError:
        # properties seem immutable
        pass
    return func


def usetriorun(func):
    """A decorator indicating the method uses trio.run

    Such functions should always be written like this:

    ::
        def function(self, *args, **kwargs):
            return trio.run(self._async_function, partial(*args, **kwargs))
    """
    try:
        func.__isusingtriorun__ = True
    except AttributeError:
        pass
    return func
