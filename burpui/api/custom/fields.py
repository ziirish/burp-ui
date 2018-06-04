# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.fields
    :platform: Unix
    :synopsis: Burp-UI api custom fields module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
import flask_restplus.fields

from flask_restplus.fields import *  # noqa # pylint: disable=locally-disabled, wildcard-import, unused-wildcard-import
from .my_fields import DateTime, DateTimeHuman, BackupNumber, SafeString, LocalizedString, Wildcard  # noqa
from .my_fields2 import Nested  # noqa

__all__ = flask_restplus.fields.__all__ + \
    (DateTime, DateTimeHuman, BackupNumber, SafeString, LocalizedString, Wildcard)
