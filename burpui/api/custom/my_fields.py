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

TZ = str(get_localzone())


class DateTime(fields.DateTime):
    """Custom DateTime parser on top of :mod:`arrow` to provide lossless dates"""
    def parse(self, value):
        """Parse the value"""
        if value is None:
            return None
        a = arrow.get(value)
        return fields.DateTime.parse(self, a.to(TZ).datetime)

    def format(self, value):
        """Format the value"""
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


class DateTimeHuman(fields.Raw):
    """Custom parser to display human readable times (like '1 hour ago')"""
    def parse(self, value):
        """Parse the value"""
        if value is None:
            return None
        try:
            return arrow.get(value).to(TZ)
        except arrow.parser.ParserError:
            return None

    def format(self, value):
        """Format the value"""
        new_value = self.parse(value)
        if new_value:
            return new_value.humanize()
        return value


class BackupNumber(fields.String):
    """Custom BackupNumber field"""
    def format(self, value):
        """Format the value"""
        try:
            return fields.String.format(self, '{0:07d}'.format(int(value)))
        except ValueError as e:
            raise fields.MarshallingError(e)
