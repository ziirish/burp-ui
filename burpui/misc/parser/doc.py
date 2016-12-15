# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.parser.doc
    :platform: Unix
    :synopsis: Burp-UI parser documentation for Burp1.
.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
from .interface import BUIparser


def __(string):
    """dummy function to fake the translation"""
    return string


class Doc(BUIparser):
    """:class:`burpui.misc.parser.doc.Doc` provides a consistent interface
    to parse burp configuration files.

    It implements :class:`burpui.misc.parser.interface.BUIparser`.
    """
    defaults = {
        u'address': u'',  # IP
        u'atime': False,  # bool
        u'autoupgrade_dir': u'',  # dir
        u'ca_burp_ca': u'',  # file
        u'ca_conf': u'',  # file
        u'ca_name': u'',
        u'ca_server_name': u'',
        u'client_can_delete': True,  # bool
        u'client_can_diff': True,  # bool
        u'client_can_force_backup': True,  # bool
        u'client_can_list': True,  # bool
        u'client_can_restore': True,  # bool
        u'client_can_verify': True,  # bool
        u'client_lockdir': u'',
        u'clientconfdir': u'',  # dir
        u'compression': u'gzip9',
        u'cross_all_filesystems': False,  # bool
        u'cross_filesystem': u'',
        u'daemon': True,  # bool
        u'dedup_group': u'',
        u'directory_tree': True,  # bool
        u'directory': u'',
        u'exclude_comp': u'',  # multi
        u'exclude_ext': u'',  # multi
        u'exclude_fs': u'',  # multi
        u'exclude_regex': u'',  # multi
        u'exclude': u'',  # multi
        u'fork': True,  # bool
        u'group': u'',
        u'hard_quota': u'',
        u'hardlinked_archive': False,  # bool
        u'include_ext': u'',  # multi
        u'include_glob': u'',  # multi
        u'include_regex': u'',  # multi
        u'include': u'',  # multi
        u'keep': [7, 6, 4],  # multi  # int
        u'librsync': True,  # bool
        u'max_children': 5,  # int
        u'max_file_size': u'',
        u'max_hardlinks': 10000,  # int
        u'max_status_children': 5,  # int
        u'max_storage_subdirs': 30000,  # int
        u'min_file_size': u'',
        u'mode': u'',
        u'monitor_browse_cache': False,  # bool
        u'network_timeout': 7200,  # int
        u'nobackup': u'',
        u'notify_failure_arg': u'',  # multi
        u'notify_failure_script': u'',  # file
        u'notify_success_arg': u'',  # multi
        u'notify_success_changes_only': False,  # bool
        u'notify_success_script': u'',  # file
        u'notify_success_warnings_only': False,  # bool
        u'password': u'',
        u'password_check': True,  # bool
        u'path_length_warn': True,  # bool
        u'pidfile': u'',
        u'port': 4971,  # int
        u'protocol': False,  # int
        u'ratelimit': False,  # int
        u'read_all_blockdevs': False,  # bool
        u'read_all_fifos': False,  # bool
        u'read_blockdev': u'',
        u'read_fifo': u'',
        u'restore_client': u'',  # multi
        u'scan_problem_raises_error': False,  # bool
        u'server_script_arg': u'',  # multi
        u'server_script_notify': False,  # bool
        u'server_script_post_arg': u'',  # multi
        u'server_script_post_notify': False,  # bool
        u'server_script_post_run_on_fail': False,  # bool
        u'server_script_post': u'',  # file
        u'server_script_pre_arg': u'',  # multi
        u'server_script_pre_notify': False,  # bool
        u'server_script_pre': u'',  # file
        u'server_script': u'',  # file
        u'soft_quota': u'',
        u'split_vss': False,  # bool
        u'ssl_cert_ca': u'',  # file
        u'ssl_cert': u'',  # file
        u'ssl_ciphers': u'',
        u'ssl_compression': u'zlib5',
        u'ssl_dhfile': u'',  # file
        u'ssl_key_password': u'',
        u'ssl_key': u'',  # file
        u'ssl_peer_cn': u'',
        u'status_address': u'',  # 127.0.0.1 / ::1
        u'status_port': 4972,  # int
        u'stdout': True,  # bool
        u'strip_vss': False,  # bool
        u'syslog': False,  # bool
        u'timer_arg': u'',  # multi
        u'timer_script': u'',  # file
        u'timestamp_format': u'',
        u'umask': u'0022',  # mode
        u'user': u'',
        u'version_warn': True,  # bool
        u'vss_drives': u'',
        u'working_dir_recovery_method': u'',
        u'server_can_restore': False,
    }
    placeholders = {
        u'.': __(u"path or glob"),
        u'atime': u"0|1",
        u'autoupgrade_dir': __(u"path"),
        u'ca_burp_ca': __(u"path"),
        u'ca_conf': __(u"path"),
        u'ca_name': __(u"name"),
        u'ca_server_name': __(u"name"),
        u'client_can_delete': u"0|1",
        u'client_can_force_backup': u"0|1",
        u'client_can_list': u"0|1",
        u'client_can_restore': u"0|1",
        u'client_can_verify': u"0|1",
        u'client_lockdir': __(u"path"),
        u'clientconfdir': __(u"path"),
        u'compression': u"gzip[0-9]",
        u'cross_all_filesystems': u"0|1",
        u'cross_filesystem': __(u"path"),
        u'daemon': u"0|1",
        u'dedup_group': __(u"string"),
        u'directory_tree': u"0|1",
        u'directory': __(u"path"),
        u'exclude_comp': __(u"extension"),
        u'exclude_ext': __(u"extension"),
        u'exclude_fs': __(u"fstype"),
        u'exclude_regex': __(u"regular expression"),
        u'exclude': __(u"path"),
        u'fork': u"0|1",
        u'group': __(u"groupname"),
        u'hard_quota': u"b/Kb/Mb/Gb",
        u'hardlinked_archive': u"0|1",
        u'include_ext': __(u"extension"),
        u'include_regex': __(u"regular expression"),
        u'include': __(u"path"),
        u'include_glob': __(u"glob"),
        u'keep': __(u"number"),
        u'librsync': u"0|1",
        u'lockfile': __(u"path"),
        u'manual_delete': __(u"path"),
        u'max_children': __(u"number"),
        u'max_file_size': u"b/Kb/Mb/Gb",
        u'max_hardlinks': __(u"number"),
        u'max_status_children': __(u"number"),
        u'max_storage_subdirs': __(u"number"),
        u'min_file_size': u"b/Kb/Mb/Gb",
        u'network_timeout': u"s",
        u'nobackup': __(u"file name"),
        u'notify_failure_arg': __(u"string"),
        u'notify_failure_script': __(u"path"),
        u'notify_success_arg': __(u"string"),
        u'notify_success_changes_only': u"0|1",
        u'notify_success_script': __(u"path"),
        u'notify_success_warnings_only': u"0|1",
        u'password': __(u"password"),
        u'password_check': u"0|1",
        u'pidfile': __(u"path"),
        u'port': __(u"port number"),
        u'ratelimit': u"Mb/s",
        u'read_all_blockdevs': u"0|1",
        u'read_all_fifos': u"0|1",
        u'read_blockdev': __(u"path"),
        u'read_fifo': __(u"path"),
        u'restore_client': __(u"client"),
        u'resume_partial': u"0|1",
        u'scan_problem_raises_error': u"0|1",
        u'server_script_arg': __(u"path"),
        u'server_script_notify': u"0|1",
        u'server_script_post_arg': __(u"string"),
        u'server_script_post_notify': u"0|1",
        u'server_script_post_run_on_fail': u"0|1",
        u'server_script_post': __(u"path"),
        u'server_script_pre_arg': __(u"string"),
        u'server_script_pre_notify': u"0|1",
        u'server_script_pre': __(u"path"),
        u'server_script': __(u"path"),
        u'soft_quota': u"b/Kb/Mb/Gb",
        u'ssl_cert_ca': __(u"path"),
        u'ssl_cert_password': __(u"password"),
        u'ssl_cert': __(u"path"),
        u'ssl_ciphers': __(u"cipher list"),
        u'ssl_dhfile': __(u"path"),
        u'ssl_key_password': __(u"password"),
        u'ssl_key': __(u"path"),
        u'ssl_peer_cn': __(u"string"),
        u'status_port': __(u"port number"),
        u'stdout': u"0|1",
        u'strip_vss': u"0|1",
        u'suplit_vss': u"0|1",
        u'syslog': u"0|1",
        u'timer_arg': __(u"string"),
        u'timer_script': __(u"path"),
        u'timestamp_format': __(u"strftime format"),
        u'umask': __(u"umask"),
        u'user': __(u"username"),
        u'version_warn': u"0|1",
        u'vss_drives': __(u"list of drive letters"),
        u'working_dir_recovery_method': u"resume|use|delete",
    }
    values = {
        u'compression': [u'gzip{0}'.format(x) for x in range(0, 10)],
        u'mode': [u'client', u'server'],
        u'ssl_compression': [u'zlib{0}'.format(x) for x in range(0, 10)],
        u'status_address': [u'127.0.0.1', u'::1'],  # 127.0.0.1 / ::1
        u'working_dir_recovery_method': [u'use', u'delete', u'resume'],
    }
    files = [
        u'ca_burp_ca',
        u'ca_conf',
        u'notify_failure_script',
        u'notify_success_script',
        u'server_script_post',
        u'server_script_pre',
        u'server_script',
        u'ssl_cert_ca',
        u'ssl_cert',
        u'ssl_dhfile',
        u'ssl_key',
        u'timer_script',
    ]
    multi_srv = [
        u'exclude_comp',
        u'exclude_ext',
        u'exclude_fs',
        u'exclude_regex',
        u'exclude',
        u'include_ext',
        u'include_glob',
        u'include_regex',
        u'include',
        u'keep',
        u'notify_failure_arg',
        u'notify_success_arg',
        u'restore_client',
        u'server_script_arg',
        u'server_script_post_arg',
        u'server_script_pre_arg',
        u'timer_arg',
    ]
    boolean_srv = [
        u'atime',
        u'client_can_delete',
        u'client_can_diff',
        u'client_can_force_backup',
        u'client_can_list',
        u'client_can_restore',
        u'client_can_verify',
        u'cross_all_filesystems',
        u'daemon',
        u'directory_tree',
        u'fork',
        u'hardlinked_archive',
        u'librsync',
        u'monitor_browse_cache',
        u'notify_success_changes_only',
        u'notify_success_warnings_only',
        u'password_check',
        u'path_length_warn',
        u'read_all_blockdevs',
        u'read_all_fifos',
        u'scan_problem_raises_error',
        u'server_script_notify',
        u'server_script_post_notify',
        u'server_script_post_run_on_fail',
        u'server_script_pre_notify',
        u'split_vss',
        u'stdout',
        u'strip_vss',
        u'syslog',
        u'version_warn',
        u'server_can_restore'
    ]
    integer_srv = [
        u'max_children',
        u'max_hardlinks',
        u'max_status_children',
        u'max_storage_subdirs',
        u'network_timeout',
        u'port',
        u'protocol',
        u'ratelimit',
        u'status_port',
    ]
    string_srv = [
        u'address',
        u'ca_burp_ca',
        u'ca_conf',
        u'ca_name',
        u'ca_server_name',
        u'client_lockdir',
        u'compression',
        u'dedup_group',
        u'directory',
        u'group',
        u'hard_quota',
        u'mode',
        u'notify_failure_script',
        u'notify_success_script',
        u'pidfile',
        u'server_script_post',
        u'server_script_pre',
        u'server_script',
        u'soft_quota',
        u'ssl_cert_ca',
        u'ssl_cert',
        u'ssl_ciphers',
        u'ssl_compression',
        u'ssl_dhfile',
        u'ssl_key_password',
        u'ssl_key',
        u'status_address',
        u'timestamp_format',
        u'umask',
        u'user',
        u'working_dir_recovery_method',
        u'min_file_size',
        u'max_file_size',
        u'cross_filesystem',
        u'nobackup',
        u'read_fifo',
        u'read_blockdev',
        u'vss_drives',
    ]
    fields_cli = [
        u'atime',
        u'client_can_delete',
        u'client_can_force_backup',
        u'client_can_list',
        u'client_can_restore',
        u'client_can_verify',
        u'compression',
        u'cross_all_filesystems',
        u'cross_filesystem',
        u'dedup_group',
        u'directory_tree',
        u'directory',
        u'exclude_comp',
        u'exclude_ext',
        u'exclude_fs',
        u'exclude_regex',
        u'exclude',
        u'hard_quota',
        u'include_ext',
        u'include_regex',
        u'include_glob',
        u'include',
        u'keep',
        u'librsync',
        u'max_file_size',
        u'min_file_size',
        u'nobackup',
        u'notify_failure_arg',
        u'notify_failure_script'
        u'notify_success_arg',
        u'notify_success_script',
        u'notify_success_warnings_only',
        u'password_check',
        u'password',
        u'path_length_warn',
        u'protocol',
        u'read_all_blockdevs',
        u'read_all_fifos',
        u'read_blockdev',
        u'read_fifo',
        u'restore_client',
        u'scan_problem_raises_error',
        u'server_script_arg',
        u'server_script_notify',
        u'server_script_post_arg',
        u'server_script_post_notify',
        u'server_script_post_run_on_fail',
        u'server_script_post',
        u'server_script_pre_arg',
        u'server_script_pre_notify',
        u'server_script_pre',
        u'server_script',
        u'soft_quota',
        u'split_vss',
        u'ssl_peer_cn',
        u'strip_vss',
        u'syslog',
        u'timer_arg',
        u'timer_script',
        u'timestamp_format',
        u'version_warn',
        u'vss_drives',
        u'working_dir_recovery_method',
        u'server_can_restore',
    ]
    string_cli = list(set(string_srv) & set(fields_cli))
    string_cli += [u'ssl_peer_cn', u'password']
    boolean_cli = list(set(boolean_srv) & set(fields_cli))
    integer_cli = list(set(integer_srv) & set(fields_cli))
    multi_cli = list(set(multi_srv) & set(fields_cli))
    doc = {
        u'.': __(u"Read additional configuration files. On Windows, the glob"
                 " is unimplemented - you will need to specify an actual"
                 " file."),
        u'address': __(u"Defines the main TCP address that the server listens"
                       " on. The default is either '::' or '0.0.0.0',"
                       " dependent upon compile time options."),
        u'atime': __(u"This allows you to control whether the client uses"
                     " O_NOATIME when opening files and directories. The"
                     " default is 0, which enables O_NOATIME. This means that"
                     " the client can read files and directories without"
                     " updating the access times. However, this is only"
                     " possible if you are running as root, or are the owner"
                     " of the file or directory. If this is not the case"
                     " (perhaps you only have group or world access to the"
                     " files), you will get errors until you set atime=1."
                     " With atime=1, the access times will be updated on the"
                     " files and directories that get backed up."),
        u'autoupgrade_dir': __(u"Path to autoupgrade directory from which"
                               " upgrades are downloaded. The option can be"
                               " left unset in order not to autoupgrade"
                               " clients. Please see docs/autoupgrade.txt in"
                               " the source package for more help with this"
                               " option."),
        u'ca_burp_ca': __(u"Path to the burp_ca script when using the ca_conf"
                          " option."),
        u'ca_conf': __(u"Path to certificate authority configuration file. The"
                       " CA configuration file will usually be"
                       " /etc/burp/CA.cnf. The CA directory indicated by"
                       " CA.cnf will usually be /etc/burp/CA. If ca_conf is"
                       " set and the CA directory does not exist, the server"
                       " will create, populate it, and the paths indicated by"
                       " ssl_cert_ca, ssl_cert, ssl_key and ssl_dhfile will be"
                       " overwritten. For more detailed information on this"
                       " and the other ca_* options, please see"
                       " docs/burp_ca.txt."),
        u'ca_name': __(u"Name of the CA that the server will generate when"
                       " using the ca_conf option."),
        u'ca_server_name': __(u"The name that the server will put into its own"
                              " SSL certficates when using the ca_conf"
                              " option."),
        u'client_can_delete': __(u"Turn this off to prevent clients from"
                                 " deleting backups with the '-a D' option."
                                 " The default is that clients can delete"
                                 " backups. Restore clients can override this"
                                 " setting."),
        u'client_can_force_backup': __(u"Turn this off to prevent clients from"
                                       " forcing backups with the '-a b'"
                                       " option. Timed backups will still"
                                       " work. The default is that clients can"
                                       " force backups."),
        u'client_can_list': __(u"Turn this off to prevent clients from listing"
                               " backups with the '-a l' option. The default"
                               " is that clients can list backups. Restore"
                               " clients can override this setting."),
        u'client_can_restore': __(u"Turn this off to prevent clients from"
                                  " initiating restores with the '-a r'"
                                  " option. The default is that clients can"
                                  " initiate restores. Restore clients can"
                                  " override this setting."),
        u'client_can_verify': __(u"Turn this off to prevent clients from"
                                 " initiating a verify job with the '-a v'"
                                 " option. The default is that clients can"
                                 " initiate a verify job. Restore clients can"
                                 " override this setting."),
        u'client_lockdir': __(u"Path to the directory in which to keep"
                              " per-client lock files. By default, this is set"
                              " to the path given by the 'directory' option."),
        u'clientconfdir': __(u"Path to the directory that contains client"
                             " configuration files."),
        u'compression': __(u"Choose the level of gzip compression for files"
                           " stored in backups. Setting 0 or gzip0 turns"
                           " compression off. The default is gzip9. This"
                           " option can be overridden by the client"
                           " configuration files in clientconfdir on the"
                           " server."),
        u'cross_all_filesystems': __(u"Allow backups to cross all filesystem"
                                     " mountpoints."),
        u'cross_filesystem': __(u"Allow backups to cross a particular"
                                " filesystem mountpoint."),
        u'daemon': __(u"Whether to daemonise. The default is 1."),
        u'dedup_group': __(u"Enables you to group clients together for file"
                           " deduplication purposes. For example, you might"
                           " want to set 'dedup_group=xp' for each Windows XP"
                           " client, and then run the bedup program on a cron"
                           " job every other day with the option '-g xp'."),
        u'directory_tree': __(u"When turned on (which is the default) and the"
                              " client is on version 1.3.6 or greater, the"
                              " structure of the storage directory will mimic"
                              " that of the original filesystem on the"
                              " client."),
        u'directory': __(u"Path to the directory in which to store backups."),
        u'exclude_comp': __(u"Extensions to exclude from compression. Case"
                            " insensitive. You can have multiple exclude"
                            " compression lines. For example, set 'gz' to"
                            " exclude gzipped files from compression."),
        u'exclude_ext': __(u"Extensions to exclude from the backup. Case"
                           " insensitive. You can have multiple exclude"
                           " extension lines. For example, set 'vdi' to"
                           " exclude VirtualBox disk images."),
        u'exclude_fs': __(u"File systems to exclude from the backup. Case"
                          " insensitive. You can have multiple exclude file"
                          " system lines. For example, set 'tmpfs' to exclude"
                          " tmpfs. Burp has an internal mapping of file system"
                          " names to file system IDs. If you know the file"
                          " system ID, you can use that instead. For example,"
                          " 'exclude_fs = 0x01021994' will also"
                          " exclude tmpfs."),
        u'exclude_regex': __(u"Exclude paths that match the regular"
                             " expression."),
        u'exclude': __(u"Path to exclude from the backup. You can have"
                       " multiple exclude lines. Use forward slashes '/', not"
                       " backslashes '\\' as path delimiters."),
        u'fork': __(u"Whether to fork children. The default is 1."),
        u'group': __(u"Run as a particular group. This can be overridden by"
                     " the client configuration files in clientconfdir on the"
                     " server."),
        u'hard_quota': __(u"Do not back up the client if the estimated size of"
                          " all files is greater than the specified size."
                          " Example: 'hard_quota = 100Gb'. Set to 0 (the"
                          " default) to have no limit."),
        u'hardlinked_archive': __(u"On the server, defines whether to keep"
                                  " hardlinked files in the backups, or"
                                  " whether to generate reverse deltas and"
                                  " delete the original files. Can be set to"
                                  " either 0 (off) or 1 (on). Disadvantage:"
                                  " More disk space will be used Advantage:"
                                  " Restores will be faster, and since no"
                                  " reverse deltas need to be generated, the"
                                  " time and effort the server needs at the"
                                  " end of a backup is reduced."),
        u'include_ext': __(u"Extensions to include in the backup. Case"
                           " insensitive. Nothing else will be included in the"
                           " backup. You can have multiple include extension"
                           " lines. For example, set 'txt' to include files"
                           " that end in '.txt'. You need to specify an"
                           " 'include' line so that burp knows where to start"
                           " looking."),
        u'include_regex': __(u"Not implemented."),
        u'include': __(u"Path to include in the backup. You can have multiple"
                       " include lines. Use forward slashes '/', not"
                       " backslashes '\\' as path delimiters."),
        u'include_glob': __(u"Include paths that match the glob expression."
                            "For example, '/home/*/Documents' will include"
                            " '/home/user1/Documents' and"
                            " '/home/user2/Documents' if directories 'user1'"
                            " and 'user2' exist in '/home'. The Windows"
                            " implementation currently limit the expression to"
                            " contain only one '*'."),
        u'keep': __(u"Number of backups to keep. This can be overridden by the"
                    " client configuration files in clientconfdir on the"
                    " server. Specify multiple 'keep' entries on separate"
                    " lines in order to keep multiple periods of backups. For"
                    " example, assuming that you are doing a backup a day,"
                    " keep=7 keep=4 keep=6 (on separate lines) will keep 7"
                    " daily backups, 4 weekly backups (7x4=28), and 6"
                    " multiples of 4 weeks (7x4x6=168) - roughly 6 monthly"
                    " backups. Effectively, you will be guaranteed to be able"
                    " to restore up to 168 days ago, with the number of"
                    " available backups exponentially decreasing as you go"
                    " back in time to that point. In this example, every 7th"
                    " backup will be hardlinked to allow burp to safely delete"
                    " intermediate backups when necessary. You can have as"
                    " many 'keep' lines as you like, as long as they don't"
                    " exceed 52560000 when multiplied together. That is, a"
                    " backup every minute for 100 years."),
        u'librsync': __(u"When set to 0, delta differencing will not take"
                        " place. That is, when a file changes, the server will"
                        " request the whole new file. The default is 1. This"
                        " option can be overridden by the client configuration"
                        " files in clientconfdir on the server."),
        u'lockfile': __(u"Path to the lockfile that ensures that two server"
                        " processes cannot run simultaneously."),
        u'manual_delete': __(u"If a path is given, the server will move"
                             " directories to be deleted into the directory"
                             " specified by the path, but will not actually"
                             " delete them. The path must be on the same file"
                             " system as the backup storage. The idea is that"
                             " a busy server may be configured to run the"
                             " deletions outside of the backup timebands, when"
                             " the server is less busy, via a cron job. The"
                             " default is unset, which means that the server"
                             " will automatically delete the directories at"
                             " the end of a backup. This option can be"
                             " overridden by the client configuration files in"
                             " clientconfdir on the server."),
        u'max_children': __(u"Defines the number of child processes to fork"
                            " (the number of clients that can simultaneously"
                            " connect. The default is 5."),
        u'max_file_size': __(u"Do not back up files that are greater than the"
                             " specified size. Example: 'max_file_size ="
                             " 10Mb'. Set to 0 (the default) to have no"
                             " limit."),
        u'max_hardlinks': __("On the server, the number of times that a single"
                             " file can be hardlinked. The bedup program also"
                             " obeys this setting. The default is 10000."),
        u'max_status_children': __(u"Defines the number of status child"
                                   " processes to fork (the number of status"
                                   " clients that can simultaneously connect."
                                   " The default is 5."),
        u'max_storage_subdirs': __(u"Defines the number of subdirectories in"
                                   " the data storage areas. The maximum number"
                                   " of subdirectories that ext3 allows is"
                                   " 32000. If you do not set this option, it"
                                   " defaults to 30000."),
        u'min_file_size': __(u"Do not back up files that are less than the"
                             " specified size. Example: 'min_file_size ="
                             " 10Mb'. Set to 0 (the default) to have no"
                             " limit."),
        u'mode': __(u"Required to run in server mode."),
        u'monitor_browse_cache': __(u"Whether or not the server should cache"
                                    " the directory tree when a monitor client"
                                    " is browsing. <br/>Advantage: browsing is"
                                    " faster. </br>Disadvantage: more memory is"
                                    " used."),
        u'network_timeout': __(u"Set the network timeout in seconds. If no"
                               " data is sent or received over a period of"
                               " this length, burp will give up. The default"
                               " is 7200 seconds (2 hours)."),
        u'nobackup': __(u"If this file system entry exists, the directory"
                        " containing it will not be backed up."),
        u'notify_failure_arg': __(u"The same as notify_success_arg, but for"
                                  " backups that failed."),
        u'notify_failure_script': __(u"The same as notify_success_script, but"
                                     " for backups that failed."),
        u'notify_success_arg': __(u"A user-definable argument to the notify"
                                  " success script. You can have many of"
                                  " these. The notify_success_arg options can"
                                  " be overridden by the client configuration"
                                  " files in clientconfdir on the server."),
        u'notify_success_script': __(u"Path to the script to run when a backup"
                                     " succeeds. User arguments are appended"
                                     " after the first five reserved"
                                     " arguments. An example notify script is"
                                     " provided. The notify_success_script"
                                     " option can be overridden by the client"
                                     " configuration files in clientconfdir on"
                                     " the server."),
        u'notify_success_warnings_only': __(u"Set to 1 to send success"
                                            " notifications when there were"
                                            " warnings. If this and"
                                            " notify_success_changes_only are"
                                            " not turned on, success"
                                            " notifications are always sent."),
        u'password': __(u"Defines the password to send to the server."),
        u'password_check': __(u"Allows you to turn client password checking on"
                              " or off. The default is on. SSL certificates"
                              " will still be checked if you turn passwords"
                              " off. This option can be overridden by the"
                              " client configuration files in clientconfdir on"
                              " the server."),
        u'path_length_warn': __(u"When this is on, which is the default, a"
                                " warning will be issued when the client sends"
                                " a path that is too long to replicate in the"
                                " storage area tree structure. The file will"
                                " still be saved in a numbered file outside of"
                                " the tree structure, regardless of the"
                                " setting of this option. This option can be"
                                " overridden by the client configuration files"
                                " in clientconfdir on the server."),
        u'pidfile': __(u"Synonym for lockfile."),
        u'port': __(u"Defines the main TCP port that the server listens on."),
        u'protocol': __(u"Choose which style of backups and restores to use. 0"
                        " (the default) automatically decides based on the"
                        " server version and which protocol is set on the"
                        " server side. 1 forces protocol1 style (file level"
                        " granularity with a pseudo mirrored storage on the"
                        " server and optional rsync). 2 forces protocol2 style"
                        " (inline deduplication with variable length blocks)."
                        " If you choose a forced setting, it will be an error"
                        " if the server also chooses a forced setting."),
        u'ratelimit': __(u"Set the network send rate limit, in Mb/s. If this"
                         " option is not given, burp will send data as fast as"
                         " it can."),
        u'read_all_blockdevs': __(u"Open all block devices for reading and"
                                  " back up the contents as if they were"
                                  " regular files."),
        u'read_all_fifos': __(u"Open all fifos for reading and back up the"
                              " contents as if they were regular files."),
        u'read_blockdev': __(u"Do not back up the given block device itself,"
                             " but open it for reading and back up the"
                             " contents as if it were a regular file."),
        u'read_fifo': __(u"Do not back up the given fifo itself, but open it"
                         " for reading and back up the contents as if it were"
                         " a regular file."),
        u'restore_client': __(u"A client that is permitted to list, verify,"
                              " restore and delete files belonging to any"
                              " other client. You may specify multiple"
                              " restore_clients. If this is too permissive,"
                              " you may set a restore_client for individual"
                              " original clients in the individual"
                              " clientconfdir files. Note that restoring a"
                              " backup from a Windows computer onto a Linux"
                              " computer will currently leave the VSS headers"
                              " in place at the beginning of each file. This"
                              " will be addressed in a future version of"
                              " burp."),
        u'resume_partial': __(u"Turn this on to enable 'resume partial' code."
                              " Requires 'working_dir_recovery_method=resume'."
                              " When resuming an interrupted transfer of a"
                              " single file, it attempts to use previously"
                              " transferred blocks of that file in order to be"
                              " more efficient. However, situations have been"
                              " reported where the file on the server side"
                              " just gets bigger forever, so this feature now"
                              " defaults to being turned off."),
        u'scan_problem_raises_error': __(u"When enabled, this causes problems"
                                         " in the phase1 scan (such as an"
                                         " 'include' being missing) to be"
                                         " treated as fatal errors. The"
                                         " default is off."),
        u'server_script_arg': __(u"Goes with server_script and overrides"
                                 " server_script_pre_arg and"
                                 " server_script_post_arg."),
        u'server_script_notify': __(u"Turn on to send a notification emails"
                                    " when the server pre and post scripts"
                                    " return non-zero. The output of the"
                                    " script will be included it the email."
                                    " The default is off. Requires the"
                                    " notify_failure options to be set."),
        u'server_script_post_arg': __(u"A user-definable argument to the"
                                      " server post script. You can have many"
                                      " of these."),
        u'server_script_post_notify': __(u"Turn on to send a notification"
                                         " email when the server post script"
                                         " returns non-zero. The output of the"
                                         " script will be included in the"
                                         " email. The default is off. Requires"
                                         " the notify_failure options to be"
                                         " set."),
        u'server_script_post_run_on_fail': __(u"If this is set to 1,"
                                              " server_script_post will always"
                                              " be run. The default is 0,"
                                              " which means that if the task"
                                              " asked for by the client fails,"
                                              " server_script_post will not be"
                                              " run."),
        u'server_script_post': __(u"Path to a script to run on the server"
                                  " before the client disconnects. The"
                                  " arguments to it are 'post', '(client"
                                  " command)', '(client name), '(0 or 1 for"
                                  " success or failure)', '(timer script exit"
                                  " code)', and"
                                  " then arguments defined by"
                                  " server_script_post_arg. This command and"
                                  " related options can be overriddden by the"
                                  " client configuration files in"
                                  " clientconfdir on the server."),
        u'server_script_pre_arg': __(u"A user-definable argument to the server"
                                     " pre script. You can have many of"
                                     " these."),
        u'server_script_pre_notify': __(u"Turn on to send a notification email"
                                        " when the server pre script returns"
                                        " non-zero. The output of the script"
                                        " will be included in the email. The"
                                        " default is off. Most people will not"
                                        " want this turned on because clients"
                                        " usually contact the server at 20"
                                        " minute intervals and this could"
                                        " cause a lot of emails to be"
                                        " generated. Requires the"
                                        " notify_failure options to be set."),
        u'server_script_pre': __(u"Path to a script to run on the server after"
                                 " each successfully authenticated connection"
                                 " but before any work is carried out. The"
                                 " arguments to it are 'pre', '(client"
                                 " command)', '(client name)', '(0 or 1 for"
                                 " success or failure)', '(timer script exit"
                                 " code)', and"
                                 " then arguments defined by"
                                 " server_script_pre_arg. If the script"
                                 " returns non-zero, the task asked for by the"
                                 " client will not be run. This command and"
                                 " related options can be overriddden by the"
                                 " client configuration files in clientconfdir"
                                 " on the server."),
        u'server_script': __(u"You can use this to save space in your config"
                             " file when you want to run the same server"
                             " script twice. It overrides server_script_pre"
                             " and server_script_post. This command and"
                             " related options can be overriddden by the"
                             " client configuration files in clientconfdir on"
                             " the server."),
        u'soft_quota': __(u"A warning will be issued when the estimated size"
                          " of all files is greater than the specified size"
                          " and smaller than hard_quota. Example: 'soft_quota"
                          " = 95Gb'. Set to 0 (the default) to have no"
                          " warning."),
        u'split_vss': __(u"When backing up Windows computers with burp"
                         " protocol 1, this option allows you to save the VSS"
                         " header data separate from the file data. The"
                         " default is off, which means that the VSS header"
                         " data is saved prepended to the file data."),
        u'ssl_cert_ca': __(u"The path to the SSL CA certificate. This file"
                           " will probably be the same on both the server and"
                           " the client. The file should contain just the"
                           " certificate in PEM format. For more information"
                           " on this, and the other ssl_* options, please see"
                           " <a href='http://burp.grke.org/docs/burp_ca.html'>"
                           " docs/burp_ca.txt</a>."),
        u'ssl_cert_password': __(u"Synonym for ssl_key_password."),
        u'ssl_cert': __(u"The path to the server SSL certificate. It works for"
                        " me when the file contains the concatenation of the"
                        " certificate and private key in PEM format."),
        u'ssl_ciphers': __(u"Allowed SSL ciphers. See openssl ciphers for"
                           " details."),
        u'ssl_compression': __(u"Choose the level of zlib compression over"
                               " SSL. Setting 0 or zlib0 turnsSSL compression"
                               " off. Setting non-zero gives zlib5 compression"
                               " (it is not currently possible for openssl to"
                               " set any other level). The default is 5."
                               " 'gzip' is a synonym of 'zlib'.is a synonym of"
                               " 'zlib'."),
        u'ssl_dhfile': __(u"Path to Diffie-Hellman parameter file. To generate"
                          " one with openssl, use a command like this: openssl"
                          " dhparam -out dhfile.pem -5 1024"),
        u'ssl_key_password': __(u"The SSL key password."),
        u'ssl_key': __(u"The path to the server SSL private key in PEM"
                       " format."),
        u'status_address': __(u"Defines the main TCP address that the server"
                              " listens on for status requests. The default is"
                              " either '::1' or '127.0.0.1', dependent upon"
                              " compile time options."),
        u'status_port': __(u"Defines the TCP port that the server listens on"
                           " for status requests."),
        u'stdout': __(u"Log to stdout. Defaults to on."),
        u'strip_vss': __(u"When backing up Windows computers with burp"
                         " protocol 1, this option allows you to prevent the"
                         " VSS header data being backed up. The default is"
                         " off. To restore a backup that has no VSS"
                         " information on Windows, you need to give the client"
                         " the '-x' command line option."),
        u'syslog': __(u"Log to syslog. Defaults to off."),
        u'timer_arg': __(u"A user-definable argument to the timer script."
                         "You can have many of these. The timer_arg options"
                         " can be overridden by the client configuration files"
                         " in clientconfdir on the server."),
        u'timer_script': __(u"Path to the script to run when a client connects"
                            " with the timed backup option. If the script"
                            " exits with code 0, a backup will run. The first"
                            " two arguments are the client name and the path"
                            " to the 'current' storage directory. The next"
                            " three arguments are reserved, and user arguments"
                            " are appended after that. An example timer script"
                            " is provided. The timer_script option can be"
                            " overridden by the client configuration files in"
                            " clientconfdir on the server."),
        u'timestamp_format': __(u"This allows you to tweak the format of the"
                                " timestamps of individual backups. See 'man"
                                " strftime' to see available substitutions."
                                " If this option is unset, burp uses"
                                " \"%Y-%m-%d %H:%M:%S\"."),
        u'umask': __(u"Set the file creation umask. Default is 0022."),
        u'user': __(u"Run as a particular user. This can be overridden by the"
                    " client configuration files in clientconfdir on the"
                    " server."),
        u'version_warn': __(u"When this is on, which is the default, a warning"
                            " will be issued when the client version does not"
                            " match the server version. This option can be"
                            " overridden by the client configuration files in"
                            " clientconfdir on the server."),
        u'vss_drives': __(u"When backing up Windows computers, this option"
                          " allows you to specify which drives have VSS"
                          " snapshots taken of them. If you omit this option,"
                          " burp will automatically decide based on the"
                          " 'include' options. If you want no drives to have"
                          " snapshots taken of them, you can specify '0'."),
        u'working_dir_recovery_method': __(u"This option tells the server what"
                                           " to do when it finds the working"
                                           " directory of an interrupted"
                                           " backup (perhaps somebody pulled"
                                           " the plug on the server, or"
                                           " something). This can be"
                                           " overridden by the client"
                                           " configurations files in"
                                           " clientconfdir on the server."
                                           " Options are... <ul><li>delete:"
                                           " Just delete the old working"
                                           " directory.</li><li>use: Convert"
                                           " the working directory into a"
                                           " complete backup.</li><li>resume:"
                                           " Simply continue the previous"
                                           " backup from the point at which it"
                                           " left off, at file granularity."
                                           " NOTE: If the client has changed"
                                           " its include/exclude configuration"
                                           " since the backup was interrupted,"
                                           " the recovery method will"
                                           " automatically switch to 'use'."
                                           " </li></ul>"),
    }
