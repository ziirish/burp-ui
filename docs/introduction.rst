Introduction
============

`Burp-UI`_ is a web-based interface for `Burp`_. Its purpose is to give you a
*nice* way to monitor your backups with some dashboards, but you will also have
the ability to download files from backups and to configure your burp-server.

The project also provides a fully documented `API <api.html>`_ so that you can
develop any front-end you like on top of it. The core will take care of the
communication with the burp server(s) for you.

.. note::
    Although the `Burp`_'s author and I exchange a lot, our products are totally
    distinct. So I would like people to understand some issues might be related
    to `Burp-UI`_, but some other might be related to `Burp`_ and I may not be
    able to help you in the later case.
    There is a dedicated mailing-list for `Burp`_ related issues. You can find
    details `here <http://burp.grke.org/contact.html>`_


Compatibility
-------------

+----------------------------+-------+-------+
|   Burp version \ Backend   |   1   |   2   |
+============================+=======+=======+
|         < 1.3.48           |       |       |
+----------------------------+-------+-------+
|     1.3.48 => 1.4.40       |   X   |       |
+----------------------------+-------+-------+
|     2.0.0 => 2.0.16        |       |       |
+----------------------------+-------+-------+
| 2.0.18 => 2.3.X protocol 1 |       |   X   |
+----------------------------+-------+-------+
| 2.0.18 => 2.3.X protocol 2 |       |   X*  |
+----------------------------+-------+-------+

\* The protocol 2 is in heavy development Burp side so the support in
`Burp-UI`_ is best effort and all features (such as server-initiated
restoration) are not available.


Known Issues
------------

Because it's an Open Source project, people are free (and encouraged) to open
issues in the `bug-tracker <https://git.ziirish.me/ziirish/burp-ui/issues>`_.
You will also find there the current opened issues.


Requirements
------------

Please note that, `Burp-UI`_ must be running on the same server that runs the
burp-server for some features.

.. note::
    At the moment, `Burp-UI`_ and this doc is mostly debian-centric but feel
    free to contribute for other distributions!


.. note::
    On RedHat/CentOS you'll have to replace every call to ``pip`` with ``pip3``.
    This can also apply to debian prior Buster.


Python
^^^^^^

`Burp-UI`_ is built against python 3.6. The support for python <=3.5 has been
removed since `v0.7.0 <upgrading.html#v0-7-0>`__. Python 2.7 is about to be EOL
and won't be supported anymore by the CPython core team by the end of 2019.
Unit tests are ran against python 3.6 and python 3.7. If you encounter
compilation errors with one of these version, feel free to report them.

Libraries
^^^^^^^^^

Some libraries are required to be able to compile ``pyOpenSSL``:

::

    apt-get install libffi-dev libssl-dev python-dev python-pip


On RedHat/CentOS the requirements should be:

::

    yum install gcc python36-devel openssl-devel


LDAP
^^^^

For `LDAP authentication <advanced_usage.html#ldap>`__ (optional), we need extra
dependencies. You can install them using the following command:

::

    pip install "burp-ui[ldap_authentication]"


Redis
^^^^^

If you wish to use redis for Caching and/or managing user sessions, you need
additional dependencies:

::

    pip install "burp-ui[gunicorn-extra]"


Redis is also a required dependency if you want to use `celery <celery.html>`__.

Celery
^^^^^^

The `celery <celery.html>`__ worker also needs additional dependencies that you
can install using:

::

    pip install "burp-ui[celery]"


SQL
^^^

If you need persistent data, you will need additional dependencies as well:

::

    pip install "burp-ui[sql]"


Now if you want to use a MySQL database, you will need the proper driver. For
instance:

::

    pip install mysqlclient


.. warning:: The MySQL driver does not seem to play nicely with concurrency, you
             should set ``preload=False`` within your gunicorn config.

To use a PostgreSQL database, you need the ``psycopg2`` driver:

::

    pip install psycopg2


.. warning:: The PostgreSQL driver does not seem to play nicely with
             concurrency, you should set ``preload=False`` within your gunicorn
             config.


Limiter
^^^^^^^

If you want to `rate-limit <advanced_usage.html#production>`__ the API, you will
need additional dependencies too:

::

    pip install flask-limiter


WebSocket
^^^^^^^^^

If you want to enable the `WebSockets <websocket.html>`__ support, you need to
install the following:

::

    pip install "burp-ui[websocket]"


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
.. _Burp: http://burp.grke.org/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
