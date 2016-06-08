# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.parser.burp1
    :platform: Unix
    :synopsis: Burp-UI configuration file parser for Burp1.
.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import re
import os
import json
import shutil
import codecs

from copy import deepcopy
from glob import glob
from hashlib import md5
from six import iteritems

from .doc import Doc
from .utils import Config, File
from .openssl import OSSLConf
from ...exceptions import BUIserverException


class Parser(Doc):
    """:class:`burpui.misc.parser.burp1.Parser` provides a consistent interface
    to parse burp configuration files.

    It implements :class:`burpui.misc.parser.interface.BUIparser`.
    """
    pver = 1

    def __init__(self, backend=None):
        """
        :param backend: Backend context
        :type backend: :class:`burpui.misc.backend.burp1.Burp`
        """
        self.backend = backend
        self.conf = backend.burpconfsrv
        self.confcli = backend.burpconfcli
        self.logger.info('Parser initialized with: {}'.format(self.conf))
        self.clients = []
        self.server_conf = {}
        self.client_conf = {}
        self.clientconfdir = None
        self.workingdir = None
        self.root = None
        self.md5 = {}
        self.filecache = {}
        if self.conf:
            self.root = os.path.dirname(self.conf)
        # first run to setup vars
        self._load_all_conf()
        ca_conf = self.server_conf.get('ca_conf')
        if self._is_secure_path(ca_conf):
            self.openssl_conf = OSSLConf(ca_conf)
        else:
            self.openssl_conf = OSSLConf(os.devnull)

    @staticmethod
    def _line_is_comment(line):
        """Check whether a given line is a comment or not"""
        if not line:
            return False
        return line.startswith('#')

    @staticmethod
    def _line_is_file_include(line):
        """Check whether a given line is a file inclusion or not"""
        if not line:
            return False
        return line.startswith('.')

    @staticmethod
    def _include_get_file(line):
        """Return the path of the included file(s)"""
        if not line:
            return None
        _, fil = re.split(r'\s+', line, 1)
        return fil

    @staticmethod
    def _get_line_key(line, ignore_comments=True):
        """Return the key of a given line"""
        if not line:
            return ''
        if '=' not in line:
            return line
        (key, _) = re.split(r'\s+|=', line, 1)
        if not ignore_comments:
            key = key.strip('#')
        return key.strip()

    @staticmethod
    def _line_removed(line, keys):
        """Check whether a given line has been removed in the updated version"""
        if not line:
            return False
        (key, _) = re.split(r'\s+|=', line, 1)
        key = key.strip()
        return key not in keys

    @staticmethod
    def _md5(path):
        """Return the md5sum of a given file"""
        hash_md5 = md5()
        with open(path, "rb") as bfile:
            for chunk in iter(lambda: bfile.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _file_changed(self, path):
        """Check whether a given file has changed since last read"""
        chksum = self._md5(path)
        if path in self.md5 and self.md5[path] == chksum:
            self.logger.debug("'{}' is already in cache".format(path))
            return False, chksum
        return True, chksum

    def _refresh_cache(self, purge=False):
        """Force cache refresh"""
        # empty all the caches
        if purge:
            self.server_conf = {}
            self.client_conf = {}
            self.md5 = {}
            self.filecache = {}
        self._list_clients(True)

    def _load_conf_srv(self):
        """Load the server configuration file"""
        self.server_conf = Config()
        data, path, cached = self._readfile(self.conf)
        if not cached:
            parsed = self._parse_lines(data, path, 'srv')
            self.server_conf.add_file(parsed, self.conf)
            self.server_conf.set_default(self.conf)
        self._parse_conf_recursive(self.server_conf)

    def _load_conf_cli(self, name=None):
        """Load a given client configuration file (or all)"""
        if name:
            clients = [name]
        else:
            clients = self._list_clients(True)

        for cli in clients:
            self.client_conf[cli['name']] = deepcopy(self.server_conf)
            data, path, cached = self._readfile(cli['value'])
            if not cached:
                parsed = self._parse_lines(data, path, 'cli')
                self.client_conf[cli['name']].add_file(parsed, path)
                self.client_conf[cli['name']].set_default(path)
            self._parse_conf_recursive(
                self.client_conf[cli['name']],
                client=True
            )

    def _load_all_conf(self):
        """Load all configurations"""
        self._load_conf_srv()
        self._load_conf_cli()

    def _parse_conf_recursive(self, conf=None, parsed=None, client=False):
        """Parses a conf recursively

        :param conf: Configuration to parse
        :type conf: :class:`burpui.misc.parser.utils.Config`

        :param parsed: Current configuration being parsed
        :type parsed: :class:`burpui.misc.parser.utils.File`

        :param mode: Parser mode
        :type mode: str
        """
        if not conf:
            return

        mode = 'srv'
        if client:
            mode = 'cli'

        curr = parsed
        if not parsed:
            curr = conf.get_default()

        for key, val in iteritems(curr.flatten('include', False)):
            for path in val:
                fil, path, cached = self._readfile(path, client)
                if not cached:
                    tmp = self._parse_lines(fil, path, mode)
                    conf.add_file(tmp, path)
                    self._parse_conf_recursive(conf, tmp, client)

    def _readfile(self, path=None, client=False):
        ret = []
        if not path:
            return ret, path, False
        if not self._is_secure_path(path):
            return ret, path, False
        if path != self.conf and not path.startswith('/'):
            if client:
                path = os.path.join(self.clientconfdir, path)
            else:
                path = os.path.join(self.root, path)

        changed, chksum = self._file_changed(path)
        if not changed:
            return self.filecache[path]['raw'], path, True

        self.logger.debug('reading file: {}'.format(path))
        try:
            with codecs.open(path, 'r', 'utf-8') as fil:
                ret = [x.rstrip('\n') for x in fil.readlines()]
        except IOError:
            return ret, path, False

        self.filecache[path] = {'raw': ret}
        self.md5[path] = chksum

        return ret, path, False

    def _parse_lines(self, data, name=None, mode='srv'):
        conffile = File(self, name, mode=mode)
        for line in data:
            if re.match(r'^\s*#', line):
                continue
            res = re.search(r'\s*([^=\s]+)\s*=?\s*(.*)$', line)
            if res:
                key = res.group(1)
                val = res.group(2)
                # We are gonna use this for server-side initiated restoration
                if mode == 'srv' and key == u'directory':
                    self.workingdir = val
                if key == u'clientconfdir':
                    if mode == 'srv':
                        if not val.startswith('/'):
                            self.clientconfdir = os.path.join(self.root, val)
                        else:
                            self.clientconfdir = val
                elif key == u'compression':
                    val = val.replace('zlib', 'gzip')
                elif key == u'ssl_compression':
                    val = val.replace('gzip', 'zlib')
                conffile[key] = val

        return conffile

    def _is_secure_path(self, path=None):
        """Check if the accessed path is allowed or not"""
        if not path:
            return False
        if not self.backend.includes:
            # don't check
            return True
        path = os.path.normpath(path)
        cond = [path.startswith(x) for x in self.backend.includes.split(',')]
        if not any(cond):
            self.logger.warning(
                'Tried to access non-allowed path: {}'.format(path)
            )
            return False
        return True

    def _list_clients(self, force=False):
        if not self.clientconfdir:
            return []

        if self.clients and not force:
            return self.clients

        res = []
        for cli in os.listdir(self.clientconfdir):
            full_file = os.path.join(self.clientconfdir, cli)
            if (os.path.isfile(full_file) and not cli.startswith('.')
                    and not cli.endswith('~')):
                res.append({
                    'name': cli,
                    'value': full_file
                })

        self.clients = res
        return res

    def _write_key(self, fil, key, data, conf, mode=None):
        if key in self.boolean_srv or key in self.boolean_cli:
            val = 0
            if data.get(key) == 'true':
                val = 1
            conf[key] = (val == 1)
            fil.write('{} = {}\n'.format(key, val))
        elif key == '.':
            conf[key] = data
            fil.write('. {}\n'.format(data))
        elif key in self.multi_srv or key in self.multi_cli:
            conf[key] = data.getlist(key)
            for val in data.getlist(key):
                fil.write('{} = {}\n'.format(key, val))
        else:
            val = data.get(key)
            # special key
            if key == 'clientconfdir' and mode == 'srv' and \
                    val != self.clientconfdir:
                self.clientconfdir = val
                self._refresh_cache(purge=True)
            if key == 'ca_conf' and mode == 'srv' and \
                    val != self.server_conf.get(key):
                self.openssl_conf = OSSLConf(val)
            fil.write('{} = {}\n'.format(key, val))
            conf[key] = val

    def _get_server_path(self, name=None, fil=None):
        """Returns the path of the 'server *fil*' file"""
        self.read_server_conf()

        if not name:
            raise BUIserverException('Missing name')

        if not self.workingdir:
            raise BUIserverException('Unable to find burp spool dir')

        found = False
        for cli in self.clients:
            if cli['name'] == name:
                found = True
                break

        if not found:
            raise BUIserverException('Client \'{}\' not found'.format(name))

        return os.path.join(self.workingdir, name, fil)

    def _get_server_restore_path(self, name=None):
        """Returns the path of the 'server restore' file"""
        return self._get_server_path(name, 'restore')

    def _get_server_backup_path(self, name=None):
        """Returns the path of the 'server backup' file"""
        return self._get_server_path(name, 'backup')

    def path_expander(self, pattern=None, source=None, client=None):
        """See :func:`burpui.misc.parser.interface.BUIparser.path_expander`"""
        if not pattern:
            return []
        if not pattern.startswith('/'):
            if source and (source.startswith(self.clientconfdir) or
                           source.startswith(self.root)):
                pattern = os.path.join(os.path.dirname(source), pattern)
            elif client:
                pattern = os.path.join(self.clientconfdir, pattern)
            else:
                pattern = os.path.join(self.root, pattern)
        if not re.search(r'\?|\*|\[.*\]', pattern):
            return [pattern] if self._is_secure_path(pattern) else []
        else:
            return [
                x for x in glob(pattern)
                if os.path.isfile(x) and not x.endswith('~') and
                not x.endswith('.back') and self._is_secure_path(x)
            ]

    def remove_client(self, client=None, delcert=False, revoke=False):
        """See :func:`burpui.misc.parser.interface.BUIparser.remove_client`"""
        res = []
        if not client:
            return [[2, "No client provided"]]
        try:
            path = os.path.join(self.clientconfdir, client)
            os.unlink(path)
            res.append([0, "'{}' successfully removed".format(client)])
            if client in self.client_conf:
                del self.client_conf[client]
            if path in self.md5:
                # we always set both at the same time so we are sure both exist
                del self.md5[path]
                del self.filecache[path]
            if revoke and self.backend.cli.revocation_enabled():
                # revoke cert
                pass
            if delcert:
                ca_dir = self.openssl_conf.values.get('CA_DIR')

            self._refresh_cache()
        except OSError as exp:
            res.append([2, str(exp)])
        return res

    def read_client_conf(self, client=None, conf=None):
        """
        See :func:`burpui.misc.parser.interface.BUIparser.read_client_conf`
        """
        res = {
            u'common': [],
            u'boolean': [],
            u'integer': [],
            u'multi': [],
            u'includes': [],
            u'includes_ext': [],
            u'clients': self._list_clients(),
        }
        if not client and not conf:
            return res

        mconf = conf
        if not conf:
            if not self.clientconfdir:
                return res
            mconf = os.path.join(self.clientconfdir, client)

        try:
            fil, path, cache = self._readfile(mconf, True)
        except Exception:
            return res

        if cache and 'parsed' in self.filecache[path]:
            res.update(self.filecache[path]['parsed'])
            return res

        parsed = self.client_conf[client].get_file(path)
        res2 = {}
        res2[u'common'] = parsed.string
        res2[u'boolean'] = parsed.boolean
        res2[u'integer'] = parsed.integer
        res2[u'multi'] = parsed.multi
        res2[u'includes'] = parsed.flatten('include', False).keys()
        res2[u'includes_ext'] = parsed.include

        self.filecache[path]['parsed'] = res2

        res.update(res2)
        return res

    def read_server_conf(self, conf=None):
        """
        See :func:`burpui.misc.parser.interface.BUIparser.read_server_conf`
        """
        mconf = None
        res = {
            u'common': [],
            u'boolean': [],
            u'integer': [],
            u'multi': [],
            u'includes': [],
            u'includes_ext': [],
            u'clients': self._list_clients(),
        }
        if not conf:
            mconf = self.conf
        else:
            mconf = conf
        if not mconf:
            return res

        try:
            fil, path, cache = self._readfile(mconf)
        except Exception:
            return res

        if cache and 'parsed' in self.filecache[path]:
            res.update(self.filecache[path]['parsed'])
            return res

        parsed = self.server_conf.get_file(path)
        res2 = {}
        res2[u'common'] = parsed.string
        res2[u'boolean'] = parsed.boolean
        res2[u'integer'] = parsed.integer
        res2[u'multi'] = parsed.multi
        res2[u'includes'] = parsed.flatten('include', False).keys()
        res2[u'includes_ext'] = parsed.include

        self.filecache[path]['parsed'] = res2

        res.update(res2)
        return res

    def list_clients(self):
        """See :func:`burpui.misc.parser.interface.BUIparser.list_clients`"""
        self.read_server_conf()
        if not self.clientconfdir:
            return []

        return self._list_clients()

    def store_client_conf(self, data, client=None, conf=None):
        """
        See :func:`burpui.misc.parser.interface.BUIparser.store_client_conf`
        """
        if conf and not conf.startswith('/'):
            conf = os.path.join(self.clientconfdir, conf)
        if not conf and not client:
            return [[2, 'Sorry, no client defined']]
        elif client and not conf:
            conf = os.path.join(self.clientconfdir, client)
        ret = self.store_conf(data, conf, client, mode='cli')
        self._refresh_cache()  # refresh client list
        return ret

    def store_conf(self, data, conf=None, client=None, mode='srv'):
        """See :func:`burpui.misc.parser.interface.BUIparser.store_conf`"""
        mconf = None
        if not conf:
            mconf = self.conf
        else:
            mconf = conf
            if mconf != self.conf and not mconf.startswith('/'):
                mconf = os.path.join(self.root, mconf)
        if not mconf:
            return [[1, 'Sorry, no configuration file defined']]

        if not self._is_secure_path(mconf):
            return [
                [
                    2,
                    'Sorry you are not allowed to access this path:'
                    ' {}'.format(mconf)
                ]
            ]

        dirname = os.path.dirname(mconf)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except OSError as exp:
                return [[1, str(exp)]]

        ref = '{}.bui.init.back~'.format(mconf)
        bak = '{}.back~'.format(mconf)

        if not os.path.isfile(ref) and os.path.isfile(mconf):
            try:
                shutil.copy(mconf, ref)
            except IOError as exp:
                return [[2, str(exp)]]
        elif os.path.isfile(mconf):
            try:
                shutil.copy(mconf, bak)
            except IOError as exp:
                return [[2, str(exp)]]

        if client:
            conffile = self.client_conf[client].get_file(mconf)
        else:
            conffile = self.server_conf.get_file(mconf)

        errs = []
        for key in data.keys():
            if key in self.files:
                dat = data.get(key)
                if not os.path.isfile(dat):
                    typ = 'strings'
                    if key in getattr(self, 'multi_{}'.format(mode)):
                        typ = 'multis'
                    elif key in getattr(self, 'boolean_{}'.format(mode)):
                        typ = 'bools'
                    elif key in getattr(self, 'integer_{}'.format(mode)):
                        typ = 'integers'
                    # highlight the wrong parameters
                    errs.append([
                        2,
                        "Sorry, the file '{}' does not exist".format(dat),
                        key,
                        typ
                    ])
        if errs:
            return errs

        orig = []
        try:
            with codecs.open(mconf, 'r', 'utf-8') as fil:
                orig = [x.rstrip('\n') for x in fil.readlines()]
        except:
            pass

        oldkeys = [self._get_line_key(x) for x in orig]
        newkeys = list(set(data.viewkeys()) - set(oldkeys))

        already_multi = []
        already_file = []
        written = []

        try:
            with codecs.open(mconf, 'w', 'utf-8') as fil:
                # f.write('# Auto-generated configuration using Burp-UI\n')
                for line in orig:
                    if (self._line_removed(line, data.viewkeys()) and
                            not self._line_is_comment(line) and
                            not self._line_is_file_include(line)):
                        # The line was removed, we comment it
                        fil.write('#{}\n'.format(line))
                        del conffile[self._get_line_key(line)]
                    elif self._line_is_file_include(line):
                        # The line is a file inclusion, we check if the line
                        # was already present
                        ori = self._include_get_file(line)
                        if ori in data.getlist('includes_ori'):
                            idx = data.getlist('includes_ori').index(ori)
                            inc = data.getlist('includes')[idx]
                            self._write_key(fil, '.', inc, conf=conffile)
                            already_file.append(inc)
                        else:
                            fil.write('#{}\n'.format(line))
                            del conffile[ori]
                    elif self._get_line_key(line, False) in data.viewkeys():
                        # The line is still present or has been un-commented,
                        # rewrite it with eventual changes
                        key = self._get_line_key(line, False)
                        if key not in already_multi:
                            self._write_key(
                                fil,
                                key,
                                data,
                                conf=conffile,
                                mode=mode
                            )
                        if key in getattr(self, 'multi_{}'.format(mode)):
                            already_multi.append(key)
                        written.append(key)
                    else:
                        # The line was empty or a comment...
                        fil.write('{}\n'.format(line))
                # Write the new keys
                for key in newkeys:
                    if (key not in written and
                            key not in ['includes', 'includes_ori']):
                        self._write_key(
                            fil,
                            key,
                            data,
                            conf=conffile,
                            mode=mode
                        )
                # Write the rest of file inclusions
                for inc in data.getlist('includes'):
                    if inc not in already_file:
                        self._write_key(fil, '.', inc, conf=conffile)
        except Exception as exp:
            return [[2, str(exp)]]

        return [[0, 'Configuration successfully saved.']]

    def cancel_restore(self, name=None):
        """See :func:`burpui.misc.parser.interface.BUIparser.cancel_restore`"""
        path = self._get_server_restore_path(name)
        try:
            if os.path.exists(path):
                os.unlink(path)
            else:
                return [1, 'There is no restoration scheduled for this client']
        except OSError as exp:
            return [2, 'Unable to cancel restoration: {}'.format(str(exp))]
        return [0, 'Restoration successfully canceled']

    def read_restore(self, name=None):
        """See :func:`burpui.misc.parser.interface.BUIparser.read_restore`"""
        path = self._get_server_restore_path(name)

        try:
            ret = {}
            with codecs.open(path, 'r', 'utf-8') as restore:
                for line in restore.readlines():
                    line = line.rstrip()
                    (key, val) = re.split(r' *= *', line)
                    if key == 'regex':
                        ret['list'] = []
                        for reg in val.split('|'):
                            reg = reg.replace('^', '', 1)
                            reg = reg.replace('\\', '')
                            if reg.endswith('$'):
                                ret['list'].append(
                                    {'key': reg.rstrip('$'), 'folder': False}
                                )
                            else:
                                ret['list'].append({'key': reg, 'folder': True})
                    else:
                        ret[key] = val
                ret['found'] = True
                ret['to'] = name

            return ret
        except Exception:
            return {}

    def server_initiated_restoration(
            self, name=None, backup=None, files=None,
            strip=None, force=None, prefix=None, restoreto=None):
        """See
        :func:`burpui.misc.parser.interface.BUIparser.server_initiated_restoration`
        """
        if not name or not backup or not files:
            raise BUIserverException('At least one argument is missing')

        if self.read_backup(name):
            raise BUIserverException(
                'A backup is already scheduled. Cannot schedule both restore'
                ' and backup at the same time.'
            )

        flist = json.loads(files)
        if 'restore' not in flist:
            raise BUIserverException('Wrong call')

        full_reg = ur''
        for rest in flist['restore']:
            reg = ur''
            if rest['folder'] and rest['key'] != '/':
                reg += '^' + re.escape(rest['key']) + '/|'
            else:
                reg += '^' + re.escape(rest['key']) + '$|'
            full_reg += reg

        try:
            client = name
            if restoreto:
                found = False
                for cli in self.clients:
                    if cli['name'] == restoreto:
                        found = True
                        break

                if not found:
                    raise BUIserverException(
                        'Client \'{}\' not found'.format(restoreto)
                    )

                client = restoreto

            path = self._get_server_restore_path(client)
            with codecs.open(path, 'w', 'utf-8') as fil:
                fil.write('backup = {}\n'.format(backup))
                fil.write('regex = {}\n'.format(full_reg.rstrip('|')))
                if strip:
                    fil.write('strip = {}\n'.format(strip))
                if prefix:
                    fil.write('restoreprefix = {}\n'.format(prefix))
                if force:
                    fil.write('overwrite = 1\n')
                if restoreto:
                    fil.write('orig_client = {}\n'.format(name))

            return [0, 'Server-initiated restoration successfully scheduled']

        except Exception as exp:
            return [
                2,
                "Unable to schedule a server-initiated restoration:"
                " {}".format(str(exp))
            ]

    def cancel_backup(self, name=None):
        """See :func:`burpui.misc.parser.interface.BUIparser.cancel_backup`"""
        path = self._get_server_backup_path(name)
        try:
            if os.path.exists(path):
                os.unlink(path)
            else:
                return [1, 'There is no backup scheduled for this client']
        except OSError as exp:
            return [2, 'Unable to cancel backup: {}'.format(str(exp))]
        return [0, 'Backup successfully canceled']

    def read_backup(self, name=None):
        """See :func:`burpui.misc.parser.interface.BUIparser.read_backup`"""
        path = self._get_server_backup_path(name)
        ret = os.path.exists(path)
        return ret

    def server_initiated_backup(self, name=None):
        """See
        :func:`burpui.misc.parser.interface.BUIparser.server_initiated_backup`
        """

        if self.read_restore(name):
            raise BUIserverException(
                'A restoration is already scheduled. Cannot schedule both'
                ' restore and backup at the same time.'
            )

        path = self._get_server_backup_path(name)
        try:
            with open(path, 'w'):
                os.utime(path, None)
        except OSError as exp:
            return [
                2,
                'Unable to schedule a server-initiated backup:'
                ' {}'.format(str(exp))
            ]
        return [0, 'Backup successfully scheduled']
