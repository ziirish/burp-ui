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
        "address": "",  # IP
        "atime": False,  # bool
        "autoupgrade_dir": "",  # dir
        "ca_burp_ca": "",  # file
        "ca_conf": "",  # file
        "ca_name": "",
        "ca_server_name": "",
        "client_can_delete": True,  # bool
        "client_can_diff": True,  # bool
        "client_can_force_backup": True,  # bool
        "client_can_list": True,  # bool
        "client_can_restore": True,  # bool
        "client_can_verify": True,  # bool
        "client_lockdir": "",
        "clientconfdir": "",  # dir
        "compression": "gzip9",
        "cross_all_filesystems": False,  # bool
        "cross_filesystem": "",
        "daemon": True,  # bool
        "dedup_group": "",
        "directory_tree": True,  # bool
        "directory": "",
        "exclude_comp": "",  # multi
        "exclude_ext": "",  # multi
        "exclude_fs": "",  # multi
        "exclude_regex": "",  # multi
        "exclude": "",  # multi
        "fork": True,  # bool
        "group": "",
        "hard_quota": "",
        "hardlinked_archive": False,  # bool
        "include_ext": "",  # multi
        "include_glob": "",  # multi
        "include_regex": "",  # multi
        "include": "",  # multi
        "keep": [7, 6, 4],  # multi  # int
        "librsync": True,  # bool
        "max_children": 5,  # int
        "max_file_size": "",
        "max_hardlinks": 10000,  # int
        "max_status_children": 5,  # int
        "max_storage_subdirs": 30000,  # int
        "min_file_size": "",
        "mode": "",
        "monitor_browse_cache": False,  # bool
        "network_timeout": 7200,  # int
        "nobackup": "",
        "notify_failure_arg": "",  # multi
        "notify_failure_script": "",  # file
        "notify_success_arg": "",  # multi
        "notify_success_changes_only": False,  # bool
        "notify_success_script": "",  # file
        "notify_success_warnings_only": False,  # bool
        "password": "",
        "password_check": True,  # bool
        "path_length_warn": True,  # bool
        "pidfile": "",
        "port": 4971,  # int
        "protocol": False,  # int
        "ratelimit": False,  # int
        "read_all_blockdevs": False,  # bool
        "read_all_fifos": False,  # bool
        "read_blockdev": "",
        "read_fifo": "",
        "restore_client": "",  # multi
        "scan_problem_raises_error": False,  # bool
        "server_script_arg": "",  # multi
        "server_script_notify": False,  # bool
        "server_script_post_arg": "",  # multi
        "server_script_post_notify": False,  # bool
        "server_script_post_run_on_fail": False,  # bool
        "server_script_post": "",  # file
        "server_script_pre_arg": "",  # multi
        "server_script_pre_notify": False,  # bool
        "server_script_pre": "",  # file
        "server_script": "",  # file
        "soft_quota": "",
        "split_vss": False,  # bool
        "ssl_cert_ca": "",  # file
        "ssl_cert": "",  # file
        "ssl_ciphers": "",
        "ssl_compression": "zlib5",
        "ssl_dhfile": "",  # file
        "ssl_key_password": "",
        "ssl_key": "",  # file
        "ssl_peer_cn": "",
        "status_address": "",  # 127.0.0.1 / ::1
        "status_port": 4972,  # int
        "stdout": True,  # bool
        "strip_vss": False,  # bool
        "syslog": False,  # bool
        "timer_arg": "",  # multi
        "timer_script": "",  # file
        "timestamp_format": "",
        "umask": "0022",  # mode
        "user": "",
        "version_warn": True,  # bool
        "vss_drives": "",
        "working_dir_recovery_method": "",
        "server_can_restore": False,
    }
    placeholders = {
        ".": __("path or glob"),
        "address": __("address"),
        "atime": "0|1",
        "autoupgrade_dir": __("path"),
        "ca_burp_ca": __("path"),
        "ca_conf": __("path"),
        "ca_name": __("name"),
        "ca_server_name": __("name"),
        "client_can_delete": "0|1",
        "client_can_force_backup": "0|1",
        "client_can_list": "0|1",
        "client_can_restore": "0|1",
        "client_can_verify": "0|1",
        "client_lockdir": __("path"),
        "clientconfdir": __("path"),
        "compression": "gzip[0-9]",
        "cross_all_filesystems": "0|1",
        "cross_filesystem": __("path"),
        "daemon": "0|1",
        "dedup_group": __("string"),
        "directory_tree": "0|1",
        "directory": __("path"),
        "exclude_comp": __("extension"),
        "exclude_ext": __("extension"),
        "exclude_fs": __("fstype"),
        "exclude_regex": __("regular expression"),
        "exclude": __("path"),
        "fork": "0|1",
        "group": __("groupname"),
        "hard_quota": "b/Kb/Mb/Gb",
        "hardlinked_archive": "0|1",
        "include_ext": __("extension"),
        "include_regex": __("regular expression"),
        "include": __("path"),
        "include_glob": __("glob"),
        "keep": __("number"),
        "librsync": "0|1",
        "lockfile": __("path"),
        "manual_delete": __("path"),
        "max_children": __("number"),
        "max_file_size": "b/Kb/Mb/Gb",
        "max_hardlinks": __("number"),
        "max_status_children": __("number"),
        "max_storage_subdirs": __("number"),
        "min_file_size": "b/Kb/Mb/Gb",
        "network_timeout": "s",
        "nobackup": __("file name"),
        "notify_failure_arg": __("string"),
        "notify_failure_script": __("path"),
        "notify_success_arg": __("string"),
        "notify_success_changes_only": "0|1",
        "notify_success_script": __("path"),
        "notify_success_warnings_only": "0|1",
        "password": __("password"),
        "password_check": "0|1",
        "pidfile": __("path"),
        "port": __("port number"),
        "ratelimit": "Mb/s",
        "read_all_blockdevs": "0|1",
        "read_all_fifos": "0|1",
        "read_blockdev": __("path"),
        "read_fifo": __("path"),
        "restore_client": __("client"),
        "resume_partial": "0|1",
        "scan_problem_raises_error": "0|1",
        "server_script_arg": __("path"),
        "server_script_notify": "0|1",
        "server_script_post_arg": __("string"),
        "server_script_post_notify": "0|1",
        "server_script_post_run_on_fail": "0|1",
        "server_script_post": __("path"),
        "server_script_pre_arg": __("string"),
        "server_script_pre_notify": "0|1",
        "server_script_pre": __("path"),
        "server_script": __("path"),
        "soft_quota": "b/Kb/Mb/Gb",
        "ssl_cert_ca": __("path"),
        "ssl_cert_password": __("password"),
        "ssl_cert": __("path"),
        "ssl_ciphers": __("cipher list"),
        "ssl_dhfile": __("path"),
        "ssl_key_password": __("password"),
        "ssl_key": __("path"),
        "ssl_peer_cn": __("string"),
        "status_port": __("port number"),
        "stdout": "0|1",
        "strip_vss": "0|1",
        "suplit_vss": "0|1",
        "syslog": "0|1",
        "timer_arg": __("string"),
        "timer_script": __("path"),
        "timestamp_format": __("strftime format"),
        "umask": __("umask"),
        "user": __("username"),
        "version_warn": "0|1",
        "vss_drives": __("list of drive letters"),
        "working_dir_recovery_method": "resume|use|delete",
    }
    values = {
        "compression": ["gzip{0}".format(x) for x in range(0, 10)],
        "mode": ["client", "server"],
        "ssl_compression": ["zlib{0}".format(x) for x in range(0, 10)],
        "status_address": ["127.0.0.1", "::1"],  # 127.0.0.1 / ::1
        "working_dir_recovery_method": ["use", "delete", "resume"],
    }
    files = [
        "ca_burp_ca",
        "ca_conf",
        "notify_failure_script",
        "notify_success_script",
        "server_script_post",
        "server_script_pre",
        "server_script",
        "ssl_cert_ca",
        "ssl_cert",
        "ssl_dhfile",
        "ssl_key",
        "timer_script",
    ]
    advanced_type = {
        "keep": "integer",
    }
    pair_srv = []
    pair_associations = {}
    multi_srv = [
        "exclude_comp",
        "exclude_ext",
        "exclude_fs",
        "exclude_regex",
        "exclude",
        "include_ext",
        "include_glob",
        "include_regex",
        "include",
        "keep",
        "notify_failure_arg",
        "notify_success_arg",
        "restore_client",
        "server_script_arg",
        "server_script_post_arg",
        "server_script_pre_arg",
        "timer_arg",
    ]
    boolean_srv = [
        "atime",
        "client_can_delete",
        "client_can_diff",
        "client_can_force_backup",
        "client_can_list",
        "client_can_restore",
        "client_can_verify",
        "cross_all_filesystems",
        "daemon",
        "directory_tree",
        "fork",
        "hardlinked_archive",
        "librsync",
        "monitor_browse_cache",
        "notify_success_changes_only",
        "notify_success_warnings_only",
        "password_check",
        "path_length_warn",
        "read_all_blockdevs",
        "read_all_fifos",
        "scan_problem_raises_error",
        "server_script_notify",
        "server_script_post_notify",
        "server_script_post_run_on_fail",
        "server_script_pre_notify",
        "split_vss",
        "stdout",
        "strip_vss",
        "syslog",
        "version_warn",
        "server_can_restore",
    ]
    integer_srv = [
        "max_children",
        "max_hardlinks",
        "max_status_children",
        "max_storage_subdirs",
        "network_timeout",
        "port",
        "protocol",
        "ratelimit",
        "status_port",
    ]
    string_srv = [
        "address",
        "ca_burp_ca",
        "ca_conf",
        "ca_name",
        "ca_server_name",
        "client_lockdir",
        "compression",
        "dedup_group",
        "directory",
        "group",
        "hard_quota",
        "mode",
        "notify_failure_script",
        "notify_success_script",
        "pidfile",
        "server_script_post",
        "server_script_pre",
        "server_script",
        "soft_quota",
        "ssl_cert_ca",
        "ssl_cert",
        "ssl_ciphers",
        "ssl_compression",
        "ssl_dhfile",
        "ssl_key_password",
        "ssl_key",
        "status_address",
        "timestamp_format",
        "umask",
        "user",
        "working_dir_recovery_method",
        "min_file_size",
        "max_file_size",
        "cross_filesystem",
        "nobackup",
        "read_fifo",
        "read_blockdev",
        "vss_drives",
    ]
    fields_cli = [
        "atime",
        "client_can_delete",
        "client_can_force_backup",
        "client_can_list",
        "client_can_restore",
        "client_can_verify",
        "compression",
        "cross_all_filesystems",
        "cross_filesystem",
        "dedup_group",
        "directory_tree",
        "directory",
        "exclude_comp",
        "exclude_ext",
        "exclude_fs",
        "exclude_regex",
        "exclude",
        "hard_quota",
        "include_ext",
        "include_regex",
        "include_glob",
        "include",
        "keep",
        "librsync",
        "max_file_size",
        "min_file_size",
        "nobackup",
        "notify_failure_arg",
        "notify_failure_script" "notify_success_arg",
        "notify_success_script",
        "notify_success_warnings_only",
        "password_check",
        "password",
        "path_length_warn",
        "protocol",
        "read_all_blockdevs",
        "read_all_fifos",
        "read_blockdev",
        "read_fifo",
        "restore_client",
        "scan_problem_raises_error",
        "server_script_arg",
        "server_script_notify",
        "server_script_post_arg",
        "server_script_post_notify",
        "server_script_post_run_on_fail",
        "server_script_post",
        "server_script_pre_arg",
        "server_script_pre_notify",
        "server_script_pre",
        "server_script",
        "soft_quota",
        "split_vss",
        "ssl_peer_cn",
        "strip_vss",
        "syslog",
        "timer_arg",
        "timer_script",
        "timestamp_format",
        "version_warn",
        "vss_drives",
        "working_dir_recovery_method",
        "server_can_restore",
    ]
    string_cli = list(set(string_srv) & set(fields_cli))
    string_cli += ["ssl_peer_cn", "password"]
    boolean_cli = list(set(boolean_srv) & set(fields_cli))
    integer_cli = list(set(integer_srv) & set(fields_cli))
    multi_cli = list(set(multi_srv) & set(fields_cli))
    doc = {
        ".": __(
            "Read additional configuration files. On Windows, the glob"
            " is unimplemented - you will need to specify an actual"
            " file."
        ),
        "address": __(
            "Defines the main TCP address that the server listens"
            " on. The default is either '::' or '0.0.0.0',"
            " dependent upon compile time options."
        ),
        "atime": __(
            "This allows you to control whether the client uses"
            " O_NOATIME when opening files and directories. The"
            " default is 0, which enables O_NOATIME. This means that"
            " the client can read files and directories without"
            " updating the access times. However, this is only"
            " possible if you are running as root, or are the owner"
            " of the file or directory. If this is not the case"
            " (perhaps you only have group or world access to the"
            " files), you will get errors until you set atime=1."
            " With atime=1, the access times will be updated on the"
            " files and directories that get backed up."
        ),
        "autoupgrade_dir": __(
            "Path to autoupgrade directory from which"
            " upgrades are downloaded. The option can be"
            " left unset in order not to autoupgrade"
            " clients. Please see docs/autoupgrade.txt in"
            " the source package for more help with this"
            " option."
        ),
        "ca_burp_ca": __(
            "Path to the burp_ca script when using the ca_conf" " option."
        ),
        "ca_conf": __(
            "Path to certificate authority configuration file. The"
            " CA configuration file will usually be"
            " /etc/burp/CA.cnf. The CA directory indicated by"
            " CA.cnf will usually be /etc/burp/CA. If ca_conf is"
            " set and the CA directory does not exist, the server"
            " will create, populate it, and the paths indicated by"
            " ssl_cert_ca, ssl_cert, ssl_key and ssl_dhfile will be"
            " overwritten. For more detailed information on this"
            " and the other ca_* options, please see"
            " docs/burp_ca.txt."
        ),
        "ca_name": __(
            "Name of the CA that the server will generate when"
            " using the ca_conf option."
        ),
        "ca_server_name": __(
            "The name that the server will put into its own"
            " SSL certficates when using the ca_conf"
            " option."
        ),
        "client_can_delete": __(
            "Turn this off to prevent clients from"
            " deleting backups with the '-a D' option."
            " The default is that clients can delete"
            " backups. Restore clients can override this"
            " setting."
        ),
        "client_can_force_backup": __(
            "Turn this off to prevent clients from"
            " forcing backups with the '-a b'"
            " option. Timed backups will still"
            " work. The default is that clients can"
            " force backups."
        ),
        "client_can_list": __(
            "Turn this off to prevent clients from listing"
            " backups with the '-a l' option. The default"
            " is that clients can list backups. Restore"
            " clients can override this setting."
        ),
        "client_can_restore": __(
            "Turn this off to prevent clients from"
            " initiating restores with the '-a r'"
            " option. The default is that clients can"
            " initiate restores. Restore clients can"
            " override this setting."
        ),
        "client_can_verify": __(
            "Turn this off to prevent clients from"
            " initiating a verify job with the '-a v'"
            " option. The default is that clients can"
            " initiate a verify job. Restore clients can"
            " override this setting."
        ),
        "client_lockdir": __(
            "Path to the directory in which to keep"
            " per-client lock files. By default, this is set"
            " to the path given by the 'directory' option."
        ),
        "clientconfdir": __(
            "Path to the directory that contains client" " configuration files."
        ),
        "compression": __(
            "Choose the level of gzip compression for files"
            " stored in backups. Setting 0 or gzip0 turns"
            " compression off. The default is gzip9. This"
            " option can be overridden by the client"
            " configuration files in clientconfdir on the"
            " server."
        ),
        "cross_all_filesystems": __(
            "Allow backups to cross all filesystem" " mountpoints."
        ),
        "cross_filesystem": __(
            "Allow backups to cross a particular" " filesystem mountpoint."
        ),
        "daemon": __("Whether to daemonise. The default is 1."),
        "dedup_group": __(
            "Enables you to group clients together for file"
            " deduplication purposes. For example, you might"
            " want to set 'dedup_group=xp' for each Windows XP"
            " client, and then run the bedup program on a cron"
            " job every other day with the option '-g xp'."
        ),
        "directory_tree": __(
            "When turned on (which is the default) and the"
            " client is on version 1.3.6 or greater, the"
            " structure of the storage directory will mimic"
            " that of the original filesystem on the"
            " client."
        ),
        "directory": __("Path to the directory in which to store backups."),
        "exclude_comp": __(
            "Extensions to exclude from compression. Case"
            " insensitive. You can have multiple exclude"
            " compression lines. For example, set 'gz' to"
            " exclude gzipped files from compression."
        ),
        "exclude_ext": __(
            "Extensions to exclude from the backup. Case"
            " insensitive. You can have multiple exclude"
            " extension lines. For example, set 'vdi' to"
            " exclude VirtualBox disk images."
        ),
        "exclude_fs": __(
            "File systems to exclude from the backup. Case"
            " insensitive. You can have multiple exclude file"
            " system lines. For example, set 'tmpfs' to exclude"
            " tmpfs. Burp has an internal mapping of file system"
            " names to file system IDs. If you know the file"
            " system ID, you can use that instead. For example,"
            " 'exclude_fs = 0x01021994' will also"
            " exclude tmpfs."
        ),
        "exclude_regex": __("Exclude paths that match the regular" " expression."),
        "exclude": __(
            "Path to exclude from the backup. You can have"
            " multiple exclude lines. Use forward slashes '/', not"
            " backslashes '\\' as path delimiters."
        ),
        "fork": __("Whether to fork children. The default is 1."),
        "group": __(
            "Run as a particular group. This can be overridden by"
            " the client configuration files in clientconfdir on the"
            " server."
        ),
        "hard_quota": __(
            "Do not back up the client if the estimated size of"
            " all files is greater than the specified size."
            " Example: 'hard_quota = 100Gb'. Set to 0 (the"
            " default) to have no limit."
        ),
        "hardlinked_archive": __(
            "On the server, defines whether to keep"
            " hardlinked files in the backups, or"
            " whether to generate reverse deltas and"
            " delete the original files. Can be set to"
            " either 0 (off) or 1 (on). Disadvantage:"
            " More disk space will be used Advantage:"
            " Restores will be faster, and since no"
            " reverse deltas need to be generated, the"
            " time and effort the server needs at the"
            " end of a backup is reduced."
        ),
        "include_ext": __(
            "Extensions to include in the backup. Case"
            " insensitive. Nothing else will be included in the"
            " backup. You can have multiple include extension"
            " lines. For example, set 'txt' to include files"
            " that end in '.txt'. You need to specify an"
            " 'include' line so that burp knows where to start"
            " looking."
        ),
        "include_regex": __("Not implemented."),
        "include": __(
            "Path to include in the backup. You can have multiple"
            " include lines. Use forward slashes '/', not"
            " backslashes '\\' as path delimiters."
        ),
        "include_glob": __(
            "Include paths that match the glob expression."
            "For example, '/home/*/Documents' will include"
            " '/home/user1/Documents' and"
            " '/home/user2/Documents' if directories 'user1'"
            " and 'user2' exist in '/home'. The Windows"
            " implementation currently limit the expression to"
            " contain only one '*'."
        ),
        "keep": __(
            "Number of backups to keep. This can be overridden by the"
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
            " backup every minute for 100 years."
        ),
        "librsync": __(
            "When set to 0, delta differencing will not take"
            " place. That is, when a file changes, the server will"
            " request the whole new file. The default is 1. This"
            " option can be overridden by the client configuration"
            " files in clientconfdir on the server."
        ),
        "lockfile": __(
            "Path to the lockfile that ensures that two server"
            " processes cannot run simultaneously."
        ),
        "manual_delete": __(
            "If a path is given, the server will move"
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
            " clientconfdir on the server."
        ),
        "max_children": __(
            "Defines the number of child processes to fork"
            " (the number of clients that can simultaneously"
            " connect. The default is 5."
        ),
        "max_file_size": __(
            "Do not back up files that are greater than the"
            " specified size. Example: 'max_file_size ="
            " 10Mb'. Set to 0 (the default) to have no"
            " limit."
        ),
        "max_hardlinks": __(
            "On the server, the number of times that a single"
            " file can be hardlinked. The bedup program also"
            " obeys this setting. The default is 10000."
        ),
        "max_status_children": __(
            "Defines the number of status child"
            " processes to fork (the number of status"
            " clients that can simultaneously connect."
            " The default is 5."
        ),
        "max_storage_subdirs": __(
            "Defines the number of subdirectories in"
            " the data storage areas. The maximum number"
            " of subdirectories that ext3 allows is"
            " 32000. If you do not set this option, it"
            " defaults to 30000."
        ),
        "min_file_size": __(
            "Do not back up files that are less than the"
            " specified size. Example: 'min_file_size ="
            " 10Mb'. Set to 0 (the default) to have no"
            " limit."
        ),
        "mode": __("Required to run in server mode."),
        "monitor_browse_cache": __(
            "Whether or not the server should cache"
            " the directory tree when a monitor client"
            " is browsing. <br/>Advantage: browsing is"
            " faster. </br>Disadvantage: more memory is"
            " used."
        ),
        "network_timeout": __(
            "Set the network timeout in seconds. If no"
            " data is sent or received over a period of"
            " this length, burp will give up. The default"
            " is 7200 seconds (2 hours)."
        ),
        "nobackup": __(
            "If this file system entry exists, the directory"
            " containing it will not be backed up."
        ),
        "notify_failure_arg": __(
            "The same as notify_success_arg, but for" " backups that failed."
        ),
        "notify_failure_script": __(
            "The same as notify_success_script, but" " for backups that failed."
        ),
        "notify_success_arg": __(
            "A user-definable argument to the notify"
            " success script. You can have many of"
            " these. The notify_success_arg options can"
            " be overridden by the client configuration"
            " files in clientconfdir on the server."
        ),
        "notify_success_script": __(
            "Path to the script to run when a backup"
            " succeeds. User arguments are appended"
            " after the first five reserved"
            " arguments. An example notify script is"
            " provided. The notify_success_script"
            " option can be overridden by the client"
            " configuration files in clientconfdir on"
            " the server."
        ),
        "notify_success_warnings_only": __(
            "Set to 1 to send success"
            " notifications when there were"
            " warnings. If this and"
            " notify_success_changes_only are"
            " not turned on, success"
            " notifications are always sent."
        ),
        "password": __("Defines the password to send to the server."),
        "password_check": __(
            "Allows you to turn client password checking on"
            " or off. The default is on. SSL certificates"
            " will still be checked if you turn passwords"
            " off. This option can be overridden by the"
            " client configuration files in clientconfdir on"
            " the server."
        ),
        "path_length_warn": __(
            "When this is on, which is the default, a"
            " warning will be issued when the client sends"
            " a path that is too long to replicate in the"
            " storage area tree structure. The file will"
            " still be saved in a numbered file outside of"
            " the tree structure, regardless of the"
            " setting of this option. This option can be"
            " overridden by the client configuration files"
            " in clientconfdir on the server."
        ),
        "pidfile": __("Synonym for lockfile."),
        "port": __("Defines the main TCP port that the server listens on."),
        "protocol": __(
            "Choose which style of backups and restores to use. 0"
            " (the default) automatically decides based on the"
            " server version and which protocol is set on the"
            " server side. 1 forces protocol1 style (file level"
            " granularity with a pseudo mirrored storage on the"
            " server and optional rsync). 2 forces protocol2 style"
            " (inline deduplication with variable length blocks)."
            " If you choose a forced setting, it will be an error"
            " if the server also chooses a forced setting."
        ),
        "ratelimit": __(
            "Set the network send rate limit, in Mb/s. If this"
            " option is not given, burp will send data as fast as"
            " it can."
        ),
        "read_all_blockdevs": __(
            "Open all block devices for reading and"
            " back up the contents as if they were"
            " regular files."
        ),
        "read_all_fifos": __(
            "Open all fifos for reading and back up the"
            " contents as if they were regular files."
        ),
        "read_blockdev": __(
            "Do not back up the given block device itself,"
            " but open it for reading and back up the"
            " contents as if it were a regular file."
        ),
        "read_fifo": __(
            "Do not back up the given fifo itself, but open it"
            " for reading and back up the contents as if it were"
            " a regular file."
        ),
        "restore_client": __(
            "A client that is permitted to list, verify,"
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
            " burp."
        ),
        "resume_partial": __(
            "Turn this on to enable 'resume partial' code."
            " Requires 'working_dir_recovery_method=resume'."
            " When resuming an interrupted transfer of a"
            " single file, it attempts to use previously"
            " transferred blocks of that file in order to be"
            " more efficient. However, situations have been"
            " reported where the file on the server side"
            " just gets bigger forever, so this feature now"
            " defaults to being turned off."
        ),
        "scan_problem_raises_error": __(
            "When enabled, this causes problems"
            " in the phase1 scan (such as an"
            " 'include' being missing) to be"
            " treated as fatal errors. The"
            " default is off."
        ),
        "server_script_arg": __(
            "Goes with server_script and overrides"
            " server_script_pre_arg and"
            " server_script_post_arg."
        ),
        "server_script_notify": __(
            "Turn on to send a notification emails"
            " when the server pre and post scripts"
            " return non-zero. The output of the"
            " script will be included it the email."
            " The default is off. Requires the"
            " notify_failure options to be set."
        ),
        "server_script_post_arg": __(
            "A user-definable argument to the"
            " server post script. You can have many"
            " of these."
        ),
        "server_script_post_notify": __(
            "Turn on to send a notification"
            " email when the server post script"
            " returns non-zero. The output of the"
            " script will be included in the"
            " email. The default is off. Requires"
            " the notify_failure options to be"
            " set."
        ),
        "server_script_post_run_on_fail": __(
            "If this is set to 1,"
            " server_script_post will always"
            " be run. The default is 0,"
            " which means that if the task"
            " asked for by the client fails,"
            " server_script_post will not be"
            " run."
        ),
        "server_script_post": __(
            "Path to a script to run on the server"
            " before the client disconnects. The"
            " arguments to it are 'post', '(client"
            " command)', '(client name), '(0 or 1 for"
            " success or failure)', '(timer script exit"
            " code)', and"
            " then arguments defined by"
            " server_script_post_arg. This command and"
            " related options can be overriddden by the"
            " client configuration files in"
            " clientconfdir on the server."
        ),
        "server_script_pre_arg": __(
            "A user-definable argument to the server"
            " pre script. You can have many of"
            " these."
        ),
        "server_script_pre_notify": __(
            "Turn on to send a notification email"
            " when the server pre script returns"
            " non-zero. The output of the script"
            " will be included in the email. The"
            " default is off. Most people will not"
            " want this turned on because clients"
            " usually contact the server at 20"
            " minute intervals and this could"
            " cause a lot of emails to be"
            " generated. Requires the"
            " notify_failure options to be set."
        ),
        "server_script_pre": __(
            "Path to a script to run on the server after"
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
            " on the server."
        ),
        "server_script": __(
            "You can use this to save space in your config"
            " file when you want to run the same server"
            " script twice. It overrides server_script_pre"
            " and server_script_post. This command and"
            " related options can be overriddden by the"
            " client configuration files in clientconfdir on"
            " the server."
        ),
        "soft_quota": __(
            "A warning will be issued when the estimated size"
            " of all files is greater than the specified size"
            " and smaller than hard_quota. Example: 'soft_quota"
            " = 95Gb'. Set to 0 (the default) to have no"
            " warning."
        ),
        "split_vss": __(
            "When backing up Windows computers with burp"
            " protocol 1, this option allows you to save the VSS"
            " header data separate from the file data. The"
            " default is off, which means that the VSS header"
            " data is saved prepended to the file data."
        ),
        "ssl_cert_ca": __(
            "The path to the SSL CA certificate. This file"
            " will probably be the same on both the server and"
            " the client. The file should contain just the"
            " certificate in PEM format. For more information"
            " on this, and the other ssl_* options, please see"
            " <a href='http://burp.grke.org/docs/burp_ca.html'>"
            " docs/burp_ca.txt</a>."
        ),
        "ssl_cert_password": __("Synonym for ssl_key_password."),
        "ssl_cert": __(
            "The path to the server SSL certificate. It works for"
            " me when the file contains the concatenation of the"
            " certificate and private key in PEM format."
        ),
        "ssl_ciphers": __("Allowed SSL ciphers. See openssl ciphers for" " details."),
        "ssl_compression": __(
            "Choose the level of zlib compression over"
            " SSL. Setting 0 or zlib0 turnsSSL compression"
            " off. Setting non-zero gives zlib5 compression"
            " (it is not currently possible for openssl to"
            " set any other level). The default is 5."
            " 'gzip' is a synonym of 'zlib'.is a synonym of"
            " 'zlib'."
        ),
        "ssl_dhfile": __(
            "Path to Diffie-Hellman parameter file. To generate"
            " one with openssl, use a command like this: openssl"
            " dhparam -out dhfile.pem -5 1024"
        ),
        "ssl_key_password": __("The SSL key password."),
        "ssl_key": __("The path to the server SSL private key in PEM" " format."),
        "ssl_peer_cn": __(
            "Must match the common name in the SSL certificate"
            " that the server giveswhen it connects. If"
            " ssl_peer_cn is not set, the server name will be"
            " used instead."
        ),
        "status_address": __(
            "Defines the main TCP address that the server"
            " listens on for status requests. The default is"
            " either '::1' or '127.0.0.1', dependent upon"
            " compile time options."
        ),
        "status_port": __(
            "Defines the TCP port that the server listens on" " for status requests."
        ),
        "stdout": __("Log to stdout. Defaults to on."),
        "strip_vss": __(
            "When backing up Windows computers with burp"
            " protocol 1, this option allows you to prevent the"
            " VSS header data being backed up. The default is"
            " off. To restore a backup that has no VSS"
            " information on Windows, you need to give the client"
            " the '-x' command line option."
        ),
        "syslog": __("Log to syslog. Defaults to off."),
        "timer_arg": __(
            "A user-definable argument to the timer script."
            "You can have many of these. The timer_arg options"
            " can be overridden by the client configuration files"
            " in clientconfdir on the server."
        ),
        "timer_script": __(
            "Path to the script to run when a client connects"
            " with the timed backup option. If the script"
            " exits with code 0, a backup will run. The first"
            " two arguments are the client name and the path"
            " to the 'current' storage directory. The next"
            " three arguments are reserved, and user arguments"
            " are appended after that. An example timer script"
            " is provided. The timer_script option can be"
            " overridden by the client configuration files in"
            " clientconfdir on the server."
        ),
        "timestamp_format": __(
            "This allows you to tweak the format of the"
            " timestamps of individual backups. See 'man"
            " strftime' to see available substitutions."
            " If this option is unset, burp uses"
            ' "%Y-%m-%d %H:%M:%S".'
        ),
        "umask": __("Set the file creation umask. Default is 0022."),
        "user": __(
            "Run as a particular user. This can be overridden by the"
            " client configuration files in clientconfdir on the"
            " server."
        ),
        "version_warn": __(
            "When this is on, which is the default, a warning"
            " will be issued when the client version does not"
            " match the server version. This option can be"
            " overridden by the client configuration files in"
            " clientconfdir on the server."
        ),
        "vss_drives": __(
            "When backing up Windows computers, this option"
            " allows you to specify which drives have VSS"
            " snapshots taken of them. If you omit this option,"
            " burp will automatically decide based on the"
            " 'include' options. If you want no drives to have"
            " snapshots taken of them, you can specify '0'."
        ),
        "working_dir_recovery_method": __(
            "This option tells the server what"
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
            " </li></ul>"
        ),
    }

    @property
    def all(self):
        return sorted(
            list(
                set(self.boolean_srv)
                | set(self.files)
                | set(self.integer_srv)
                | set(self.multi_srv)
                | set(self.string_srv)
                | set(self.boolean_cli)
                | set(self.integer_cli)
                | set(self.multi_cli)
                | set(self.string_cli)
            )
        )
