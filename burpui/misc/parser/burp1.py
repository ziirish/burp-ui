# -*- coding: utf8 -*-
import re
import os
import shutil
import codecs

from glob import glob

from burpui.misc.utils import BUIlogging
from burpui.misc.parser.interface import BUIparser


class Parser(BUIparser, BUIlogging):
    defaults = {
        u'address': '',  # IP
        u'atime': False,  # bool
        u'autoupgrade_dir': '',  # dir
        u'ca_burp_ca': '',  # file
        u'ca_conf': '',  # file
        u'ca_name': '',
        u'ca_server_name': '',
        u'client_can_delete': True,  # bool
        u'client_can_diff': True,  # bool
        u'client_can_force_backup': True,  # bool
        u'client_can_list': True,  # bool
        u'client_can_restore': True,  # bool
        u'client_can_verify': True,  # bool
        u'client_lockdir': '',
        u'clientconfdir': '',  # dir
        u'compression': 'gzip9',
        u'cross_all_filesystems': False,  # bool
        u'cross_filesystem': '',
        u'daemon': True,  # bool
        u'dedup_group': '',
        u'directory_tree': True,  # bool
        u'directory': '',
        u'exclude_comp': '',  # multi
        u'exclude_ext': '',  # multi
        u'exclude_fs': '',  # multi
        u'exclude_regex': '',  # multi
        u'exclude': '',  # multi
        u'fork': True,  # bool
        u'group': '',
        u'hard_quota': '',
        u'hardlinked_archive': False,  # bool
        u'include_ext': '',  # multi
        u'include_glob': '',  # multi
        u'include_regex': '',  # multi
        u'include': '',  # multi
        u'keep': [7, 6, 4],  # multi  # int
        u'librsync': True,  # bool
        u'max_children': 5,  # int
        u'max_file_size': '',
        u'max_hardlinks': 10000,  # int
        u'max_status_children': 5,  # int
        u'max_storage_subdirs': 30000,  # int
        u'min_file_size': '',
        u'mode': '',
        u'monitor_browse_cache': False,  # bool
        u'network_timeout': 7200,  # int
        u'nobackup': '',
        u'notify_failure_arg': '',  # multi
        u'notify_failure_script': '',  # file
        u'notify_success_arg': '',  # multi
        u'notify_success_changes_only': False,  # bool
        u'notify_success_script': '',  # file
        u'notify_success_warnings_only': False,  # bool
        u'password_check': True,  # bool
        u'path_length_warn': True,  # bool
        u'pidfile': '',
        u'port': 4971,  # int
        u'protocol': False,  # int
        u'ratelimit': False,  # int
        u'read_all_blockdevs': False,  # bool
        u'read_all_fifos': False,  # bool
        u'read_blockdev': '',
        u'read_fifo': '',
        u'restore_client': '',  # multi
        u'scan_problem_raises_error': False,  # bool
        u'server_script_arg': '',  # multi
        u'server_script_notify': False,  # bool
        u'server_script_post_arg': '',  # multi
        u'server_script_post_notify': False,  # bool
        u'server_script_post_run_on_fail': False,  # bool
        u'server_script_post': '',  # file
        u'server_script_pre_arg': '',  # multi
        u'server_script_pre_notify': False,  # bool
        u'server_script_pre': '',  # file
        u'server_script': '',  # file
        u'soft_quota': '',
        u'split_vss': False,  # bool
        u'ssl_cert_ca': '',  # file
        u'ssl_cert': '',  # file
        u'ssl_ciphers': '',
        u'ssl_compression': 'zlib5',
        u'ssl_dhfile': '',  # file
        u'ssl_key_password': '',
        u'ssl_key': '',  # file
        u'ssl_peer_cn': '',
        u'status_address': '',  # 127.0.0.1 / ::1
        u'status_port': 4972,  # int
        u'stdout': True,  # bool
        u'strip_vss': False,  # bool
        u'syslog': False,  # bool
        u'timer_arg': '',  # multi
        u'timer_script': '',  # file
        u'timestamp_format': '',
        u'umask': '0022',  # mode
        u'user': '',
        u'version_warn': True,  # bool
        u'vss_drives': '',
        u'working_dir_recovery_method': '',
    }
    placeholders = {
        u'.': "path or glob",
        u'atime': "0|1",
        u'autoupgrade_dir': "path",
        u'ca_burp_ca': "path",
        u'ca_conf': "path",
        u'ca_name': "name",
        u'ca_server_name': "name",
        u'client_can_delete': "0|1",
        u'client_can_force_backup': "0|1",
        u'client_can_list': "0|1",
        u'client_can_restore': "0|1",
        u'client_can_verify': "0|1",
        u'client_lockdir': "path",
        u'clientconfdir': "path",
        u'compression': "gzip[0-9]",
        u'cross_all_filesystems': "0|1",
        u'cross_filesystem': "path",
        u'daemon': "0|1",
        u'dedup_group': "string",
        u'directory_tree': "0|1",
        u'directory': "path",
        u'exclude_comp': "extension",
        u'exclude_ext': "extension",
        u'exclude_fs': "fstype",
        u'exclude_regex': "regular expression",
        u'exclude': "path",
        u'fork': "0|1",
        u'group': "groupname",
        u'hard_quota': "b/Kb/Mb/Gb",
        u'hardlinked_archive': "0|1",
        u'include_ext': "extension",
        u'include_regex': "regular expression",
        u'include': "path",
        u'keep': "number",
        u'librsync': "0|1",
        u'lockfile': "path",
        u'manual_delete': "path",
        u'max_children': "number",
        u'max_file_size': "b/Kb/Mb/Gb",
        u'max_hardlinks': "number",
        u'max_status_children': "number",
        u'max_storage_subdirs': "number",
        u'min_file_size': "b/Kb/Mb/Gb",
        u'network_timeout': "s",
        u'nobackup': "file name",
        u'notify_failure_arg': "string",
        u'notify_failure_script': "path",
        u'notify_success_arg': "string",
        u'notify_success_changes_only': "0|1",
        u'notify_success_script': "path",
        u'notify_success_warnings_only': "0|1",
        u'password_check': "0|1",
        u'pidfile': "path",
        u'port': "port number",
        u'ratelimit': "Mb/s",
        u'read_all_blockdevs': "0|1",
        u'read_all_fifos': "0|1",
        u'read_blockdev': "path",
        u'read_fifo': "path",
        u'restore_client': "client",
        u'resume_partial': "0|1",
        u'scan_problem_raises_error': "0|1",
        u'server_script_arg': "path",
        u'server_script_notify': "0|1",
        u'server_script_post_arg': "string",
        u'server_script_post_notify': "0|1",
        u'server_script_post_run_on_fail': "0|1",
        u'server_script_post': "path",
        u'server_script_pre_arg': "string",
        u'server_script_pre_notify': "0|1",
        u'server_script_pre': "path",
        u'server_script': "path",
        u'soft_quota': "b/Kb/Mb/Gb",
        u'ssl_cert_ca': "path",
        u'ssl_cert_password': "password",
        u'ssl_cert': "path",
        u'ssl_ciphers': "cipher list",
        u'ssl_dhfile': "path",
        u'ssl_key_password': "password",
        u'ssl_key': "path",
        u'ssl_peer_cn': "string",
        u'status_port': "port number",
        u'stdout': "0|1",
        u'strip_vss': "0|1",
        u'suplit_vss': "0|1",
        u'syslog': "0|1",
        u'timer_arg': "string",
        u'timer_script': "path",
        u'timestamp_format': "strftime format",
        u'umask': "umask",
        u'user': "username",
        u'version_warn': "0|1",
        u'vss_drives': "list of drive letters",
        u'working_dir_recovery_method': "resume|use|delete",
    }
    values = {
        u'compression': ['gzip{0}'.format(x) for x in range(1, 10)],
        u'mode': ['client', 'server'],
        u'ssl_compression': ['zlib{0}'.format(x) for x in range(1, 10)],
        u'status_address': ['127.0.0.1', '::1'],  # 127.0.0.1 / ::1
        u'working_dir_recovery_method': ['use', 'delete', 'resume'],
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
        u'syslog'
        u'timer_arg',
        u'timer_script',
        u'timestamp_format',
        u'version_warn',
        u'vss_drives',
        u'working_dir_recovery_method',
    ]
    string_cli = list(set(string_srv) & set(fields_cli))
    string_cli += [u'ssl_peer_cn']
    boolean_cli = list(set(boolean_srv) & set(fields_cli))
    integer_cli = list(set(integer_srv) & set(fields_cli))
    multi_cli = list(set(multi_srv) & set(fields_cli))
    doc = {
        u'.': "Read additional configuration files. On Windows, the glob is unimplemented - you will need to specify an actual file.",
        u'address': "Defines the main TCP address that the server listens on. The default is either '::' or '0.0.0.0', dependent upon compile time options.",
        u'atime': "This allows you to control whether the client uses O_NOATIME when opening files and directories. The default is 0, which enables O_NOATIME. This means that the client can read files and directories without updating the access times. However, this is only possible if you are running as root, or are the owner of the file or directory. If this is not the case (perhaps you only have group or world access to the files), you will get errors until you set atime=1. With atime=1, the access times will be updated on the files and directories that get backed up.",
        u'autoupgrade_dir': "Path to autoupgrade directory from which upgrades are downloaded. The option can be left unset in order not to autoupgrade clients. Please see docs/autoupgrade.txt in the source package for more help with this option.",
        u'ca_burp_ca': "Path to the burp_ca script when using the ca_conf option.",
        u'ca_conf': "Path to certificate authority configuration file. The CA configuration file will usually be /etc/burp/CA.cnf. The CA directory indicated by CA.cnf will usually be /etc/burp/CA. If ca_conf is set and the CA directory does not exist, the server will create, populate it, and the paths indicated by ssl_cert_ca, ssl_cert, ssl_key and ssl_dhfile will be overwritten. For more detailed information on this and the other ca_* options, please see docs/burp_ca.txt.",
        u'ca_name': "Name of the CA that the server will generate when using the ca_conf option.",
        u'ca_server_name': "The name that the server will put into its own SSL certficates when using the ca_conf option.",
        u'client_can_delete': "Turn this off to prevent clients from deleting backups with the '-a D' option. The default is that clients can delete backups. Restore clients can override this setting.",
        u'client_can_force_backup': "Turn this off to prevent clients from forcing backups with the '-a b' option. Timed backups will still work. The default is that clients can force backups.",
        u'client_can_list': "Turn this off to prevent clients from listing backups with the '-a l' option. The default is that clients can list backups. Restore clients can override this setting.",
        u'client_can_restore': "Turn this off to prevent clients from initiating restores with the '-a r' option. The default is that clients can initiate restores. Restore clients can override this setting.",
        u'client_can_verify': "Turn this off to prevent clients from initiating a verify job with the '-a v' option. The default is that clients can initiate a verify job. Restore clients can override this setting.",
        u'client_lockdir': "Path to the directory in which to keep per-client lock files. By default, this is set to the path given by the 'directory' option.",
        u'clientconfdir': "Path to the directory that contains client configuration files.",
        u'compression': "Choose the level of gzip compression for files stored in backups. Setting 0 or gzip0 turns compression off. The default is gzip9. This option can be overridden by the client configuration files in clientconfdir on the server.",
        u'cross_all_filesystems': "Allow backups to cross all filesystem mountpoints.",
        u'cross_filesystem': "Allow backups to cross a particular filesystem mountpoint.",
        u'daemon': "Whether to daemonise. The default is 1.",
        u'dedup_group': "Enables you to group clients together for file deduplication purposes. For example, you might want to set 'dedup_group=xp' for each Windows XP client, and then run the bedup program on a cron job every other day with the option '-g xp'.",
        u'directory_tree': "When turned on (which is the default) and the client is on version 1.3.6 or greater, the structure of the storage directory will mimic that of the original filesystem on the client.",
        u'directory': "Path to the directory in which to store backups.",
        u'exclude_comp': "Extensions to exclude from compression. Case insensitive. You can have multiple exclude compression lines. For example, set 'gz' to exclude gzipped files from compression.",
        u'exclude_ext': "Extensions to exclude from the backup. Case insensitive. You can have multiple exclude extension lines. For example, set 'vdi' to exclude VirtualBox disk images.",
        u'exclude_fs': "File systems to exclude from the backup. Case insensitive. You can have multiple exclude file system lines. For example, set 'tmpfs' to exclude tmpfs. Burp has an internal mapping of file system names to file system IDs. If you know the file system ID, you can use that instead. For example, 'exclude_fs = 0x01021994' will also exclude tmpfs.",
        u'exclude_regex': "Exclude paths that match the regular expression.",
        u'exclude': "Path to exclude from the backup. You can have multiple exclude lines. Use forward slashes '/', not backslashes '\' as path delimiters.",
        u'fork': "Whether to fork children. The default is 1.",
        u'group': "Run as a particular group. This can be overridden by the client configuration files in clientconfdir on the server.",
        u'hard_quota': "Do not back up the client if the estimated size of all files is greater than the specified size. Example: 'hard_quota = 100Gb'. Set to 0 (the default) to have no limit.",
        u'hardlinked_archive': "On the server, defines whether to keep hardlinked files in the backups, or whether to generate reverse deltas and delete the original files. Can be set to either 0 (off) or 1 (on). Disadvantage: More disk space will be used Advantage: Restores will be faster, and since no reverse deltas need to be generated, the time and effort the server needs at the end of a backup is reduced.",
        u'include_ext': "Extensions to include in the backup. Case insensitive. Nothing else will be included in the backup. You can have multiple include extension lines. For example, set 'txt' to include files that end in '.txt'. You need to specify an 'include' line so that burp knows where to start looking.",
        u'include_regex': "Not implemented.",
        u'include': "Path to include in the backup. You can have multiple include lines. Use forward slashes '/', not backslashes '\' as path delimiters.",
        u'keep': "Number of backups to keep. This can be overridden by the client configuration files in clientconfdir on the server. Specify multiple 'keep' entries on separate lines in order to keep multiple periods of backups. For example, assuming that you are doing a backup a day, keep=7 keep=4 keep=6 (on separate lines) will keep 7 daily backups, 4 weekly backups (7x4=28), and 6 multiples of 4 weeks (7x4x6=168) - roughly 6 monthly backups. Effectively, you will be guaranteed to be able to restore up to 168 days ago, with the number of available backups exponentially decreasing as you go back in time to that point. In this example, every 7th backup will be hardlinked to allow burp to safely delete intermediate backups when necessary. You can have as many 'keep' lines as you like, as long as they don't exceed 52560000 when multiplied together. That is, a backup every minute for 100 years.",
        u'librsync': "When set to 0, delta differencing will not take place. That is, when a file changes, the server will request the whole new file. The default is 1. This option can be overridden by the client configuration files in clientconfdir on the server.",
        u'lockfile': "Path to the lockfile that ensures that two server processes cannot run simultaneously.",
        u'manual_delete': "If a path is given, the server will move directories to be deleted into the directory specified by the path, but will not actually delete them. The path must be on the same file system as the backup storage. The idea is that a busy server may be configured to run the deletions outside of the backup timebands, when the server is less busy, via a cron job. The default is unset, which means that the server will automatically delete the directories at the end of a backup. This option can be overridden by the client configuration files in clientconfdir on the server.",
        u'max_children': "Defines the number of child processes to fork (the number of clients that can simultaneously connect. The default is 5.",
        u'max_file_size': "Do not back up files that are greater than the specified size. Example: 'max_file_size = 10Mb'. Set to 0 (the default) to have no limit.",
        u'max_hardlinks': "On the server, the number of times that a single file can be hardlinked. The bedup program also obeys this setting. The default is 10000.",
        u'max_status_children': "Defines the number of status child processes to fork (the number of status clients that can simultaneously connect. The default is 5.",
        u'max_storage_subdirs': "Defines the number of subdirectories in the data storage areas. The maximum number of subdirectories that ext3 allows is 32000. If you do not set this option, it defaults to 30000.",
        u'min_file_size': "Do not back up files that are less than the specified size. Example: 'min_file_size = 10Mb'. Set to 0 (the default) to have no limit.",
        u'mode': "Required to run in server mode.",
        u'monitor_browse_cache': "Whether or not the server should cache the directory tree when a monitor client is browsing. <br/>Advantage: browsing is faster. </br>Disadvantage: more memory is used.",
        u'network_timeout': "Set the network timeout in seconds. If no data is sent or received over a period of this length, burp will give up. The default is 7200 seconds (2 hours).",
        u'nobackup': "If this file system entry exists, the directory containing it will not be backed up.",
        u'notify_failure_arg': "The same as notify_success_arg, but for backups that failed.",
        u'notify_failure_script': "The same as notify_success_script, but for backups that failed.",
        u'notify_success_arg': "A user-definable argument to the notify success script. You can have many of these. The notify_success_arg options can be overriddden by the client configuration files in clientconfdir on the server.",
        u'notify_success_script': "Path to the script to run when a backup succeeds. User arguments are appended after the first five reserved arguments. An example notify script is provided. The notify_success_script option can be overriddden by the client configuration files in clientconfdir on the server.",
        u'notify_success_warnings_only': "Set to 1 to send success notifications when there were warnings. If this and notify_success_changes_only are not turned on, success notifications are always sent.",
        u'password_check': "Allows you to turn client password checking on or off. The default is on. SSL certificates will still be checked if you turn passwords off. This option can be overridden by the client configuration files in clientconfdir on the server.",
        u'path_length_warn': "When this is on, which is the default, a warning will be issued when the client sends a path that is too long to replicate in the storage area tree structure. The file will still be saved in a numbered file outside of the tree structure, regardless of the setting of this option. This option can be overridden by the client configuration files in clientconfdir on the server.",
        u'pidfile': "Synonym for lockfile.",
        u'port': "Defines the main TCP port that the server listens on.",
        u'protocol': "Choose which style of backups and restores to use. 0 (the default) automatically decides based on the server version and which protocol is set on the server side. 1 forces protocol1 style (file level granularity with a pseudo mirrored storage on the server and optional rsync). 2 forces protocol2 style (inline deduplication with variable length blocks). If you choose a forced setting, it will be an error if the server also chooses a forced setting.",
        u'ratelimit': "Set the network send rate limit, in Mb/s. If this option is not given, burp will send data as fast as it can.",
        u'read_all_blockdevs': "Open all block devices for reading and back up the contents as if they were regular files.",
        u'read_all_fifos': "Open all fifos for reading and back up the contents as if they were regular files.",
        u'read_blockdev': "Do not back up the given block device itself, but open it for reading and back up the contents as if it were a regular file.",
        u'read_fifo': "Do not back up the given fifo itself, but open it for reading and back up the contents as if it were a regular file.",
        u'restore_client': "A client that is permitted to list, verify, restore and delete files belonging to any other client. You may specify multiple restore_clients. If this is too permissive, you may set a restore_client for individual original clients in the individual clientconfdir files. Note that restoring a backup from a Windows computer onto a Linux computer will currently leave the VSS headers in place at the beginning of each file. This will be addressed in a future version of burp.",
        u'resume_partial': "Turn this on to enable 'resume partial' code. Requires 'working_dir_recovery_method=resume'. When resuming an interrupted transfer of a single file, it attempts to use previously transferred blocks of that file in order to be more efficient. However, situations have been reported where the file on the server side just gets bigger forever, so this feature now defaults to being turned off.",
        u'scan_problem_raises_error': "When enabled, this causes problems in the phase1 scan (such as an 'include' being missing) to be treated as fatal errors. The default is off.",
        u'server_script_arg': "Goes with server_script and overrides server_script_pre_arg and server_script_post_arg.",
        u'server_script_notify': "Turn on to send a notification emails when the server pre and post scripts return non-zero. The output of the script will be included it the email. The default is off. Requires the notify_failure options to be set.",
        u'server_script_post_arg': "A user-definable argument to the server post script. You can have many of these.",
        u'server_script_post_notify': "Turn on to send a notification email when the server post script returns non-zero. The output of the script will be included in the email. The default is off. Requires the notify_failure options to be set.",
        u'server_script_post_run_on_fail': "If this is set to 1, server_script_post will always be run. The default is 0, which means that if the task asked for by the client fails, server_script_post will not be run.",
        u'server_script_post': "Path to a script to run on the server before the client disconnects. The arguments to it are 'post', '(client command)', 'reserved3' to 'reserved5', and then arguments defined by server_script_post_arg. This command and related options can be overriddden by the client configuration files in clientconfdir on the server.",
        u'server_script_pre_arg': "A user-definable argument to the server pre script. You can have many of these.",
        u'server_script_pre_notify': "Turn on to send a notification email when the server pre script returns non-zero. The output of the script will be included in the email. The default is off. Most people will not want this turned on because clients usually contact the server at 20 minute intervals and this could cause a lot of emails to be generated. Requires the notify_failure options to be set.",
        u'server_script_pre': "Path to a script to run on the server after each successfully authenticated connection but before any work is carried out. The arguments to it are 'pre', '(client command)', 'reserved3' to 'reserved5', and then arguments defined by server_script_pre_arg. If the script returns non-zero, the task asked for by the client will not be run. This command and related options can be overriddden by the client configuration files in clientconfdir on the server.",
        u'server_script': "You can use this to save space in your config file when you want to run the same server script twice. It overrides server_script_pre and server_script_post. This command and related options can be overriddden by the client configuration files in clientconfdir on the server.",
        u'soft_quota': "A warning will be issued when the estimated size of all files is greater than the specified size and smaller than hard_quota. Example: 'soft_quota = 95Gb'. Set to 0 (the default) to have no warning.",
        u'split_vss': "When backing up Windows computers with burp protocol 1, this option allows you to save the VSS header data separate from the file data. The default is off, which means that the VSS header data is saved prepended to the file data.",
        u'ssl_cert_ca': "The path to the SSL CA certificate. This file will probably be the same on both the server and the client. The file should contain just the certificate in PEM format. For more information on this, and the other ssl_* options, please see docs/burp_ca.txt.",
        u'ssl_cert_password': "Synonym for ssl_key_password.",
        u'ssl_cert': "The path to the server SSL certificate. It works for me when the file contains the concatenation of the certificate and private key in PEM format.",
        u'ssl_ciphers': "Allowed SSL ciphers. See openssl ciphers for details.",
        u'ssl_compression': "Choose the level of zlib compression over SSL. Setting 0 or zlib0 turnsSSL compression off. Setting non-zero gives zlib5 compression (it is not currently possible for openssl to set any other level). The default is 5. 'gzip' is a synonym of 'zlib'.is a synonym of 'zlib'.",
        u'ssl_dhfile': "Path to Diffie-Hellman parameter file. To generate one with openssl, use a command like this: openssl dhparam -out dhfile.pem -5 1024",
        u'ssl_key_password': "The SSL key password.",
        u'ssl_key': "The path to the server SSL private key in PEM format.",
        u'status_address': "Defines the main TCP address that the server listens on for status requests. The default is either '::1' or '127.0.0.1', dependent upon compile time options.",
        u'status_port': "Defines the TCP port that the server listens on for status requests.",
        u'stdout': "Log to stdout. Defaults to on.",
        u'strip_vss': "When backing up Windows computers with burp protocol 1, this option allows you to prevent the VSS header data being backed up. The default is off. To restore a backup that has no VSS information on Windows, you need to give the client the '\-x' command line option.",
        u'syslog': "Log to syslog. Defaults to off.",
        u'timer_arg': "A user-definable argument to the timer script. You can have many of these. The timer_arg options can be overridden by the client configuration files in clientconfdir on the server.",
        u'timer_script': "Path to the script to run when a client connects with the timed backup option. If the script exits with code 0, a backup will run. The first two arguments are the client name and the path to the 'current' storage directory. The next three arguments are reserved, and user arguments are appended after that. An example timer script is provided. The timer_script option can be overridden by the client configuration files in clientconfdir on the server.",
        u'timestamp_format': "This allows you to tweak the format of the timestamps of individual backups. See 'man strftime' to see available substitutions. If this option is unset, burp uses \"%Y-%m-%d %H:%M:%S\".",
        u'umask': "Set the file creation umask. Default is 0022.",
        u'user': "Run as a particular user. This can be overridden by the client configuration files in clientconfdir on the server.",
        u'version_warn': "When this is on, which is the default, a warning will be issued when the client version does not match the server version. This option can be overridden by the client configuration files in clientconfdir on the server.",
        u'vss_drives': "When backing up Windows computers, this option allows you to specify which drives have VSS snapshots taken of them. If you omit this option, burp will automatically decide based on the 'include' options. If you want no drives to have snapshots taken of them, you can specify '0'.",
        u'working_dir_recovery_method': "This option tells the server what to do when it finds the working directory of an interrupted backup (perhaps somebody pulled the plug on the server, or something). This can be overridden by the client configurations files in clientconfdir on the server. Options are... <ul><li>delete: Just delete the old working directory.</li><li>use: Convert the working directory into a complete backup.</li><li>resume: Simply continue the previous backup from the point at which it left off, at file granularity. NOTE: If the client has changed its include/exclude configuration since the backup was interrupted, the recovery method will automatically switch to 'use'.</li></ul>",
    }

    def __init__(self, app=None, conf=None):
        super(Parser, self).__init__(app, conf)
        self._logger('info', 'Parser initialized with: %s', self.conf)
        self.clientconfdir = None
        self.root = None
        if self.conf:
            self.root = os.path.dirname(self.conf)
        # first run to setup vars
        self.read_server_conf()

    def _readfile(self, f=None, client=False):
        if not f:
            return []
        if f != self.conf and not f.startswith('/'):
            if client:
                f = os.path.join(self.clientconfdir, f)
            else:
                f = os.path.join(self.root, f)
        self._logger('debug', 'reading file: %s', f)
        with codecs.open(f, 'r', 'utf-8') as ff:
            ret = [x.rstrip('\n') for x in ff.readlines()]

        return ret

    def _parse_lines_srv(self, fi):
        return self._parse_lines(fi, 'srv')

    def _parse_lines_cli(self, fi):
        return self._parse_lines(fi, 'cli')

    def _parse_lines(self, fi, mode='srv'):
        other_files = []
        dic = []
        boolean = []
        multi = []
        integer = []
        includes = []
        includes_ext = []
        for l in fi:
            if re.match('^\s*#', l):
                continue
            r = re.search('\s*(\S+)\s*=?\s*(.*)$', l)
            if r:
                key = r.group(1)
                val = r.group(2)
                if key in getattr(self, 'boolean_{}'.format(mode)):
                    boolean.append({'name': key, 'value': int(val) == 1})
                    continue
                elif key in getattr(self, 'integer_{}'.format(mode)):
                    integer.append({'name': key, 'value': int(val)})
                    continue
                if key == u'.':
                    i = val
                    if not val.startswith('/'):
                        if mode == 'srv':
                            i = os.path.join(self.root, val)
                        else:
                            i = os.path.join(self.clientconfdir, val)
                    for p in glob(i):
                        includes_ext.append({'name': p, 'value': val})
                    includes.append(val)
                    continue
                if key in getattr(self, 'multi_{}'.format(mode)):
                    found = False
                    for m in multi:
                        if m['name'] == key:
                            m['value'].append(val)
                            found = True
                            break
                    if not found:
                        multi.append({'name': key, 'value': [val]})
                    continue
                if key == u'clientconfdir':
                    if mode != 'srv':
                        continue
                    if not val.startswith('/'):
                        self.clientconfdir = os.path.join(self.root, val)
                    else:
                        self.clientconfdir = val
                dic.append({'name': key, 'value': val})

        return dic, boolean, multi, integer, includes, includes_ext

    def read_client_conf(self, client=None, conf=None):
        res = {}
        if not client and not conf:
            return res

        mconf = conf
        if not conf:
            mconf = os.path.join(self.clientconfdir, client)

        try:
            f = self._readfile(mconf, True)
        except Exception as e:
            return res

        strings, boolean, multi, integer, includes, includes_ext = self._parse_lines_cli(f)
        res['common'] = strings
        res['boolean'] = boolean
        res['integer'] = integer
        res['multi'] = multi
        res['includes'] = includes
        res['includes_ext'] = includes_ext
        res['clients'] = self.list_clients()

        return res

    def read_server_conf(self, conf=None):
        mconf = None
        res = {}
        if not conf:
            mconf = self.conf
        else:
            mconf = conf
        if not mconf:
            return res

        try:
            f = self._readfile(mconf)
        except Exception as e:
            return res

        strings, boolean, multi, integer, includes, includes_ext = self._parse_lines_srv(f)
        res['common'] = strings
        res['boolean'] = boolean
        res['integer'] = integer
        res['multi'] = multi
        res['includes'] = includes
        res['includes_ext'] = includes_ext
        res['clients'] = self.list_clients()

        return res

    def list_clients(self):
        if not self.clientconfdir:
            return []
        res = []
        for f in os.listdir(self.clientconfdir):
            ff = os.path.join(self.clientconfdir, f)
            if os.path.isfile(ff) and not f.startswith('.') and not f.endswith('~'):
                res.append({'name': f, 'value': os.path.join(self.clientconfdir, f)})

        return res

    def store_server_conf(self, data, conf=None):
        mconf = None
        if not conf:
            mconf = self.conf
        else:
            mconf = conf
            if mconf != self.conf and not mconf.startswith('/'):
                mconf = os.path.join(self.root, mconf)
        if not mconf:
            return [[1, 'Sorry, no configuration file defined']]
        orig = []
        ref = '{}.bui.init.back'.format(mconf)
        bak = '{}.bak'.format(mconf)
        if not os.path.isfile(ref):
            try:
                shutil.copy(mconf, ref)
            except Exception as e:
                return [[2, str(e)]]
        else:
            try:
                shutil.copy(mconf, bak)
            except Exception as e:
                return [[2, str(e)]]

        errs = []
        for key in data.keys():
            if key in self.files:
                d = data.get(key)
                if not os.path.isfile(d):
                    typ = 'strings'
                    if key in self.multi_srv:
                        typ = 'multis'
                    elif key in self.boolean_srv:
                        typ = 'bools'
                    elif key in self.integer_srv:
                        typ = 'integers'
                    # highlight the wrong parameters
                    errs.append([2, "Sorry, the file '{}' does not exist".format(d), key, typ])
        if errs:
            return errs

        with codecs.open(mconf, 'r', 'utf-8') as ff:
            orig = [x.rstrip('\n') for x in ff.readlines()]

        oldkeys = [self._get_line_key(x) for x in orig]
        newkeys = list(set(data.viewkeys()) - set(oldkeys))

        already_multi = []
        already_file = []
        written = []

        with codecs.open(mconf, 'w', 'utf-8') as f:
            # f.write('# Auto-generated configuration using Burp-UI\n')
            for line in orig:
                if (self._line_removed(line, data.viewkeys()) and
                        not self._line_is_comment(line) and
                        not self._line_is_file_include(line)):
                    # The line was removed, we comment it
                    f.write('#{}\n'.format(line))
                elif self._line_is_file_include(line):
                    # The line is a file inclusion, we check if the line was already present
                    ori = self._include_get_file(line)
                    if ori in data.getlist('includes_ori'):
                        idx = data.getlist('includes_ori').index(ori)
                        file = data.getlist('includes')[idx]
                        self._write_key(f, '.', file)
                        already_file.append(file)
                    else:
                        f.write('#{}\n'.format(line))
                elif self._get_line_key(line, False) in data.viewkeys():
                    # The line is still present or has been un-commented, rewrite it with eventual changes
                    key = self._get_line_key(line, False)
                    if key not in already_multi:
                        self._write_key(f, key, data)
                    if key in self.multi_srv:
                        already_multi.append(key)
                    written.append(key)
                else:
                    # The line was empty or a comment...
                    f.write('{}\n'.format(line))
            # Write the new keys
            for key in newkeys:
                if key not in written and key not in ['includes', 'includes_ori']:
                    self._write_key(f, key, data)
            # Write the rest of file inclusions
            for file in data.getlist('includes'):
                if file not in already_file:
                    self._write_key(f, '.', file)

        return [[0, 'Configuration successfully saved.']]

    def _write_key(self, f, key, data):
        if key in self.boolean_srv:
            val = 0
            if data.get(key) == 'true':
                val = 1
            f.write('{} = {}\n'.format(key, val))
        elif key == '.':
            f.write('. {}\n'.format(data))
        elif key in self.multi_srv:
            for val in data.getlist(key):
                f.write('{} = {}\n'.format(key, val))
        else:
            f.write('{} = {}\n'.format(key, data.get(key)))

    def _line_is_comment(self, line):
        if not line:
            return False
        return line.startswith('#')

    def _line_is_file_include(self, line):
        if not line:
            return False
        return line.startswith('.')

    def _include_get_file(self, line):
        if not line:
            return None
        _, file = re.split('\s+', line, 1)
        return file

    def _get_line_key(self, line, ignore_comments=True):
        if not line:
            return ''
        if '=' not in line:
            return line
        (key, rest) = re.split('\s+|=', line, 1)
        if not ignore_comments:
            key = key.strip('#')
        return key.strip()

    def _line_removed(self, line, keys):
        if not line:
            return False
        (key, _) = re.split('\s+|=', line, 1)
        key = key.strip()
        return key not in keys

    def get_priv_attr(self, key):
        try:
            return getattr(self, key)
        except:
            return None
