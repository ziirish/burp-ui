# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.my_fields2
    :platform: Unix
    :synopsis: Burp-UI api custom fields module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
from flask_restplus import fields
from .my_marshalling import marshal


class Nested(fields.Nested):
    def output(self, key, obj):
        value = fields.get_value(key if self.attribute is None else self.attribute, obj)
        if value is None:
            if self.allow_null:
                return None
            elif self.default is not None:
                return self.default

        return marshal(value, self.nested)
