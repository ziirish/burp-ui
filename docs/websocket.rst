WebSocket
=========

Since *v0.6.0*, `Burp-UI`_ supports WebSockets for better/smarter notifications.
In order to use this feature, you need some extra requirements:

::

    pip install "burp-ui[websocket]"


It is highly recommended to use a `Redis`_ *Broker* for the websocket server to
interact with the celery workers and other pieces of the code.
It is also advised to run one or several dedicated WebSocket servers behind a
reverse-proxy because *gunicorn* does not play well with it.

The details of the configuration may be found in the `WebSocket
<advanced_usage.html#websocket>`__ section.

Dedicated Server
----------------

You can choose to either run an embedded WebSocket server though this is not
recommended in production or you can run one or several dedicated WebSocket
servers through the ``bui-manage`` command like this:

::

    bui-manage websocket --bind 0.0.0.0 --port 5001


If you are running the above command, you'll need to set the ``url`` option
under the ``[WebSocket]`` section to ``"document.domain + ':5001'"`` (unless you
use a reverse-proxy, see bellow).

.. warning:: The quotes are **MANDATORY** in this case.

Alternatively, you can setup a reverse-proxy as explained bellow.

.. note:: A systemd service example file is shiped in the *contrib* directory

Reverse-proxy
-------------

Running one or several dedicated WebSocket server is the recommended setup in
production.
You will find more details on this in the
`Flask-SocketIO <https://flask-socketio.readthedocs.io/en/latest/#deployment>`_
documentation.

Running a dedicated server on a dedicated port and/or IP may be a pain. That's
the reason why you can/should setup a reverse-proxy in front of this using a
configuration like:

::

	server {
		listen 80;
		server_name _;

		location / {
			proxy_pass http://127.0.0.1:5000;
		}

		location /socket.io {
			proxy_http_version 1.1;
			proxy_buffering off;
			proxy_set_header Upgrade $http_upgrade;
			proxy_set_header Connection "Upgrade";
			proxy_pass http://127.0.0.1:5001/socket.io;
		}
	}


If you ran several servers, you can use this config:

::

	upstream socketio_nodes {
		ip_hash;

		server 127.0.0.1:5001;
		server 127.0.0.1:5002;
		# to scale the app, just add more nodes here!
	}

	server {
		listen 80;
		server_name _;

		location / {
			proxy_pass http://127.0.0.1:5000;
		}

		location /socket.io {
			proxy_http_version 1.1;
			proxy_buffering off;
			proxy_set_header Upgrade $http_upgrade;
			proxy_set_header Connection "Upgrade";
			proxy_pass http://socketio_nodes/socket.io;
		}
	}


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Redis: http://redis.io/
