# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.my_fields
    :platform: Unix
    :synopsis: Burp-UI api custom fields module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
import re
import datetime
import inspect
import arrow
import fnmatch

from ...ext.i18n import get_locale

from flask_restplus import fields
from flask_babel import gettext as _
from flask import escape
from tzlocal import get_localzone

TZ = str(get_localzone())


class DateTime(fields.DateTime):
    """Custom DateTime parser on top of :mod:`arrow` to provide lossless dates"""
    def parse(self, value):
        """Parse the value"""
        if value is None:
            return None
        try:
            value = float(value)
            a = arrow.get(datetime.datetime.utcfromtimestamp(value))
            a = a.replace(tzinfo=TZ)
        except (ValueError, TypeError):
            a = arrow.get(value)
            a = a.to(TZ)
        return fields.DateTime.parse(self, a.datetime)

    def format(self, value):
        """Format the value"""
        try:
            new_value = self.parse(value)
            if not new_value:
                return value
            if self.dt_format == 'iso8601':
                return new_value.isoformat()
            else:
                return fields.DateTime.format(self, value)
        except (AttributeError, ValueError) as e:
            raise fields.MarshallingError(e)
        except arrow.parser.ParserError as e:
            return _(str(value))


class DateTimeHuman(fields.Raw):
    """Custom parser to display human readable times (like '1 hour ago')"""
    def parse(self, value):
        """Parse the value"""
        if value is None:
            return None
        try:
            return arrow.get(value)
        except arrow.parser.ParserError:
            return None

    def format(self, value):
        """Format the value"""
        new_value = self.parse(value)
        if new_value:
            locale = get_locale()
            return new_value.humanize(locale=locale)
        return _(str(value))


class BackupNumber(fields.String):
    """Custom BackupNumber field"""
    def format(self, value):
        """Format the value"""
        try:
            return fields.String.format(self, '{0:07d}'.format(int(value)))
        except ValueError as e:
            raise fields.MarshallingError(e)


class SafeString(fields.String):
    """Custom SafeString field to encode HTML entities"""
    def format(self, value):
        """Format the value"""
        return fields.String.format(self, escape(value))


class LocalizedString(fields.String):
    """Custom LocalizedString to return localized strings"""
    def format(self, value):
        """Format the value"""
        return fields.String.format(self, _(value))


class Wildcard(fields.List):
    exclude = []
    _exclude = ['__dict__', '__doc__', '__module__', '__weakref__']
    # keep a track of the last object
    _idx = 0
    # cache the flat object
    _flat = None
    _obj = None
    _cache = []
    _last = None

    def _flatten(self, obj):
        if obj == self._obj and self._flat:
            return self._flat
        if isinstance(obj, dict):
            self._flat = obj.items()
        else:
            self._flat.extend(inspect.getmembers(obj, match_attributes))

        self._idx = 0
        self._cache = []
        self._obj = obj
        return self._flat

    @property
    def key(self):
        return self._last

    def output(self, key, obj):
        flat = self._flatten(obj)
        value = None
        reg = fnmatch.translate(key)

        for idx, (objkey, val) in enumerate(flat):
            if idx < self._idx:
                continue
            if objkey not in self._cache and \
                    objkey not in self.exclude and \
                    re.match(reg, objkey, re.IGNORECASE):
                value = val
                self._cache.append(objkey)
                self._last = objkey
                self._idx = idx
                break

        if value is None:
            if self.default is not None:
                return self.default
            return None

        return self.container.format(value)


def match_attributes(attr):
    return not(inspect.isroutine(attr) or
               (attr.__name__.startswith('__') and
                attr.__name__.endswith('__')))
