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
      compile_translation  Compile translations.
      create_user          Create a new user.
      db                   Perform database migrations.
      init_translation     Initialize a new translation for the given...
      run                  Runs a development server.
      setup_burp           Setup burp client for burp-ui.
      shell                Runs a shell in the app context.
      update_translation   Update translation files.


Database
--------

To manage database migration, you first need to enable database support within
your configuration file (see `Production <usage.html#production>`__ section)

You will also need some extra requirements:

::

    pip install "burp-ui[sql]"


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

    bui-manage create_user <new_username>


By default, the script will create new users for the `Basic <usage.html#basic>`_
authentication backend.
Without further details, a new password will be generated.
You can either provide a password through the command line or tell the script to
ask you what to setup using either the ``-p`` or ``-a`` options.

Examples:

::

    bui-manage create_user user1
    [*] Adding 'user1' user...
    [+] Generated password: 71VIanuJ
    [+] Success: True

    bui-manage create_user -p toto user2
    [*] Adding 'user2' user...
    [+] Success: True

    bui-manage create_user -a user3     
    [*] Adding 'user3' user...
    Password: 
    Confirm: 
    [+] Success: True


Configure
---------

Since *v0.4.0*, the ``bui-manage`` tool is now able to help you setup both
`Burp`_ and `Burp-UI`_ so they speak to each other.

The available options are:

::

    bui-manage setup_burp --help
    Usage: flask setup_burp [OPTIONS]

      Setup burp client for burp-ui.

    Options:
      -b, --burp-conf-cli TEXT   Burp client configuration file
      -s, --burp-conf-serv TEXT  Burp server configuration file
      -c, --client TEXT          Name of the burp client that will be used by
                                 Burp-UI (defaults to "bui")
      -h, --host TEXT            Address of the status server (defaults to "::1")
      -r, --redis TEXT           Redis URL to connect to
      -d, --database TEXT        Database to connect to for persistent storage
      -n, --dry                  Dry mode. Do not edit the files but display
                                 changes
      --help                     Show this message and exit.


The script needs the `Burp`_ configuration files to be readable **AND**
writable.

.. note::
    This script was initially developped to setup the docker image. I do not
    guarantee to be able to support it out of the docker context.


.. note::
    This script only supports Burp 2.0.x.


The docker image uses this script like this:

::

    bui-manage -c $BURPUI_CONFIG setup_burp -b $BURP_CLIENT_CONFIG \
        -s $BURP_SERVER_CONFIG -h $BURP_SERVER_ADDR -c $BURPUI_CLIENT_NAME \
        -r $REDIS_SERVER -d $DATABASE_URL


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Burp: http://burp.grke.org/
