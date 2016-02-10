# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.fields
    :platform: Unix
    :synopsis: Burp-UI api custom fields module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
from flask.ext.restplus.fields import *
from .my_fields import DateTime, BackupNumber
