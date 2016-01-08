# -*- coding: utf8 -*-
"""
.. module:: burpui.exceptions
    :platform: Unix
    :synopsis: Burp-UI exceptions module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
# Agent does not need "real" HTTP errors
try:
    from werkzeug.exceptions import HTTPException
except ImportError:
    HTTPException = object


class BUIserverException(HTTPException):
    """Raised in case of internal error. This exception should never reach the
    end-user.
    """
    code = 500

    def __init__(self, message):
        self.description = message

    def __str__(self):
        return self.description
