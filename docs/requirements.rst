Requirements
============

Please note that, `Burp-UI`_ must be running on the same server that runs the
burp-server for some features.


LDAP
----

For LDAP authentication (optional), we need extra dependencies. You can install
them using the following command:

::

    pip install "burp-ui[ldap_authentication]"


SSL
---

If you would like to use SSL, you will need the ``python-openssl`` package.
On Debian:

::

    aptitude install python-openssl


Burp2
-----

The `burp2 backend <usage.html#burp2>`_ supports only burp 2.0.18 and above.
If you are using an older version of burp2 `Burp-UI`_ will fail to start.

.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
