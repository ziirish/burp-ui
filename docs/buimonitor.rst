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
`parallel`_ one), you can now take advantage of some requests parallelisation.

Cherry on the cake, the `parallel`_ backend is available within both the *local*
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


Installation
------------

There is a dedicated Pypi package: ``burp-ui-monitor`` that you can install
with ``pip install burp-ui-monitor`` if you want the bare minimun that you can
use alongside with the `bui-agent`_.
Alternatively, the `bui-monitor` command is also part of the full ``burp-ui``
installation.

Presentation
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

.. warning:: Please note there was a bug in burp versions prior 2.2.12 that is
             easily triggered by this new asynchronous workload.

Benchmark
---------

On my development VM which has 2 vCPUs I noticed the `parallel`_ backend which
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

    # for the parallel backend
    gunicorn -b 0.0.0.0:5000 -w 2 'burpui:create_app(conf="path/to/burpui.cfg")'
    # for the burp2 backend
    gunicorn -k gevent -b 0.0.0.0:5000 -w 2 'burpui:create_app(conf="path/to/burpui.cfg")'


.. note:: The `parallel`_ backend is not compatible with gevent hence the different
          launching command.

Here are the results:

::

    # with burp2 backend
    bash /tmp/bench.sh  0.10s user 0.06s system 0% cpu 20.377 total
    bash /tmp/bench.sh  0.11s user 0.04s system 0% cpu 21.447 total
    # with parallel backend
    bash /tmp/bench.sh  0.12s user 0.04s system 1% cpu 10.267 total
    bash /tmp/bench.sh  0.11s user 0.05s system 1% cpu 9.735 total


My feeling is, the more you have CPU cores, the more performance improvements
you'll notice over the `burp2`_ backend because we let the kernel handle the I/O
parallelization with the `parallel`_ backend and `bui-monitor`_.


I also ran similar tests on a *production* environment with more than 100
clients and here are the results:

::

	# Tests agains the *parallel* backend with 16 processes in the pool
	➜  ~ ab -A user:password -H "X-No-Cache:True" -n 100 -c 10 https://backup1.example.org/api/client/stats/client1
	This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
	Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
	Licensed to The Apache Software Foundation, http://www.apache.org/

	Benchmarking backup1.example.org (be patient).....done


	Server Software:        nginx
	Server Hostname:        backup1.example.org
	Server Port:            443
	SSL/TLS Protocol:       TLSv1.2,ECDHE-RSA-AES256-GCM-SHA384,4096,256
	TLS Server Name:        backup1.example.org

	Document Path:          /api/client/stats/client1
	Document Length:        2713 bytes

	Concurrency Level:      10
	Time taken for tests:   18.832 seconds
	Complete requests:      100
	Failed requests:        0
	Total transferred:      313100 bytes
	HTML transferred:       271300 bytes
	Requests per second:    5.31 [#/sec] (mean)
	Time per request:       1883.233 [ms] (mean)
	Time per request:       188.323 [ms] (mean, across all concurrent requests)
	Transfer rate:          16.24 [Kbytes/sec] received

	Connection Times (ms)
				  min  mean[+/-sd] median   max
	Connect:        9   16  13.0     12      72
	Processing:    75 1862 3347.6    222   13963
	Waiting:       75 1862 3347.6    222   13963
	Total:         86 1878 3358.2    237   14009

	Percentage of the requests served within a certain time (ms)
	  50%    237
	  66%    679
	  75%   2355
	  80%   2930
	  90%   8556
	  95%  11619
	  98%  11878
	  99%  14009
	 100%  14009 (longest request)

	# Tests against gunicorn+gevent with the plain *burp2* backend
	➜  ~ ab -A user:password -H "X-No-Cache:True" -n 100 -c 10 https://backup1.example.org/api/client/stats/client1
	This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
	Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
	Licensed to The Apache Software Foundation, http://www.apache.org/

	Benchmarking backup1.example.org (be patient).....done


	Server Software:        nginx
	Server Hostname:        backup1.example.org
	Server Port:            443
	SSL/TLS Protocol:       TLSv1.2,ECDHE-RSA-AES256-GCM-SHA384,4096,256
	TLS Server Name:        backup1.example.org

	Document Path:          /api/client/stats/client1
	Document Length:        2713 bytes

	Concurrency Level:      10
	Time taken for tests:   54.601 seconds
	Complete requests:      100
	Failed requests:        0
	Total transferred:      313100 bytes
	HTML transferred:       271300 bytes
	Requests per second:    1.83 [#/sec] (mean)
	Time per request:       5460.086 [ms] (mean)
	Time per request:       546.009 [ms] (mean, across all concurrent requests)
	Transfer rate:          5.60 [Kbytes/sec] received

	Connection Times (ms)
				  min  mean[+/-sd] median   max
	Connect:        9   18  11.1     13      52
	Processing:    27 5357 4021.1   4380   18894
	Waiting:       27 5357 4021.0   4380   18894
	Total:         40 5375 4024.5   4402   18940

	Percentage of the requests served within a certain time (ms)
	  50%   4402
	  66%   6048
	  75%   7412
	  80%   8114
	  90%  11077
	  95%  12767
	  98%  18916
	  99%  18940
	 100%  18940 (longest request)


What's interesting with the *parallel* backend is it can handle even more
requests with a low overhead as you can see here:

::

	➜  ~ ab -A user:password -H "X-No-Cache:True" -n 500 -c 10 https://backup1.example.org/api/client/stats/client1
	This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
	Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
	Licensed to The Apache Software Foundation, http://www.apache.org/

	Benchmarking backup1.example.org (be patient)
	Completed 100 requests
	Completed 200 requests
	Completed 300 requests
	Completed 400 requests
	Completed 500 requests
	Finished 500 requests


	Server Software:        nginx
	Server Hostname:        backup1.example.org
	Server Port:            443
	SSL/TLS Protocol:       TLSv1.2,ECDHE-RSA-AES256-GCM-SHA384,4096,256
	TLS Server Name:        backup1.example.org

	Document Path:          /api/client/stats/client1
	Document Length:        2713 bytes

	Concurrency Level:      10
	Time taken for tests:   28.073 seconds
	Complete requests:      500
	Failed requests:        0
	Total transferred:      1565500 bytes
	HTML transferred:       1356500 bytes
	Requests per second:    17.81 [#/sec] (mean)
	Time per request:       561.454 [ms] (mean)
	Time per request:       56.145 [ms] (mean, across all concurrent requests)
	Transfer rate:          54.46 [Kbytes/sec] received

	Connection Times (ms)
				  min  mean[+/-sd] median   max
	Connect:        8   15   8.8     13      72
	Processing:   101  546 856.5    209    3589
	Waiting:      101  546 856.5    209    3589
	Total:        114  561 860.3    223    3661

	Percentage of the requests served within a certain time (ms)
	  50%    223
	  66%    241
	  75%    264
	  80%    298
	  90%   2221
	  95%   2963
	  98%   3316
	  99%   3585
	 100%   3661 (longest request)

	This is ApacheBench, Version 2.3 <$Revision: 655654 $>
	Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
	Licensed to The Apache Software Foundation, http://www.apache.org/

	➜  ~ ab -A user:password -H "X-No-Cache:True" -n 1000 -c 10 https://backup1.example.org/api/client/stats/client1
	Benchmarking backup1.example.org (be patient)
	Completed 100 requests
	Completed 200 requests
	Completed 300 requests
	Completed 400 requests
	Completed 500 requests
	Completed 600 requests
	Completed 700 requests
	Completed 800 requests
	Completed 900 requests
	Completed 1000 requests
	Finished 1000 requests


	Server Software:        nginx
	Server Hostname:        backup1.example.org
	Server Port:            443
	SSL/TLS Protocol:       TLSv1/SSLv3,ECDHE-RSA-AES256-GCM-SHA384,4096,256

	Document Path:          /api/client/stats/client1
	Document Length:        2708 bytes

	Concurrency Level:      10
	Time taken for tests:   69.908 seconds
	Complete requests:      1000
	Failed requests:        0
	Write errors:           0
	Total transferred:      3126000 bytes
	HTML transferred:       2708000 bytes
	Requests per second:    14.30 [#/sec] (mean)
	Time per request:       699.081 [ms] (mean)
	Time per request:       69.908 [ms] (mean, across all concurrent requests)
	Transfer rate:          43.67 [Kbytes/sec] received

	Connection Times (ms)
				  min  mean[+/-sd] median   max
	Connect:        8   12   5.1     10      65
	Processing:    77  687 1070.7    245    5122
	Waiting:       77  687 1070.7    245    5122
	Total:         86  698 1072.4    256    5149

	Percentage of the requests served within a certain time (ms)
	  50%    256
	  66%    290
	  75%    329
	  80%    367
	  90%   2938
	  95%   3408
	  98%   3827
	  99%   4693
	 100%   5149 (longest request)

	This is ApacheBench, Version 2.3 <$Revision: 655654 $>
	Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
	Licensed to The Apache Software Foundation, http://www.apache.org/


In comparison, this is the result for 500 requests against gunicorn+gevent:

::

	➜  ~ ab -A user:password -H "X-No-Cache:True" -n 500 -c 10 https://backup1.example.org/api/client/stats/client1
	Benchmarking backup1.example.org (be patient)
	Completed 100 requests
	Completed 200 requests
	Completed 300 requests
	Completed 400 requests
	Completed 500 requests
	Finished 500 requests


	Server Software:        nginx
	Server Hostname:        backup1.example.org
	Server Port:            443
	SSL/TLS Protocol:       TLSv1/SSLv3,ECDHE-RSA-AES256-GCM-SHA384,4096,256

	Document Path:          /api/client/stats/client1
	Document Length:        2708 bytes

	Concurrency Level:      10
	Time taken for tests:   232.800 seconds
	Complete requests:      500
	Failed requests:        0
	Write errors:           0
	Total transferred:      1563000 bytes
	HTML transferred:       1354000 bytes
	Requests per second:    2.15 [#/sec] (mean)
	Time per request:       4655.994 [ms] (mean)
	Time per request:       465.599 [ms] (mean, across all concurrent requests)
	Transfer rate:          6.56 [Kbytes/sec] received

	Connection Times (ms)
				  min  mean[+/-sd] median   max
	Connect:        8   14  10.3     10      69
	Processing:    25 4628 3601.4   4219   28806
	Waiting:       25 4627 3601.4   4219   28806
	Total:         34 4642 3602.4   4233   28815

	Percentage of the requests served within a certain time (ms)
	  50%   4233
	  66%   5306
	  75%   6131
	  80%   6505
	  90%   8856
	  95%  10798
	  98%  14538
	  99%  18397
	 100%  28815 (longest request)


In conclusion, if you have several users using burp-ui you will probably notice
a nice performance improvement when using the new bui-monitor with the parallel
backend.

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
.. _parallel: advanced_usage.html#parallel
.. _celery: http://www.celeryproject.org/
