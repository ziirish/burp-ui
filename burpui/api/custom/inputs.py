# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.inputs
    :platform: Unix
    :synopsis: Burp-UI api custom inputs module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
import inspect
import flask_restplus.inputs
from flask_restplus.inputs import *  # noqa # pylint: disable=locally-disabled, wildcard-import, unused-wildcard-import
from .my_inputs import boolean  # noqa

ALL = inspect.getmembers(flask_restplus.inputs, inspect.isfunction)
__all__ = [x for x, _ in ALL if not x.startswith('_')] + ['boolean']
