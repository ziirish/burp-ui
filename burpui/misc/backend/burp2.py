# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.backend.burp2
    :platform: Unix
    :synopsis: Burp-UI burp2 backend module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import re
import os
import time
import json

from .burp1 import Burp as Burp1
from .interface import BUIbackend
from .burp.utils import Monitor
from .burp.constant import BURP_REVERSE_COUNTERS
from ..parser.burp2 import Parser
from ...utils import human_readable as _hr, utc_to_local
from ...exceptions import BUIserverException
from ..._compat import to_unicode

try:
    import gevent
    from gevent.lock import RLock

    WITH_GEVENT = True
except ImportError:
    class RLock(object):
        def __enter__(self):
            return self

        def __exit__(*x):
            pass

    WITH_GEVENT = False


# Some functions are the same as in Burp1 backend
class Burp(Burp1):
    """The :class:`burpui.misc.backend.burp2.Burp` class provides a consistent
    backend for ``burp-2`` servers.

    It extends the :class:`burpui.misc.backend.burp1.Burp` class because a few
    functions can be reused. The rest is just overrided.

    :param server: ``Burp-UI`` server instance in order to access logger
                   and/or some global settings
    :type server: :class:`burpui.engines.server.BUIServer`

    :param conf: Configuration to use
    :type conf: :class:`burpui.config.BUIConfig`
    """

    # backend version
    _vers = 2
    # cache to store the guessed OS
    _os_cache = {}

    def __init__(self, server=None, conf=None):
        """
        :param server: ``Burp-UI`` server instance in order to access logger
                       and/or some global settings
        :type server: :class:`burpui.engines.server.BUIServer`

        :param conf: Configuration to use
        :type conf: :class:`burpui.config.BUIConfig`
        """

        self.plock = RLock()

        BUIbackend.__init__(self, server, conf)

        self.monitor = Monitor(self.burpbin, self.burpconfcli, self.app, self.timeout)
        self.parser = Parser(self)

        self.batch_list_supported = self.monitor.batch_list_supported

        self.logger.info('burp binary: {}'.format(self.burpbin))
        self.logger.info('strip binary: {}'.format(self.stripbin))
        self.logger.info('burp conf cli: {}'.format(self.burpconfcli))
        self.logger.info('burp conf srv: {}'.format(self.burpconfsrv))
        self.logger.info('command timeout: {}'.format(self.timeout))
        self.logger.info('tmpdir: {}'.format(self.tmpdir))
        self.logger.info('zip64: {}'.format(self.zip64))
        self.logger.info('includes: {}'.format(self.includes))
        self.logger.info('enforce: {}'.format(self.enforce))
        self.logger.info('revoke: {}'.format(self.revoke))
        self.logger.info(f'client version: {self.client_version}')
        self.logger.info(f'server version: {self.server_version}')

    @property
    def client_version(self):
        return self.monitor.client_version

    @property
    def server_version(self):
        return self.monitor.server_version

    @staticmethod
    def _human_st_mode(mode):
        """Convert the st_mode returned by stat in human readable (ls-like)
        format
        """
        hur = ''
        if os.path.stat.S_ISREG(mode):
            hur = '-'
        elif os.path.stat.S_ISLNK(mode):
            hur = 'l'
        elif os.path.stat.S_ISSOCK(mode):
            hur = 's'
        elif os.path.stat.S_ISDIR(mode):
            hur = 'd'
        elif os.path.stat.S_ISBLK(mode):
            hur = 'b'
        elif os.path.stat.S_ISFIFO(mode):
            hur = 'p'
        elif os.path.stat.S_ISCHR(mode):
            hur = 'c'
        else:
            hur = '-'

        for who in 'USR', 'GRP', 'OTH':
            for perm in 'R', 'W', 'X':
                if mode & getattr(os.path.stat, 'S_I' + perm + who):
                    hur += perm.lower()
                else:
                    hur += '-'

        return hur

    def status(self, query='c:\n', timeout=None, cache=True, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.status`"""
        with self.plock:
            return self.monitor.status(query, timeout, cache)

    def get_backup_logs(self, number, client, forward=False, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_backup_logs`
        """
        ret = {}
        if not client or not number:
            return ret

        query = self.status('c:{0}:b:{1}\n'.format(client, number))
        if not query:
            return ret
        try:
            logs = query['clients'][0]['backups'][0]['logs']['list']
        except KeyError:
            self.logger.warning('No logs found')
            return ret
        if 'backup_stats' in logs:
            ret = self._parse_backup_stats(number, client, forward)

        ret['encrypted'] = False
        if 'files_enc' in ret and ret['files_enc']['total'] > 0:
            ret['encrypted'] = True
        return ret

    def _guess_backup_protocol(self, number, client):
        """The :func:`burpui.misc.backend.burp2.Burp._guess_backup_protocol`
        function helps you determine if the backup is protocol 2 or 1

        :param number: Backup number to work on
        :type number: int

        :param client: Client name to work on
        :type client: str

        :returns: 1 or 2
        """
        query = self.status('c:{0}:b:{1}:l:backup\n'.format(client, number))
        try:
            log = query['clients'][0]['backups'][0]['logs']['backup']
            for line in log:
                if re.search(r'Protocol: 2$', line):
                    return 2
        except KeyError:
            # Assume protocol 1 in all cases unless explicitly found Protocol 2
            return 1
        return 1

    def _parse_backup_stats(self, number, client, forward=False, agent=None):
        """The :func:`burpui.misc.backend.burp2.Burp._parse_backup_stats`
        function is used to parse the burp logs.

        :param number: Backup number to work on
        :type number: int

        :param client: Client name to work on
        :type client: str

        :param forward: Is the client name needed in later process
        :type forward: bool

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: Dict containing the backup log
        """
        ret = {}
        backup = {'os': self._guess_os(client), 'number': int(number)}
        if forward:
            backup['name'] = client
        translate = {
            'time_start': 'start',
            'time_end': 'end',
            'time_taken': 'duration',
            'bytes': 'totsize',
            'bytes_received': 'received',
            'bytes_estimated': 'estimated_bytes',
            'files': 'files',
            'files_encrypted': 'files_enc',
            'directories': 'dir',
            'soft_links': 'softlink',
            'hard_links': 'hardlink',
            'meta_data': 'meta',
            'meta_data_encrypted': 'meta_enc',
            'special_files': 'special',
            'efs_files': 'efs',
            'vss_headers': 'vssheader',
            'vss_headers_encrypted': 'vssheader_enc',
            'vss_footers': 'vssfooter',
            'vss_footers_encrypted': 'vssfooter_enc',
            'total': 'total',
            'grand_total': 'total',
        }
        counts = {
            'new': 'count',
            'changed': 'changed',
            'unchanged': 'same',
            'deleted': 'deleted',
            'total': 'scanned',
            'scanned': 'scanned',
        }
        single = [
            'time_start',
            'time_end',
            'time_taken',
            'bytes_received',
            'bytes_estimated',
            'bytes'
        ]
        query = self.status(
            'c:{0}:b:{1}:l:backup_stats\n'.format(client, number)
        )
        if not query:
            return ret
        try:
            back = query['clients'][0]['backups'][0]
        except KeyError:
            self.logger.warning('No backup found')
            return ret
        if 'backup_stats' not in back['logs']:
            self.logger.warning('No stats found for backup')
            return ret
        stats = None
        try:
            stats = json.loads(''.join(back['logs']['backup_stats']))
        except:
            stats = back['logs']['backup_stats']
        if not stats:
            return ret
        # server was upgraded but backup comes from an older version
        if 'counters' not in stats:
            return super(Burp, self)._parse_backup_stats(
                number,
                client,
                forward,
                stats,
                agent
            )
        counters = stats['counters']
        for counter in counters:
            name = counter['name']
            if name in translate:
                name = translate[name]
            if counter['name'] in single:
                backup[name] = counter['count']
            else:
                backup[name] = {}
                for (key, val) in counts.items():
                    if val in counter:
                        backup[name][key] = counter[val]
                    else:
                        backup[name][key] = 0
        if 'start' in backup and 'end' in backup:
            backup['duration'] = backup['end'] - backup['start']
            # convert utc timestamp to local
            # example: 1468850307 -> 1468857507
            backup['start'] = utc_to_local(backup['start'])
            backup['end'] = utc_to_local(backup['end'])

        # Needed for graphs
        if 'received' not in backup:
            backup['received'] = 1

        return backup

    # TODO: support old clients
    # NOTE: this should now be partly done since we fallback to the Burp1 code
    # def _parse_backup_log(self, fh, number, client=None, agent=None):
    #    """
    #    parse_backup_log parses the log.gz of a given backup and returns a
    #    dict containing different stats used to render the charts in the
    #    reporting view
    #    """
    #    return {}

    # def get_clients_report(self, clients, agent=None):

    def get_counters(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_counters`"""
        ret = {}
        query = self.status('c:{0}\n'.format(name), cache=False)
        # check the status returned something
        if not query:
            return ret

        try:
            client = query['clients'][0]
        except KeyError:
            self.logger.warning('Client not found')
            return ret

        # check the client is currently backing-up
        if 'run_status' not in client or client['run_status'] != 'running':
            return ret

        backup = None
        phases = ['working', 'finishing']
        try:
            for child in client['children']:
                if 'action' in child and child['action'] == 'backup':
                    backup = child
                    break
        except KeyError:
            for back in client['backups']:
                if 'flags' in back and any([x in back['flags'] for x in phases]):
                    backup = back
                    break
        # check we found a working backup
        if not backup:
            return ret

        # list of single counters (type CNTR_SINGLE_FIELD in cntr.c)
        single = [
            'bytes_estimated',
            'bytes',
            'bytes_received',
            'bytes_sent',
            'time_start',
            'time_end',
            'warnings',
            'errors'
        ]

        # translation table to be compatible with burp1
        def translate(cntr):
            translate_table = {'bytes_estimated': 'estimated_bytes'}
            try:
                return translate_table[cntr]
            except KeyError:
                return cntr

        for counter in backup.get('counters', {}):
            name = translate(counter['name'])
            if counter['name'] not in single:
                # Prior burp-2.1.6 some counters are reversed
                # See https://github.com/grke/burp/commit/adeb3ad68477303991a393fa7cd36bc94ff6b429
                if self.server_version and self.server_version < BURP_REVERSE_COUNTERS:
                    ret[name] = [
                        counter['count'],
                        counter['same'],     # reversed
                        counter['changed'],  # reversed
                        counter['deleted'],
                        counter['scanned']
                    ]
                else:
                    ret[name] = [
                        counter['count'],
                        counter['changed'],
                        counter['same'],
                        counter['deleted'],
                        counter['scanned']
                    ]
            else:
                ret[name] = counter['count']

        if 'phase' in backup:
            ret['phase'] = backup['phase']
        else:
            for phase in phases:
                if phase in backup.get('flags', []):
                    ret['phase'] = phase
                    break

        if 'bytes' not in ret:
            ret['bytes'] = 0
        if set(['time_start', 'estimated_bytes', 'bytes']) <= set(ret.keys()):
            try:
                diff = time.time() - int(ret['time_start'])
                byteswant = int(ret['estimated_bytes'])
                bytesgot = int(ret['bytes'])
                bytespersec = bytesgot / diff
                bytesleft = byteswant - bytesgot
                ret['speed'] = bytespersec
                if bytespersec > 0:
                    timeleft = int(bytesleft / bytespersec)
                    ret['timeleft'] = timeleft
                else:
                    ret['timeleft'] = -1
            except:
                ret['timeleft'] = -1
        try:
            ret['percent'] = round(
                float(ret['bytes']) / float(ret['estimated_bytes']) * 100
            )
        except:
            # You know... division by 0
            ret['percent'] = 0

        return ret

    def is_backup_running(self, name=None, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.is_backup_running`
        """
        if not name:
            return False
        try:
            query = self.status('c:{0}\n'.format(name))
        except BUIserverException:
            return False
        if not query:
            return False
        try:
            return query['clients'][0]['run_status'] in ['running']
        except KeyError:
            self.logger.warning('Client not found')
            return False
        return False

    def is_one_backup_running(self, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.is_one_backup_running`
        """
        ret = []
        try:
            clients = self.get_all_clients()
        except BUIserverException:
            return ret
        for client in clients:
            if client['state'] in ['running']:
                ret.append(client['name'])
        return ret

    def _status_human_readable(self, status):
        """The label has changed in burp2, we override it to be compatible with
        burp1's format

        :param status: The status returned by the burp2 server
        :type status: str

        :returns: burp1 status compatible
        """
        if not status:
            return None
        if status == 'c crashed':
            return 'client crashed'
        if status == 's crashed':
            return 'server crashed'
        return status

    def _get_last_backup(self, name):
        """Return the last backup of a given client

        :param name: Name of the client
        :type name: str

        :returns: The last backup
        """
        try:
            clients = self.status('c:{}'.format(name))
            client = clients['clients'][0]
            return client['backups'][0]
        except (KeyError, BUIserverException):
            return None

    def _guess_os(self, name):
        """Return the OS of the given client based on the magic *os* label

        :param name: Name of the client
        :type name: str

        :returns: The guessed OS of the client

        ::

            grep label /etc/burp/clientconfdir/toto
            label = os: Darwin OS
        """
        ret = 'Unknown'
        if name in self._os_cache:
            return self._os_cache[name]

        labels = self.get_client_labels(name)
        OSES = []

        for label in labels:
            if re.match('os:', label, re.IGNORECASE):
                _os = label.split(':', 1)[1].strip()
                if _os not in OSES:
                    OSES.append(_os)

        if OSES:
            ret = OSES[-1]
        else:
            # more aggressive check
            last = self._get_last_backup(name)
            if last:
                try:
                    tree = self.get_tree(name, last['number'])

                    if tree[0]['name'] != '/':
                        ret = 'Windows'
                    else:
                        ret = 'Unix/Linux'
                except (IndexError, KeyError, BUIserverException):
                    pass

        self._os_cache[name] = ret
        return ret

    def get_all_clients(self, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_all_clients`
        """
        ret = []
        query = self.status()
        if not query or 'clients' not in query:
            return ret
        clients = query['clients']
        for client in clients:
            cli = {}
            cli['name'] = client['name']
            cli['state'] = self._status_human_readable(client['run_status'])
            infos = client['backups']
            if cli['state'] in ['running']:
                cli['last'] = 'now'
            elif not infos:
                cli['last'] = 'never'
            else:
                infos = infos[0]
                cli['last'] = infos['timestamp']
            ret.append(cli)
        return ret

    def get_client_status(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_status`"""
        ret = {}
        if not name:
            return ret
        query = self.status('c:{0}\n'.format(name))
        if not query:
            return ret
        try:
            client = query['clients'][0]
        except (KeyError, IndexError):
            self.logger.warning('Client not found')
            return ret
        ret['state'] = self._status_human_readable(client['run_status'])
        infos = client['backups']
        if ret['state'] in ['running']:
            try:
                ret['phase'] = client['phase']
            except KeyError:
                for child in client.get('children', []):
                    if 'action' in child and child['action'] == 'backup':
                        ret['phase'] = child['phase']
                        break
            counters = self.get_counters(name)
            if 'percent' in counters:
                ret['percent'] = counters['percent']
            else:
                ret['percent'] = 0
            ret['last'] = 'now'
        elif not infos:
            ret['last'] = 'never'
        else:
            infos = infos[0]
            ret['last'] = infos['timestamp']
        return ret

    def get_client(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client`"""
        return self.get_client_filtered(name)

    def get_client_filtered(self, name=None, limit=-1, page=None, start=None, end=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_filtered`"""
        ret = []
        if not name:
            return ret
        query = self.status('c:{0}\n'.format(name))
        if not query:
            return ret
        try:
            backups = query['clients'][0]['backups']
        except (KeyError, IndexError):
            self.logger.warning('Client not found')
            return ret
        threads = []
        for idx, backup in enumerate(backups):
            # skip the first elements if we are in a page
            if page and page > 1 and limit > 0:
                if idx < (page - 1) * limit:
                    continue
            back = {}
            # skip running backups since data will be inconsistent
            if 'flags' in backup and 'working' in backup['flags']:
                continue
            back['number'] = backup['number']
            if 'flags' in backup and 'deletable' in backup['flags']:
                back['deletable'] = True
            else:
                back['deletable'] = False
            back['date'] = backup['timestamp']
            # skip backups before "start"
            if start and backup['timestamp'] < start:
                continue
            # skip backups after "end"
            if end and backup['timestamp'] > end:
                continue

            def __get_log(client, bkp, res):
                log = self.get_backup_logs(bkp['number'], client)
                try:
                    res['encrypted'] = log['encrypted']
                    try:
                        res['received'] = log['received']
                    except KeyError:
                        res['received'] = 0
                    try:
                        res['size'] = log['totsize']
                    except KeyError:
                        res['size'] = 0
                    res['end'] = log['end']
                    # override date since the timestamp is odd
                    res['date'] = log['start']
                except Exception:
                    self.logger.warning('Unable to parse logs')
                    return None
                return res

            if WITH_GEVENT:
                threads.append(gevent.spawn(__get_log, name, backup, back))
            else:
                with_log = __get_log(name, backup, back)
                if with_log:
                    ret.append(with_log)

            # stop after "limit" elements
            if page and page > 1 and limit > 0:
                if idx >= page * limit:
                    break
            elif limit > 0 and idx >= limit:
                break

        if WITH_GEVENT:
            gevent.joinall(threads)
            ret = [x.value for x in threads if x.value]

        # Here we need to reverse the array so the backups are sorted by num
        # ASC
        ret.reverse()
        return ret

    def is_backup_deletable(self, name=None, backup=None, agent=None):
        """Check if a given backup is deletable"""
        if not name or not backup:
            return False
        query = self.status('c:{0}:b:{1}\n'.format(name, backup))
        if not query:
            return False
        try:
            flags = query['clients'][0]['backups'][0]['flags']
            return 'deletable' in flags
        except KeyError:
            return False

    def get_tree(self, name=None, backup=None, root=None, level=-1, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_tree`"""
        ret = []
        if not name or not backup:
            return ret
        if not root:
            top = ''
        else:
            top = to_unicode(root)

        # we know this operation may take a while so we arbitrary increase the
        # read timeout
        timeout = None
        if top == '*':
            timeout = max(self.timeout, 300)

        query = self.status(
            'c:{0}:b:{1}:p:{2}\n'.format(name, backup, top),
            timeout
        )
        if not query:
            return ret
        try:
            backup = query['clients'][0]['backups'][0]
        except KeyError:
            return ret
        for entry in backup['browse']['entries']:
            data = {}
            base = None
            dirn = None
            if top == '*':
                base = os.path.basename(entry['name'])
                dirn = os.path.dirname(entry['name'])
            if entry['name'] == '.':
                continue
            else:
                data['name'] = base or entry['name']
            data['mode'] = self._human_st_mode(entry['mode'])
            if re.match('^(d|l)', data['mode']):
                data['type'] = 'd'
                data['folder'] = True
            else:
                data['type'] = 'f'
                data['folder'] = False
            data['inodes'] = entry['nlink']
            data['uid'] = entry['uid']
            data['gid'] = entry['gid']
            data['parent'] = dirn or top
            data['size'] = '{0:.1eM}'.format(_hr(entry['size']))
            data['date'] = entry['mtime']
            data['fullname'] = os.path.join(top, entry['name']) if top != '*' \
                else entry['name']
            data['level'] = level
            data['children'] = []
            ret.append(data)
        return ret

    def get_client_version(self, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_client_version`
        """
        return self.client_version

    def get_server_version(self, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_server_version`
        """
        if not self.server_version:
            self.status()
        return self.server_version

    def get_client_labels(self, client=None, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.get_client_labels`
        """
        ret = []
        if not client:
            return ret
        # micro optimization since the status results are cached in memory for a
        # couple seconds, using the same global query and iterating over it
        # will be more efficient than filtering burp-side
        query = self.status('c:\n')
        if not query:
            return ret
        try:
            for cli in query['clients']:
                if cli['name'] == client:
                    return cli['labels']
        except KeyError:
            return ret

    # Same as in Burp1 backend
    # def restore_files(
    #     self,
    #     name=None,
    #     backup=None,
    #     files=None,
    #     strip=None,
    #     archive='zip',
    #     password=None,
    #     agent=None):

    # def read_conf_cli(self, agent=None):

    # def read_conf_srv(self, agent=None):

    # def store_conf_cli(self, data, agent=None):

    # def store_conf_srv(self, data, agent=None):

    # def get_parser_attr(self, attr=None, agent=None):
