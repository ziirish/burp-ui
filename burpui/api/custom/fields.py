# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.fields
    :platform: Unix
    :synopsis: Burp-UI api custom fields module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
import flask_restx.fields
from flask_restx.fields import *  # noqa # pylint: disable=locally-disabled, wildcard-import, unused-wildcard-import

from .my_fields import DateTimeHuman  # noqa
from .my_fields import BackupNumber, DateTime, LocalizedString, SafeString

__all__ = flask_restx.fields.__all__ + (
    DateTime,
    DateTimeHuman,
    BackupNumber,
    SafeString,
    LocalizedString,
)
