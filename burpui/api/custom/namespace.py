# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.namespace
    :platform: Unix
    :synopsis: Burp-UI api custom namespace module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
# All of this is creepy hacky since Flask-Resplus seem dead...
from functools import wraps
from werkzeug.wrappers import Response
from flask import Response as FlaskResponse, request, current_app, \
    has_app_context
from flask_restplus import Namespace as NamespacePlus
from flask_restplus.utils import unpack, merge
from flask_restplus.marshalling import marshal_with as marshal_with_plus, \
    marshal


class marshal_with(marshal_with_plus):
    """Subclass default marshal_with to manage custom API responses"""
    def __init__(self, fields, envelope=None, mask=None, strict=True):
        super(marshal_with, self).__init__(fields, envelope, mask)
        self.strict = strict

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            resp = f(*args, **kwargs)
            if not self.strict and (isinstance(resp, Response) or
                                    isinstance(resp, FlaskResponse)):
                return resp
            mask = self.mask
            if has_app_context():
                mask_header = current_app.config['RESTPLUS_MASK_HEADER']
                mask = request.headers.get(mask_header) or mask
            if isinstance(resp, tuple):
                data, code, headers = unpack(resp)
                return marshal(data, self.fields, self.envelope, mask), code, headers
            else:
                return marshal(resp, self.fields, self.envelope, mask)
        return wrapper


class Namespace(NamespacePlus):
    """Subclass default Namespace to manage custom API responses"""

    def marshal_with(self, fields, as_list=False, code=200, description=None, strict=True, **kwargs):
        """If the decorated function returns a :class:`Flask.Response` object,
        we don't marshal it
        """
        def wrapper(func):
            doc = {
                'responses': {
                    code: (description, [fields]) if as_list else (description, fields)
                },
                '__mask__': kwargs.get('mask', True),  # Mask values can't be determined outside app context
            }
            func.__apidoc__ = merge(getattr(func, '__apidoc__', {}), doc)
            kwargs['strict'] = strict
            return marshal_with(fields, **kwargs)(func)
        return wrapper
