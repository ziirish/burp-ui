Advanced usage
==============

.. highlight:: ini

`Burp-UI`_ has been written with modularity in mind. The aim is to support
`Burp`_ from the stable to the latest versions. `Burp`_ exists in two major
versions: 1.x.x and 2.x.x.

Both `Versions`_ are supported by `Burp-UI`_ thanks to its modular design.
The consequence is you have various options in the configuration file to suite
everybody needs.

There are also different modules to support `Authentication`_ and `ACL`_ within
the web-interface.

.. warning::
    `Burp-UI`_ tries to be as less intrusive as possible, nevertheless it ships
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
    # burp server version 1 or 2
    version = 2
    # Handle multiple bui-servers or not
    # If set to 'false', you will need to declare at least one 'Agent' section (see
    # bellow)
    single = true
    # authentication plugin (mandatory)
    # list the misc/auth directory to see the available backends
    # to disable authentication you can set "auth = none"
    # you can also chain multiple backends. Example: "auth = ldap,basic"
    # the order will be respected unless you manually set a higher backend priority
    auth = basic
    # acl plugin
    # list misc/acl directory to see the available backends
    # default is no ACL
    acl = basic
    # You can change the prefix if you are behind a reverse-proxy under a custom
    # root path. For example: /burpui
    # You can also configure your reverse-proxy to announce the prefix through the
    # 'X-Script-Name' header. In this case, the bellow prefix will be ignored in
    # favour of the one announced by your reverse-proxy
    prefix = none
    # list of paths to look for external plugins
    plugins = none


Each option is commented, but here is a more detailed documentation:

- *version*: What version of `Burp`_ this `Burp-UI`_ instance manages. Can
  either be *1* or *2*. This parameter determines which backend is loaded at
  runtime.

  (see `Versions`_ for more details)
- *single*: `Burp-UI`_ can run in two different modes. If it runs in
  single mode (meaning you set this parameter to *true*), you can only
  address **one** `Burp`_ server of the version specified by the previous
  parameter.

  If this option is set to *false*, `Burp-UI`_ will run as a *proxy* allowing
  you to address multiple `Burp`_ servers. In this mode, you need to configure
  **at least one** *Agent* section in your configuration file. You also need to
  run one ``bui-agent`` per server.

  (see `Modes`_ for more details)
- *auth*: What `Authentication`_ backend to use.
- *acl*: What `ACL`_ module to use.
- *prefix*: You can host `Burp-UI`_ behind a sub-root path. See the `gunicorn
  <gunicorn.html#sub-root-path>`__ page for details.
- *plugins*: Specify a list of paths to look for external plugins. See the
  `Plugins <plugins.html>`_ page for details on how to write plugins.


There is also a ``[UI]`` section in which you can configure some *UI*
parameters:

::

    [UI]
    # refresh interval of the pages in seconds
    refresh = 180
    # refresh interval of the live-monitoring page in seconds
    liverefresh = 5
    # list of labels to ignore (you can use regex)
    ignore_labels = "color:.*", "custom:.*"
    # format label using sed-like syntax
    format_labels = "s/^os:\s*//"
    # default strip leading path value for file restorations
    default_strip = 0


Each option is commented, but here is a more detailed documentation:

- *refresh*: Time in seconds between two refresh of the interface.
- *liverefresh*: Time in seconds between two refresh of the *live-monitor* page.
- *ignore_labels*: List of labels to ignore from parsing (regex are supported).
- *format_labels*: List of *sed-like* expressions to transform labels. Example: ``"s/^os:\s*//", "s/i/o/"`` will transform the label ``os: Windows`` into ``Wondows``.
- *default_strip*: Number of leading paths to strip by default while restoring files.

Production
----------

The `burpui.cfg`_ configuration file contains a ``[Production]`` section as
follow:

::

    [Production]
    # storage backend for session and cache
    # may be either 'default' or 'redis'
    storage = default
    # session database to use
    # may also be a backend url like: redis://localhost:6379/0
    # if set to 'redis', the backend url defaults to:
    # redis://<redis_host>:<redis_port>/0
    # where <redis_host> is the host part, and <redis_port> is the port part of
    # the below "redis" setting
    session = default
    # cache database to use
    # may also be a backend url like: redis://localhost:6379/0
    # if set to 'redis', the backend url defaults to:
    # redis://<redis_host>:<redis_port>/1
    # where <redis_host> is the host part, and <redis_port> is the port part of
    # the below "redis" setting
    cache = default
    # redis server to connect to
    redis = localhost:6379
    # whether to use celery or not
    # may also be a broker url like: redis://localhost:6379/0
    # if set to "true", the broker url defaults to:
    # redis://<redis_host>:<redis_port>/2
    # where <redis_host> is the host part, and <redis_port> is the port part of
    # the above "redis" setting
    celery = false
    # database url to store some persistent data
    # none or a connect string supported by SQLAlchemy:
    # http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls
    # example: sqlite:////var/lib/burpui/store.db
    database = none
    # whether to rate limit the API or not
    # may also be a redis url like: redis://localhost:6379/0
    # if set to "true" or "redis" or "default", the url defaults to:
    # redis://<redis_host>:<redis_port>/3
    # where <redis_host> is the host part, and <redis_port> is the port part of
    # the above "redis" setting
    # Note: the limiter only applies to the API routes
    limiter = false
    # limiter ratio
    # see https://flask-limiter.readthedocs.io/en/stable/#ratelimit-string
    ratio = 60/minute


WebSocket
---------

The ``[WebSocket]`` section defines specific options for the WebSocket server.
You will find details on how to use this feature in the
`WebSocket <websocket.html>`_ page.

::

    [WebSocket]
    ## This section contains WebSocket server specific options.
    # whether to enable websocket or not
    enabled = true
    # whether to embed the websocket server or not
    # if set to "true", you should have only *one* gunicorn worker
    # see here for details:
    # https://flask-socketio.readthedocs.io/en/latest/#gunicorn-web-server
    embedded = false
    # what broker to use to interact between websocket servers
    # may be a redis url like: redis://localhost:6379/0
    # if set to "true" or "redis" or "default", the url defaults to:
    # redis://<redis_host>:<redis_port>/4
    # where <redis_host> is the host part, and <redis_port> is the port part of
    # the above "redis" setting
    # set this to none to disable the broker
    broker = redis
    # if you choose to run a dedicated websocket server (with embedded = false)
    # you can specify here the websocket url. You'll need to double quote your
    # string though.
    # example:
    # url = "document.domain + ':5001'"
    url = none
    # whether to enable verbose websocket server logs or not (for development)
    debug = false


Experimental
------------

There is a ``[Experimental]`` section for features that have not been deeply
tested:

::

    [Experimental]
    ## This section contains some experimental features that have not been deeply
    ## tested yet
    # enable zip64 feature. Python doc says:
    # « ZIP64 extensions are disabled by default because the default zip and unzip
    # commands on Unix (the InfoZIP utilities) don’t support these extensions. »
    zip64 = false


These options are also available in the `bui-agent`_ configuration file.

Security
--------

The ``[Security]`` section contains options to harden the security of the
application:

::

    [Security]
    ## This section contains some security options. Make sure you understand the
    ## security implications before changing these.
    # list of 'root' paths allowed when sourcing files in the configuration.
    # Set this to 'none' if you don't want any restrictions, keeping in mind this
    # can lead to accessing sensible files. Defaults to '/etc/burp'.
    # Note: you can have several paths separated by comas.
    # Example: /etc/burp,/etc/burp.d
    includes = /etc/burp
    # if files already included in config do not respect the above restriction, we
    # prune them
    enforce = false
    # enable certificates revocation
    revoke = false
    # remember_cookie duration in days
    cookietime = 14
    # whether to use a secure cookie for https or not. If set to false, cookies
    # won't have the 'secure' flag.
    # This setting is only useful when HTTPS is detected
    scookie = true
    # application secret to secure cookies. If you don't set anything, the default
    # value is 'random' which will generate a new secret after every restart of your
    # application. You can also set it to 'none' although this is not recommended.
    appsecret = random


Some of these options are also available in the `bui-agent`_ configuration file.

Modes
-----

`Burp-UI`_ provides two modes:

- `Single`_
- `Multi-Agent`_

These modes allow you to either access a single `Burp`_ server or multiple
`Burp`_ servers hosted on separated hosts.


Single
^^^^^^

This mode is the **default** and the easiest one. It can be activated by setting
the *single* parameter in the ``[Global]`` section of your `burpui.cfg`_
file to *true*:

::

    [Global]
    single = true


That's all you need to do for this mode to work.


Multi-Agent
^^^^^^^^^^^

This mode allows you to access multiple `Burp`_ servers through the `bui-agent`_.
The architecture is available on the bui-agent
`page <buiagent.html#architecture>`__.


To enable this mode, you need to set the *single* parameter of the
``[Global]`` section of your `burpui.cfg`_ file to *false*:

::

    [Global]
    single = false


Once this mode is enabled, you have to create **one** ``[Agent]`` section
**per** agent you want to connect to in your `burpui.cfg`_ file:

::

    # If you set single to 'false', add at least one section like this per
    # bui-agent
    [Agent:agent1]
    # bui-agent address
    host = 192.168.1.1
    # bui-agent port
    port = 10000
    # bui-agent password
    password = azerty
    # enable SSL
    ssl = true

    [Agent:agent2]
    # bui-agent address
    host = 192.168.2.1
    # bui-agent port
    port = 10000
    # bui-agent password
    password = ytreza
    # enable SSL
    ssl = true


.. note:: The sections must be called ``[Agent:<label>]`` (case sensitive)

To configure your agents, please refer to the `bui-agent`_ page.


Versions
--------

`Burp-UI`_ ships with two different backends:

- `Burp1`_
- `Burp2`_

These backends allow you to either connect to a `Burp`_ server version 1.x.x or
2.x.x.

.. note::
    If you are using a `Burp`_ server version 2.x.x you **have** to use the
    `Burp2`_ backend, no matter what `Burp`_'s protocol you are using.


Burp1
^^^^^

.. note::
    Make sure you have read and understood the `requirements
    <requirements.html#burp1>`__ first.

The *burp-1* backend can be enabled by setting the *version* option to *1* in
the ``[Global]`` section of your `burpui.cfg`_ file:

::

    [Global]
    version = 1


Now you can refer to the `Options`_ section for further setup.


Burp2
^^^^^

.. note::
    Make sure you have read and understood the `requirements
    <requirements.html#burp2>`__ first.

.. note::
    The `gunicorn <gunicorn.html#daemon>`__ documentation may help you
    configuring your system.

The *burp-2* backend can be enabled by setting the *version* option to *2* in
the ``[Global]`` section of your `burpui.cfg`_ file:

::

    [Global]
    version = 2


Now you can refer to the `Options`_ section for further setup.


Options
^^^^^^^

::

    # burp backend specific options
    [Burp]
    # burp status address (can only be '127.0.0.1' or '::1')
    bhost = ::1
    # burp status port
    bport = 4972
    # burp binary
    burpbin = /usr/sbin/burp
    # vss_strip binary
    stripbin = /usr/sbin/vss_strip
    # burp client configuration file used for the restoration (Default: None)
    bconfcli = /etc/burp/burp.conf
    # burp server configuration file used for the setting page
    bconfsrv = /etc/burp/burp-server.conf
    # temporary directory to use for restoration
    tmpdir = /tmp
    # how many time to wait for the monitor to answer (in seconds)
    timeout = 5


Each option is commented, but here is a more detailed documentation:

- *bhost*: The address of the `Burp`_ server. In burp-1.x.x, it can only be
  *127.0.0.1* or *::1*
- *bport*: The port of `Burp`_'s status port.
- *burpbin*: Path to the `Burp`_ binary (used for restorations).
- *stripbin*: Path to the `Burp`_ *vss_strip* binary (used for restorations).
- *bconfcli*: Path to the `Burp`_ client configuration file (see
  `restoration <installation.html#restoration>`__).
- *bconfsrv*: Path to the `Burp`_ server configuration file.
- *tmpdir*: Path to a temporary directory where to perform restorations.
- *timeout*: Time to wait for the monitor to answer in seconds.


Authentication
--------------

`Burp-UI`_ provides some authentication backends in order to restrict access
only to granted users.
There are currently three different backends:

- `LDAP`_
- `Basic`_
- `Local`_

To disable the *authentication* backend, set the *auth* option of the
``[Global]`` section of your `burpui.cfg`_ file to *none*:

::

    [Global]
    auth = none


You can use multiple backends, they will be sorted by priority or in the order
they are defined if no priority is found.
If a user is present in several backends, the first one that matches both login
and password will be used.

Example:

::

    [Global]
    auth = basic,ldap


LDAP
^^^^

The *ldap* authentication backend has some dependencies, please refer to the
`requirements <requirements.html#ldap>`_ page. To enable this backend, you need
to set the *auth* option of the ``[Global]`` section of your `burpui.cfg`_ file
to *ldap*:

::

    [Global]
    auth = ldap


Now you can add *ldap* specific options:

::

    # ldapauth specific options
    [LDAP]
    # Backend priority. Higher is first
    priority = 50
    # LDAP host
    host = 127.0.0.1
    # LDAP port
    port = 389
    # Encryption type to LDAP server (none, ssl or tls)
    # - try tls if unsure, otherwise ssl on port 636
    encryption = tls
    # specifies if the server certificate must be validated, values can be:
    #  - none (certificates are ignored)
    #  - optional (not required, but validated if provided)
    #  - required (required and validated)
    validate = none
    # SSL or TLS version to use, can be one of the following:
    #  - SSLv2
    #  - SSLv3
    #  - SSLv23
    #  - TLSv1
    #  - TLSv1_1 (Available only with openssl version 1.0.1+, requires python 2.7.9 or higher)
    version = TLSv1
    # the file containing the certificates of the certification authorities
    cafile = none
    # Attribute to use when searching the LDAP repository
    #searchattr = sAMAccountName
    searchattr = uid
    # LDAP filter to find users in the LDAP repository
    #  - {0} will be replaced by the search attribute
    #  - {1} will be replaced by the login name
    filter = (&({0}={1})(burpui=1))
    #filter = (&({0}={1})(|(userAccountControl=512)(userAccountControl=66048)))
    # LDAP base
    base = "ou=users,dc=example,dc=com"
    # Binddn to list existing users
    binddn = "cn=admin,dc=example,dc=com"
    # Bindpw to list existing users
    bindpw = Sup3rS3cr3tPa$$w0rd


.. note:: The *host* options accepts URI style (ex: ldap://127.0.0.1:389)

.. warning:: The quotes (") around *base* and *binddn* are **MANDATORY**

Basic
^^^^^

In order for the *basic* authentication backend to be enabled, you need to set
the *auth* option of the ``[Global]`` section of your `burpui.cfg`_ file to
*basic*:

::

    [Global]
    auth = basic


Now you can add *basic* specific options:

::

    # basicauth specific options
    # Note: in case you leave this section commented, the default login/password
    # is admin/admin
    [BASIC]
    # Backend priority. Higher is first
    priority = 100
    admin = pbkdf2:sha1:1000$12345678$password
    user1 = pbkdf2:sha1:1000$87654321$otherpassword


.. note::
    Each line defines a new user with the *key* as the username and the *value*
    as the password

.. warning::
    Since *v0.3.0*, passwords must be hashed (see `manage <manage.html#users>`_
    to know how to create new users with hashed passwords)

Local
^^^^^

In order for the *local* authentication backend to be enabled, you need to set
the *auth* option of the ``[Global]`` section of your `burpui.cfg`_ file to
*local*:

::

    [Global]
    auth = local


Now you can add *local* specific options:

::

    # localauth specific options
    # Note: if not running as root, then burp-ui must be run as group 'shadow' to
    # allow PAM to work
    [LOCAL]
    # Backend priority. Higher is first
    priority = 0
    # List of local users allowed to login. If you don't set this setting, users
    # with uid greater than limit will be able to login
    users = user1,user2
    # Minimum uid that will be allowed to login
    limit = 1000


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
    acl = none


The *ACL* engine has some settings as bellow:

::

    # acl engine global options
    [ACL]
    # Enable extended matching rules (enabled by default)
    # If the rule is a string like 'user1 = desk*', it will match any client that
    # matches 'desk*' no mater what agent it is attached to.
    # If it is a coma separated list of strings like 'user1 = desk*,laptop*' it
    # will match the first matching rule no mater what agent it is attached to.
    # If it is a dict like:
    # user1 = '{"agents": ["srv*", "www*"], "clients": ["desk*", "laptop*"]}'
    # It will also validate against the agent name.
    extended = true
    # If you don't explicitly specify ro/rw grants, what should we assume?
    assume_rw = true
    # The inheritance order maters, it means depending the order you choose,
    # the ACL engine won't handle the grants the same way.
    # By default, ACL inherited by groups will have lower priority, unless you
    # choose otherwise
    inverse_inheritance = false
    # If you specify agents and clients separately, should we link them implicitly?
    # For instance, '{"agents": ["agent1", "agent2"], "clients": ["client1", "client2"]}'
    # will become: '{"agents": {"agent1": ["client1", "client2"], "agent2": ["client1", "client2"]}}'
    implicit_link = true
    # Enable 'legacy' behavior
    # Since v0.6.0, if you don't specify the agents name explicitly, users will be
    # granted on every agents where a client matches user's ACL. If you enable the
    # 'legacy' behavior, you will need to specify the agents explicitly.
    # Note: enabling this option will also disable the extended mode
    legacy = false


Basic ACL
^^^^^^^^^


The *basic* acl backend can be enabled by setting the *acl* option of the
``[Global]`` section of your `burpui.cfg`_ file to *basic*:

::

    [Global]
    acl = basic


Now you can add *basic acl* specific options:

::

    # basicacl specific options
    # Note: in case you leave this section commented, the user 'admin' will have
    # access to all clients whereas other users will only see the client that have
    # the same name
    [BASIC:ACL]
    # Backend priority. Higher is first
    priority = 100
    # List of administrators
    admin = user1,user2
    # List of moderators. Users listed here will inherit the grants of the
    # group '@moderator'
    +moderator = user5,user6
    @moderator = '{"agents":{"ro":["agent1"]}}'
    # NOTE: if you are running single-agent mode, you should specify the ro/rw
    # rights of the moderators using this special 'local' agent name:
    # NOTE: this is the default when running single-agent mode if you don't
    # specify anything else
    #@moderator = '{"agents": {"rw": "local"}}'
    # Please note the double-quotes and single-quotes on the following lines are
    # mandatory!
    # You can also overwrite the default behavior by specifying which clients a
    # user can access
    # Suppose you are running single-agent mode (the default), you only need to
    # specify a list of clients a user can access:
    user3 = '{"clients": {"ro": ["prod*"], "rw": ["dev*", "test1"]}}'
    # In case you are not in a single mode, you can also specify which clients
    # a user can access on a specific Agent
    user4 = '{"agents": {"agent1": ["client6", "client7"], "agent2": ["client8"]}}'
    # You can define read-only and/or read-write grants using:
    user5 = '{"agents": {"www*": {"ro": ["desk*"], "rw": ["desk1"]}}}'
    # Finally, you can define groups using the syntax "@groupname" and adding
    # members using "+groupname". Note: groups can inherit groups!
    @group1 = '{"agents": {"ro": ["*"]}}'
    @group2 = '{"clients": {"rw": ["dev*"]}}'
    +group1 = @group2
    +group2 = user5
    # As a result, user5 will be granted the following rights:
    # '{"ro": {"agents": ["*", "agent1"], "www*": ["desk*"]}, "rw": {"clients": ["dev*"], "www*": ["desk1"]}}


.. warning:: The double-quotes and single-quotes are **MANDATORY**


By default, if a user is named ``admin`` it will be granted the admin role.
Here are the default grants:


1. *admin* => you can do anything
2. *non admin* => you can only see the client that matches your username
3. *custom* => you can manually assign username to clients using the syntax
   ``username = '{"agents": {"agent1": ["client1-1"], "agent2": ["client2-3", "client2-4"]}}'``
   (if you are running a multi-agent setup)
4. *moderators* => can edit the Burp server configurations of any agent unless
   told other wise (with ``ro`` rights), but cannot restore files unless told
   otherwise (with ``rw`` rights). Besides, moderators can create new users.
   They can also delete backups if they have ``rw`` rights on the client.


Since *v0.6.0*, you can define advanced grants through the ``rw`` and ``ro``
keyword.


- ``ro`` means you can only see backup stats and reports (this is great for
  monitoring teams/tools)
- ``rw`` means you can interact with the server in some way. For the *regular*
  users, ``rw`` means you can perform file restorations.
  For moderators, ``rw`` means you can delete backups (if burp thinks they are
  deletable), you can also create/update/delete client configuration files.


About the ``inverse_inheritance`` option, here is a concrete example. We assume
you have this piece of configuration:

::

    [ACL]
    inverse_inheritance = false

    [BASIC:ACL]
    example = '{"agents": {"test": {"rw": ["demo"]}}}'
    @gp_ro = '{"agents": {"*": {"ro": ["*"]}}}'
    +gp_ro = example


Then the client ``demo`` on the ``test`` agent will be granted ``rw`` rights,
anything else will be ``ro``.
Now if you set ``inverse_inheritance = true``, the ``@gp_ro`` grants will have
the highest priority, meaning the client ``demo`` on the ``test`` agent will be
granted ``ro`` rights like any other client.


Please also note the order of your rules matters (although the UI is unable to
re-order your rules).
For instance, this:

::

    [BASIC:ACL]
    user1 =
    @gp1 = '{"clients": {"rw": ["tata", "titi"]}}'
    +gp1 = user1
    @gp2 = '{"clients": {"ro": ["*"]}, "agents": {"rw": "local"}}'
    +gp2 = @gp1


Is not the same as:

::

    [BASIC:ACL]
    user1 =
    @gp2 = '{"clients": {"ro": ["*"]}, "agents": {"rw": "local"}}'
    +gp2 = @gp1
    @gp1 = '{"clients": {"rw": ["tata", "titi"]}}'
    +gp1 = user1


.. _Burp: http://burp.grke.org/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _burpui.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/share/burpui/etc/burpui.sample.cfg
.. _bui-agent: buiagent.html
