# -*- coding: utf8 -*-
from .burp1 import Parser as Burp1


# inherit Burp1 parser so we can just override available options
class Parser(Burp1):
    """Implements :class:`burpui.misc.parser.burp1.Parser`"""
    pver = 2

    boolean_srv = Burp1.boolean_srv + [
        u'acl',
        u'xattr',
    ]
    fields_cli = Burp1.fields_cli + [
        u'acl',
        u'xattr',
    ]
    placeholders = Burp1.placeholders
    placeholders.update({
        u'acl': u"0|1",
        u'xattr': u"0|1",
    })
