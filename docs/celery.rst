Celery
======

Since *v0.3.0*, `Burp-UI`_ supports asynchronous operations thanks to `Celery`_.
In order to use this feature, you need to enable it in the configuration (see
`Production <advanced_usage.html#production>`__ section)

You will also need some extra requirements:

::

    pip install "burp-ui[celery]"


`Celery`_ needs a *Broker* to communicate between the workers and your
application. I chose `Redis`_ so you will need a working `Redis`_ server
(Basically you just need to run ``apt-get install redis-server`` on Debian based
distributions)

Configure `Burp-UI`_ to enable `Celery`_ support by setting both the ``redis``
and ``celery`` option of the ``[Production]`` section. Example:

::

    [Production]
    # redis server to connect to
    redis = localhost:6379
    # whether to use celery or not
    # may also be a broker url like: redis://localhost:6379/0
    # if set to "true", the broker url defaults to:
    # redis://<redis_host>:<redis_port>/2
    # where <redis_host> is the host part, and <redis_port> is the port part of
    # the above "redis" setting
    celery = true


Runner
------

Once everything is setup, you need to launch a worker. `Burp-UI`_ ships with a
helper script called ``bui-celery``. You can use it like this:

::

    bui-celery --beat


If your configuration is not in a *common* location, you can specify it like
this:

::

    bui-celery -c path/to/burpui.cfg -- --beat


.. note:: A systemd service example file is shiped in the *contrib* directory

.. note:: The ``--beat`` option is recommended since some operations need to be
          executed periodically

.. note:: The usage of a `database <manage.html#database>`_ is recommended to
          keep a track of executed tasks


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Celery: http://www.celeryproject.org/
.. _Redis: http://redis.io/
