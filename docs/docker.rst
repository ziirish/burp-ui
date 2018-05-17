Docker
======

Since the *v0.4.0*, a docker image is provided. It ships with the latest stable
release of `Burp-UI`_ and supports the celery worker introduced in *v0.3.0* if
you link it to a redis container.

Introduction
------------

All you need is `docker`_ and `docker-compose`_. A *docker-compose.yml* file is
provided. There are a few variables supported to setup your system:


 - **BURPUI_CONFIG** - Specify where the `Burp-UI`_ configuration file is
   located. It defaults to "/etc/burp/burpui.cfg".
 - **BURPUI_VERBOSE** - Specify the log verbosity (between 0 and 4). It defaults
   to 0.
 - **BURPUI_CLIENT_NAME** - Specify the name of the burp client that will be
   used by `Burp-UI`_. It defaults to "bui".
 - **BURPUI_UID** - uid of the *burpui* user you want to map in your host. It
   defaults to 5337.
 - **BURPUI_GID** - gid of the *burpui* group you want to map in your host. It
   defaults to 5337.
 - **BURPUI_PLUGINS** - Directory where to look for plugins. It defaults to none
   which means no plugins will be loaded.
 - **BURPUI_WS_WORKERS** - How many WebSocket servers to spawn. Defaults to the
   number of CPU cores/sockets/threads found.
 - **BURPUI_RP_SCHEME** - HTTP Scheme to set for the reverse-proxy. If you are
   behind a reverse-proxy that provides SSL, you should set this to *https*
   which is the default value.
 - **BURP_CLIENT_CONFIG** - Specify the path of the burp client configuration
   file to use for the `Burp-UI`_ client. It defaults to "/tmp/burp.conf". It
   means you won't have access to it outside of the container. It is intended
   to not override the */etc/burp/burp.conf* file if you already use it.
 - **BURP_SERVER_CONFIG** - Specify the path of the burp-server configuration
   file. It defaults to "/etc/burp/burp-server.conf".
 - **DATABASE_URL** - Specify the URL of the database to connect to. It defaults
   to "sqlite:////var/lib/burpui/store.db".
 - **GUNICORN_WORKERS** - How many gunicorn workers to spawn. Defaults to the
   number of CPU cores/sockets/threads found.
 - **REDIS_SERVER** - Specify the address of the redis server. It defaults to
   "redis:6379".
 - **BURP_SERVER_ADDR** - Specify the address of the burp-server status port.
   If set to "auto", we will use the address of the docker host.
   Make sure your status port is listening on this interface.
   Defaults to "burp-server" which is the burp container in the stack.
 - **TIMEZONE** - Specify the timezone of your burp-server. It defaults to
   Europe/Paris.


The provided *docker-compose.yml* file suggests that you *mount* the */etc/burp*
and */var/spool/burp* paths inside the container (this is automatic) so that
`Burp-UI`_ is able to access some required files.

Requirements
------------

The docker image only works with a burp server version 2.0.x.

`Burp-UI` will be launched with the user *burpui* inside the container. This
user has the UID ``$BURPUI_UID`` and the GID ``$BURPUI_GID`` so you may want to
create a user with the associated UID/GID in your host and make sure it has read
**AND** write access to */etc/burp* and */var/spool/burp*.

For instance:

::

    groupadd -g 5337 burpui
    useradd -r -m -d /var/lib/burpui -c 'Burp-UI daemon user' -u 5337 -g 5337 burpui


Usage
-----

All you have to do is to retrieve the *docker-compose.yml* file, edit the
variables if needed and launch the docker containers.
For instance you could do:

::

    mkdir -p ~/workspace
    cd ~/workspace
    git clone https://git.ziirish.me/ziirish/burp-ui.git
    cd burp-ui
    docker-compose up -d


That's it. Really. Now profit and go to http://localhost:5000/

Troubleshooting
---------------

Here are some hints to help you troubleshoot your `Burp-UI`_ container.

Cannot launch burp process: Unable to spawn burp process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This means `Burp-UI`_ was not able to spawn a burp client that is able to
communicate with the server. You can check the containers logs using the
``docker-compose logs`` command.
If the output contains something like:

::

    It looks like your burp server is not exposing it's status port in a way that is reachable by Burp-UI!
    You may want to set the 'status_address' setting with either '1.2.3.4', '::' or '0.0.0.0' in the /etc/burp/burp-server.conf file in order to make Burp-UI work


It means your burp-server is not exposing its status port. The above output
gives you the instructions to fix it.

.. note:: You'll have to restart your burp-server to bind to the new *status_address*


Other errors may be reported as well by the ``docker-compose logs`` command.
Please read its output carefully.


If the error still occurs, you may need to investigate further.
You can run these commands:

::

    # docker-compose ps
    Name                    Command               State            Ports
    -----------------------------------------------------------------------------------
    burpui_burpui_1   /app/init app:start              Up      127.0.0.1:5000->5000/tcp
    burpui_redis_1    docker-entrypoint.sh redis ...   Up      6379/tcp
    # docker exec -it burpui_burpui_1 /bin/ash
    root@59d883806fc7:/# su - burpui
    $ /usr/sbin/burp -c /tmp/burp.conf -a m
    { "logline": "Could not find ssl_cert_ca /etc/burp/ssl_cert_ca-client-bui.pem: No such file or directory" }
    { "logline": "auth ok" }
    { "logline": "Server version: 2.0.52" }
    { "logline": "nocsr ok" }
    { "logline": "SSL is using cipher: DHE-RSA-AES256-GCM-SHA384 TLSv1.2 Kx=DH       Au=RSA  Enc=AESGCM(256) Mac=AEAD
    " }
    { "logline": "Certificate doesn't verify." }
    { "logline": "check cert failed" }


In this case, we see a pem file is missing. You can usually fix this issue by
running:

::

    # ln -s /etc/burp/ssl_cert_ca.pem /etc/burp/ssl_cert_ca-client-bui.pem


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _docker: https://docs.docker.com/engine/installation/linux/ubuntulinux/
.. _docker-compose: https://docs.docker.com/compose/install/
