# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.parser.openssl
    :platform: Unix
    :synopsis: Burp-UI configuration file parser OpenSSL configuration.
.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import os
import re
import codecs
import logging
import subprocess

from ..._compat import PY3

from hashlib import md5
from six import iteritems
from OpenSSL import crypto

if PY3:
    long = int


class OSSLAuth(object):
    """OpenSSL wrapper"""

    def __init__(self, ca_name, ossl_conf, global_conf):
        """
        :param ca_name: CA name
        :type ca_name: str

        :param ossl_conf: OpenSSL config
        :type ossl_conf: :class:`burpui.misc.parser.openssl.OSSLConf`

        :param global_conf: Global config
        :type global_conf: :class:`burpui.misc.parser.utils.Config`
        """
        self.logger = logging.getLogger('burp-ui')
        self.name = ca_name
        self.ossl_conf = ossl_conf
        self.global_conf = global_conf
        self._load_crl()

    def _load_crl(self):
        crl_path = self._get_crl_path()
        try:
            with open(crl_path) as crl:
                self.crl = crypto.load_crl(
                    crypto.FILETYPE_PEM,
                    crl.read()
                )
        except IOError as err:
            self.logger.warning(str(err))
            self.crl = None

    def _get_crt_path(self, client):
        return '{}.crt'.format(
            os.path.join(self.ossl_conf.values.get('CA_DIR'), client)
        )

    def _get_crl_path(self):
        """Returns the CRL path of a given CA"""
        path = self.ossl_conf.values.get('CA_DIR')
        if not path:
            return ''
        return '{}/CA_{}.crl'.format(path, self.name)

    def check_client_revoked(self, client):
        """Check whether the given client certificate has been revoked
        :param client: Client name
        :type client: str

        :returns: True or False
        """
        if not self.crl:
            return False

        c_cert = self._get_crt_path(client)
        try:
            with open(c_cert) as crt:
                client_crt = crypto.load_certificate(
                    crypto.FILETYPE_PEM,
                    crt.read()
                )
        except IOError as err:
            self.logger.warning(str(err))
            return False

        for rvk in self.crl.get_revoked():
            if client_crt.get_serial_number() == long(rvk.get_serial(), 16):
                return True

        return False

    def revoke_client(self, client, update=True):
        """Revoke a given client

        :param client: Client name
        :type client: str

        :param update: Whether to update the CRL or not
        :type update: bool

        :returns: True or False
        """
        if not client:
            return False
        c_cert = self._get_crt_path(client)
        try:
            DEVNULL = open(os.devnull, 'w')
            openssl = subprocess.check_output([
                'which',
                'openssl'],
                stderr=DEVNULL
            ).rstrip('\n')
            # FIXME: Don't know why pyOpenssl does not return the hex serial :-/
            _, serial = subprocess.check_output([
                openssl,
                'x509',
                '-serial',
                '-noout',
                '-in',
                c_cert],
                stderr=DEVNULL
            ).rstrip('\n').split('=')
            self.logger.debug('{} serial: {}'.format(client, serial))
            subprocess.check_call([
                self.global_conf.get('ca_burp_ca'),
                '--name',
                self.name,
                '--config',
                self.global_conf.get('ca_conf'),
                '--dir',
                self.ossl_conf.values.get('CA_DIR'),
                '--revoke',
                serial],
                stderr=subprocess.STDOUT,
                stdout=DEVNULL
            )
            if update:
                subprocess.check_call([
                    self.global_conf.get('ca_burp_ca'),
                    '--name',
                    self.name,
                    '--config',
                    self.global_conf.get('ca_conf'),
                    '--dir',
                    self.ossl_conf.values.get('CA_DIR'),
                    '--crl'],
                    stderr=subprocess.STDOUT,
                    stdout=DEVNULL
                )
                self._load_crl()
        except subprocess.CalledProcessError as err:
            self.logger.warning(str(err))
            return False
        return True


class OSSLConf(object):
    """Parse the given OpenSSL configuration file

    :param conffile: Configuration file to parse
    :type conffile: str
    """

    def __init__(self, conffile=None):
        self.conffile = conffile
        self.conf = {}
        self.env_cache = {}
        self.md5 = None

    @property
    def values(self):
        """Mapping of the configuration file into a dict"""
        self._parse()
        return self.conf

    def _read(self):
        """Read the file if possible"""
        ret = []
        try:
            if self.conffile:
                with codecs.open(self.conffile, 'r', 'utf-8', errors='ignore') as fil:
                    ret = [x.rstrip('\n') for x in fil.readlines()]
        except IOError:
            pass
        return ret

    def _parse(self):
        """Parse the file if it has changed since last read and replace all
        variables using a multi-passes loop
        """
        dic = {}
        chksum = self._md5(self.conffile)
        if self.md5 and self.md5 == chksum:
            return

        for line in self._read():
            if re.match(r'^\s*#', line):
                continue
            res = re.search(r'\s*([^#][^=\s]+)\s*=\s*(.*)$', line)
            if res:
                key = res.group(1)
                val = res.group(2)

                dic[key] = val

        for key, val in iteritems(dic):
            self.conf[key] = dic[key] = val = self._translate(dic, key, val)

        self.md5 = chksum

    def _translate(self, temp, key, val):
        """Translate variables if needed until the returned value does not seem
        to contain variables anymore
        """
        res = val
        dic = temp
        env = self._is_env(res)
        if env:
            for match in env:
                res = dic[key] = self._translate_env(
                    dic,
                    match,
                    res
                )
        lcl = self._is_local(res)
        if lcl:
            for match in lcl:
                res = dic[key] = self._translate_local(
                    dic,
                    match,
                    res
                )
        if not lcl and not env:
            return res
        return self._translate(dic, key, res)

    @staticmethod
    def _is_local(val):
        """Look for 'local' variables (ie. $dir)"""
        lcl = re.compile(r'\${?(\w+)}?')
        res = [x for x in lcl.findall(val) if x.lower() != 'env']
        return res if res else False

    def _translate_local(self, temp, pattern, val):
        """Translate 'local' variables (ie. $dir is replaced by the content of
        the 'dir' variable)
        """
        res = self.conf.get(pattern) or temp.get(pattern) or ''
        return re.sub(r'\${?' + pattern + '}?', res, val)

    @staticmethod
    def _is_env(val):
        """Look for 'global' variables (ie. $ENV::HOME)"""
        env = re.compile(r'\${?ENV::(\w+)}?')
        res = env.findall(val)
        return res if res else False

    def _translate_env(self, temp, pattern, val):
        """Translate 'global' variables (ie. $ENV::HOME is replace by the
        content of the 'HOME' variable if available in the file or with the
        $HOME environment variable
        """
        res = self.env_cache.get(pattern) or os.getenv(pattern) or \
            self.conf.get(pattern) or temp.get(pattern) or ''
        self.env_cache[pattern] = res
        return re.sub(r'\${?ENV::' + pattern + '}?', res, val)

    @staticmethod
    def _md5(path):
        """Compute the md5sum of the configuration file to detect changes"""
        hash_md5 = md5()
        try:
            if path:
                with open(path, "rb") as bfile:
                    for chunk in iter(lambda: bfile.read(4096), b""):
                        hash_md5.update(chunk)
                return hash_md5.hexdigest()
        except IOError:
            pass
        return None
