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
        except arrow.parser.ParserError:
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


class Wildcard(fields.Raw):
    exclude = set()
    # cache the flat object
    _flat = None
    _obj = None
    _cache = set()
    _last = None

    def __init__(self, cls_or_instance, **kwargs):
        super(Wildcard, self).__init__(**kwargs)
        error_msg = 'The type of the wildcard elements must be a subclass of fields.Raw'
        if isinstance(cls_or_instance, type):
            if not issubclass(cls_or_instance, fields.Raw):
                raise fields.MarshallingError(error_msg)
            self.container = cls_or_instance()
        else:
            if not isinstance(cls_or_instance, fields.Raw):
                raise fields.MarshallingError(error_msg)
            self.container = cls_or_instance

    def _flatten(self, obj):
        if obj is None:
            return None
        if obj == self._obj and self._flat is not None:
            return self._flat
        if isinstance(obj, dict):
            # self._flat needs to implement pop()
            self._flat = [x for x in obj.items()]
        else:

            def __match_attributes(attribute):
                attr_name, attr_obj = attribute
                if inspect.isroutine(attr_obj) or \
                        (attr_name.startswith('__') and attr_name.endswith('__')):
                    return False
                return True

            attributes = inspect.getmembers(obj)
            self._flat = [x for x in attributes if __match_attributes(x)]

        self._cache = set()
        self._obj = obj
        return self._flat

    @property
    def key(self):
        return self._last

    def reset(self):
        self.exclude = set()
        self._flat = None
        self._obj = None
        self._cache = set()
        self._last = None

    def output(self, key, obj, ordered=False, **kwargs):
        value = None
        reg = fnmatch.translate(key)

        if self._flatten(obj):
            while True:
                try:
                    # we are using pop() so that we don't
                    # loop over the whole object every time dropping the
                    # complexity to O(n)
                    (objkey, val) = self._flat.pop()
                    if objkey not in self._cache and \
                            objkey not in self.exclude and \
                            re.match(reg, objkey, re.IGNORECASE):
                        value = val
                        self._cache.add(objkey)
                        self._last = objkey
                        break
                except IndexError:
                    break

        if value is None:
            if self.default is not None:
                return self.container.format(self.default)
            return None

        return self.container.format(value)

    def schema(self):
        schema = super(Wildcard, self).schema()
        schema['type'] = 'object'
        schema['additionalProperties'] = self.container.__schema__
        return schema

    def clone(self, mask=None):
        kwargs = self.__dict__.copy()
        model = kwargs.pop('container')
        if mask:
            model = mask.apply(model)
        return self.__class__(model, **kwargs)
