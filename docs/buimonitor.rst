bui-monitor
===========

The `bui-monitor`_ is a `Burp`_ client monitor processes pool.

This pool only supports the `burp2`_ backend.

The goal of this pool is to have a consistent amount of burp client processes
related to your `Burp-UI`_ stack.

Before this pool, you could have 1 process per `Burp-UI`_ instance (so if you
use gunicorn with several workers, that would multiply the amount of processes),
you also had 1 process per `celery`_ worker instance (which is one per CPU core
available on your machine by default).
In the end, it could be difficult to anticipate the resources to provision
beforehand.
Also, this wasn't very scalable.

If you choose to use the `bui-monitor`_ pool with the appropriate backend (the
`async`_ one), you can now take advantage of some requests parallelisation.

Cherry on the cake, the `async`_ backend is available within both the *local*
`Burp-UI`_ process but also within the `bui-agent`_!


Architecture
------------

The architecture is described bellow:

::

    +---------------------+
    |                     |
    |     celery          |
    |                     |
    +---------------------+
    | +-----------------+ |                                 +----------------------+
    | |                 | |                                 |                      |
    | |  worker 1       +----------------+------------------>     bui-monitor      |
    | |                 | |              |                  |                      |
    | +-----------------+ |              |                  +----------------------+
    | +-----------------+ |              |                  | +------------------+ |
    | |                 | |              |                  | |                  | |
    | |  worker n       +----------------+                  | | burp -a m   (1)  | |
    | |                 | |              |                  | |                  | |
    | +-----------------+ |              |                  | +------------------+ |
    +---------------------+              |                  | +------------------+ |
                                         |                  | |                  | |
    +---------------------+              |                  | | burp -a m   (2)  | |
    |                     |              |                  | |                  | |
    |     burp-ui         |              |                  | +------------------+ |
    |                     |              |                  | +------------------+ |
    +---------------------+              |                  | |                  | |
    | +-----------------+ |              |                  | | burp -a m   (n)  | |
    | |                 | |              |                  | |                  | |
    | |  worker 1       +----------------+                  | +------------------+ |
    | |                 | |              |                  +----------------------+
    | +-----------------+ |              |
    | +-----------------+ |              |
    | |                 | |              |
    | |  worker n       +----------------+
    | |                 | |
    | +-----------------+ |
    +---------------------+


Requirements
------------

The monitor pool is powered by asyncio through trio.
It is part of the `Burp-UI`_ package.
You can launch it with the ``bui-monitor`` command.

Configuration
-------------

There is a specific `buimonitor.cfg`_ configuration file with a ``[Global]``
section as below:

::

	# Burp-UI monitor configuration file
	[Global]
	# On which port is the application listening
	port = 11111
	# On which address is the application listening
	# '::1' is the default for local IPv6
	# set it to '127.0.0.1' if you want to listen on local IPv4 address
	bind = ::1
	# Pool size: number of 'burp -a m' process to load
	pool = 2
	# enable SSL
	ssl = true
	# ssl cert
	sslcert = /var/lib/burp/ssl/server/ssl_cert-server.pem
	# ssl key
	sslkey = /var/lib/burp/ssl/server/ssl_cert-server.key
	# monitor password
	password = password123456

	## burp backend specific options
	#[Burp]
	## burp binary
	#burpbin = /usr/sbin/burp
	## burp client configuration file used for the restoration
	#bconfcli = /etc/burp/burp.conf
	## how many time to wait for the monitor to answer (in seconds)
	#timeout = 15


Each option is commented, but here is a more detailed documentation:

- *port*: On which port is `bui-monitor`_ listening.
- *bind*: On which address is `bui-monitor`_ listening.
- *pool*: Number of burp client processes to launch.
- *ssl*: Whether to communicate with the `Burp-UI`_ server over SSL or not.
- *sslcert*: What SSL certificate to use when SSL is enabled.
- *sslkey*: What SSL key to use when SSL is enabled.
- *password*: The shared secret between the `Burp-UI`_ server and `bui-monitor`_.

As with `Burp-UI`_, you need the ``[Burp]`` section to specify `Burp`_ client
options. There are fewer options because we only launch client processes.

.. warning:: Please note there seem to be an issue Burp side when you request
             concurrently too much status monitor processes. I'll tend to say
             the pool size should not exeed the number of CPU cores available
             on your machine.

Benchmark
---------

On my development VM which has 2 vCPUs I noticed the `async`_ backend which
interacts with the `bui-monitor`_ was twice faster than the `burp2`_ backend.

The test script was something like:

::

    #!/bin/bash

    for client in client1 client2 client3 client4 client6 client6
    do
        echo "----------------------------$client--------------------------"
        (time curl -u user:password burp-ui.server:5000/api/client/stats/$client) &
        (time curl -u user:password burp-ui.server:5000/api/client/stats/$client) &
    done


The server was launched with gunicorn:

::

    # for the async backend
    gunicorn -b 0.0.0.0:5000 -w 2 'burpui:create_app(conf="path/to/burpui.cfg")'
    # for the burp2 backend
    gunicorn -k gevent -b 0.0.0.0:5000 -w 2 'burpui:create_app(conf="path/to/burpui.cfg")'


.. info:: The `async`_ backend is not compatible with gevent hence the different
          launching command.

Here are the results:

::

    # with burp2 backend
    bash /tmp/bench.sh  0.10s user 0.06s system 0% cpu 20.377 total
    bash /tmp/bench.sh  0.11s user 0.04s system 0% cpu 21.447 total
    # with async backend
    bash /tmp/bench.sh  0.12s user 0.04s system 1% cpu 10.267 total
    bash /tmp/bench.sh  0.11s user 0.05s system 1% cpu 9.735 total


My feeling is, the more you have CPU cores, the more performance improvements
you'll notice over the `burp2`_ backend because we let the kernel handle the I/O
parallelization with the `async`_ backend and `bui-monitor`_.

Service
-------

I have no plan to implement daemon features, but there are a lot of tools
available to help you achieve such a behavior.

To run bui-monitor as a service, a systemd file is provided. You can use it like
this:

::

    cp /usr/local/share/burpui/contrib/systemd/bui-monitor.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable bui-monitor.service
    systemctl start bui-monitor.service



.. _Burp: http://burp.grke.org/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _buimonitor.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/share/burpui/etc/buimonitor.sample.cfg
.. _bui-agent: buiagent.html
.. _bui-monitor: buimonitor.html
.. _burp2: advanced_usage.html#burp2
.. _async: advanced_usage.html#async
.. _celery: http://www.celeryproject.org/
