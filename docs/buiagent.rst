bui-agent
=========

The `bui-agent`_ is a kind of proxy between a `Burp`_ server and your `Burp-UI`_
server.

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


Configuration
-------------

These agents must be launched on every server hosting a `Burp`_ instance you'd
like to monitor.

They have a specific `buiagent.cfg`_ configuration file with a ``[Global]``
section as below:

::

    [Global]
    # On which port is the application listening
    port: 10000
    # On which address is the application listening
    # '0.0.0.0' is the default for all IPv4
    bind: 0.0.0.0
    # enable SSL
    ssl: true
    # ssl cert
    sslcert: /etc/burp/ssl_cert-server.pem
    # ssl key
    sslkey: /etc/burp/ssl_cert-server.key
    # burp server version (currently only burp 1.x is implemented)
    version: 1
    # agent password
    password: password
    # number of threads that will handle requests
    threads: 5


Each option is commented, but here is a more detailed documentation:

- *port*: On which port is `bui-agent`_ listening.
- *bind*: On which address is `bui-agent`_ listening.
- *ssl*: Whether to communicate with the `Burp-UI`_ server over SSL or not.
- *sslcert*: What SSL certificate to use when SSL is enabled.
- *sslkey*: What SSL key to use when SSL is enabled.
- *version*: What version of `Burp`_ this `bui-agent`_ instance manages. (see
  `Burp-UI versions <usage.html#versions>`__ for more details)
- *password*: The shared secret between the `Burp-UI`_ server and `bui-agent`_.
- *threads*: Number of threads that will handle requests.
  You'll have to set *max_status_children* accordingly in your burp-server
  configuration because every thread makes a connection to the status port.

As with `Burp-UI`_, you need a specific section depending on the *version*
value. Please refer to the `Burp-UI versions <usage.html#versions>`__ section
for more details.


Example
-------

Here is a full usage example:

::

    # On the server called 'agent1'
    agent1:~$ python path/to/bui-agent -c path/to/buiagent.cfg

    # On the server called 'agent2'
    agent2:~$ python path/to/bui-agent -c path/to/buiagent.cfg

    # On the server called 'front'
    front:~$ python path/to/burp-ui -c path/to/burpui.cfg


This example uses three servers. You then only need to point your browser to
http://front:5000/ for instance, and the `Burp-UI`_ instance (front) will
*proxify* the requests to the two agents for you.


.. _Burp: http://burp.grke.org/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _buiagent.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/share/burpui/etc/buiagent.sample.cfg
.. _bui-agent: buiagent.html
