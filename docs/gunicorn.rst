Gunicorn
========

Starting from v0.0.6, `Burp-UI`_ supports `Gunicorn`_ in
order to handle multiple users simultaneously because some operations (like the
online restoration) may take some time and thus may block any further requests.
With `Gunicorn`_, you have several workers that can proceed the requests so you
can handle more users.

You need to install ``gunicorn`` and ``eventlet``:

::

    pip install eventlet
    pip install gunicorn

You will then be able to launch `Burp-UI`_ this way:

::

    gunicorn -k eventlet -w 4 'burpui:init(conf="/path/to/burpui.cfg")'

When using ``gunicorn``, the command line options are not available. Instead,
run the `Burp-UI`_ ``init`` method directly. Here are the parameters you can
play with:

- conf: Path to the `Burp-UI`_ configuration file
- debug: Whether to run `Burp-UI`_ in debug mode or not to get some extra logging
- logfile: Path to a logfile in order to log `Burp-UI`_ internal messages

Daemon
------

If you wish to run `Burp-UI`_ as a daemon process, the recommanded way is to use
`Gunicorn`_.

When installing the *gunicorn* package on debian, there is a handler script that
is able to start several instances of `Gunicorn`_ as daemons.

All you need to do is installing the *gunicorn* package and adding a
configuration file in */etc/gunicorn.d/*.

There is a sample configuration file available
`here <https://git.ziirish.me/ziirish/burp-ui/blob/master/contrib/gunicorn.d/burp-ui>`__.

If you are using this sample configuration file, make sure to create the
*burpui* user with the appropriate permissions first:

::

    apt-get install gunicorn
    useradd -r -d /var/lib/burpui -c 'Burp-UI daemon user' burpui
    mkdir /etc/burp
    cp /usr/local/share/burpui/etc/burpui.sample.cfg /etc/burp/burpui.cfg
    mkdir -p /var/log/gunicorn
    chown -R burpui: /var/log/gunicorn
    service gunicorn restart


Reverse Proxy
-------------

You may want to add a reverse proxy so `Burp-UI`_ can be accessed on port 80 (or
443) along with other applications.

Here is a sample configuration for nginx:

::

    server {
        listen 80;
        server_name burpui.example.com;

        access_log  /var/log/nginx/burpui.access.log;
        error_log   /var/log/nginx/burpui.error.log;

        location / {

            # you need to change this to "https", if you set "ssl" directive to "on"
            proxy_set_header   X-FORWARDED_PROTO http;
            proxy_set_header   Host              $http_host;
            proxy_set_header   X-Forwarded-For   $remote_addr;

            proxy_read_timeout 300;
            proxy_connect_timeout 300;

            proxy_pass http://localhost:5000;
        }
    }


.. _Gunicorn: http://gunicorn.org/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
