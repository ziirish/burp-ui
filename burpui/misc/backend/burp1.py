# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.backend.burp1
    :platform: Unix
    :synopsis: Burp-UI burp1 backend module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import re
import os
import socket
import time
import datetime
import json
import shutil
import subprocess
import tempfile

from .interface import BUIbackend
from ..parser.burp1 import Parser
from ...utils import human_readable as _hr, BUIcompress, utc_to_local
from ...security import sanitize_string
from ...exceptions import BUIserverException
from ..._compat import unquote, to_unicode, to_bytes

from shlex import quote


class Burp(BUIbackend):
    """The :class:`burpui.misc.backend.burp1.Burp` class provides a consistent
    backend for ``burp-1`` servers.

    It implements the :class:`burpui.misc.backend.interface.BUIbackend` class
    in order to have consistent data whatever backend is used.

    :param server: ``Burp-UI`` server instance in order to access logger
                   and/or some global settings
    :type server: :class:`burpui.engines.server.BUIServer`

    :param conf: Configuration file to use
    :type conf: str

    :param dummy: Does not instanciate the object (used for development
                  purpose)
    :type dummy: boolean
    """

    # backend version
    _vers = 1

    states = {
        "i": "idle",
        "r": "running",
        "c": "client crashed",
        "C": "server crashed",
        "1": "scanning",
        "2": "backup",
        "3": "merging",
        "4": "shuffling",
        "7": "listing",
        "8": "restoring",
        "9": "verifying",
        "0": "deleting",
    }

    counters = [
        "phase",
        "total",
        "files",
        "files_encrypted",
        "meta_data",
        "meta_data_encrypted",
        "directories",
        "soft_links",
        "hard_links",
        "special_files",
        "vss_headers",
        "vss_headers_encrypted",
        "vss_footers",
        "vss_footers_encrypted",
        "grand_total",
        "warning",
        "estimated_bytes",
        "bytes",
        "bytes_in",
        "bytes_out",
        "start",
        "path",
    ]

    def __init__(self, server=None, conf=None, dummy=False):
        """The :class:`burpui.misc.backend.burp1.Burp` class provides a consistent
        backend for ``burp-1`` servers.

        It implements the :class:`burpui.misc.backend.interface.BUIbackend` class
        in order to have consistent data whatever backend is used.

        :param server: ``Burp-UI`` server instance in order to access logger
                       and/or some global settings
        :type server: :class:`burpui.engines.server.BUIServer`

        :param conf: Configuration to use
        :type conf: :class:`burpui.config.BUIConfig`

        :param dummy: Does not instantiate the object (used for development
                      purpose)
        :type dummy: boolean
        """
        if dummy:
            return
        self.client_version = ""
        self.server_version = ""

        BUIbackend.__init__(self, server, conf)

        self.parser = Parser(self)

        self.family = Burp._get_inet_family(self.host)
        self._test_burp_server_address(self.host)

        try:
            cmd = [self.burpbin, "-v"]
            self.client_version = (
                subprocess.check_output(cmd).rstrip().replace("burp-", "")
            )
        except:
            pass

        try:  # pragma: no cover
            cmd = [self.burpbin, "-a", "l"]
            if self.burpconfcli:
                cmd += ["-c", self.burpconfcli]
            for line in subprocess.check_output(cmd).split("\n"):
                result = re.search(r"^.*Server version:\s+(\d+\.\d+\.\d+)", line)
                if result:
                    self.server_version = result.group(1)
                    break
        except:
            pass

        self.logger.info(f"burp port: {self.port}")
        self.logger.info(f"burp host: {self.host}")
        self.logger.info(f"burp binary: {self.burpbin}")
        self.logger.info(f"strip binary: {self.stripbin}")
        self.logger.info(f"burp conf cli: {self.burpconfcli}")
        self.logger.info(f"burp conf srv: {self.burpconfsrv}")
        self.logger.info(f"command timeout: {self.timeout}")
        self.logger.info(f"tmpdir: {self.tmpdir}")
        self.logger.info(f"zip64: {self.zip64}")
        self.logger.info(f"includes: {self.includes}")
        self.logger.info(f"enforce: {self.enforce}")
        self.logger.info(f"revoke: {self.revoke}")
        self.logger.info(f"client version: {self.client_version}")
        self.logger.info(f"server version: {self.server_version}")
        try:
            # make the connection
            self.status()
        except BUIserverException:
            pass

    @staticmethod
    def _get_inet_family(addr):
        """The :func:`burpui.misc.backend.burp1.Burp._get_inet_family` function
        determines the inet family of a given address.

        :param addr: Address to look at
        :type addr: str

        :returns: Inet family of the given address: :const:`socket.AF_INET` of
                  :const:`socket.AF_INET6`
        """
        if addr == "127.0.0.1":
            return socket.AF_INET
        else:
            return socket.AF_INET6

    def _test_burp_server_address(self, addr, retry=False):
        """The :func:`burpui.misc.backend.burp1.Burp._test_burp_server_address`
        function determines if the given address is reachable or not.

        :param addr: Address to look at
        :type addr: str

        :param retry: Flag to stop trying because this function is recursive
        :type retry: bool

        :returns: True or False whether we could find a valid address or not
        """
        family = Burp._get_inet_family(addr)
        try:
            sock = socket.socket(family, socket.SOCK_STREAM)
            sock.connect((addr, self.port))
            sock.close()
            return True
        except socket.error:
            self.logger.warning("Cannot contact burp server at %s:%s", addr, self.port)
            if not retry:
                new_addr = ""
                if self.host == "127.0.0.1":
                    new_addr = "::1"
                else:
                    new_addr = "127.0.0.1"
                self.logger.info("Trying %s:%s instead", new_addr, self.port)
                if self._test_burp_server_address(new_addr, True):
                    self.logger.info(
                        "%s:%s is reachable, switching to it for this runtime",
                        new_addr,
                        self.port,
                    )
                    self.host = new_addr
                    self.family = Burp._get_inet_family(new_addr)
                    return True
                self.logger.error("Cannot guess burp server address")
        return False

    def statistics(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.statistics`"""
        return {
            "alive": self._test_burp_server_address(self.host),
            "client_version": self.client_version,
            "server_version": self.server_version,
        }

    def status(self, query="\n", timeout=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.status`"""
        result = []
        try:
            query = query.rstrip()
            self.logger.info("query: '{}'".format(query))
            # FIXME: cannot sanitize string due to unicode :/
            # NOTE: converting it to bytes should minimize the risks though
            # query = sanitize_string(query.rstrip())
            qry = to_bytes("{}\n".format(query))
            sock = socket.socket(self.family, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            sock.send(qry)
            sock.shutdown(socket.SHUT_WR)
            fileobj = sock.makefile()
            sock.close()
            for line in fileobj.readlines():
                line = line.rstrip("\n")
                if not line:
                    continue
                try:
                    line = to_unicode(line)
                except UnicodeDecodeError:  # pragma: no cover
                    pass
                result.append(line)
            fileobj.close()
            self.logger.debug("=> {}".format(result))
            return result
        except socket.error:
            self.logger.error(
                "Cannot contact burp server at {0}:{1}".format(self.host, self.port)
            )
            raise BUIserverException(
                "Cannot contact burp server at {0}:{1}".format(self.host, self.port)
            )

    def _get_all_backup_logs(self, client, forward=False, deep=False):
        ret = []
        backups = self.get_client(client)
        queue = []
        for back in backups:
            queue.append(self._get_backup_logs(back["number"], client, forward, deep))

        ret = sorted(queue, key=lambda x: x["number"])
        return ret

    def _get_backup_logs(self, number, client, forward=False, deep=False):
        if not client or not number:
            return {}

        filemap = self.status("c:{0}:b:{1}\n".format(client, number))
        ret = {}
        for line in filemap:
            if line == "backup_stats":
                ret = self._parse_backup_stats(number, client, forward)
                break
        else:
            cli = None
            if forward:
                cli = client

            filemap = self.status("c:{0}:b:{1}:f:log.gz\n".format(client, number))
            ret = self._parse_backup_log(filemap, number, cli)

        ret["encrypted"] = False
        if "files_enc" in ret and ret["files_enc"]["total"] > 0:
            ret["encrypted"] = True
        return ret

    def get_backup_logs(self, number, client, forward=False, deep=False, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_backup_logs`"""
        if not client or not number:
            return {} if number and number != -1 else []

        if number == -1:
            return self._get_all_backup_logs(client, forward, deep)
        return self._get_backup_logs(number, client, forward, deep)

    def _parse_backup_stats(
        self, number, client, forward=False, stats=None, agent=None
    ):
        """The :func:`burpui.misc.backend.burp1.Burp._parse_backup_stats`
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
        backup = {"os": "unknown", "number": int(number)}
        if forward:
            backup["name"] = client
        keys = {
            "time_start": "start",
            "time_end": "end",
            "time_taken": "duration",
            "bytes_in_backup": "totsize",
            "bytes_received": "received",
            "files": ["files", "new"],
            "files_changed": ["files", "changed"],
            "files_same": ["files", "unchanged"],
            "files_deleted": ["files", "deleted"],
            "files_scanned": ["files", "scanned"],
            "files_total": ["files", "total"],
            "files_encrypted": ["files_enc", "new"],
            "files_encrypted_changed": ["files_enc", "changed"],
            "files_encrypted_same": ["files_enc", "unchanged"],
            "files_encrypted_deleted": ["files_enc", "deleted"],
            "files_encrypted_scanned": ["files_enc", "scanned"],
            "files_encrypted_total": ["files_enc", "total"],
            "directories": ["dir", "new"],
            "directories_changed": ["dir", "changed"],
            "directories_same": ["dir", "unchanged"],
            "directories_deleted": ["dir", "deleted"],
            "directories_scanned": ["dir", "scanned"],
            "directories_total": ["dir", "total"],
            "soft_links": ["softlink", "new"],
            "soft_links_changed": ["softlink", "changed"],
            "soft_links_same": ["softlink", "unchanged"],
            "soft_links_deleted": ["softlink", "deleted"],
            "soft_links_scanned": ["softlink", "scanned"],
            "soft_links_total": ["softlink", "total"],
            "hard_links": ["hardlink", "new"],
            "hard_links_changed": ["hardlink", "changed"],
            "hard_links_same": ["hardlink", "unchanged"],
            "hard_links_deleted": ["hardlink", "deleted"],
            "hard_links_scanned": ["hardlink", "scanned"],
            "hard_links_total": ["hardlink", "total"],
            "meta_data": ["meta", "new"],
            "meta_data_changed": ["meta", "changed"],
            "meta_data_same": ["meta", "unchanged"],
            "meta_data_deleted": ["meta", "deleted"],
            "meta_data_scanned": ["meta", "scanned"],
            "meta_data_total": ["meta", "total"],
            "meta_data_encrypted": ["meta_enc", "new"],
            "meta_data_encrypted_changed": ["meta_enc", "changed"],
            "meta_data_encrypted_same": ["meta_enc", "unchanged"],
            "meta_data_encrypted_deleted": ["meta_enc", "deleted"],
            "meta_data_encrypted_scanned": ["meta_enc", "scanned"],
            "meta_data_encrypted_total": ["meta_enc", "total"],
            "special_files": ["special", "new"],
            "special_files_changed": ["special", "changed"],
            "special_files_same": ["special", "unchanged"],
            "special_files_deleted": ["special", "deleted"],
            "special_files_scanned": ["special", "scanned"],
            "special_files_total": ["special", "total"],
            "efs_files": ["efs", "new"],
            "efs_files_changed": ["efs", "changed"],
            "efs_files_same": ["efs", "unchanged"],
            "efs_files_deleted": ["efs", "deleted"],
            "efs_files_scanned": ["efs", "scanned"],
            "efs_files_total": ["efs", "total"],
            "vss_headers": ["vssheader", "new"],
            "vss_headers_changed": ["vssheader", "changed"],
            "vss_headers_same": ["vssheader", "unchanged"],
            "vss_headers_deleted": ["vssheader", "deleted"],
            "vss_headers_scanned": ["vssheader", "scanned"],
            "vss_headers_total": ["vssheader", "total"],
            "vss_headers_encrypted": ["vssheader_enc", "new"],
            "vss_headers_encrypted_changed": ["vssheader_enc", "changed"],
            "vss_headers_encrypted_same": ["vssheader_enc", "unchanged"],
            "vss_headers_encrypted_deleted": ["vssheader_enc", "deleted"],
            "vss_headers_encrypted_scanned": ["vssheader_enc", "scanned"],
            "vss_headers_encrypted_total": ["vssheader_enc", "total"],
            "vss_footers": ["vssfooter", "new"],
            "vss_footers_changed": ["vssfooter", "changed"],
            "vss_footers_same": ["vssfooter", "unchanged"],
            "vss_footers_deleted": ["vssfooter", "deleted"],
            "vss_footers_scanned": ["vssfooter", "scanned"],
            "vss_footers_total": ["vssfooter", "total"],
            "vss_footers_encrypted": ["vssfooter_enc", "new"],
            "vss_footers_encrypted_changed": ["vssfooter_enc", "changed"],
            "vss_footers_encrypted_same": ["vssfooter_enc", "unchanged"],
            "vss_footers_encrypted_deleted": ["vssfooter_enc", "deleted"],
            "vss_footers_encrypted_scanned": ["vssfooter_enc", "scanned"],
            "vss_footers_encrypted_total": ["vssfooter_enc", "total"],
            "total": ["total", "new"],
            "total_changed": ["total", "changed"],
            "total_same": ["total", "unchanged"],
            "total_deleted": ["total", "deleted"],
            "total_scanned": ["total", "scanned"],
            "total_total": ["total", "total"],
        }
        if not stats:
            filemap = self.status(
                "c:{0}:b:{1}:f:backup_stats\n".format(client, number), agent=agent
            )
        else:
            filemap = stats
        for line in filemap:
            if line == "-list begin-" or line == "-list end-":
                continue
            (key, val) = line.split(":")
            if backup["os"] == "unknown" and key == "client_is_windows":
                if val == "1":
                    backup["os"] = "Windows"
                else:
                    backup["os"] = "Unix/Linux"
                continue
            if key not in keys:
                continue
            ckey = keys[key]
            if isinstance(ckey, list):
                if ckey[0] not in backup:
                    backup[ckey[0]] = {}
                backup[ckey[0]][ckey[1]] = int(val)
            else:
                backup[ckey] = int(val)

        # Needed for graphs
        if "received" not in backup:
            backup["received"] = 1

        return backup

    def _parse_backup_log(self, filemap, number, client=None, agent=None):
        """The :func:`burpui.misc.backend.burp1.Burp._parse_backup_log` function
        is used to parse the log.gz of a given backup and returns a dict
        containing different stats used to render the charts in the reporting
        view.

        :param filemap: List representing the content of the log file
        :type filemap: list

        :param number: Backup number to work on
        :type number: int

        :param client: Client name to work on
        :type client: str

        :param agent: What server to ask (only in multi-agent mode)
        :type agent: str

        :returns: Dict containing the backup log
        """
        lookup_easy = {
            "start": r"^Start time: (.+)$",
            "end": r"^\s*End time: (.+)$",
            "duration": r"^Time taken: (.+)$",
            "totsize": r"^\s*Bytes in backup:\s+(\d+)",
            "received": r"^\s*Bytes received:\s+(\d+)",
        }
        lookup_complex = {
            "files": r"^\s*Files:?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "files_enc": r"^\s*Files \(encrypted\):?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "dir": r"^\s*Directories:?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "softlink": r"^\s*Soft links:?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "hardlink": r"^\s*Hard links:?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "meta": r"^\s*Meta data:?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "meta_enc": r"^\s*Meta data\(enc\):?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "special": r"^\s*Special files:?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "efs": r"^\s*EFS files:?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "vssheader": r"^\s*VSS headers:?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "vssheader_enc": r"^\s*VSS headers \(enc\):?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "vssfooter": r"^\s*VSS footers:?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "vssfooter_enc": r"^\s*VSS footers \(enc\):?\s+([\d\s]+)\s+\|\s+(\d+)$",
            "total": r"^\s*Grand total:?\s+([\d\s]+)\s+\|\s+(\d+)$",
        }
        _ = agent  # noqa
        backup = {"os": "Unix/Linux", "number": int(number)}
        if client is not None:
            backup["name"] = client
        useful = False
        for line in filemap:
            if re.match(
                r"^\d{4}-\d{2}-\d{2} (\d{2}:){3} \w+\[\d+\] Client is Windows$", line
            ):
                backup["os"] = "Windows"
            elif not useful and not re.match(r"^-+$", line):
                continue
            elif useful and re.match(r"^-+$", line):
                useful = False
                continue
            elif re.match(r"^-+$", line):
                useful = True
                continue

            found = False
            # this method is not optimal, but it is easy to read and to maintain
            for (key, regex) in lookup_easy.items():
                reg = re.search(regex, line)
                if reg:
                    found = True
                    if key in ["start", "end"]:
                        backup[key] = int(
                            time.mktime(
                                datetime.datetime.strptime(
                                    reg.group(1), "%Y-%m-%d %H:%M:%S"
                                ).timetuple()
                            )
                        )
                    elif key == "duration":
                        tmp = reg.group(1).split(":")
                        tmp.reverse()
                        fields = [0] * 4
                        for (i, val) in enumerate(tmp):
                            fields[i] = int(val)
                        seconds = 0
                        seconds += fields[0]
                        seconds += fields[1] * 60
                        seconds += fields[2] * (60 * 60)
                        seconds += fields[3] * (60 * 60 * 24)
                        backup[key] = seconds
                    else:
                        backup[key] = int(reg.group(1))
                    # break the loop as soon as we find a match
                    break

            # if found is True, we already parsed the line so we can jump to the next one
            if found:
                continue

            for (key, regex) in lookup_complex.items():
                reg = re.search(regex, line)
                if reg:
                    # self.logger.debug("match[1]: '{0}'".format(reg.group(1)))
                    spl = re.split(r"\s+", reg.group(1))
                    if len(spl) < 5:
                        return {}
                    backup[key] = {
                        "new": int(spl[0]),
                        "changed": int(spl[1]),
                        "unchanged": int(spl[2]),
                        "deleted": int(spl[3]),
                        "total": int(spl[4]),
                        "scanned": int(reg.group(2)),
                    }
                    break
        return backup

    def get_clients_report(self, clients, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_clients_report`"""
        data = []
        for cli in clients:
            if not cli:
                continue
            client = self.get_client(cli["name"])
            if not client or not client[-1]:
                continue
            stats = self.get_backup_logs(client[-1]["number"], cli["name"])
            data.append((cli, client, stats))
        return self._do_get_clients_report(data)

    def _do_get_clients_report(self, data):
        ret = {}
        clients = []
        bkp = []
        for client, backups, stats in data:
            os = stats["os"] if "os" in stats else "unknown"
            totsize = stats["totsize"] if "totsize" in stats else 0
            total = (
                stats["total"]["total"]
                if "total" in stats and "total" in stats["total"]
                else 0
            )
            clients.append(
                {
                    "name": client["name"],
                    "stats": {"os": os, "totsize": totsize, "total": total},
                }
            )
            bkp.append({"name": client["name"], "number": len(backups)})
        ret = {"clients": clients, "backups": bkp}
        return ret

    def get_counters(
        self, name=None, agent=None
    ):  # pragma: no cover (hard to test, requires a running backup)
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_counters`"""
        res = {}
        filemap = self.status("c:{0}\n".format(name))
        if not filemap:
            return res
        for line in filemap:
            # self.logger.debug('line: {0}'.format(line))
            reg = re.search(r"^{0}\s+(\d)\s+(\S)\s+(.+)$".format(name), line)
            if reg and reg.group(2) == "r" and int(reg.group(1)) == 2:
                count = 0
                for val in reg.group(3).split("\t"):
                    # self.logger.debug('{0}: {1}'.format(self.counters[c], v))
                    if val and count > 0 and count < 15:
                        try:
                            vals = list(map(int, val.split("/")))
                            if vals[0] > 0 or vals[1] > 0 or vals[2] or vals[3] > 0:
                                res[self.counters[count]] = vals
                        except (ValueError, IndexError):
                            count += 1
                            continue
                    elif val:
                        if self.counters[count] == "path":
                            res[self.counters[count]] = val
                        else:
                            try:
                                res[self.counters[count]] = int(val)
                            except ValueError:
                                count += 1
                                continue
                    count += 1

        # the client was not running
        if not res:
            return res

        if "bytes" not in res:
            res["bytes"] = 0
        if set(["start", "estimated_bytes", "bytes_in"]) <= set(res.keys()):
            try:
                diff = time.time() - int(res["start"])
                byteswant = int(res["estimated_bytes"])
                bytesgot = int(res["bytes_in"])
                bytespersec = bytesgot / diff
                bytesleft = byteswant - bytesgot
                res["speed"] = bytespersec
                if bytespersec > 0:
                    timeleft = int(bytesleft / bytespersec)
                    res["timeleft"] = timeleft
                else:
                    res["timeleft"] = -1
            except:
                res["timeleft"] = -1
        try:
            res["percent"] = round(
                float(res["bytes"]) / float(res["estimated_bytes"]) * 100
            )
        except ZeroDivisionError:
            # You know... division by 0
            res["percent"] = 0
        return res

    def is_backup_running(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.is_backup_running`"""
        if not name:
            return False
        try:
            filemap = self.status("c:{0}\n".format(name))
        except BUIserverException:
            return False
        for line in filemap:
            reg = re.search(r"^{0}\s+\d\s+(\w)".format(name), line)
            if reg and reg.group(1) not in ["i", "c", "C"]:
                return True
        return False

    def is_one_backup_running(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.is_one_backup_running`"""
        res = []
        try:
            clients = self.get_all_clients(last_attempt=False)
        except BUIserverException:
            return res
        for client in clients:
            if self.is_backup_running(client["name"]):
                res.append(client["name"])
        return res

    def get_all_clients(self, agent=None, last_attempt=True):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_all_clients`"""
        res = []
        filemap = self.status()
        for line in filemap:
            regex = re.compile(r"\s*(\S+)\s+\d\s+(\S)\s+(.+)")
            match = regex.search(line)
            cli = {}
            cli["name"] = match.group(1)
            cli["state"] = self.states[match.group(2)]
            infos = match.group(3)
            if cli["state"] in ["running"]:
                regex = re.compile(r"\s*(\S+)")
                reg = regex.search(infos)
                phase = reg.group(0)
                if phase and phase in self.states:
                    cli["phase"] = self.states[phase]
                else:
                    cli["phase"] = "unknown"
                cli["last"] = "now"
                counters = self.get_counters(cli["name"])
                if "percent" in counters:
                    cli["percent"] = counters["percent"]
                else:
                    cli["percent"] = 0
            elif infos == "0":
                cli["last"] = "never"
            elif re.match(r"^\d+\s\d+\s\d+$", infos):
                spl = infos.split()
                cli["last"] = int(spl[2])
            else:
                spl = infos.split("\t")
                cli["last"] = int((spl[-1].split())[-1])
            cli["last"] = utc_to_local(cli["last"])
            cli["last_attempt"] = cli["last"]
            res.append(cli)
        return res

    def get_client_status(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_status`"""
        cli = {}
        filemap = self.status("c:{0}\n".format(name))
        for line in filemap:
            if not re.match("^{0}\t".format(name), line):
                continue
            regex = re.compile(r"\s*(\S+)\s+\d\s+(\S)\s+(.+)")
            match = regex.search(line)
            cli["state"] = self.states[match.group(2)]
            infos = match.group(3)
            if cli["state"] in ["running"]:
                regex = re.compile(r"\s*(\S+)")
                reg = regex.search(infos)
                phase = reg.group(0)
                if phase and phase in self.states:
                    cli["phase"] = self.states[phase]
                else:
                    cli["phase"] = "unknown"
                cli["last"] = "now"
                counters = self.get_counters(name)
                if "percent" in counters:
                    cli["percent"] = counters["percent"]
                else:
                    cli["percent"] = 0
            elif infos == "0":
                cli["last"] = "never"
            elif re.match(r"^\d+\s\d+\s\d+$", infos):
                spl = infos.split()
                cli["last"] = int(spl[2])
            else:
                spl = infos.split("\t")
                cli["last"] = int((spl[-1].split())[-1])
            cli["last"] = utc_to_local(cli["last"])
            break
        return cli

    def get_client(self, name=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client`"""
        return self.get_client_filtered(name)

    def get_client_filtered(
        self, name=None, limit=-1, page=None, start=None, end=None, agent=None
    ):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_filtered`"""
        res = []
        if not name:
            return res
        cli = name
        filemap = self.status("c:{0}\n".format(cli))
        for line in filemap:
            if not re.match("^{0}\t".format(cli), line):
                continue
            # self.logger.debug("line: '{0}'".format(line))
            regex = re.compile(r"\s*(\S+)\s+\d\s+(\S)\s+(.+)")
            match = regex.search(line)
            if match.group(3) == "0" or match.group(2) not in ["i", "c", "C"]:
                continue
            backups = match.group(3).split("\t")
            for cpt, backup in enumerate(backups):
                # skip the first elements if we are in a page
                if page and page > 1 and limit > 0:
                    if cpt < (page - 1) * limit:
                        continue
                bkp = {}
                spl = backup.split()
                backup_date = int(spl[2])
                bkp["number"] = spl[0]
                bkp["deletable"] = spl[1] == "1"
                bkp["date"] = utc_to_local(backup_date)
                # skip backups before "start"
                if start and backup_date < start:
                    continue
                # skip backups after "end"
                if end and backup_date > end:
                    continue
                log = self.get_backup_logs(spl[0], name)
                bkp["encrypted"] = log["encrypted"]
                bkp["received"] = log["received"]
                bkp["size"] = log["totsize"]
                bkp["end"] = utc_to_local(log["end"])
                res.append(bkp)
                # stop after "limit" elements
                if page and page > 1 and limit > 0:
                    if cpt >= page * limit:
                        break
                if limit > 0 and cpt >= limit:
                    break
        # Here we need to reverse the array so the backups are sorted by num ASC
        res.reverse()
        return res

    def is_backup_deletable(self, name=None, backup=None, agent=None):
        """Check if a given backup is deletable"""
        # This feature won't be available in the burp 1 backend so we always
        # return False
        return False

    def get_tree(self, name=None, backup=None, root=None, level=-1, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_tree`"""
        res = []
        if not name or not backup:
            return res
        if not root:
            top = ""
        else:
            top = to_unicode(root)

        filemap = self.status("c:{0}:b:{1}:p:{2}\n".format(name, backup, top))
        useful = False
        for line in filemap:
            if not useful and re.match(r"^-list begin-$", line):
                useful = True
                continue
            if useful and re.match(r"^-list end-$", line):
                useful = False
                continue
            if useful:
                tree = {}
                match = re.search(r"^(.{10})\s", line)
                if match:
                    if re.match(r"^(d|l)", match.group(1)):
                        tree["type"] = "d"
                        tree["folder"] = True
                    else:
                        tree["type"] = "f"
                        tree["folder"] = False
                    spl = re.split(r"\s+", line, 7)
                    tree["mode"] = spl[0]
                    tree["inodes"] = spl[1]
                    tree["uid"] = spl[2]
                    tree["gid"] = spl[3]
                    tree["size"] = "{0:.1eM}".format(_hr(spl[4]))
                    tree["date"] = "{0} {1}".format(spl[5], spl[6])
                    tree["name"] = spl[7]
                    tree["parent"] = top
                    tree["fullname"] = os.path.join(top, spl[7])
                    tree["level"] = level
                    tree["children"] = []
                    res.append(tree)
        return res

    def is_server_restore(self, client=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.is_server_restore`"""
        return self.parser.read_restore(client)

    def cancel_server_restore(self, client=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.cancel_server_restore`"""
        return self.parser.cancel_restore(client)

    def server_restore(
        self,
        client=None,
        backup=None,
        files=None,
        strip=None,
        force=None,
        prefix=None,
        restoreto=None,
        agent=None,
    ):
        """See :func:`burpui.misc.backend.interface.BUIbackend.server_restore`"""
        if not client or not backup or not files:
            raise BUIserverException("At least one argument is missing")

        # TODO: maybe someday we'd like to block server initiated restore
        # if not self.parser.client_conf.get('server_can_restore'):
        #     raise BUIserverException('Server initiated restoration is disabled')

        return self.parser.server_initiated_restoration(
            client, backup, files, strip, force, prefix, restoreto
        )

    def is_server_backup(self, client=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.is_server_backup`"""
        try:
            return self.parser.read_backup(client)
        except BUIserverException:
            return None

    def cancel_server_backup(self, client=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.cancel_server_backup`"""
        try:
            return self.parser.cancel_backup(client)
        except BUIserverException:
            return None

    def server_backup(self, client=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.server_backup`"""
        try:
            return self.parser.server_initiated_backup(client)
        except BUIserverException:
            return None

    def delete_backup(self, name=None, backup=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.delete_backup`"""
        if self._vers == 1:
            return "Sorry, this feature is not available"
        if not name or not backup:
            return "At least one argument is missing"
        if not self.burpbin:
            return "Missing 'burp' binary"
        if not self.is_backup_deletable(name, backup):
            return "Sorry, this backup is not deletable"
        cmd = [
            self.burpbin,
            "-C",
            quote(name),
            "-a",
            "delete",
            "-b",
            quote(str(backup)),
            "-c",
            self.burpconfcli,
        ]
        self.logger.debug(cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = proc.communicate()
        status = proc.wait()
        self.logger.debug(out)
        self.logger.debug("command returned: %d", status)
        if status != 0:
            return "The command failed with status {}: {}".format(status, out)
        return None

    def restore_files(
        self,
        name=None,
        backup=None,
        files=None,
        strip=None,
        archive="zip",
        password=None,
        agent=None,
    ):
        """See :func:`burpui.misc.backend.interface.BUIbackend.restore_files`"""
        if not name or not backup or not files:
            return None, "At least one argument is missing"
        if not self.stripbin:
            return None, "Missing 'strip' binary"
        if not self.burpbin:
            return None, "Missing 'burp' binary"
        if not self.tmpdir:
            return None, "Missing 'tmpdir'"
        flist = json.loads(files)
        if password:
            tmphandler, tmpfile = tempfile.mkstemp()
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)
        tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        if "restore" not in flist:
            return None, "Wrong call"
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)
        full_reg = ""

        def _escape(s):
            return re.sub(r"[(){}\[\].*?|^$\\+-]", r"\\\g<0>", s)

        for restore in flist["restore"]:
            reg = ""
            if restore["folder"] and restore["key"] != "/":
                reg += "^" + _escape(restore["key"]) + "/|"
            else:
                reg += "^" + _escape(restore["key"]) + "$|"
            full_reg += to_unicode(reg)

        cmd = [
            self.burpbin,
            "-C",
            quote(name),
            "-a",
            "r",
            "-b",
            quote(str(backup)),
            "-r",
            full_reg.rstrip("|").replace(r"\n", r"\\n"),
            "-d",
            tmpdir,
        ]
        if password:
            if not self.burpconfcli:
                return None, "No client configuration file specified"
            tmpdesc = os.fdopen(tmphandler, "wb+")
            with open(self.burpconfcli, "rb") as fileobj:
                shutil.copyfileobj(fileobj, tmpdesc)

            tmpdesc.write(
                to_bytes("encryption_password = {}\n".format(sanitize_string(password)))
            )
            tmpdesc.close()
            cmd.append("-c")
            cmd.append(tmpfile)
        elif self.burpconfcli:
            cmd.append("-c")
            cmd.append(self.burpconfcli)
        if strip and strip > 0:  # 0 is False, but we are sure now
            cmd.append("-s")
            cmd.append(str(strip))
        self.logger.debug(cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = proc.communicate()
        status = proc.wait()
        if password:
            os.remove(tmpfile)
        self.logger.debug(out)
        self.logger.debug("command returned: %d", status)
        # hack to handle client-side encrypted backups
        # this is now handled client-side, but we should never trust user input
        # so we need to handle it server-side too
        decode = to_unicode(out)
        if (
            "zstrm inflate error: -3" in decode
            and "transfer file returning: -1" in decode
        ):
            status = 1
            out = "encrypted"
        # a return code of 2 means there were some warnings during restoration
        # so we can assume the restoration was successful anyway
        if status not in [0, 2]:
            return None, out

        if not os.path.isdir(tmpdir):
            return None, "Nothing to restore"

        zip_dir = tmpdir.rstrip(os.sep)
        zip_file = zip_dir + ".zip"
        if os.path.isfile(zip_file):
            os.remove(zip_file)
        zip_len = len(zip_dir) + 1
        stripping = True
        test_strip = True
        with BUIcompress(zip_file, archive, self.zip64) as zfh:
            for dirname, _, files in os.walk(zip_dir):
                for filename in files:
                    path = os.path.join(dirname, filename)
                    # try to detect if the file contains vss headers
                    if test_strip:
                        test_strip = False
                        otp = None
                        try:
                            with open(os.devnull, "w") as devnul:
                                otp = subprocess.check_output(
                                    [self.stripbin, "-p", "-i", path], stderr=devnul
                                )
                        except subprocess.CalledProcessError as exc:
                            self.logger.debug(
                                "Stripping failed on '{}': {}".format(path, str(exc))
                            )
                        if not otp:
                            stripping = False

                    if stripping and os.path.isfile(path):
                        self.logger.debug("stripping file: %s", path)
                        shutil.move(path, path + ".tmp")
                        status = subprocess.call(
                            [self.stripbin, "-i", path + ".tmp", "-o", path]
                        )
                        if status != 0:
                            os.remove(path)
                            shutil.move(path + ".tmp", path)
                            stripping = False
                            self.logger.debug(
                                "Disable stripping since this file does not seem to embed VSS headers"
                            )
                        else:
                            os.remove(path + ".tmp")

                    entry = path[zip_len:]
                    zfh.append(path, entry)

        shutil.rmtree(tmpdir)
        return zip_file, None

    def read_conf_cli(self, client=None, conf=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.read_conf_cli`"""
        if not self.parser:
            return []
        return self.parser.read_client_conf(client, conf)

    def read_conf_srv(self, conf=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.read_conf_srv`"""
        if not self.parser:
            return []
        return self.parser.read_server_conf(conf)

    def store_conf_cli(
        self,
        data,
        client=None,
        conf=None,
        template=False,
        statictemplate=False,
        content="",
        agent=None,
    ):
        """See :func:`burpui.misc.backend.interface.BUIbackend.store_conf_cli`"""
        if not self.parser:
            return []
        try:
            conf = unquote(conf)
        except:
            pass
        return self.parser.store_client_conf(
            data, client, conf, template, statictemplate, content
        )

    def store_conf_srv(self, data, conf=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.store_conf_srv`"""
        if not self.parser:
            return []
        try:
            conf = unquote(conf)
        except:
            pass
        return self.parser.store_conf(data, conf)

    def expand_path(self, path=None, source=None, client=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.expand_path`"""
        if not path:
            return []
        return self.parser.path_expander(path, source, client)

    def delete_client(
        self, client=None, keepconf=False, delcert=False, revoke=False, agent=None
    ):
        """See :func:`burpui.misc.backend.interface.BUIbackend.delete_client`"""
        if not client:
            return [[2, "No client provided"]]
        return self.parser.remove_client(client, keepconf, delcert, revoke)

    def clients_list(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.clients_list`"""
        return self.parser.list_clients()

    def get_parser_attr(self, attr=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_parser_attr`"""
        if not attr or not self.parser:
            raise BUIserverException("Wrong call")
        return getattr(self.parser, attr, [])

    def revocation_enabled(self, agent=None):
        """See
        :func:`burpui.misc.backend.interface.BUIbackend.revocation_enabled`
        """
        return self.revoke

    def get_client_version(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_version`"""
        return self.client_version

    def get_server_version(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_server_version`"""
        return self.server_version

    def get_client_labels(self, client=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_client_labels`"""
        # Not supported with Burp 1.x.x so we just return an empty list
        return []

    def get_attr(self, name, default=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_attr`"""
        try:
            return getattr(self, name, default)
        except AttributeError:
            return default

    def get_parser(self, assume_version=None, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_parser`"""
        if self.parser:
            if assume_version:
                self.parser._assume_server_version = assume_version
            return self.parser
        raise BUIserverException("Missing parser")

    def get_file(self, path, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.get_file`"""
        # only used by the multi backend. We do nothing
        return path

    def del_file(self, path, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.del_file`"""
        # only used by the multi backend. We do nothing
        return path

    def version(self, agent=None):
        """See :func:`burpui.misc.backend.interface.BUIbackend.version`"""
        return self._vers
