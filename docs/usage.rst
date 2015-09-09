Usage
=====

`Burp-UI`_ has been written with modularity in mind. The aim is to support
`Burp`_ from the stable to the latest versions. `Burp`_ exists in two major
versions: 1.x.x and 2.x.x.
The version 2.x.x is currently in heavy development and should bring a lot of
improvements, but also a lot of rework especially regarding the ``status port``
which is the main communication system between `Burp`_ and `Burp-UI`_.

Both `Versions`_ are supported by `Burp-UI`_ thanks to its modular design.
The consequence is you have various options in the configuration file to suite
every bodies needs.

There are also different modules to support `Authentication`_ and `ACL`_ within
the web-interface.

.. warning::
   `Burp-UI`_ tries to be the less intrusive as possible, nevertheless it ships
   with the ability to manage `Burp`_'s configuration files.
   This feature **requires** `Burp-UI`_ to be launched on the **same** server
   that hosts your `Burp`_ instance.
   You also have to make sure the user that runs `Burp-UI`_ has **enough**
   privileges to edit those files.


Configuration
-------------

The `burpui.cfg`_ configuration file contains a ``[Global]`` section as follow:

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


Each option is commented, but here is a more detailed documentation:

- *port*: On which port is `Burp-UI`_ listening. This option is ignored when
  using `Gunicorn`_.
- *bind*: On which address is `Burp-UI`_ listening. This option is ignored when
  using `Gunicorn`_.
- *ssl*: Whether to enable SSL or not. This option is ignored when using
  `Gunicorn`_.
- *sslcert*: SSL certificate to use when SSL support is enabled.
- *sslkey*: SSL key to use when SSL support is enabled.
- *version*: What version of `Burp`_ this `Burp-UI`_ instance manages. Can
  either be *1* or *2*. This parameter determines which backend is loaded at
  runtime.

  (see `Versions`_ for more details)
- *standalone*: `Burp-UI`_ can run in two different modes. If it runs in
  standalone mode (meaning you set this parameter to *true*), you can only
  address **one** `Burp`_ server of the version specified by the previous
  parameter.

  If this option is set to *false*, `Burp-UI`_ will run as a *proxy* allowing
  you to address multiple `Burp`_ servers. In this mode, you need to configure
  **at least one** *Agent* section in your configuration file. You also need to
  run one ``bui-agent`` per server.

  (see `Modes`_ for more details)
- *auth*: What `Authentication`_ backend to use.
- *acl*: What `ACL`_ module to use.


There is also a ``[UI]`` section in which you can configure some *UI*
parameters:

::

    [UI]
    # refresh interval of the pages in seconds
    refresh: 180
    # refresh interval of the live-monitoring page in seconds
    liverefresh: 5


Each option is commented, but here is a more detailed documentation:

- *refresh*: Time in seconds between two refresh of the interface.
- *liverefresh*: Time in seconds between two refresh of the *live-monitor* page.

Modes
-----

`Burp-UI`_ provides two modes:

- `Standalone`_
- `Multi-Agent`_

These modes allow you to either access a single `Burp`_ server or multiple
`Burp`_ servers hosted on separated hosts.


Standalone
^^^^^^^^^^

This mode is the **default** and the easiest one. It can be activated by setting
the *standalone* parameter in the ``[Global]`` section of your `burpui.cfg`_
file to *true*:

::

    [Global]
    standalone: true


That's all you need to do for this mode to work.


Multi-Agent
^^^^^^^^^^^

This mode allows you access multiple `Burp`_ servers through the `bui-agent`_.
Here is a schema to illustrate the architecture:

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


To enable this mode, you need to set the *standalone* parameter of the
``[Global]`` section of your `burpui.cfg`_ file to *false*:

::

    [Global]
    standalone: false


Once this mode is enabled, you have to create **one** ``[Agent]`` section
**per** agent you want to connect to in your `burpui.cfg`_ file:

::

    # If you set standalone to 'false', add at least one section like this per
    # bui-agent
    [Agent:agent1]
    # bui-agent address
    host: 192.168.1.1
    # bui-agent port
    port: 10000
    # bui-agent password
    password: azerty
    # enable SSL
    ssl: true
    # socket timeout (in seconds)
    timeout: 5

    [Agent:agent2]
    # bui-agent address
    host: 192.168.2.1
    # bui-agent port
    port: 10000
    # bui-agent password
    password: ytreza
    # enable SSL
    ssl: true
    # socket timeout (in seconds)
    timeout: 5


.. note:: The sections must be called ``[Agent:<label>]`` (case sensitive)

To configure your agents, please refer to the `bui-agent`_ page.


Versions
--------

`Burp-UI`_ ships with two different backends:

- `Burp1`_
- `Burp2`_

These backends allow you to either connect to a `Burp`_ server version 1.x.x or
2.x.x.


Burp1
^^^^^

The *burp-1* backend can be enabled by setting the *version* option to *1* in
the ``[Global]`` section of your `burpui.cfg`_ file:

::

    [Global]
    version: 1


Now you can add *burp-1* backend specific options:

::

    # burp1 backend specific options
    [Burp1]
    # burp status address (can only be '127.0.0.1' or '::1')
    bhost: ::1
    # burp status port
    bport: 4972
    # burp binary
    burpbin: /usr/sbin/burp
    # vss_strip binary
    stripbin: /usr/sbin/vss_strip
    # burp client configuration file used for the restoration (Default: None)
    bconfcli: /etc/burp/burp.conf
    # burp server configuration file used for the setting page
    bconfsrv: /etc/burp/burp-server.conf
    # temporary directory to use for restoration
    tmpdir: /tmp


Each option is commented, but here is a more detailed documentation:

- *bhost*: The address of the `Burp`_ server. In burp-1.x.x, it can only be
  *127.0.0.1* or *::1*
- *bport*: The port of `Burp`_'s status port.
- *burpbin*: Path to the `Burp`_ binary (used for restorations).
- *stripbin*: Path to the `Burp`_ *vss_strip* binary (used for restorations).
- *bconfcli*: Path to the `Burp`_ client configuration file.
- *bconfsrv*: Path to the `Burp`_ server configuration file.
- *tmpdir*: Path to a temporary directory where to perform restorations.


Burp2
^^^^^

The *burp-2* backend can be enabled by setting the *version* option to *2* in
the ``[Global]`` section of your `burpui.cfg`_ file:

::

    [Global]
    version: 2


Now you can add *burp-2* backend specific options:

::

    # burp2 backend specific options
    [Burp2]
    # burp binary
    burpbin: /usr/sbin/burp
    # vss_strip binary
    stripbin: /usr/sbin/vss_strip
    # burp client configuration file used for the restoration (Default: None)
    bconfcli: /etc/burp/burp.conf
    # burp server configuration file used for the setting page
    bconfsrv: /etc/burp/burp-server.conf
    # temporary directory to use for restoration
    tmpdir: /tmp


Each option is commented, but here is a more detailed documentation:

- *burpbin*: Path to the `Burp`_ binary (used for restorations).
- *stripbin*: Path to the `Burp`_ *vss_strip* binary (used for restorations).
- *bconfcli*: Path to the `Burp`_ client configuration file.
- *bconfsrv*: Path to the `Burp`_ server configuration file.
- *tmpdir*: Path to a temporary directory where to perform restorations.


Authentication
--------------

`Burp-UI`_ provides some authentication backends in order to restrict access
only to granted users.
There are currently two different backends:

- `LDAP`_
- `Basic`_

To disable the *authentication* backend, set the *auth* option of the
``[Global]`` section of your `burpui.cfg`_ file to *none*:

::

    [Global]
    auth: none


LDAP
^^^^

The *ldap* authentication backend has some dependencies, please refer to the
`requirements <requirements.html>`_ page. To enable this backend, you need to
set the *auth* option of the ``[Global]`` section of your `burpui.cfg`_ file to
*ldap*:

::

    [Global]
    auth: ldap


Now you can add *ldap* specific options:

::

    # ldapauth specific options
    [LDAP]
    # LDAP host
    host: 127.0.0.1
    # LDAP port
    port: 389
    # Encryption type to LDAP server (none, ssl or tls)
    # - try tls if unsure, otherwise ssl on port 636
    encryption: tls
    # specifies if the server certificate must be validated, values can be:
    #  - none (certificates are ignored)
    #  - optional (not required, but validated if provided)
    #  - required (required and validated)
    validate: none
    # SSL or TLS version to use, can be one of the following:
    #  - SSLv2
    #  - SSLv3
    #  - SSLv23
    #  - TLSv1
    #  - TLSv1_1 (Available only with openssl version 1.0.1+, requires python 2.7.9 or higher)
    version: TLSv1
    # the file containing the certificates of the certification authorities
    cafile: none
    # Attribute to use when searching the LDAP repository
    #searchattr: sAMAccountName
    searchattr: uid
    # LDAP filter to find users in the LDAP repository
    #  - {0} will be replaced by the search attribute
    #  - {1} will be replaced by the login name
    filter: (&({0}={1})(burpui=1))
    #filter: (&({0}={1})(|(userAccountControl=512)(userAccountControl=66048)))
    # LDAP base
    base: ou=users,dc=example,dc=com
    # Binddn to list existing users
    binddn: cn=admin,dc=example,dc=com
    # Bindpw to list existing users
    bindpw: Sup3rS3cr3tPa$$w0rd


.. note:: The *host* options accepts URI style (ex: ldap://127.0.0.1:389)


Basic
^^^^^

In order for the *basic* authentication backend to be enabled, you need to set
the *auth* option of the ``[Global]`` section of your `burpui.cfg`_ file to
*basic*:

::

    [Global]
    auth: basic


Now you can add *basic* specific options:

::

    # basicauth specific options
    # Note: in case you leave this section commented, the default login/password
    # is admin/admin
    [BASIC]
    admin: password
    user1: otherpassword


.. note:: Each line defines a new user with the *key* as the username and the *value* as the password


ACL
---

`Burp-UI`_ implements some mechanisms to restrict access on some resources only
for some users.
There is currently only one backend:

- `Basic ACL`_

To disable the *acl* backend, set the *acl* option of the ``[Global]`` section
of your `burpui.cfg`_ file to *none*:

::

    [Global]
    acl: none


Basic ACL
^^^^^^^^^


The *basic* acl backend can be enabled by setting the *acl* option of the
``[Global]`` section of your `burpui.cfg`_ file to *basic*:

::

    [Global]
    acl: basic


Now you can add *basic acl* specific options:

::

    # basicacl specific options
    # Note: in case you leave this section commented, the user 'admin' will have
    # access to all clients whereas other users will only see the client that have
    # the same name
    [BASIC:ACL]
    # Please note the double-quote around the username on the admin line are
    # mandatory!
    admin: ["user1","user2"]
    # You can also overwrite the default behavior by specifying which clients a
    # user can access
    user3: ["client4", "client5"]
    # In case you are not in a standalone mode, you can also specify which clients
    # a user can access on a specific Agent
    user4: {"agent1": ["client6", "client7"], "agent2": ["client8"]}


.. warning:: The double-quotes are **mendatory**


.. _Burp: http://burp.grke.org/
.. _Gunicorn: http://gunicorn.org/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _burpui.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/share/burpui/etc/burpui.sample.cfg
.. _bui-agent: buiagent.html
