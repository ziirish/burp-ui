# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.fields
    :platform: Unix
    :synopsis: Burp-UI api custom fields module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
from flask_restplus.fields import *  # noqa # pylint: disable=locally-disabled, wildcard-import, unused-wildcard-import
from .my_fields import DateTime, DateTimeHuman, BackupNumber, SafeString, LocalizedString  # noqa
