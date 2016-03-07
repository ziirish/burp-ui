# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.my_fields
    :platform: Unix
    :synopsis: Burp-UI api custom fields module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
import arrow

from flask_restplus import fields
from tzlocal import get_localzone


class DateTime(fields.DateTime):
    """Custom DateTime parser on top of :mod:`arrow` to provide lossless dates"""
    def parse(self, value):
        if value is None:
            return None
        a = arrow.get(value)
        return fields.DateTime.parse(self, a.to(str(get_localzone())).datetime)

    def format(self, value):
        try:
            new_value = self.parse(value)
            if self.dt_format == 'iso8601':
                return new_value.isoformat(' ')
            else:
                return fields.DateTime.format(self, value)
        except (AttributeError, ValueError) as e:
            raise fields.MarshallingError(e)
        except arrow.parser.ParserError as e:
            return value


class BackupNumber(fields.String):
    """Custom BackupNumber field"""
    def format(self, value):
        try:
            return fields.String.format(self, '{0:07d}'.format(int(value)))
        except ValueError as e:
            raise fields.MarshallingError(e)
