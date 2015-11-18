# -*- coding: utf8 -*-
"""
.. module:: burpui.exceptions
    :platform: Unix
    :synopsis: Burp-UI exceptions module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""


class BUIserverException(Exception):
    """Raised in case of internal error. This exception should never reach the
    end-user.
    """
    pass


class BUIhttpException(Exception):
    """Raised in case of insufficient permissions."""

    def __init__(self, status=500, message=''):
        self.status = status
        self.message = message
