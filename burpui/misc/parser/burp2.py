# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.parser.burp2
    :platform: Unix
    :synopsis: Burp-UI configuration file parser for Burp2.
.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
from .burp1 import Parser as Burp1


def __(string):
    """dummy function to fake the translation"""
    return string


# inherit Burp1 parser so we can just override available options
class Parser(Burp1):
    """Extends :class:`burpui.misc.parser.burp1.Parser`"""
    pver = 2

    pair_srv = [
        u'port',
        u'max_children',
        u'status_port',
        u'max_status_children',
    ]
    pair_associations = {
        u'port': u'max_children',
        u'max_children': u'port',
        u'status_port': u'max_status_children',
        u'max_status_children': u'status_port',
    }
    integer_srv = Burp1.integer_srv
    for rem in ['port', 'max_children', 'status_port', 'max_status_children']:
        integer_srv.remove(rem)
    advanced_type = Burp1.advanced_type
    advanced_type.update({
        u'port': u'integer',
        u'max_children': u'integer',
        u'status_port': u'integer',
        u'max_status_children': u'integer',
    })
    multi_srv = Burp1.multi_srv + [
        u'label',
    ]
    string_srv = Burp1.string_srv + [
        u'manual_delete',
        u'rblk_memory_max',
    ]
    boolean_add = [
        u'acl',
        u'xattr',
        u'glob_after_script_pre',
        u'cname_fqdn',
        u'cname_lowercase',
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
        u'randomise': __(u"max secs"),
        u'manual_delete': __(u"path"),
        u'label': __(u"some informations"),
        u'status_address': __(u"address|localhost"),
        u'glob_after_script_pre': u"0|1",
        u'enabled': u"0|1",
        u'cname_fqdn': u"0|1",
        u'cname_lowercase': u"0|1",
        u'rblk_memory_max': u"b/Kb/Mb/Gb",
    })
    values = Burp1.values
    # status_address can now listen on any address
    del values['status_address']
    defaults = Burp1.defaults
    defaults.update({
        u'acl': True,
        u'xattr': True,
        u'glob_after_script_pre': True,
        u'randomise': 0,
        u'manual_delete': u'',
        u'label': u'',
        u'enabled': True,
        u'cname_fqdn': True,
        u'cname_lowercase': False,
        u'rblk_memory_max': u'256Mb',
    })
    doc = Burp1.doc
    doc.update({
        u'acl': __(u"If acl support is compiled into burp, this allows you to"
                   " decide whether or not to backup acls at runtime. The"
                   " default is '1'."),
        u'xattr': __(u"If xattr support is compiled into burp, this allows you"
                     " to decide whether or not to backup xattrs at runtime."
                     " The default is '1'."),
        u'randomise': __(u"When running a timed backup, sleep for a random"
                         " number of seconds (between 0 and the number given)"
                         " before contacting the server. Alternatively, this"
                         " can be specified by the '-q' command line option."),
        u'manual_delete': __(u"This can be overridden by the clientconfdir"
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
                             " filesystem as the client storage directory."),
        u'label': __(u"You can have multiple labels, and they can be"
                     " overridden in the client configuration files in"
                     " clientconfdir on the server. They will appear as an"
                     " array of strings in the server status monitor JSON"
                     " output. The idea is to provide a mechanism for"
                     " arbitrary values to be passed to clients of the server"
                     " status monitor."),
        u'status_address': __(u"Defines the main TCP address that the server "
                              "listens on for status requests. The default  "
                              "is  special  value  'localhost'  that includes "
                              "both '::1' (if available) and '127.0.0.1' "
                              "(always)."),
        u'glob_after_script_pre': __(u"Set this to 0 if you do not want"
                                     " include_glob settings to be evaluated"
                                     " after the pre script is run. The"
                                     " default is 1."),
        u'enabled': __(u"Set this to 0 if you want to disable all clients. The"
                       " default is 1. This option can be overridden"
                       " per-client in the client configuration files in"
                       " clientconfdir on the server."),
        u'cname_fqdn': __(u"Whether to keep fqdn cname (like"
                          " 'testclient.example.com') when looking-up in"
                          " clientconfdir. This also affects the fqdn lookup"
                          " on the client (see client configuration options"
                          " for details). The default is 1. When set to 0, the"
                          " fqdn provided by the client while authenticating"
                          " will be stripped ('testclient.example.com'"
                          " becomes 'testclient')."),
        u'cname_lowercase': __(u"Whether to force lowercase cname when"
                               " looking-up in clientconfdir. This also"
                               " affects the fqdn lookup on the client (see"
                               " client configuration options for details)."
                               " The default is 0. When set to 1 the name"
                               " provided by the client while authenticating"
                               " will be lowercased."),
        u'port': __(u"Defines the main TCP port that the server listens on. "
                    "Specify multiple 'port' entries on separate lines in "
                    "order to listen on multiple ports. Each port can be "
                    "configured with its own 'max_children' value."),
        u'max_children': __(u"Defines the number of child processes to fork "
                            "(the number of clients that can simultaneously "
                            "connect. The default is 5. Specify multiple "
                            "'max_children' entries on separate lines if you "
                            "have configured multiple port entries."),
        u'status_port': __(u"Defines the TCP port that the server listens on "
                           "for status requests. Comment this out to have no "
                           "status server. Specify multiple 'status_port' "
                           "entries on separate lines in order to listen on "
                           "multiple ports. Each port can be configured with "
                           "its own 'max_status_children' value."),
        u'max_status_children': __(u"Defines the number of status child "
                                   "processes to fork (the number of status "
                                   "clients that can simultaneously connect. "
                                   "The default is 5. Specify multiple "
                                   "'max_status_children' entries on separate "
                                   "lines if you have configured multiple "
                                   "status_port entries."),
        u'rblk_memory_max': __("The maximum amount of data from the disk "
                               "cached in server memory during a protocol2 "
                               "restore/verify. The default is 256Mb. This "
                               "option can be overriden per-client in the "
                               "client configuration files in clientconfdir "
                               "on the server."),
    })
