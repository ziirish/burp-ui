# -*- coding: utf8 -*-
from .burp1 import Parser as Burp1


# inherit Burp1 parser so we can just override available options
class Parser(Burp1):
    """Extends :class:`burpui.misc.parser.burp1.Parser`"""
    pver = 2

    multi_srv = Burp1.multi_srv + [
        u'label',
    ]
    string_srv = Burp1.string_srv + [
        u'manual_delete',
    ]
    boolean_add = [
        u'acl',
        u'xattr',
        u'server_can_override_includes',
        u'glob_after_script_pre',
    ]
    boolean_add_cli = [
        u'enabled',
    ]
    boolean_srv = Burp1.boolean_srv + boolean_add
    boolean_cli = Burp1.boolean_cli + boolean_add + boolean_add_cli
    multi_cli = Burp1.multi_cli + [
        u'label',
    ]
    integer_cli = Burp1.integer_cli + [
        u'randomise',
    ]
    fields_cli = Burp1.fields_cli + boolean_add + boolean_add_cli + [
        u'randomise',
        u'manual_delete',
        u'label',
    ]
    placeholders = Burp1.placeholders
    placeholders.update({
        u'acl': u"0|1",
        u'xattr': u"0|1",
        u'randomise': u"max secs",
        u'manual_delete': u"path",
        u'label': u"some informations",
        u'server_can_override_includes': u"0|1",
        u'glob_after_script_pre': u"0|1",
        u'enabled': u"0|1",
    })
    defaults = Burp1.defaults
    defaults.update({
        u'acl': True,
        u'xattr': True,
        u'server_can_override_includes': True,
        u'glob_after_script_pre': True,
        u'randomise': 0,
        u'manual_delete': u'',
        u'label': u'',
        u'enabled': True,
    })
    doc = Burp1.doc
    doc.update({
        u'acl': u"If acl support is compiled into burp, this allows you to"
                " decide whether or not to backup acls at runtime. The"
                " default is '1'.",
        u'xattr': u"If xattr support is compiled into burp, this allows you"
                  " to decide whether or not to backup xattrs at runtime."
                  " The default is '1'.",
        u'randomise': u"When running a timed backup, sleep for a random"
                      " number of seconds (between 0 and the number given)"
                      " before contacting the server. Alternatively, this"
                      " can be specified by the '-q' command line option.",
        u'manual_delete': u"This can be overridden by the clientconfdir"
                          " configuration files in clientconfdir on the"
                          " server. When the server needs to delete old"
                          " backups, or rubble left over from generating"
                          " reverse patches with librsync=1, it will"
                          " normally delete them in place. If you use the"
                          " 'manual_delete' option, the files will be moved"
                          " to the path specified for deletion at a later"
                          " point. You will then need to configure a cron"
                          " job, or similar, to delete the files yourself."
                          " Do not specify a path that is not on the same"
                          " filesystem as the client storage directory.",
        u'label': u"You can have multiple labels, and they can be overridden"
                  " in the client configuration files in clientconfdir on"
                  " the server. They will appear as an array of strings in"
                  " the server status monitor JSON output. The idea is to"
                  " provide a mechanism for arbitrary values to be passed"
                  " to clients of the server status monitor.",
        u'server_can_override_includes': u"To prevent the server from being"
                                         " able to override your local"
                                         " include/exclude list, set this"
                                         " to 0. The default is 1.",
        u'glob_after_script_pre': u"Set this to 0 if you do not want"
                                  " include_glob settings to be evaluated"
                                  " after the pre script is run. The default"
                                  " is 1.",
        u'enabled': u"Set this to 0 if you want to disable all clients. The"
                    " default is 1. This option can be overridden per-client"
                    " in the client configuration files in clientconfdir on"
                    " the server.",
    })
