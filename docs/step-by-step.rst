Step By Step
============

Although `Burp-UI`_ tries to make `Burp`_ accessible to everyone, both products
have their complexity.

In this *Step by Step*, I would like to introduce you different use-cases with
their associated configurations, descriptions and comments.
In every case, we will consider neither `Burp`_ or `Burp-UI`_ are installed and
describe the steps to setup your server from Scratch.

.. note::
    Again, this part of the doc is mostly debian-centric. If some users are
    willing to adapt these examples with other distros I would be very thankful.


1. `Burp1 server`_ with `Burp-UI`_
2. `Burp2 server`_ with `Burp-UI`_
3. `Multiple servers`_ with `bui-agents <buiagent.html>`_


Burp1 server
------------

In this scenario, we are going to install a `Burp`_ server version 1.4.40 which
is the current stable version. We assume you are using the user *root* to run
the following commands.

We begin with the installation of `Burp`_ itself.

First, we need some system requirements in order to compile `Burp`_ and to
install `Burp-UI`_:

::

    apt-get update
    apt-get install uthash-dev g++ make libssl-dev librsync-dev python2.7-dev \
    git python-pip libffi-dev


Now we retrieve the `Burp`_ sources and then we compile and install it:

::

    cd /usr/src
    git clone https://github.com/grke/burp.git
    cd burp
    git checkout tags/1.4.40
    ./configure --disable-ipv6
    make
    make install
    # we also install init scripts
    cp debian/init /etc/init.d/burp
    cat >/etc/default/burp<<EOF
    RUN="yes"
    DAEMON_ARGS="-c /etc/burp/burp-server.conf"
    EOF
    chmod +x /etc/init.d/burp
    update-rc.d burp defaults


It is now time to install `Burp-UI`_:

::

    pip install --upgrade burp-ui


Now that everything is installed, let's configure our tools!

In order to perform online restorations, `Burp-UI`_ relies on a classical
`Burp`_ client.

We need to define our client, and we also need to allow it to perform
restorations for other clients. We will set it up globally. Our client will be
named *bui*:

::

    # burp-ui client's definition
    cat >/etc/burp/clientconfdir/bui<<EOF
    password = abcdefgh
    EOF

    # grant our client to perform restorations for others
    echo "restore_client = bui" >>/etc/burp/burp-server.conf

    # now we generate ou client configuration
    cat >/etc/burp/burp.conf<<EOF
    mode = client
    port = 4971
    server = 127.0.0.1
    password = abcdefgh
    cname = bui
    pidfile = /var/run/burp.bui.pid
    syslog = 0
    stdout = 1
    progress_counter = 1
    ca_burp_ca = /usr/sbin/burp_ca
    ca_csr_dir = /etc/burp/CA-client
    # SSL certificate authority - same file on both server and client
    ssl_cert_ca = /etc/burp/ssl_cert_ca.pem
    # Client SSL certificate
    ssl_cert = /etc/burp/ssl_cert-client.pem
    # Client SSL key
    ssl_key = /etc/burp/ssl_cert-client.key
    # SSL key password
    ssl_key_password = password
    # Common name in the certificate that the server gives us
    ssl_peer_cn = burpserver
    # The following options specify exactly what to backup.
    include = /home
    EOF


Our `Burp`_ server is now set up, we can start it:

::

    /etc/init.d/burp start


Now we can configure `Burp-UI`_. The package comes with a default configuration
and init scripts. We copy them at the right place:

::

    cp /usr/local/share/burpui/contrib/debian/init.sh /etc/init.d/burp-ui
    chmod +x /etc/init.d/burp-ui
    update-rc.d burp-ui defaults
    cp /usr/local/share/burpui/etc/burpui.sample.cfg /etc/burp/burpui.cfg


The default configuration is plug and play for this case, we just have to start
`Burp-UI`_:

::

    /etc/init.d/burp-ui start


Your server is now fully set-up, you can access `Burp-UI`_ by pointing your
browser to: http://server_ip:5000/

The default user / password is: admin / admin

For further customization, you can refer to the `usage`_ page of this
documentation.


Burp2 server
------------

In this scenario, we are going to install a `Burp`_ server version 2.0.28.
We assume you are using the user *root* to run the following commands.

We begin with the installation of `Burp`_ itself.

First, we need some system requirements in order to compile `Burp`_ and to
install `Burp-UI`_:

::

    apt-get update
    apt-get install uthash-dev g++ make libssl-dev librsync-dev python2.7-dev \
    git python-pip libffi-dev libyajl-dev libz-dev


Now we retrieve the `Burp`_ sources and then we compile and install it:

::

    cd /usr/src
    git clone https://github.com/grke/burp.git
    cd burp
    git checkout tags/2.0.28
    ./configure
    make
    make install
    # we also install init scripts
    cp debian/init /etc/init.d/burp
    cat >/etc/default/burp<<EOF
    RUN="yes"
    DAEMON_ARGS="-c /etc/burp/burp-server.conf"
    EOF
    chmod +x /etc/init.d/burp
    update-rc.d burp defaults


It is now time to install `Burp-UI`_:

::

    pip install --upgrade burp-ui


Now that everything is installed, let's configure our tools!

In order to perform online restorations, `Burp-UI`_ relies on a classical
`Burp`_ client.

We need to define our client, and we also need to allow it to perform
restorations for other clients. We will set it up globally. Our client will be
named *bui*:

::

    # burp-ui client's definition
    cat >/etc/burp/clientconfdir/bui<<EOF
    password = abcdefgh
    EOF

    # grant our client to perform restorations for others
    echo "restore_client = bui" >>/etc/burp/burp-server.conf
    # Burp 2 is able to cache the manifests for better performances
    echo "monitor_browse_cache = 1" >>/etc/burp/burp-server.conf

    # now we generate ou client configuration
    cat >/etc/burp/burp.conf<<EOF
    mode = client
    port = 4971
    status_port = 4972
    server = ::1
    password = abcdefgh
    cname = bui
    pidfile = /var/run/burp.bui.pid
    syslog = 0
    stdout = 1
    progress_counter = 1
    network_timeout = 72000
    ca_burp_ca = /usr/sbin/burp_ca
    ca_csr_dir = /etc/burp/CA-client
    # SSL certificate authority - same file on both server and client
    ssl_cert_ca = /etc/burp/ssl_cert_ca.pem
    # Client SSL certificate
    ssl_cert = /etc/burp/ssl_cert-client.pem
    # Client SSL key
    ssl_key = /etc/burp/ssl_cert-client.key
    # SSL key password
    ssl_key_password = password
    # Common name in the certificate that the server gives us
    ssl_peer_cn = burpserver
    # The following options specify exactly what to backup.
    include = /home
    EOF


Our `Burp`_ server is now set up, we can start it:

::

    /etc/init.d/burp start


Now we can configure `Burp-UI`_. The package comes with a default configuration
and init scripts. We copy them at the right place:

::

    cp /usr/local/share/burpui/contrib/debian/init.sh /etc/init.d/burp-ui
    chmod +x /etc/init.d/burp-ui
    update-rc.d burp-ui defaults
    cp /usr/local/share/burpui/etc/burpui.sample.cfg /etc/burp/burpui.cfg


We have to edit the default configuration in order to work with a `Burp`_-2
server:

::

    sed -i "s/^version: .*/version: 2/" /etc/burp/burpui.cfg


That's it, the other default parameter should be able to handle such a setup.
We can start `Burp-UI`_:

::

    /etc/init.d/burp-ui start


Your server is now fully set-up, you can access `Burp-UI`_ by pointing your
browser to: http://server_ip:5000/

The default user / password is: admin / admin

For further customization, you can refer to the `usage`_ page of this
documentation.


Multiple servers
----------------

[TODO]


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Burp: http://burp.grke.net/
.. _usage: usage.html
