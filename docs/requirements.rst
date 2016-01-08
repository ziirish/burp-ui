Requirements
============

Please note that, `Burp-UI`_ must be running on the same server that runs the
burp-server for some features.

.. note::
    At the moment, `Burp-UI`_ and this doc is mostly debian-centric but feel
    free to contribute for other distributions!


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


Alternatively, you can install the python package using the following command:

::

    pip install "burp-ui[ssl]"


Burp1
-----

The `burp1 backend <usage.html#burp1>`__ supports burp versions from 1.3.48 to
1.4.40.
With these versions of burp, the status port is only listening on the machine
loopback (ie. ``localhost`` or ``127.0.0.1``). It means you *MUST* run
`Burp-UI`_ on the same host that is running your burp server in order to be able
to access burp's statistics.
Alternatively, you can use a `bui-agent <buiagent.html>`__.


Burp2
-----

The `burp2 backend <usage.html#burp2>`__ supports only burp 2.0.18 and above.
If you are using an older version of burp2 `Burp-UI`_ will fail to start.

.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
