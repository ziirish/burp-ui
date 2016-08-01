Manage
======

Since *v0.3.0*, `Burp-UI`_ ships with a tool called ``bui-manage``. This tool
allows you to create new users and to manage database migrations.

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

    bui-manage -c path/to/burpui.cfg -- db upgrade


If you did not install `Burp-UI`_ in a *common* location or you want to run it
without installing it directly through the sources, you may need to specify the
location of the *migrations* scripts like this:

::

    bui-manage -c path/to/burpui.cfg -i path/to/migrations -- db upgrade


.. note:: Double-dash (--) are important because ``bui-manage`` is a wrapper
          script

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


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
