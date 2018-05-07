# -*- coding: utf8 -*-
"""
.. module:: burpui.exceptions
    :platform: Unix
    :synopsis: Burp-UI exceptions module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
# Agent do not need "real" HTTP errors
try:
    from werkzeug.exceptions import HTTPException
    WERKZEUG = True
except ImportError:
    HTTPException = Exception
    WERKZEUG = False


class BUIserverException(HTTPException):
    """Raised in case of internal error."""
    code = 500

    def __init__(self, message="Internal Error", response=None):
        if WERKZEUG:
            HTTPException.__init__(self, message, response)
        else:
            self.description = message
            self.response = response

    def __str__(self):
        return self.description
