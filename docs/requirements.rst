Requirements
============

Please note that, `Burp-UI`_ must be running on the same server that runs the
burp-server for some features.

.. note::
    At the moment, `Burp-UI`_ and this doc is mostly debian-centric but feel
    free to contribute for other distributions!


Python
------

`Burp-UI`_ is built against python 2.7. The support for python 2.6 has been
removed since it is not supported anymore by the CPython core team.
Unit tests are ran against python 2.7 and python 3.4. If you encounter
compilation errors with one of these version, feel free to report them.

Libraries
---------

Some libraries are required to be able to compile some requirements:

::

    apt-get install libffi-dev libssl-dev python-dev python-pip


Debian Wheezy
-------------

It looks like some requirements are not automatically installed on *Debian
Wheezy*. You can install them with the following command:

::

    pip install "burp-ui[debian_wheezy]"


LDAP
----

For LDAP authentication (optional), we need extra dependencies. You can install
them using the following command:

::

    pip install "burp-ui[ldap_authentication]"


Redis
-----

If you wish to use redis for Caching and/or managing uses sessions, you need
additional dependencies:

::

    pip install "burp-ui[gunicorn-extra]"


Celery
------

The celery worker also needs additional dependencies that you can install using:

::

    pip install "burp-ui[celery]"


SQL
---

If you need persistent data, you will need additional dependencies as well:

::

    pip install burp-ui-sql


Now if you want to use a MySQL database, you will need the proper driver. For
instance:

::

    pip install mysqlclient


.. warning:: The MySQL driver does not seem to play nicely with concurrency, you
             should set ``preload=False`` within your gunicorn config.

Limiter
-------

If you want to rate-limit the API, you will need additional dependencies too:

::

    pip install flask-limiter


Burp1
-----

The `burp1 backend <advanced_usage.html#burp1>`__ supports burp versions from
1.3.48 to 1.4.40.
With these versions of burp, the status port is only listening on the local
machine loopback interface (ie. ``localhost`` or ``127.0.0.1``). It means you
*MUST* run `Burp-UI`_ on the same host that is running your burp server in order
to be able to access burp's statistics.
Alternatively, you can use a `bui-agent <buiagent.html>`__.


Burp2
-----

The `burp2 backend <advanced_usage.html#burp2>`__ supports only burp 2.0.18 and
above.
Some versions are known to contain critical issues resulting in a non-functional
`Burp-UI`_: 2.0.24, 2.0.26 and 2.0.30
If you are using an older version of burp2 `Burp-UI`_ will fail to start.


Getting started
---------------

The first thing to do before digging into `Burp-UI`_ is probably to read its
`architecture <architecture.html>`_ in order to understand how it works.
Once it's done, you can refer to the `installation <installation.html>`_ page.


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
