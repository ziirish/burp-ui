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
    integer_cli = Burp1.integer_cli + [
        u'randomise',
    ]
    fields_cli = Burp1.fields_cli + [
        u'acl',
        u'xattr',
        u'randomise',
    ]
    placeholders = Burp1.placeholders
    placeholders.update({
        u'acl': u"0|1",
        u'xattr': u"0|1",
        u'randomise': u"max secs",
    })
    defaults = Burp1.defaults
    defaults.update({
        u'acl': True,
        u'xattr': True,
        u'randomise': 0,
    })
    doc = Burp1.doc
    doc.update({
        u'acl': "If acl support is compiled into burp, this allows you to" +
                " decide whether or not to backup acls at runtime. The" +
                " default is '1'.",
        u'xattr': "If xattr support is compiled into burp, this allows you" +
                  " to decide whether or not to backup xattrs at runtime." +
                  " The default is '1'.",
        u'randomise': "When running a timed backup, sleep for a random" +
                      " number of seconds (between 0 and the number given)" +
                      " before contacting the server. Alternatively, this" +
                      " can be specified by the '-q' command line option.",
    })
