# -*- coding: utf8 -*-
import re
import os
import sys
import shutil
import codecs

from burpui.misc.utils import human_readable as _hr
from burpui.misc.parser.interface import BUIparser

def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        return sys.exc_info()[2].tb_frame.f_back

class Parser(BUIparser):
    defaults_server = {
            u'mode': '',
            u'address': '', #IP
            u'port': 4971, #int
            u'status_port': 4972, #int
            u'status_address': '', #127.0.0.1 / ::1
            u'daemon': 1, #bool
            u'fork': 1, #bool
            u'directory': '',
            u'directory_tree': 1, #bool
            u'timestamp_format': '',
            u'password_check': 1, #bool
            u'clientconfdir': '', #dir
            u'pidfile': '',
            u'syslog': 0, #bool
            u'stdout': 1, #bool
            u'keep': 168, #multi #int
            u'hardlinked_archive': 0, #bool
            u'max_hardlinks': 10000, #int
            u'librsync': 1, #bool
            u'compression': 'zlib9',
            u'version_warn': 1, #bool
            u'path_length_warn': 1, #bool
            u'protocol': 0, #int
            u'client_lockdir': '',
            u'user': '',
            u'group': '',
            u'umask': 0022, #int #mode
            u'ratelimit': 0, #int
            u'network_timeout': 7200, #int
            u'working_dir_recovery_method': '',
            u'client_can_delete': 1, #bool
            u'client_can_diff': 1, #bool
            u'client_can_force_backup': 1, #bool
            u'client_can_list': 1, #bool
            u'client_can_restore': 1, #bool
            u'client_can_verify': 1, #bool
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
            u'notify_success_warnings_only': 0, #bool
            u'notify_success_changes_only': 0, #bool
            u'notify_failure_script': '', #file
            u'notify_failure_arg': '', #multi
            u'dedup_group': '',
            u'server_script_pre': '', #file
            u'server_script_pre_arg': '', #multi
            u'server_script_pre_notify': 0, #bool
            u'server_script_post': '', #file
            u'server_script_post_arg': '', #multi
            u'server_script_post_notify': 0, #bool
            u'server_script': '', #file
            u'server_script_arg': '', #multi
            u'server_script_notify': 0, #bool
            u'server_script_post_run_on_fail': 0, #bool
            u'autoupgrade_dir': '', #dir
            u'ca_conf': '', #file
            u'ca_name': '',
            u'ca_server_name': '',
            u'ca_burp_ca': '', #file
            u'monitor_browse_cache': 0, #bool
        }
    values_server = {
            u'mode': ['client', 'server'],
            u'status_address': ['127.0.0.1', '::1'], #127.0.0.1 / ::1
            u'compression': ['zlib{0}'.format(x) for x in range(1, 10)],
            u'ssl_compression': ['zlib{0}'.format(x) for x in range(1, 10)],
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
            u'ca_burp_ca'
        ]
    multi = [
            u'keep',
            u'restore_client',
            u'notify_success_arg',
            u'notify_failure_arg',
            u'timer_arg',
            u'server_script_arg',
            u'server_script_pre_arg',
            u'server_script_post_arg'
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
            u'monitor_browse_cache'
        ]
    integer = [
            u'port',
            u'status_port',
            u'keep',
            u'max_hardlinks',
            u'protocol',
            u'ratelimit',
            u'network_timeout',
            u'max_children',
            u'max_status_children',
            u'max_storage_subdirs'
        ]

    #def __init__(self, app=None, conf=None):
        #self._logger('info', 'temporary dir: %s', self.tmpdir)

    def _logger(self, level, *args):
        if self.app:
            logs = {
                'info': self.app.logger.info,
                'error': self.app.logger.error,
                'debug': self.app.logger.debug,
                'warning': self.app.logger.warning
            }
            if level in logs:
                """
                Try to guess where was call the function
                """
                cf = currentframe()
                if cf is not None:
                    cf = cf.f_back
                    """
                    Ugly hack to reformat the message
                    """
                    ar = list(args)
                    if isinstance(ar[0], str):
                        ar[0] = '('+str(cf.f_lineno)+') '+ar[0]
                    else:
                        ar = ['('+str(cf.f_lineno)+') {0}'.format(ar)]
                    args = tuple(ar)
                logs[level](*args)

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
        dic = {}
        boolean = []
        multi = {}
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
                    if not key in multi:
                        multi[key] = []
                    multi[key].append(val)
                    continue
                dic[key] = val

        return dic, boolean, multi, integer, other_files

    def readfile(self):
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

    def getkey(self, key):
        try:
            return getattr(self, key)
        except:
            return None
