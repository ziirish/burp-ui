# -*- coding: utf8 -*-
import re
import os
import shutil
import codecs

from burpui.misc.utils import human_readable as _hr, BUIlogging
from burpui.misc.parser.interface import BUIparser

class Parser(BUIparser,BUIlogging):
    defaults_server = {
            u'mode': '',
            u'address': '', #IP
            u'port': 4971, #int
            u'status_port': 4972, #int
            u'status_address': '', #127.0.0.1 / ::1
            u'daemon': True, #bool
            u'fork': True, #bool
            u'directory': '',
            u'directory_tree': True, #bool
            u'timestamp_format': '',
            u'password_check': True, #bool
            u'clientconfdir': '', #dir
            u'pidfile': '',
            u'syslog': False, #bool
            u'stdout': True, #bool
            u'keep': [7, 6, 4], #multi #int
            u'hardlinked_archive': False, #bool
            u'max_hardlinks': 10000, #int
            u'librsync': True, #bool
            u'compression': 'gzip9',
            u'version_warn': True, #bool
            u'path_length_warn': True, #bool
            u'protocol': False, #int
            u'client_lockdir': '',
            u'user': '',
            u'group': '',
            u'umask': 0022, #mode
            u'ratelimit': False, #int
            u'network_timeout': 7200, #int
            u'working_dir_recovery_method': '',
            u'client_can_delete': True, #bool
            u'client_can_diff': True, #bool
            u'client_can_force_backup': True, #bool
            u'client_can_list': True, #bool
            u'client_can_restore': True, #bool
            u'client_can_verify': True, #bool
            u'restore_client': '', #multi
            u'ssl_cert_ca': '', #file
            u'ssl_cert': '', #file
            u'ssl_key': '', #file
            u'ssl_key_password': '',
            u'ssl_ciphers': '',
            u'ssl_compression': 'zlib5',
            u'ssl_dhfile': '', #file
            u'max_children': 5, #int
            u'max_status_children': 5, #int
            u'max_storage_subdirs': 30000, #int
            u'timer_script': '', #file
            u'timer_arg': '', #multi
            u'notify_success_script': '', #file
            u'notify_success_arg': '', #multi
            u'notify_success_warnings_only': False, #bool
            u'notify_success_changes_only': False, #bool
            u'notify_failure_script': '', #file
            u'notify_failure_arg': '', #multi
            u'dedup_group': '',
            u'server_script_pre': '', #file
            u'server_script_pre_arg': '', #multi
            u'server_script_pre_notify': False, #bool
            u'server_script_post': '', #file
            u'server_script_post_arg': '', #multi
            u'server_script_post_notify': False, #bool
            u'server_script': '', #file
            u'server_script_arg': '', #multi
            u'server_script_notify': False, #bool
            u'server_script_post_run_on_fail': False, #bool
            u'autoupgrade_dir': '', #dir
            u'ca_conf': '', #file
            u'ca_name': '',
            u'ca_server_name': '',
            u'ca_burp_ca': '', #file
            u'monitor_browse_cache': False, #bool
            u'hard_quota': '',
            u'soft_quota': '',
        }
    placeholders = {
            u'port': "port number",
            u'status_port': "port number",
            u'daemon': "0|1",
            u'fork': "0|1",
            u'directory': "path",
            u'directory_tree': "0|1",
            u'timestamp_format': "strftime format",
            u'password_check': "0|1",
            u'manual_delete': "path",
            u'clientconfdir': "path",
            u'lockfile': "path",
            u'pidfile': "path",
            u'syslog': "0|1",
            u'stdout': "0|1",
            u'keep': "number",
            u'hardlinked_archive': "0|1",
            u'max_hardlinks': "number",
            u'librsync': "0|1",
            u'compression': "gzip[0-9]",
            u'hard_quota': "b/Kb/Mb/Gb",
            u'soft_quota': "b/Kb/Mb/Gb",
            u'version_warn': "0|1",
            u'client_lockdir': "path",
            u'user': "username",
            u'group': "groupname",
            u'umask': "umask",
            u'ratelimit': "Mb/s",
            u'network_timeout': "s",
            u'working_dir_recovery_method': "resume|use|delete",
            u'resume_partial': "0|1",
            u'client_can_delete': "0|1",
            u'client_can_force_backup': "0|1",
            u'client_can_list': "0|1",
            u'client_can_restore': "0|1",
            u'client_can_verify': "0|1",
            u'restore_client': "client",
            u'ssl_cert_ca': "path",
            u'ssl_cert': "path",
            u'ssl_key': "path",
            u'ssl_key_password': "password",
            u'ssl_cert_password': "password",
            u'ssl_ciphers': "cipher list",
            u'ssl_dhfile': "path",
            u'max_children': "number",
            u'max_status_children': "number",
            u'max_storage_subdirs': "number",
            u'timer_script': "path",
            u'timer_arg': "string",
            u'notify_success_script': "path",
            u'notify_success_arg': "string",
            u'notify_success_warnings_only': "0|1",
            u'notify_success_changes_only': "0|1",
            u'notify_failure_script': "path",
            u'notify_failure_arg': "string",
            u'dedup_group': "string",
            u'server_script_pre': "path",
            u'server_script_pre_arg': "string",
            u'server_script_pre_notify': "0|1",
            u'server_script_post': "path",
            u'server_script_post_arg': "string",
            u'server_script_post_notify': "0|1",
            u'server_script': "path",
            u'server_script_arg': "path",
            u'server_script_notify': "0|1",
            u'server_script_post_run_on_fail': "0|1",
            u'autoupgrade_dir': "path",
            u'ca_conf': "path",
            u'ca_name': "name",
            u'ca_server_name': "name",
            u'ca_burp_ca': "path",
        }
    values_server = {
            u'mode': ['client', 'server'],
            u'status_address': ['127.0.0.1', '::1'], #127.0.0.1 / ::1
            u'compression': ['gzip{0}'.format(x) for x in range(1, 10)],
            u'ssl_compression': ['zlib{0}'.format(x) for x in range(1, 10)],
            u'working_dir_recovery_method': ['use', 'delete', 'resume'],
        }
    files = [
            u'ssl_cert_ca',
            u'ssl_cert',
            u'ssl_key',
            u'ssl_dhfile',
            u'timer_script',
            u'notify_success_script',
            u'notify_failure_script',
            u'server_script_pre',
            u'server_script_post',
            u'server_script',
            u'ca_conf',
            u'ca_burp_ca',
        ]
    multi = [
            u'keep',
            u'restore_client',
            u'notify_success_arg',
            u'notify_failure_arg',
            u'timer_arg',
            u'server_script_arg',
            u'server_script_pre_arg',
            u'server_script_post_arg',
        ]
    boolean = [
            u'daemon',
            u'fork',
            u'directory_tree',
            u'password_check',
            u'syslog',
            u'stdout',
            u'hardlinked_archive',
            u'librsync',
            u'version_warn',
            u'path_length_warn',
            u'client_can_delete',
            u'client_can_diff',
            u'client_can_force_backup',
            u'client_can_list',
            u'client_can_restore',
            u'client_can_verify',
            u'notify_success_warnings_only',
            u'notify_success_changes_only',
            u'server_script_pre_notify',
            u'server_script_post_notify',
            u'server_script_notify',
            u'server_script_post_run_on_fail',
            u'monitor_browse_cache',
        ]
    integer = [
            u'port',
            u'status_port',
            u'max_hardlinks',
            u'protocol',
            u'ratelimit',
            u'network_timeout',
            u'max_children',
            u'max_status_children',
            u'max_storage_subdirs',
        ]
    string = [
            u'mode',
            u'address',
            u'status_address',
            u'directory',
            u'timestamp_format',
            u'pidfile',
            u'compression',
            u'client_lockdir',
            u'user',
            u'group',
            u'working_dir_recovery_method',
            u'ssl_key_password',
            u'ssl_ciphers',
            u'ssl_compression',
            u'dedup_group',
            u'ca_name',
            u'ca_server_name',
            u'ssl_cert_ca',
            u'ssl_cert',
            u'ssl_key',
            u'ssl_dhfile',
            u'ca_conf',
            u'ca_burp_ca',
            u'notify_success_script',
            u'notify_failure_script',
            u'server_script_pre',
            u'server_script_post',
            u'server_script',
            u'umask',
            u'hard_quota',
            u'soft_quota',
        ]
    server_doc = {
            u'ssl_compression': "Choose the level of zlib compression over SSL. Setting 0 or zlib0 turnsSSL compression off. Setting non-zero gives zlib5 compression (it is not currently possible for openssl to set any other level). The default is 5. 'gzip' is a synonym of 'zlib'.is a synonym of 'zlib'.",
            u'address': "Defines the main TCP address that the server listens on. The default is either '::' or '0.0.0.0', dependent upon compile time options.",
            u'status_address': "Defines the main TCP address that the server listens on for status requests. The default is either '::1' or '127.0.0.1', dependent upon compile time options.",
            u'mode': "Required to run in server mode.",
            u'port': "Defines the main TCP port that the server listens on.",
            u'status_port': "Defines the TCP port that the server listens on for status requests.",
            u'daemon': "Whether to daemonise. The default is 1.",
            u'fork': "Whether to fork children. The default is 1.",
            u'directory': "Path to the directory in which to store backups.",
            u'directory_tree': "When turned on (which is the default) and the client is on version 1.3.6 or greater, the structure of the storage directory will mimic that of the original filesystem on the client.",
            u'timestamp_format': "This allows you to tweak the format of the timestamps of individual backups. See 'man strftime' to see available substitutions. If this option is unset, burp uses \"%Y-%m-%d %H:%M:%S\".",
            u'password_check': "Allows you to turn client password checking on or off. The default is on. SSL certificates will still be checked if you turn passwords off. This option can be overridden by the client configuration files in clientconfdir on the server.",
            u'manual_delete': "If a path is given, the server will move directories to be deleted into the directory specified by the path, but will not actually delete them. The path must be on the same file system as the backup storage. The idea is that a busy server may be configured to run the deletions outside of the backup timebands, when the server is less busy, via a cron job. The default is unset, which means that the server will automatically delete the directories at the end of a backup. This option can be overridden by the client configuration files in clientconfdir on the server.",
            u'clientconfdir': "Path to the directory that contains client configuration files.",
            u'lockfile': "Path to the lockfile that ensures that two server processes cannot run simultaneously.",
            u'pidfile': "Synonym for lockfile.",
            u'syslog': "Log to syslog. Defaults to off.",
            u'stdout': "Log to stdout. Defaults to on.",
            u'keep': "Number of backups to keep. This can be overridden by the client configuration files in clientconfdir on the server. Specify multiple 'keep' entries on separate lines in order to keep multiple periods of backups. For example, assuming that you are doing a backup a day, keep=7 keep=4 keep=6 (on separate lines) will keep 7 daily backups, 4 weekly backups (7x4=28), and 6 multiples of 4 weeks (7x4x6=168) - roughly 6 monthly backups. Effectively, you will be guaranteed to be able to restore up to 168 days ago, with the number of available backups exponentially decreasing as you go back in time to that point. In this example, every 7th backup will be hardlinked to allow burp to safely delete intermediate backups when necessary. You can have as many 'keep' lines as you like, as long as they don't exceed 52560000 when multiplied together. That is, a backup every minute for 100 years.",
            u'hardlinked_archive': "On the server, defines whether to keep hardlinked files in the backups, or whether to generate reverse deltas and delete the original files. Can be set to either 0 (off) or 1 (on). Disadvantage: More disk space will be used Advantage: Restores will be faster, and since no reverse deltas need to be generated, the time and effort the server needs at the end of a backup is reduced.",
            u'max_hardlinks': "On the server, the number of times that a single file can be hardlinked. The bedup program also obeys this setting. The default is 10000.",
            u'librsync': "When set to 0, delta differencing will not take place. That is, when a file changes, the server will request the whole new file. The default is 1. This option can be overridden by the client configuration files in clientconfdir on the server.",
            u'compression': "Choose the level of gzip compression for files stored in backups. Setting 0 or gzip0 turns compression off. The default is gzip9. This option can be overridden by the client configuration files in clientconfdir on the server.",
            u'version_warn': "When this is on, which is the default, a warning will be issued when the client version does not match the server version. This option can be overridden by the client configuration files in clientconfdir on the server.",
            u'path_length_warn': "When this is on, which is the default, a warning will be issued when the client sends a path that is too long to replicate in the storage area tree structure. The file will still be saved in a numbered file outside of the tree structure, regardless of the setting of this option. This option can be overridden by the client configuration files in clientconfdir on the server.",
            u'client_lockdir': "Path to the directory in which to keep per-client lock files. By default, this is set to the path given by the 'directory' option.",
            u'user': "Run as a particular user. This can be overridden by the client configuration files in clientconfdir on the server.",
            u'group': "Run as a particular group. This can be overridden by the client configuration files in clientconfdir on the server.",
            u'umask': "Set the file creation umask. Default is 0022.",
            u'ratelimit': "Set the network send rate limit, in Mb/s. If this option is not given, burp will send data as fast as it can.",
            u'network_timeout': "Set the network timeout in seconds. If no data is sent or received over a period of this length, burp will give up. The default is 7200 seconds (2 hours).",
            u'working_dir_recovery_method': "This option tells the server what to do when it finds the working directory of an interrupted backup (perhaps somebody pulled the plug on the server, or something). This can be overridden by the client configurations files in clientconfdir on the server. Options are... <ul><li>delete: Just delete the old working directory.</li><li>use: Convert the working directory into a complete backup.</li><li>resume: Simply continue the previous backup from the point at which it left off, at file granularity. NOTE: If the client has changed its include/exclude configuration since the backup was interrupted, the recovery method will automatically switch to 'use'.</li></ul>",
            u'resume_partial': "Turn this on to enable 'resume partial' code. Requires 'working_dir_recovery_method=resume'. When resuming an interrupted transfer of a single file, it attempts to use previously transferred blocks of that file in order to be more efficient. However, situations have been reported where the file on the server side just gets bigger forever, so this feature now defaults to being turned off.",
            u'client_can_delete': "Turn this off to prevent clients from deleting backups with the '-a D' option. The default is that clients can delete backups. Restore clients can override this setting.",
            u'client_can_force_backup': "Turn this off to prevent clients from forcing backups with the '-a b' option. Timed backups will still work. The default is that clients can force backups.",
            u'client_can_list': "Turn this off to prevent clients from listing backups with the '-a l' option. The default is that clients can list backups. Restore clients can override this setting.",
            u'client_can_restore': "Turn this off to prevent clients from initiating restores with the '-a r' option. The default is that clients can initiate restores. Restore clients can override this setting.",
            u'client_can_verify': "Turn this off to prevent clients from initiating a verify job with the '-a v' option. The default is that clients can initiate a verify job. Restore clients can override this setting.",
            u'restore_client': "A client that is permitted to list, verify, restore and delete files belonging to any other client. You may specify multiple restore_clients. If this is too permissive, you may set a restore_client for individual original clients in the individual clientconfdir files. Note that restoring a backup from a Windows computer onto a Linux computer will currently leave the VSS headers in place at the beginning of each file. This will be addressed in a future version of burp.",
            u'ssl_cert_ca': "The path to the SSL CA certificate. This file will probably be the same on both the server and the client. The file should contain just the certificate in PEM format. For more information on this, and the other ssl_* options, please see docs/burp_ca.txt.",
            u'ssl_cert': "The path to the server SSL certificate. It works for me when the file contains the concatenation of the certificate and private key in PEM format.",
            u'ssl_key': "The path to the server SSL private key in PEM format.",
            u'ssl_key_password': "The SSL key password.",
            u'ssl_cert_password': "Synonym for ssl_key_password.",
            u'ssl_ciphers': "Allowed SSL ciphers. See openssl ciphers for details.",
            u'ssl_dhfile': "Path to Diffie-Hellman parameter file. To generate one with openssl, use a command like this: openssl dhparam -out dhfile.pem -5 1024",
            u'max_children': "Defines the number of child processes to fork (the number of clients that can simultaneously connect. The default is 5.",
            u'max_status_children': "Defines the number of status child processes to fork (the number of status clients that can simultaneously connect. The default is 5.",
            u'max_storage_subdirs': "Defines the number of subdirectories in the data storage areas. The maximum number of subdirectories that ext3 allows is 32000. If you do not set this option, it defaults to 30000.",
            u'timer_script': "Path to the script to run when a client connects with the timed backup option. If the script exits with code 0, a backup will run. The first two arguments are the client name and the path to the 'current' storage directory. The next three arguments are reserved, and user arguments are appended after that. An example timer script is provided. The timer_script option can be overridden by the client configuration files in clientconfdir on the server.",
            u'timer_arg': "A user-definable argument to the timer script. You can have many of these. The timer_arg options can be overridden by the client configuration files in clientconfdir on the server.",
            u'notify_success_script': "Path to the script to run when a backup succeeds. User arguments are appended after the first five reserved arguments. An example notify script is provided. The notify_success_script option can be overriddden by the client configuration files in clientconfdir on the server.",
            u'notify_success_arg': "A user-definable argument to the notify success script. You can have many of these. The notify_success_arg options can be overriddden by the client configuration files in clientconfdir on the server.",
            u'notify_success_warnings_only': "Set to 1 to send success notifications when there were warnings. If this and notify_success_changes_only are not turned on, success notifications are always sent.",
            u'notify_failure_script': "The same as notify_success_script, but for backups that failed.",
            u'notify_failure_arg': "The same as notify_success_arg, but for backups that failed.",
            u'dedup_group': "Enables you to group clients together for file deduplication purposes. For example, you might want to set 'dedup_group=xp' for each Windows XP client, and then run the bedup program on a cron job every other day with the option '-g xp'.",
            u'server_script_pre': "Path to a script to run on the server after each successfully authenticated connection but before any work is carried out. The arguments to it are 'pre', '(client command)', 'reserved3' to 'reserved5', and then arguments defined by server_script_pre_arg. If the script returns non-zero, the task asked for by the client will not be run. This command and related options can be overriddden by the client configuration files in clientconfdir on the server.",
            u'server_script_pre_arg': "A user-definable argument to the server pre script. You can have many of these.",
            u'server_script_pre_notify': "Turn on to send a notification email when the server pre script returns non-zero. The output of the script will be included in the email. The default is off. Most people will not want this turned on because clients usually contact the server at 20 minute intervals and this could cause a lot of emails to be generated. Requires the notify_failure options to be set.",
            u'server_script_post': "Path to a script to run on the server before the client disconnects. The arguments to it are 'post', '(client command)', 'reserved3' to 'reserved5', and then arguments defined by server_script_post_arg. This command and related options can be overriddden by the client configuration files in clientconfdir on the server.",
            u'server_script_post_arg': "A user-definable argument to the server post script. You can have many of these.",
            u'server_script_post_notify': "Turn on to send a notification email when the server post script returns non-zero. The output of the script will be included in the email. The default is off. Requires the notify_failure options to be set.",
            u'server_script': "You can use this to save space in your config file when you want to run the same server script twice. It overrides server_script_pre and server_script_post. This command and related options can be overriddden by the client configuration files in clientconfdir on the server.",
            u'server_script_arg': "Goes with server_script and overrides server_script_pre_arg and server_script_post_arg.",
            u'server_script_notify': "Turn on to send a notification emails when the server pre and post scripts return non-zero. The output of the script will be included it the email. The default is off. Requires the notify_failure options to be set.",
            u'server_script_post_run_on_fail': "If this is set to 1, server_script_post will always be run. The default is 0, which means that if the task asked for by the client fails, server_script_post will not be run.",
            u'autoupgrade_dir': "Path to autoupgrade directory from which upgrades are downloaded. The option can be left unset in order not to autoupgrade clients. Please see docs/autoupgrade.txt in the source package for more help with this option.",
            u'ca_conf': "Path to certificate authority configuration file. The CA configuration file will usually be /etc/burp/CA.cnf. The CA directory indicated by CA.cnf will usually be /etc/burp/CA. If ca_conf is set and the CA directory does not exist, the server will create, populate it, and the paths indicated by ssl_cert_ca, ssl_cert, ssl_key and ssl_dhfile will be overwritten. For more detailed information on this and the other ca_* options, please see docs/burp_ca.txt.",
            u'ca_name': "Name of the CA that the server will generate when using the ca_conf option.",
            u'ca_server_name': "The name that the server will put into its own SSL certficates when using the ca_conf option.",
            u'ca_burp_ca': "Path to the burp_ca script when using the ca_conf option.",
            u'soft_quota': "A warning will be issued when the estimated size of all files is greater than the specified size and smaller than hard_quota. Example: 'soft_quota = 95Gb'. Set to 0 (the default) to have no warning.",
            u'hard_quota': "Do not back up the client if the estimated size of all files is greater than the specified size. Example: 'hard_quota = 100Gb'. Set to 0 (the default) to have no limit.",
        }

    #def __init__(self, app=None, conf=None):
        #self._logger('info', 'temporary dir: %s', self.tmpdir)


    def _readfile(self, f=None, sourced=False):
        if not f:
            return []
        if (f != self.conf or sourced) and not f.startswith('/'):
            root = os.path.dirname(self.conf)
            f = os.path.join(root, f)
        self._logger('debug', 'reading file: %s', f)
        with codecs.open(f, 'r', 'utf-8') as ff:
            ret = [x.strip('\n') for x in ff.readlines()]

        return ret

    def _parse_lines_srv(self, fi):
        other_files = []
        dic = []
        boolean = []
        multi = []
        integer = []
        for l in fi:
            if re.match('^\s*#', l):
                continue
            r = re.search('\s*(\S+)\s*=?\s*(.*)$', l)
            if r:
                key = r.group(1)
                val = r.group(2)
                if key in self.boolean:
                    boolean.append({'name': key, 'value': bool(val)})
                    continue
                elif key in self.integer:
                    integer.append({'name': key, 'value': int(val)})
                    continue
                if key == u'.':
                    other_files.append(val)
                    continue
                if key in self.multi:
                    found = False
                    for m in multi:
                        if m['name'] == key:
                            m['value'].append(val)
                            found = True
                            break
                    if not found:
                        multi.append({'name': key, 'value': [val]})
                    continue
                dic.append({'name': key, 'value': val})

        return dic, boolean, multi, integer, other_files

    def read_server_conf(self):
        if not self.conf:
            return []
        self.content = []
        res = {}
        other_files = []
        f = self._readfile(self.conf)

        tmp, boolean, multi, integer, other_files = self._parse_lines_srv(f)
        res['common'] = tmp
        res['boolean'] = boolean
        res['integer'] = integer
        res['multi'] = multi

        if other_files:
            while True:
                other_files2 = []
                for fi in other_files:
                    f = self._readfile(fi)
                    tmp, boolean, multi, integer, dummy2 = self._parse_lines_srv(f)
                    res['common'].update(tmp)
                    res['boolean'] += boolean
                    res['multi'].update(multi)
                    res['integer'] += integer
                    other_files2 += dummy2
                if other_files2:
                    other_files = other_files2
                else:
                    break

        return res

    def store_server_conf(self, data):
        if not self.conf:
            return [[0, 'Sorry, no configuration file defined']]
        ref = '{}.bui.init.back'.format(self.conf)
        if not os.path.isfile(ref):
            try:
                shutil.copy(self.conf, ref)
            except Exception, e:
                return [[2, str(e)]]

        with codecs.open(self.conf, 'w', 'utf-8') as f:
            f.write('# Auto-generated configuration using Burp-UI\n')
            for key in data.keys():
                if key in self.boolean:
                    val = 0
                    if data.get(key):
                        val = 1
                    f.write('{} = {}\n'.format(key, val))
                elif key in self.multi:
                    for val in data.getlist(key):
                        f.write('{} = {}\n'.format(key, val))
                else:
                    f.write('{} = {}\n'.format(key, data.get(key)))

        return [[0, 'Configuration successfully saved.']]

    def get_priv_attr(self, key):
        try:
            return getattr(self, key)
        except:
            return None
