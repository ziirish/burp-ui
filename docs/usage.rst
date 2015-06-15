Usage
=====

``Burp-UI`` has been written with modularity in mind. The aim is to support
`Burp`_ from the stable to the latest versions. `Burp`_ exists in two major
versions: 1.x.x and 2.x.x. The version 2.x.x is currently in heavy development
and should bring a lot of improvements, but also a lot of rework especially
regarding the ``status port`` which is the main communication system between
`Burp`_ and ``Burp-UI``.

Both versions are supported by ``Burp-UI`` thanks to its modular design.
The consequence is you have various options in the configuration file to suite
every bodies needs.

There are also different modules to support authentication and ACL within the
web-interface.


Configuration
-------------

The configuration file contains a *Global* section as follow:

::

    [Global]
    # On which port is the application listening
    port: 5000
    # On which address is the application listening
    # '::' is the default for all IPv6
    bind: ::
    # enable SSL
    ssl: false
    # ssl cert
    sslcert: /etc/burp/ssl_cert-server.pem
    # ssl key
    sslkey: /etc/burp/ssl_cert-server.key
    # burp server version 1 or 2
    version: 1
    # Handle multiple bui-servers or not
    # If set to 'false', you will need to declare at least one 'Agent' section (see
    # bellow)
    standalone: true
    # authentication plugin (mandatory)
    # list the misc/auth directory to see the available backends
    # to disable authentication you can set "auth: none"
    auth: basic
    # acl plugin
    # list misc/acl directory to see the available backends
    # default is no ACL
    acl: basic


Each option is documented, but here is a more detailed documentation:

- *port*: On which port is ``Burp-UI`` listening. This option is ignored when
  using `Gunicorn`_.
- *bind*: On which address is ``Burp-UI`` listening. This option is ignored when
  using `Gunicorn`_.
- *ssl*: Whether to enable SSL or not. This option is ignored when using
  `Gunicorn`_.
- *sslcert*: SSL certificate to use when SSL support is enabled.
- *sslkey*: SSL key to use when SSL support is enabled.
- *version*: What version of `Burp`_ this ``Burp-UI`` instance manages. Can
  either be *1* or *2*. This parameter determines which backend is loaded at
  runtime.
- *standalone*: ``Burp-UI`` can run in two different modes. If it runs in
  standalone mode (meaning you set this parameter to *true*), you can only
  address **one** `Burp`_ server of the version specified by the previous
  parameter.
  If this option is set to *false*, ``Burp-UI`` will run as a *proxy* allowing
  you to address multiple `Burp`_ servers. In this mode, you need to configure
  **at least one** *Agent* section in your configuration file. You also need to
  run one ``bui-agent`` per server.
- *auth*: What authentication backend to use.
- *acl*: What ACL module to use.


Burp1
-----


.. _Burp: http://burp.grke.org/
.. _Gunicorn: http://gunicorn.org/
