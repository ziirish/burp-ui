Requirements
============

Please note that, `Burp-UI`_ must be running on the same server that runs the
burp-server for some features.

You need python **2.7** in order to run `Burp-UI`_. Python 3 is not yet
officially supported.


For LDAP authentication (optional), we need the ``ldap3`` module.

::

    pip install ldap3


If you would like to use SSL, you will need the ``python-openssl`` package.
On Debian:

::

    aptitude install python-openssl


The `burp2 backend <usage.html#burp2>`_ supports only burp 2.0.18 and above.
If you are using an older version of burp2 `Burp-UI`_ will fail to start.

.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
