# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.my_marshalling
    :platform: Unix
    :synopsis: Burp-UI api custom marshalling module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>


"""
from flask_restplus.mask import apply as apply_mask
from flask_restplus._compat import OrderedDict

from .my_fields import Wildcard


def marshal(data, fields, envelope=None, mask=None):
    """Takes raw data (in the form of a dict, list, object) and a dict of
    fields to output and filters the data based on those fields.
    :param data: the actual object(s) from which the fields are taken from
    :param fields: a dict of whose keys will make up the final serialized
                   response output
    :param envelope: optional key that will be used to envelop the serialized
                     response
    >>> from flask_restplus import fields, marshal
    >>> data = { 'a': 100, 'b': 'foo' }
    >>> mfields = { 'a': fields.Raw }
    >>> marshal(data, mfields)
    OrderedDict([('a', 100)])
    >>> marshal(data, mfields, envelope='data')
    OrderedDict([('data', OrderedDict([('a', 100)]))])
    """

    def make(cls):
        if isinstance(cls, type):
            return cls()
        return cls

    mask = mask or getattr(fields, '__mask__', None)
    fields = getattr(fields, 'resolved', fields)
    if mask:
        fields = apply_mask(fields, mask, skip=True)

    if isinstance(data, (list, tuple)):
        out = [marshal(d, fields) for d in data]
        if envelope:
            out = OrderedDict([(envelope, out)])
        return out

    items = []
    keys = []
    for dkey, val in fields.items():
        key = dkey
        if isinstance(val, dict):
            value = marshal(data, val)
        else:
            field = make(val)
            # exclude already parsed keys from the wildcard
            if isinstance(field, Wildcard):
                for tmp in keys:
                    if tmp not in field.exclude:
                        field.exclude.append(tmp)
                keys = []
            value = field.output(dkey, data)
            if isinstance(field, Wildcard):
                key = field.key or dkey
                items.append((key, value))
                while True:
                    value = field.output(dkey, data)
                    if value is None:
                        break
                    key = field.key
                    items.append((key, value))
                continue
        keys.append(key)
        items.append((key, value))
    items = tuple(items)

    out = OrderedDict(items)

    if envelope:
        out = OrderedDict([(envelope, out)])

    return out
