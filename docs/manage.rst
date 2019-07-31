Manage
======

Since *v0.3.0*, `Burp-UI`_ ships with a tool called ``bui-manage``. This tool
allows you to create new users and to manage database migrations.

This tool is actually a wrapper script that interacts with the core of
`Burp-UI`_. You can use it like this:

::

    bui-manage [wrapper options...] [--] <subcommand>


This page details the *subcommand* usage.
The tool provides some inline help too:

::

    bui-manage -h
    usage: bui-manage [-h] [-c <CONFIG>] [-i <MIGRATIONSDIR>]
                      [-m <agent|server|worker|manage>]
                      ...

    positional arguments:
      remaining

    optional arguments:
      -h, --help            show this help message and exit
      -c <CONFIG>, --config <CONFIG>
                            burp-ui configuration file
      -i <MIGRATIONSDIR>, --migrations <MIGRATIONSDIR>
                            migrations directory
      -m <agent|server|worker|manage>, --mode <agent|server|worker|manage>
                            application mode


::

    # note the -- used to separate the wrapper from the actual command
    bui-manage -- --help
    Usage: flask [OPTIONS] COMMAND [ARGS]...

      This shell command acts as general utility script for Flask applications.

      It loads the application configured (either through the FLASK_APP
      environment variable) and then provides commands either provided by the
      application or Flask itself.

      The most useful commands are the "run" and "shell" command.

      Example usage:

        $ export FLASK_APP=hello
        $ export FLASK_DEBUG=1
        $ flask run

    Options:
      --help  Show this message and exit.

    Commands:
      compile-translation  Compile translations.
      create-user          Create a new user.
      db                   Perform database migrations.
      diag                 Check Burp-UI is correctly setup.
      hash-password        Hash a given password to fill the...
      init-translation     Initialize a new translation for the given...
      legacy               Legacy server for backward compatibility.
      run                  Runs a local development server for the...
      setup-burp           Setup burp client for burp-ui.
      shell                Runs a shell in the app context.
      sysinfo              Returns a couple of system informations to...
      update-translation   Update translation files.
      websocket            Start a new websocket server.


Database
--------

To manage database migration, you first need to enable database support within
your configuration file (see `Production <advanced_usage.html#production>`__
section)

You will also need some extra requirements:

::

    pip install --upgrade "burp-ui[sql]"


Configure `Burp-UI`_ in order to enable SQL support by editing the ``database``
option of the ``[Production]`` section. Example:

::

    [Production]
    # ...
    # database url to store some persistent data
    # none or a connect string supported by SQLAlchemy:
    # http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls
    # example: sqlite:////var/lib/burpui/store.db
    database = sqlite:////var/lib/burpui/store.db


Then you just have to run the following command to have your database setup:

::

    bui-manage db upgrade


If your configuration is not in a *common* location, you can specify it like
this:

::

    bui-manage -c path/to/burpui.cfg db upgrade


If you did not install `Burp-UI`_ in a *common* location or you want to run it
without installing it directly through the sources, you may need to specify the
location of the *migrations* scripts like this:

::

    bui-manage -c path/to/burpui.cfg -i path/to/migrations db upgrade


Users
-----

You can create new users using the ``bui-manage`` file like this:

::

    bui-manage create-user <new_username>


By default, the script will create new users for the `Basic <advanced_usage.html#basic>`_
authentication backend.
Without further details, a new password will be generated.
You can either provide a password through the command line or tell the script to
ask you what to setup using either the ``-p`` or ``-a`` options.

Examples:

::

    bui-manage create-user user1
    [*] Adding 'user1' user...
    [+] Generated password: 71VIanuJ
    [+] Success: True

    bui-manage create-user -p toto user2
    [*] Adding 'user2' user...
    [+] Success: True

    bui-manage create-user -a user3     
    [*] Adding 'user3' user...
    Password: 
    Confirm: 
    [+] Success: True


Hashing passwords
-----------------

Since *v0.3.0*, the `BASIC <advanced_usage.html#basic>`_ authentication backend
supports hashed passwords.
Support for *legacy* plain-text passwords **will be removed in *v0.7.0***.

In order to automate user creation using external scripts, a new ``bui-manage``
subcommand has been introduced in  *v0.6.0*.

Usage:

::

	Usage: flask hash-password [OPTIONS]

	  Hash a given password to fill the configuration file.

	Options:
	  -p, --password TEXT  Password to assign to user.
	  -u, --username TEXT  Provide the username to get the full configuration
						   line.
	  -b, --batch          Don't be extra verbose so that you can use the output
						   directly in your scripts. Requires both -u and -p.
	  --help               Show this message and exit.



Examples:

::

	$ bui-manage hash-password --password demo --username demo --batch
	demo = pbkdf2:sha256:50000$w5jD2WT1$d89cd4da1b6c3c3f05173faaf3feea802eee7b5b9a378ae8987d5ac6676d166b

	$ bui-manage hash-password --password demo --username demo
	'demo' hashed into: pbkdf2:sha256:50000$feQoDIIp$d42e056b75092beda52736ce792c6518061b21d6e1b2c755fdd71a764184ebd9
	#8<-----------------------------------------------------------------------------
	demo = pbkdf2:sha256:50000$feQoDIIp$d42e056b75092beda52736ce792c6518061b21d6e1b2c755fdd71a764184ebd9
	#8<-----------------------------------------------------------------------------

	$ bui-manage hash-password -u demo
	Password:
	'********' hashed into: pbkdf2:sha256:50000$MNHOgtdr$22d64b17bb8135be3ad61249d649e89ed96a5d4878b23e4889be24dfc062c126
	#8<-----------------------------------------------------------------------------
	demo = pbkdf2:sha256:50000$MNHOgtdr$22d64b17bb8135be3ad61249d649e89ed96a5d4878b23e4889be24dfc062c126
	#8<-----------------------------------------------------------------------------

	$ bui-manage hash-password
	Password:
	'********' hashed into: pbkdf2:sha256:50000$eWzSCvSW$9df9cdf854461a5f927708475e0470ad648f8cd0613ca61f8cee639db165ab53


Configure
---------

Since *v0.4.0*, the ``bui-manage`` tool is now able to help you setup both
`Burp`_ and `Burp-UI`_ so they speak to each other.

The available options are:

::

    bui-manage setup-burp --help

    Usage: flask setup-burp [OPTIONS]

      Setup burp client for burp-ui.

    Options:
      -b, --burp-conf-cli TEXT        Burp client configuration file
      -s, --burp-conf-serv TEXT       Burp server configuration file
      -c, --client TEXT               Name of the burp client that will be used by
                                      Burp-UI (defaults to "bui")
      -h, --host TEXT                 Address of the status server (defaults to
                                      "::1")
      -r, --redis TEXT                Redis URL to connect to
      -d, --database TEXT             Database to connect to for persistent
                                      storage
      -p, --plugins TEXT              Plugins location
      -m, --monitor TEXT              bui-monitor configuration file
      -C, --concurrency INTEGER       Number of concurrent requests addressed to
                                      the monitor
      -P, --pool-size INTEGER         Number of burp-client processes to spawn in
                                      the monitor
      -B, --backend [burp2|parallel]  Switch to another backend
      -n, --dry                       Dry mode. Do not edit the files but display
                                      changes
      --help                          Show this message and exit.


The script needs the `Burp`_ configuration files to be readable **AND**
writable.

.. note::
    This script was initially developped to setup the docker image. I do not
    guarantee to be able to support it out of the docker context.


.. note::
    This script only supports Burp 2.0.x.


The docker image uses this script like this:

::

    bui-manage -c $BURPUI_CONFIG setup-burp -b $BURP_CLIENT_CONFIG \
        -s $BURP_SERVER_CONFIG -h $BURP_SERVER_ADDR -c $BURPUI_CLIENT_NAME \
        -r $REDIS_SERVER -d $DATABASE_URL


WebSocket
---------

.. note::
    This tool first appeared with `Burp-UI`_ *v0.6.0*.

Launch a dedicated websocket server so you can have more than one worker.
You may need a dedicated reverse-proxy though.

Example:

::

	bui-manage websocket --help
	Usage: flask websocket [OPTIONS]

	  Start a new websocket server.

	Options:
	  -b, --bind TEXT     Which address to bind to for the websocket server
	  -p, --port INTEGER  Which port to listen on for the websocket server
	  -d, --debug         Whether to start the websocket server in debug mode
	  --help              Show this message and exit.


Sysinfo
-------

.. note::
    This tool first appeared with `Burp-UI`_ *v0.5.0*.

This tool will help you to gather system informations in order to make a
detailed bug report.

Example:

::

    bui-manage sysinfo

    Python version:      3.6.5
    Burp-UI version:     0.6.1 (stable)
    OS:                  Linux:4.16.0-1-amd64 (posix)
    Distribution:        debian buster/sid
    Single mode:         True
    Backend version:     2
    WebSocket embedded:  False
    WebSocket available: True
    Config file:         share/burpui/etc/burpui.sample.cfg


You can also add the ``-v`` flag while running ``sysinfo`` but please **MAKE
SURE NO SENSITIVE DATA GET EXPOSED**.

Example:

::

    bui-manage sysinfo -v

    Python version:      3.6.5
    Burp-UI version:     0.6.1 (stable)
    OS:                  Linux:4.16.0-1-amd64 (posix)
    Distribution:        debian buster/sid
    Single mode:         True
    Backend version:     2
    WebSocket embedded:  False
    WebSocket available: True
    Config file:         share/burpui/etc/burpui.sample.cfg
    >>>>> Extra verbose informations:
    !!! PLEASE MAKE SURE NO SENSITIVE DATA GET EXPOSED !!!

        8<-------------------------------------------------------------BEGIN[Global]
        version = 2
        single = true
        auth = basic
        acl = basic
        prefix = none
        plugins = none
        8<---------------------------------------------------------------END[Global]

        8<---------------------------------------------------------BEGIN[Production]
        storage = default
        session = default
        cache = default
        redis = localhost:6379
        celery = false
        database = none
        limiter = false
        ratio = 60/minute
        8<-----------------------------------------------------------END[Production]

        8<---------------------------------------------------------------BEGIN[Burp]
        bconfcli = /etc/burp/burp.conf
        stripbin = /usr/bin/vss_strip
        bconfsrv = /etc/burp/burp-server.conf
        tmpdir = /tmp/bui/
        8<-----------------------------------------------------------------END[Burp]

        8<----------------------------------------------------------BEGIN[WebSocket]
        enabled = true
        embedded = false
        url = document.domain + ':5001'
        debug = true
        8<------------------------------------------------------------END[WebSocket]


Diag
----

.. note::
    This tool first appeard with `Burp-UI`_ *v0.5.0*.

This tool will help you detect misconfiguration. It will **not** modify your
files, you will have to use the `Configure <#configure>`_ tool for that.

The available options are:

::

    bui-manage diag --help

    Usage: flask diag [OPTIONS]

      Check Burp-UI is correctly setup

    Options:
      -c, --client TEXT  Name of the burp client that will be used by Burp-UI
                         (defaults to "bui")
      -h, --host TEXT    Address of the status server (defaults to "::1")
      -t, --tips         Show you some tips
      --help             Show this message and exit.


Examples:

::

    bui-manage diag

    The cname of your burp client does not match: hydrogen != bui
    The burp server address does not match: 127.0.0.1 != ::1
    'max_status_children' is to low, you need to set it to 15 or more. Please edit your /etc/burp/burp-server.conf file
    Your burp client is not listed as a 'restore_client'. You won't be able to view other clients stats!
    For performance reasons, it is recommanded to enable the 'monitor_browse_cache'
    Unable to find the /etc/burp/clientconfdir/bui file
    Some errors have been found in your configuration. Please make sure you ran this command with the right flags! (see --help for details)

    bui-manage diag -c hydrogen -h 127.0.0.1 -t

    'max_status_children' is to low, you need to set it to 15 or more. Please edit your /etc/burp/burp-server.conf file
    Your burp client is not listed as a 'restore_client'. You won't be able to view other clients stats!
    For performance reasons, it is recommanded to enable the 'monitor_browse_cache'
    Well, if you are sure about your settings, you can run the following command to help you setup your Burp-UI agent. (Note, the '--dry' flag is here to show you the modifications that will be applied. Once you are OK with those, you can re-run the command without the '--dry' flag):
        > bui-manage setup_burp --host="127.0.0.1" --client="hydrogen" --dry


When your configuration is OK, you should see this message:

::

    Congratulations! It seems everything is alright. Burp-UI should run without any issue now.

.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Burp: http://burp.grke.org/
