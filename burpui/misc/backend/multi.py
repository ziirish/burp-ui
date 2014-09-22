# -*- coding: utf8 -*-
import re
import copy
import socket
import sys
import json
import time
import struct
import ConfigParser

from burpui.misc.backend.interface import BUIbackend, BUIserverException

class Burp(BUIbackend):

    def __init__(self, app=None, conf=None):
        self.app = app
        self.servers = {}
        self.app.config['SERVERS'] = []
        self.running = {}
        if conf:
            config = ConfigParser.ConfigParser()
            with open(conf) as fp:
                config.readfp(fp)
                for sec in config.sections():
                    r = re.match('^Agent:(.+)$', sec)
                    if r:
                        try:
                            host = config.get(sec, 'host')
                            port = config.getint(sec, 'port')
                            password = config.get(sec, 'password')
                            ssl = config.getboolean(sec, 'ssl')
                        except Exception, e:
                            self.app.logger.error(str(e))
                        self.servers[r.group(1)] = NClient(app, host, port, password, ssl)

        self.app.logger.debug(self.servers)
        for key, serv in self.servers.iteritems():
            self.app.config['SERVERS'].append(key)

    """
    Utilities functions
    """

    def status(self, query='\n', agent=None):
        """
        status connects to the burp status port, ask the given 'question' and
        parses the output in an array
        """
        return self.servers[agent].status(query)

    def parse_backup_log(self, f, n, c=None, agent=None):
        """
        parse_backup_log parses the log.gz of a given backup and returns a dict
        containing different stats used to render the charts in the reporting view
        """
        return self.servers[agent].parse_backup_log(f, n, c)

    def get_counters(self, name=None, agent=None):
        """
        get_counters parses the stats of the live status for a given client and
        returns a dict
        """
        return self.servers[agent].get_counters(name)

    def is_backup_running(self, name=None, agent=None):
        """
        is_backup_running returns True if the given client is currently running a
        backup
        """
        return self.servers[agent].is_backup_running(name)

    def is_one_backup_running(self, agent=None):
        """
        is_one_backup_running returns a list of clients name that are currently
        running a backup
        """
        r = []
        if agent:
            r = self.servers[agent].is_one_backup_running(agent)
            self.running[agent] = r
        else:
            r = {}
            for a in self.servers:
                r[a] = self.servers[a].is_one_backup_running(a)
            self.running = r
        return r

    def get_all_clients(self, agent=None):
        """
        get_all_clients returns a list of dict representing each clients with their
        name, state and last backup date
        """
        if agent not in self.servers:
            return []
        return self.servers[agent].get_all_clients()

    def get_client(self, name=None, agent=None):
        """
        get_client returns a list of dict representing the backups (with its number
        and date) of a given client
        """
        return self.servers[agent].get_client(name)

    def get_tree(self, name=None, backup=None, root=None, agent=None):
        """
        get_tree returns a list of dict representing files/dir (with their attr)
        within a given path
        """
        return self.servers[agent].get_tree(name, backup, root)

    def restore_files(self, name=None, backup=None, files=None, agent=None):
        return self.servers[agent].restore_files(name, backup, files)

class NClient(BUIbackend):

    def __init__(self, app=None, host=None, port=None, password=None, ssl=None):
        self.host = host
        self.port = port
        self.password = password
        self.ssl = ssl
        self.connected = False
        self.app = app

    def conn(self):
        try:
            if self.connected:
                return
            self.sock = self.do_conn()
            self.connected = True
            self.app.logger.debug('OK, connected to agent %s:%s', self.host, self.port)
        except Exception, e:
            self.connected = False
            self.app.logger.error('Could not connect to %s:%s => %s', self.host, self.port, str(e))

    def do_conn(self):
        ret = None
        if self.ssl:
            import ssl
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            ret = ssl.wrap_socket(s, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
            try:
                ret.connect((self.host, self.port))
            except Exception, e:
                self.app.logger.error('ERROR: %s', str(e))
                raise e
        else:
            ret = socket.create_connection((self.host, self.port))
        return ret

    def ping(self):
        self.conn()
        res = self.connected
        return res

    def close(self, force=True):
        if self.connected and force:
            self.sock.close()
        self.connected = False

    def do_command(self, data=None):
        self.conn()
        res = '[]'
        toclose = True
        if not data:
            return res
        try:
            data['password'] = self.password
            raw = json.dumps(data)
            length = len(raw)
            self.sock.sendall(struct.pack('!Q', length))
            self.sock.sendall(raw)
            self.app.logger.debug("Sending: %s", raw)
            tmp = self.recvall(2)
            self.app.logger.debug("recv: '%s'", tmp)
            if 'OK' != tmp:
                self.app.logger.debug('Ooops, unsuccessful!')
                return res
            self.app.logger.debug("Data sent successfully")
            lengthbuf = self.recvall(8, False)
            length, = struct.unpack('!Q', lengthbuf)
            if data['func'] == 'restore_files':
                toclose = False
                res = (self.sock, length)
            else:
                res = self.recvall(length)
        except Exception, e:
            self.app.logger.error(str(e))
        finally:
            self.close(toclose)
            return res

    def recvall(self, length=1024, debug=True, timeout=5):
        buf = b''
        bsize = 1024
        received = 0
        tries = 0
        if length < bsize:
            bsize = length
        while received < length and tries < timeout:
            newbuf = self.sock.recv(bsize)
            if not newbuf:
                tries += 1
                time.sleep(0.1)
                continue
            buf += newbuf
            received += len(newbuf)
        if debug:
            self.app.logger.debug('result (%d/%d): %s', len(buf), length, buf)
        return buf

    """
    Utilities functions
    """

    def status(self, query='\n', agent=None):
        """
        status connects to the burp status port, ask the given 'question' and
        parses the output in an array
        """
        data = {'func': 'status', 'args': {'query': query}}
        return json.loads(self.do_command(data))

    def parse_backup_log(self, f, n, c=None, agent=None):
        """
        parse_backup_log parses the log.gz of a given backup and returns a dict
        containing different stats used to render the charts in the reporting view
        """
        data = {'func': 'parse_backup_log', 'args': {'f': f, 'n': n, 'c': c}}
        return json.loads(self.do_command(data))

    def get_counters(self, name=None, agent=None):
        """
        get_counters parses the stats of the live status for a given client and
        returns a dict
        """
        data = {'func': 'get_counters', 'args': {'name': name}}
        return json.loads(self.do_command(data))

    def is_backup_running(self, name=None, agent=None):
        """
        is_backup_running returns True if the given client is currently running a
        backup
        """
        data = {'func': 'is_backup_running', 'args': {'name': name}}
        return json.loads(self.do_command(data))

    def is_one_backup_running(self, agent=None):
        """
        is_one_backup_running returns a list of clients name that are currently
        running a backup
        """
        data = {'func': 'is_one_backup_running', 'args': {'agent': agent}}
        return json.loads(self.do_command(data))

    def get_all_clients(self, agent=None):
        """
        get_all_clients returns a list of dict representing each clients with their
        name, state and last backup date
        """
        data = {'func': 'get_all_clients', 'args': None}
        return json.loads(self.do_command(data))

    def get_client(self, name=None, agent=None):
        """
        get_client returns a list of dict representing the backups (with its number
        and date) of a given clientm
        """
        data = {'func': 'get_client', 'args': {'name': name}}
        return json.loads(self.do_command(data))

    def get_tree(self, name=None, backup=None, root=None, agent=None):
        """
        get_tree returns a list of dict representing files/dir (with their attr)
        within a given path
        """
        data = {'func': 'get_tree', 'args': {'name': name, 'backup': backup, 'root': root}}
        return json.loads(self.do_command(data))

    def restore_files(self, name=None, backup=None, files=None, agent=None):
        data = {'func': 'restore_files', 'args': {'name': name, 'backup': backup, 'files': files}}
        return self.do_command(data)

