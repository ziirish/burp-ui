bui-agent
=========

The `bui-agent`_ is a kind of proxy between a `Burp`_ server and your `Burp-UI`_
server.

It is useful when you have several servers to monitor and/or when you don't want
(or can't) install the full `Burp-UI`_ on your server.


Architecture
------------

The architecture is described bellow:

::

    +--------------------+       +--------------------+       +--------------------+       +--------------------+
    |                    |       |                    |       |                    |       |                    |
    |  burp-server 1     |       |  burp-server 2     |       |        ...         |       |  burp-server n     |
    |                    |       |                    |       |                    |       |                    |
    +--------------------+       +--------------------+       +--------------------+       +--------------------+
    |                    |       |                    |       |                    |       |                    |
    |                    |       |                    |       |                    |       |                    |
    |                    |       |                    |       |                    |       |                    |
    |                    |       |                    |       |                    |       |                    |
    | +----------------+ |       | +----------------+ |       | +----------------+ |       | +----------------+ |
    | |                | |       | |                | |       | |                | |       | |                | |
    | |  bui-agent 1   | |       | |  bui-agent 2   | |       | |      ...       | |       | |  bui-agent n   | |
    | |                | |       | |                | |       | |                | |       | |                | |
    | +-------^--------+ |       | +-------^--------+ |       | +--------^-------+ |       | +-------^--------+ |
    +---------|----------+       +---------|----------+       +----------|---------+       +---------|----------+
              |                            |                             |                           |
              |                            |                             |                           |
              |                            |                             |                           |
              |                            |                             |                           |
              |                            |                             |                           |
              |                            |                             |                           |
              |                            |                             |                           |
              |                            |                             |                           |
              |                            |      +--------------------+ |                           |
              |                            |      |                    | |                           |
              |                            |      |   front-server     | |                           |
              |                            |      |                    | |                           |
              |                            |      +--------------------+ |                           |
              |                            |      |                    | |                           |
              |                            |      |                    | |                           |
              |                            |      |                    | |                           |
              |                            |      |                    | |                           |
              |                            |      | +----------------+ | |                           |
              |                            |      | |                | | |                           |
              |                            +--------+  burp-ui front +---+                           |
              +-------------------------------------+                +-------------------------------+
                                                  | +--------^-------+ |
                                                  +----------|---------+
                                                             |
                                                             |
                                                  +----------+---------+
                                                  |                    |
                                                  |      client        |
                                                  |                    |
                                                  +--------------------+
                                                  |                    |
                                                  |                    |
                                                  |                    |
                                                  |                    |
                                                  |                    |
                                                  |                    |
                                                  |                    |
                                                  |                    |
                                                  |                    |
                                                  +--------------------+


Requirements
------------

The agent is powered by gevent. In order to install it, you can run the
following command:

::

    pip install "burp-ui[agent]"


Configuration
-------------

These agents must be launched on every server hosting a `Burp`_ instance you'd
like to monitor.

They have a specific `buiagent.cfg`_ configuration file with a ``[Global]``
section as below:

::

    [Global]
    # On which port is the application listening
    port = 10000
    # On which address is the application listening
    # '::' is the default for all IPv6
    # set it to '0.0.0.0' if you want to listen on all IPv4 addresses
    bind = ::
    # enable SSL
    ssl = true
    # ssl cert
    sslcert = /etc/burp/ssl_cert-server.pem
    # ssl key
    sslkey = /etc/burp/ssl_cert-server.key
    # burp server version 1 or 2
    version = 1
    # agent password
    password = password


Each option is commented, but here is a more detailed documentation:

- *port*: On which port is `bui-agent`_ listening.
- *bind*: On which address is `bui-agent`_ listening.
- *ssl*: Whether to communicate with the `Burp-UI`_ server over SSL or not.
- *sslcert*: What SSL certificate to use when SSL is enabled.
- *sslkey*: What SSL key to use when SSL is enabled.
- *version*: What version of `Burp`_ this `bui-agent`_ instance manages. (see
  `Burp-UI versions <usage.html#versions>`__ for more details)
- *password*: The shared secret between the `Burp-UI`_ server and `bui-agent`_.

As with `Burp-UI`_, you need a specific section depending on the *version*
value. Please refer to the `Burp-UI versions <usage.html#versions>`__ section
for more details.

Daemon
------

I have no plan to implement daemon features, but there are a lot of tools
available to help you achieve such a behavior.

For instance, you can create a systemd service file containing:

::

    [Unit]
    Description=Burp-UI agent service
    After=network.target

    [Service]
    ExecStart=/usr/local/bin/bui-agent
    User=burpui


You can also have a look at how the demo works (it uses supervisor)

Example
-------

Here is a full usage example:

::

    # On the server called 'agent1'
    agent1:~$ bui-agent -c path/to/buiagent.cfg

    # On the server called 'agent2'
    agent2:~$ bui-agent -c path/to/buiagent.cfg

    # On the server called 'front'
    front:~$ burp-ui -c path/to/burpui.cfg


This example uses three servers. You then only need to point your browser to
http://front:5000/ for instance, and the `Burp-UI`_ instance (front) will
*proxify* the requests to the two agents for you.

Service
=======

To run bui-agent as service. 



.. _Burp: http://burp.grke.org/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _buiagent.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/share/burpui/etc/buiagent.sample.cfg
.. _bui-agent: buiagent.html
