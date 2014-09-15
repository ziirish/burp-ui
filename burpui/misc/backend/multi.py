# -*- coding: utf8 -*-
import re

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
        self.servers_status = {}
        self.app.config['SERVERS'] = []
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
            self.servers_status[key] = {'clients': [], 'alive': serv.connected}
            self.app.config['SERVERS'].append(key)
            if not serv.connected:
                continue
            for c in serv.get_all_clients(key):
                self.servers_status[key]['clients'].append(c['name'])

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
        return self.servers[agent].is_one_backup_running()

    def get_all_clients(self, agent=None):
        """
        get_all_clients returns a list of dict representing each clients with their
        name, state and last backup date
        """
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
        pass

class NClient(BUIbackend):

    def __init__(self, app=None, host=None, port=None, password=None, ssl=None):
        self.host = host
        self.port = port
        self.password = password
        self.ssl = ssl
        self.nok = False
        self.connected = False
        self.retry = False
        self.app = app
        self.conn()

    def conn(self):
        try:
            self.sock = socket.create_connection((self.host, self.port))
            self.connected = True
            self.retry = False
            self.app.logger.debug('OK, connected to agent %s:%s', self.host, self.port)
        except Exception, e:
            self.connected = False
            self.app.logger.error('Could not connect to %s:%s => %s', self.host, self.port, str(e))

    def send_command(self, data=None):
        if not data:
            return
        old_data = data
        try:
            data['password'] = self.password
            raw = json.dumps(data)
            length = len(raw)
            self.sock.sendall(struct.pack('!Q', length))
            self.sock.sendall(raw)
            self.app.logger.debug("Sending: %s", raw)
            #time.sleep(1)
            res = b''
            res += self.recvall(2)
            self.app.logger.debug("recv: '%s'", res)
            if 'OK' != res:
                self.app.logger.debug('Ooops, unsuccessful!')
                self.nok = True
                return
            self.app.logger.debug("Data sent successfully")
            self.nok = False
        except Exception, e:
            self.app.logger.error(str(e))
            self.nok = True
            if not self.retry:
                self.retry = True
                self.conn()
                self.send_command(old_data)

    def get_result(self):
        if self.nok:
            return None
        self.app.logger.debug('What now?')
        lengthbuf = self.sock.recv(8)
        length, = struct.unpack('!Q', lengthbuf)
        return self.recvall(length)

    def recvall(self, length=1024):
        buf = b''
        bsize = 1024
        received = 0
        if length < bsize:
            bsize = length
        while received < length:
            newbuf = self.sock.recv(bsize)
            if not newbuf:
                time.sleep(0.1)
                continue
            buf += newbuf
            received += len(newbuf)
        self.app.logger.debug('result (%d/%d): %s', length, len(buf), buf)
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
        self.send_command(data)
        return json.loads(self.get_result())

    def parse_backup_log(self, f, n, c=None, agent=None):
        """
        parse_backup_log parses the log.gz of a given backup and returns a dict
        containing different stats used to render the charts in the reporting view
        """
        data = {'func': 'parse_backup_log', 'args': {'f': f, 'n': n, 'c': c}}
        self.send_command(data)
        return json.loads(self.get_result())

    def get_counters(self, name=None, agent=None):
        """
        get_counters parses the stats of the live status for a given client and
        returns a dict
        """
        data = {'func': 'get_counters', 'args': {'name': name}}
        self.send_command(data)
        return json.loads(self.get_result())

    def is_backup_running(self, name=None, agent=None):
        """
        is_backup_running returns True if the given client is currently running a
        backup
        """
        data = {'func': 'is_backup_running', 'args': {'name': name}}
        self.send_command(data)
        return json.loads(self.get_result())

    def is_one_backup_running(self, agent=None):
        """
        is_one_backup_running returns a list of clients name that are currently
        running a backup
        """
        data = {'func': 'is_one_backup_running', 'args': None}
        self.send_command(data)
        return json.loads(self.get_result())

    def get_all_clients(self, agent=None):
        """
        get_all_clients returns a list of dict representing each clients with their
        name, state and last backup date
        """
        data = {'func': 'get_all_clients', 'args': None}
        self.send_command(data)
        return json.loads(self.get_result())

    def get_client(self, name=None, agent=None):
        """
        get_client returns a list of dict representing the backups (with its number
        and date) of a given clientm
        """
        data = {'func': 'get_client', 'args': {'name': name}}
        self.send_command(data)
        return json.loads(self.get_result())

    def get_tree(self, name=None, backup=None, root=None, agent=None):
        """
        get_tree returns a list of dict representing files/dir (with their attr)
        within a given path
        """
        data = {'func': 'get_tree', 'args': {'name': name, 'backup': backup, 'root': root}}
        self.send_command(data)
        return json.loads(self.get_result())

    def restore_files(self, name=None, backup=None, files=None, agent=None):
        return None

