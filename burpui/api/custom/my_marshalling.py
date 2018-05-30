# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.my_marshalling
    :platform: Unix
    :synopsis: Burp-UI api custom marshalling module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
from flask_restplus.mask import apply as apply_mask
from collections import OrderedDict

from .my_fields import Wildcard


def make(cls):
    if isinstance(cls, type):
        return cls()
    return cls


def marshal(data, fields, envelope=None, skip_none=False, mask=None, ordered=False):
    """Takes raw data (in the form of a dict, list, object) and a dict of
    fields to output and filters the data based on those fields.
    :param data: the actual object(s) from which the fields are taken from
    :param fields: a dict of whose keys will make up the final serialized
                   response output
    :param envelope: optional key that will be used to envelop the serialized
                     response
    :param bool skip_none: optional key will be used to eliminate fields
                           which value is None or the field's key not
                           exist in data
    :param bool ordered: Wether or not to preserve order
    >>> from flask_restplus import fields, marshal
    >>> data = { 'a': 100, 'b': 'foo', 'c': None }
    >>> mfields = { 'a': fields.Raw, 'c': fields.Raw, 'd': fields.Raw }
    >>> marshal(data, mfields)
    {'a': 100, 'c': None, 'd': None}
    >>> marshal(data, mfields, envelope='data')
    {'data': {'a': 100, 'c': None, 'd': None}}
    >>> marshal(data, mfields, skip_none=True)
    {'a': 100}
    >>> marshal(data, mfields, ordered=True)
    OrderedDict([('a', 100), ('c', None), ('d', None)])
    >>> marshal(data, mfields, envelope='data', ordered=True)
    OrderedDict([('data', OrderedDict([('a', 100), ('c', None), ('d', None)]))])
    >>> marshal(data, mfields, skip_none=True, ordered=True)
    OrderedDict([('a', 100)])
    """
    out, has_wildcards = _marshal(data, fields, envelope, skip_none, mask, ordered)

    if has_wildcards:
        mask = mask or getattr(fields, '__mask__', None)
        fields = getattr(fields, 'resolved', fields)
        if mask:
            fields = apply_mask(fields, mask, skip=True)

        wild_items = []
        keys = []
        for dkey, val in fields.items():
            key = dkey
            if isinstance(val, dict):
                value = marshal(data, val, skip_none=skip_none, ordered=ordered)
            else:
                field = make(val)
                # exclude already parsed keys from the wildcard
                is_wildcard = isinstance(field, Wildcard)
                if is_wildcard:
                    field.reset()
                    if keys:
                        field.exclude |= set(keys)
                        keys = []
                value = field.output(dkey, data, ordered=ordered)
                if is_wildcard:

                    def _append(k, v):
                        if skip_none and (v is None or v == OrderedDict() or v == {}):
                            return
                        wild_items.append((k, v))

                    key = field.key or key
                    _append(key, value)
                    while True:
                        value = field.output(dkey, data, ordered=ordered)
                        if value is None or \
                                value == field.container.format(field.default):
                            break
                        key = field.key
                        _append(key, value)
                    continue

            keys.append(key)
            if skip_none and (value is None or value == OrderedDict() or value == {}):
                continue
            wild_items.append((key, value))

        items = tuple(wild_items)

        out = OrderedDict(items) if ordered else dict(items)

        if envelope:
            out = OrderedDict([(envelope, out)]) if ordered else {envelope: out}

        return out

    return out


def _marshal(data, fields, envelope=None, skip_none=False, mask=None, ordered=False):
    """Takes raw data (in the form of a dict, list, object) and a dict of
    fields to output and filters the data based on those fields.
    :param data: the actual object(s) from which the fields are taken from
    :param fields: a dict of whose keys will make up the final serialized
                   response output
    :param envelope: optional key that will be used to envelop the serialized
                     response
    :param bool skip_none: optional key will be used to eliminate fields
                           which value is None or the field's key not
                           exist in data
    :param bool ordered: Wether or not to preserve order
    >>> from flask_restplus import fields, marshal
    >>> data = { 'a': 100, 'b': 'foo', 'c': None }
    >>> mfields = { 'a': fields.Raw, 'c': fields.Raw, 'd': fields.Raw }
    >>> marshal(data, mfields)
    {'a': 100, 'c': None, 'd': None}
    >>> marshal(data, mfields, envelope='data')
    {'data': {'a': 100, 'c': None, 'd': None}}
    >>> marshal(data, mfields, skip_none=True)
    {'a': 100}
    >>> marshal(data, mfields, ordered=True)
    OrderedDict([('a', 100), ('c', None), ('d', None)])
    >>> marshal(data, mfields, envelope='data', ordered=True)
    OrderedDict([('data', OrderedDict([('a', 100), ('c', None), ('d', None)]))])
    >>> marshal(data, mfields, skip_none=True, ordered=True)
    OrderedDict([('a', 100)])
    """
    mask = mask or getattr(fields, '__mask__', None)
    fields = getattr(fields, 'resolved', fields)
    if mask:
        fields = apply_mask(fields, mask, skip=True)

    if isinstance(data, (list, tuple)):
        out = [marshal(d, fields, skip_none=skip_none, ordered=ordered) for d in data]
        if envelope:
            out = OrderedDict([(envelope, out)]) if ordered else {envelope: out}
        return out, False

    has_wildcards = {'present': False}

    def __format_field(key, val):
        field = make(val)
        if isinstance(field, Wildcard):
            has_wildcards['present'] = True
        value = field.output(key, data, ordered=ordered)
        return (key, value)

    items = (
        (k, marshal(data, v, skip_none=skip_none, ordered=ordered))
        if isinstance(v, dict)
        else __format_field(k, v)
        for k, v in fields.items()
    )

    if skip_none:
        items = ((k, v) for k, v in items
                 if v is not None and v != OrderedDict() and v != {})

    out = OrderedDict(items) if ordered else dict(items)

    if envelope:
        out = OrderedDict([(envelope, out)]) if ordered else {envelope: out}

    return out, has_wildcards['present']
