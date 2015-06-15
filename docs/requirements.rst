Requirements
============

Please note that currently, ``Burp-UI`` must be running on the same server that
runs the burp-server.


For LDAP authentication (optional), we need the ``ldap3`` module.

::

    pip install ldap3


If you would like to use SSL, you will need the ``python-openssl`` package.
On Debian:

::

    aptitude install python-openssl
