# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.parser.burp1
    :platform: Unix
    :synopsis: Burp-UI configuration file parser for Burp1.
.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
# TODO: have a look at https://github.com/tsileo/dirtools to manage dir changes
import re
import os
import json
import codecs

from glob import glob
from six import iteritems

from .doc import Doc
from .utils import Config
from .openssl import OSSLConf, OSSLAuth
from ...exceptions import BUIserverException
from ...utils import NOTIF_ERROR, NOTIF_OK, NOTIF_WARN


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
        self._server_conf = {}
        self._client_conf = {}
        self._clients_conf = {}
        self.clientconfdir = None
        self.clientconfdir_mtime = None
        self.filescache = {}
        self._configs = {}
        self.root = None
        if self.conf:
            self.root = os.path.dirname(self.conf)
        # first run to setup vars
        self._load_all_conf()
        ca_conf = self.server_conf.get('ca_conf')
        if self._is_secure_path(ca_conf):
            self.openssl_conf = OSSLConf(ca_conf)
        else:
            self.openssl_conf = OSSLConf(os.devnull)
        self.openssl_auth = OSSLAuth(
            self.server_conf.get('ca_name'),
            self.openssl_conf,
            self.server_conf
        )

    @property
    def server_conf(self):
        if self._server_conf.changed:
            self._load_conf_srv()
        return self._server_conf

    @property
    def client_conf(self):
        if self._client_conf.changed:
            self._load_conf_cli()
        return self._client_conf

    @property
    def clients_conf(self):
        for client, conf in iteritems(self._clients_conf):
            if conf.changed:
                conf.parse(True)
        return self._clients_conf

    def _refresh_cache(self, purge=False):
        """Force cache refresh"""
        # empty all the caches
        if purge:
            self._server_conf.clear()
            self._client_conf.clear()
            self._clients_conf.clear()
        self._list_clients(True)

    def _load_conf_srv(self):
        """Load the server configuration file"""
        self._server_conf = Config(self.conf, self, 'srv')
        self._server_conf.parse()
        self.clientconfdir = self._server_conf.get('clientconfdir')

    def _load_conf_cli(self):
        """Load the client configuration file"""
        self._client_conf = Config(self.confcli, self, 'cli')
        self._client_conf.parse()

    def _load_conf_clients(self, name=None, in_path=None):
        """Load a given client configuration file (or all)"""
        if name:
            clients = [{'name': name, 'value': in_path}]
        else:
            clients = self._list_clients(True)

        for cli in clients:
            conf = self.server_conf.clone()
            path = cli['value'] or cli['name']
            if cli['name'] not in self._clients_conf:
                if not os.path.isabs(path):
                    path = os.path.join(self.clientconfdir, path)
                conf.add_file(path)
                conf.set_default(path)
                conf.parse()
                self._clients_conf[cli['name']] = conf

    def _load_all_conf(self):
        """Load all configurations"""
        self._load_conf_srv()
        self._load_conf_cli()
        self._load_conf_clients()

    def _new_client_conf(self, name, path):
        """Create new client conf"""
        self._load_conf_clients(name, path)
        return self.clients_conf[name]

    def _clientconfdir_changed(self):
        """Detect changes in clientconfdir"""
        if not self.clientconfdir:
            return False
        mtime = os.path.getmtime(self.clientconfdir)
        changed = mtime != self.clientconfdir_mtime
        if changed:
            self.clientconfdir_mtime = mtime
            return True
        return False

    def _get_client(self, name, path):
        """Return client conf and refresh it if necessary"""
        if self._clientconfdir_changed() and name not in self._clients_conf:
            self._clients_conf.clear()
            self._load_conf_clients()
        if name not in self._clients_conf:
            return self._new_client_conf(name, path)
        if self._clients_conf[name].changed:
            self._clients_conf[name].parse()
        return self._clients_conf[name]

    def _get_config(self, path, mode='cli'):
        """Return conf by it's path"""
        if path in self._configs:
            ret = self._configs[path]
        else:
            ret = Config(path, self, mode)
        if ret.changed:
            ret.parse()
        return ret

    def _is_secure_path(self, path=None):
        """Check if the accessed path is allowed or not"""
        if not path or not self.backend.includes:
            # don't check
            return True

        path = os.path.normpath(path)
        cond = [path.startswith(x) for x in self.backend.includes]
        if not any(cond):
            self.logger.warning(
                'Tried to access non-allowed path: {}'.format(path)
            )
            return False

        return True

    def _list_clients(self, force=False):
        if not self.clientconfdir:
            return []

        if self.clients and not force and not self._clientconfdir_changed():
            return self.clients

        res = []
        for cli in os.listdir(self.clientconfdir):
            full_file = os.path.join(self.clientconfdir, cli)
            if (os.path.isfile(full_file) and not cli.startswith('.') and
                    not cli.endswith('~')):
                res.append({
                    'name': cli,
                    'value': full_file
                })

        self.clients = res
        self.clientconfdir_mtime = os.path.getmtime(self.clientconfdir)
        return res

    def _get_server_path(self, name=None, fil=None):
        """Returns the path of the 'server *fil*' file"""
        if not name:
            raise BUIserverException('Missing name')

        conf = self.clients_conf.get(name)
        if not conf:
            if not self.conf:
                raise BUIserverException('No burp-server configuration found')
            elif not self.clientconfdir:
                raise BUIserverException('No \'clientconfdir\' found in configuration')
            else:
                raise BUIserverException('Client \'{}\' not found'.format(name))

        workingdir = conf.get('directory')
        if not workingdir:
            raise BUIserverException('Unable to find burp spool dir')

        return os.path.join(workingdir, name, fil)

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
        if not os.path.isabs(pattern):
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

    def is_client_revoked(self, client=None):
        """See :func:`burpui.misc.parser.interface.BUIparser.is_client_revoked`
        """
        if not client:
            return False
        return self.openssl_auth.check_client_revoked(client)

    def remove_client(self, client=None, keepconf=False, delcert=False, revoke=False):
        """See :func:`burpui.misc.parser.interface.BUIparser.remove_client`"""
        res = []
        revoked = False
        removed = False
        if not client:
            return [[NOTIF_ERROR, "No client provided"]]
        try:
            if not keepconf:
                path = os.path.join(self.clientconfdir, client)
                os.unlink(path)
                res.append([NOTIF_OK, "'{}' successfully removed".format(client)])
                removed = True

                if client in self._clients_conf:
                    del self._clients_conf[client]

                self._refresh_cache()

        except OSError as exp:
            res.append([NOTIF_ERROR, str(exp)])

        if revoke and self.backend.revocation_enabled() and removed:
            # revoke cert
            revoked = self.openssl_auth.revoke_client(client)
            if revoked:
                res.append([NOTIF_OK, "'{}' successfully revoked".format(client)])
            else:
                res.append([NOTIF_ERROR, "Error while revoking the certificate"])

        if delcert:
            ca_dir = self.openssl_conf.values.get('CA_DIR')
            path = os.path.join(ca_dir, client)
            try:
                os.unlink('{}.csr'.format(path))
            except OSError as exp:
                res.append([NOTIF_WARN, str(exp)])
            try:
                os.unlink('{}.crt'.format(path))
            except OSError as exp:
                res.append([NOTIF_ERROR, str(exp)])
            if not revoked:
                res.append([NOTIF_WARN, "The client certificate may still be used!"])

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
        if not mconf:
            if not self.clientconfdir:
                return res
            mconf = os.path.join(self.clientconfdir, client)
            config = self._get_client(client, mconf)
        else:
            config = self._get_config(mconf)

        parsed = config.get_file(mconf)
        if mconf in self.filescache and self.filescache[mconf]['md5'] == parsed.md5:
            return self.filescache[mconf]['dict']

        res2 = {}
        res2[u'common'] = parsed.string
        res2[u'boolean'] = parsed.boolean
        res2[u'integer'] = parsed.integer
        res2[u'multi'] = parsed.multi
        res2[u'includes'] = [
            x
            for x in parsed.flatten('include', False).keys()
        ]
        res2[u'includes_ext'] = parsed.include

        res.update(res2)
        self.filescache[mconf] = {
            'dict': res,
            'md5': parsed.md5
        }
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

        parsed = self.server_conf.get_file(mconf)
        if mconf in self.filescache and self.filescache[mconf]['md5'] == parsed.md5:
            return self.filescache[mconf]['dict']

        clientconfdir = parsed.get('clientconfdir')
        if clientconfdir and clientconfdir.parse() != self.clientconfdir:
            self.clientconfdir = clientconfdir.parse()
            self.clientconfdir_mtime = -1
            res['clients'] = self._list_clients()

        res2 = {}
        res2[u'common'] = parsed.string
        res2[u'boolean'] = parsed.boolean
        res2[u'integer'] = parsed.integer
        res2[u'multi'] = parsed.multi
        res2[u'includes'] = [
            x
            for x in parsed.flatten('include', False).keys()
        ]
        res2[u'includes_ext'] = parsed.include

        res.update(res2)
        self.filescache[mconf] = {
            'dict': res,
            'md5': parsed.md5
        }
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
        if conf and not os.path.isabs(conf):
            conf = os.path.join(self.clientconfdir, conf)
        if not conf and not client:
            return [[NOTIF_ERROR, 'Sorry, no client defined']]
        elif client and not conf:
            conf = os.path.join(self.clientconfdir, client)
        ret = self.store_conf(data, conf, client, mode='cli')
        self._refresh_cache()  # refresh client list
        return ret

    def store_conf(self, data, conf=None, client=None, mode='srv',
                   insecure=False):
        """See :func:`burpui.misc.parser.interface.BUIparser.store_conf`"""
        mconf = None
        if not conf:
            mconf = self.conf
        else:
            mconf = conf
            if mconf != self.conf and not mconf.startswith('/'):
                mconf = os.path.join(self.root, mconf)
        if not mconf:
            return [[NOTIF_WARN, 'Sorry, no configuration file defined']]

        if not self._is_secure_path(mconf) and not insecure:
            return [
                [
                    NOTIF_ERROR,
                    'Sorry you are not allowed to access this path:'
                    ' {}'.format(mconf)
                ]
            ]

        check = False
        if client:
            conffile = self._get_client(client, mconf).get_file(mconf)
        else:
            conffile = self.server_conf.get_file(mconf)
            check = True

        ret = conffile.store_data(data, insecure)

        if check:
            clientconfdir = conffile.get('clientconfdir')
            if clientconfdir and clientconfdir.parse() != self.clientconfdir:
                self.clientconfdir = clientconfdir.parse()
                self.clientconfdir_mtime = -1

        return ret

    def cancel_restore(self, name=None):
        """See :func:`burpui.misc.parser.interface.BUIparser.cancel_restore`"""
        path = self._get_server_restore_path(name)
        try:
            if os.path.exists(path):
                os.unlink(path)
            else:
                return [NOTIF_WARN, 'There is no restoration scheduled for this client']
        except OSError as exp:
            return [NOTIF_ERROR, 'Unable to cancel restoration: {}'.format(str(exp))]
        return [NOTIF_OK, 'Restoration successfully canceled']

    def read_restore(self, name=None):
        """See :func:`burpui.misc.parser.interface.BUIparser.read_restore`"""
        path = self._get_server_restore_path(name)

        try:
            ret = {}
            with codecs.open(path, 'r', 'utf-8', errors='ignore') as restore:
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

        full_reg = r''
        for rest in flist['restore']:
            reg = r''
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
            with codecs.open(path, 'w', 'utf-8', errors='ignore') as fil:
                fil.write('backup = {}\n'.format(backup))
                fil.write('regex = {}\n'.format(full_reg.rstrip('|')))
                if strip and strip > 0:  # 0 is False, but we are sure now
                    fil.write('strip = {}\n'.format(strip))
                if prefix:
                    fil.write('restoreprefix = {}\n'.format(prefix))
                if force:
                    fil.write('overwrite = 1\n')
                if restoreto:
                    fil.write('orig_client = {}\n'.format(name))

            return [NOTIF_OK, 'Server-initiated restoration successfully scheduled']

        except Exception as exp:
            return [
                NOTIF_ERROR,
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
                return [NOTIF_WARN, 'There is no backup scheduled for this client']
        except OSError as exp:
            return [NOTIF_ERROR, 'Unable to cancel backup: {}'.format(str(exp))]
        return [NOTIF_OK, 'Backup successfully canceled']

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
                NOTIF_ERROR,
                'Unable to schedule a server-initiated backup:'
                ' {}'.format(str(exp))
            ]
        return [NOTIF_OK, 'Backup successfully scheduled']

    def param(self, name, obj='server_conf', client=None):
        """See :func:`burpui.misc.parser.interface.BUIparser.param`"""
        try:
            if client:
                obj = 'clients_conf'
            my_obj = getattr(self, obj)
        except AttributeError:
            raise BUIserverException('The requested object could not be found')
        if client:
            return my_obj.get(client, {}).get(name, '')
        return my_obj.get(name, '')
