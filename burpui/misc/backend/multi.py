# -*- coding: utf8 -*-
import re
import copy
import socket
import select
import sys
import json
import time
import struct
import pickle
import ConfigParser

from burpui.misc.backend.interface import BUIbackend, BUIserverException

class Burp(BUIbackend):

    def __init__(self, server=None, conf=None):
        self.app = None
        self.acl_handler = False
        if server:
            if hasattr(server, 'app'):
                self.app = server.app
            self.acl_handler = server.acl_handler
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
                        timeout = 5
                        ssl = False
                        try:
                            host = config.get(sec, 'host')
                            port = config.getint(sec, 'port')
                            password = config.get(sec, 'password')
                            ssl = config.getboolean(sec, 'ssl')
                            timeout = config.getint(sec, 'timeout')
                        except Exception, e:
                            self.app.logger.error(str(e))

                        self.servers[r.group(1)] = NClient(self.app, host, port, password, ssl, timeout)

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

    def get_backup_logs(self, number, client, forward=False, agent=None):
        """
        parse_backup_log parses the log.gz of a given backup and returns a dict
        containing different stats used to render the charts in the reporting view
        """
        return self.servers[agent].get_backup_logs(number, client, forward)

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

    def restore_files(self, name=None, backup=None, files=None, strip=None, archive='zip', password=None, agent=None):
        return self.servers[agent].restore_files(name, backup, files, strip, archive, password)

    def read_conf_cli(self, agent=None):
        return self.servers[agent].read_conf_cli()

    def read_conf_srv(self, agent=None):
        return self.servers[agent].read_conf_srv()

    def store_conf_cli(self, data, agent=None):
        return self.servers[agent].store_conf_cli(data)

    def store_conf_srv(self, data, agent=None):
        return self.servers[agent].store_conf_srv(data)

    def get_parser_attr(self, attr=None, agent=None):
        return self.servers[agent].get_parser_attr(attr)

class NClient(BUIbackend):

    def __init__(self, app=None, host=None, port=None, password=None, ssl=None, timeout=5):
        self.host = host
        self.port = port
        self.password = password
        self.ssl = ssl
        self.connected = False
        self.app = app
        self.timeout = 5
        if timeout:
            self.timeout = timeout

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
        if not data or not self.connected:
            return res
        try:
            data['password'] = self.password
            raw = json.dumps(data)
            length = len(raw)
            self.sock.sendall(struct.pack('!Q', length))
            self.sock.sendall(raw)
            self.app.logger.debug("Sending: %s", raw)
            r, _, _ = select.select([self.sock], [], [], self.timeout)
            if not r:
                raise Exception ('Socket timed-out 1')
            tmp = self.sock.recv(2)
            self.app.logger.debug("recv: '%s'", tmp)
            if 'OK' != tmp:
                self.app.logger.debug('Ooops, unsuccessful!')
                return res
            self.app.logger.debug("Data sent successfully")
            r, _, _ = select.select([self.sock], [], [], self.timeout)
            if not r:
                raise Exception ('Socket timed-out 2')
            tmp = 'OK'
            if data['func'] == 'restore_files':
                tmp = self.sock.recv(2)
            lengthbuf = self.sock.recv(8)
            length, = struct.unpack('!Q', lengthbuf)
            if data['func'] == 'restore_files':
                err = None
                if tmp == 'KO':
                    err = self.recvall(length)
                toclose = False
                res = (self.sock, length, err)
            else:
                r, _, _ = select.select([self.sock], [], [], self.timeout)
                if not r:
                    raise Exception ('Socket timed-out 3')
                res = self.recvall(length)
        except Exception, e:
            self.close(True)
            self.app.logger.error(str(e))
        finally:
            self.close(toclose)
            return res

    def recvall(self, length=1024):
        buf = b''
        bsize = 1024
        received = 0
        if length < bsize:
            bsize = length
        while received < length:
            newbuf = self.sock.recv(bsize)
            if not newbuf:
                return None
            buf += newbuf
            received += len(newbuf)
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

    def get_backup_logs(self, number, client, forward=False, agent=None):
        """
        parse_backup_log parses the log.gz of a given backup and returns a dict
        containing different stats used to render the charts in the reporting view
        """
        data = {'func': 'get_backup_logs', 'args': {'number': number, 'client': client, 'forward': forward}}
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
        and date) of a given client
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

    def restore_files(self, name=None, backup=None, files=None, strip=None, archive='zip', password=None, agent=None):
        data = {'func': 'restore_files', 'args': {'name': name, 'backup': backup, 'files': files, 'strip': strip, 'archive': archive, 'password': password}}
        return self.do_command(data)

    def read_conf_cli(self, agent=None):
        data = {'func': 'read_conf_cli', 'args': None}
        return json.loads(self.do_command(data))

    def read_conf_srv(self, agent=None):
        data = {'func': 'read_conf_srv', 'args': None}
        return json.loads(self.do_command(data))

    def store_conf_cli(self, data, agent=None):
        data = {'func': 'store_conf_cli', 'args': pickle.dumps({'data': data}), 'pickled': True}
        return json.loads(self.do_command(data))

    def store_conf_srv(self, data, agent=None):
        data = {'func': 'store_conf_srv', 'args': pickle.dumps({'data': data}), 'pickled': True}
        print data
        return json.loads(self.do_command(data))

    def get_parser_attr(self, attr=None, agent=None):
        data = {'func': 'get_parser_attr', 'args': {'attr': attr}}
        return json.loads(self.do_command(data))
