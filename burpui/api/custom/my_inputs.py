# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.my_inputs
    :platform: Unix
    :synopsis: Burp-UI api custom inputs module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
from flask_restplus.inputs import boolean as boolean_ori


def boolean(value):
    """
    Parse the string ``"true"`` or ``"false"`` as a boolean (case insensitive).

    Also accepts ``"1"`` and ``"0"`` as ``True``/``False`` (respectively).

    A form checkbox returns ``"on"`` when checked. This will be treated as
    ``True``.

    If the input is from the request JSON body, the type is already a native
    python boolean, and will be passed through without further parsing.

    :raises ValueError: if the boolean value is invalid
    """
    try:
        return boolean_ori(value)
    except ValueError as e:
        if not value:
            return False
        value = value.lower()
        if value == 'on':
            return True
        raise e
