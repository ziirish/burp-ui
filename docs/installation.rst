Installation
============

`Burp-UI`_ is written in Python with the `Flask`_ micro-framework.
The easiest way to install `Burp-UI`_ is to use ``pip``.

On Debian, you can install ``pip`` with the following command:

::

    aptitude install python-pip


Once ``pip`` is installed, you can install ``Burp-UI`` this way:

::

    pip install burp-ui


You can setup various parameters in the `burpui.cfg`_ file.
This file can be specified with the ``-c`` flag or should be present in
``/etc/burp/burpui.cfg``.
By default `Burp-UI`_ ships with a sample file located in
``$INSTALLDIR/share/burpui/etc/burpui.sample.cfg``.
(*$INSTALLDIR* defaults to */usr/local* when using pip **outside** a
virtualenv)

.. note::
    It is advised to copy the sample configuration in ``/etc/burp/burpui.cfg``
    and to edit this file so that it is not overwritten on every upgrade.

Then you can run ``burp-ui``: ``burp-ui``

By default, ``burp-ui`` listens on all interfaces (including IPv6) on port 5000.

You can then point your browser to http://127.0.0.1:5000/

Upgrade
-------

In order to upgrade `Burp-UI`_ to the latest stable version, you can run the
following command:

::

   pip install --upgrade burp-ui


.. note::
    If you encounter any issue after upgrading to the latest stable release,
    make sure you read the `upgrading <upgrading.html>`__ page.

Debian Wheezy
-------------

The version of ``pip`` available on *Debian Wheezy* does not support all the
features needed to build and install the latest `Burp-UI`_ version.

Instead, you may want to run the following command either to install it from
scratch or to upgrade your current version to the latest one:

::

    easy_install --upgrade burp-ui


General Instructions
--------------------

Restoration
^^^^^^^^^^^

`Burp-UI`_ tries to be as less intrusive as possible with `Burp`_ internals.
In order to make the *online* restoration/download functionality work, you
need to check a few things:

1. Provide the full path of the burp (client) binary file (field *burpbin* in 
   `burp-ui configuration <usage.html#versions>`__)
2. Provide a burp-client configuration file (field *bconfcli* in
   `burp-ui configuration <usage.html#versions>`__)
3. Provide the full path of an empty directory where a temporary restoration
   will be made. This involves you have enough space left on that location on
   the server that runs `Burp-UI`_
4. Launch `Burp-UI`_ with a user that can proceed restorations and that can
   write in the directory mentioned above
5. Make sure the client provided in 2. can restore files of other clients
   (option *restore_client* in burp-server configuration).
   The *restore_client* is the *cname* you provided in your client configuration
   file (see 2.)

Burp 2
^^^^^^

When using the `burp2 backend <usage.html#burp2>`_, `Burp-UI`_ can be executed
on any machine as long as you can access the burp status port, but you will not
be able to edit the burp server configuration file within the *settings* view of
`Burp-UI`_.
You also need to configure a *restore_client* on your burp server corresponding
to the client you will use through `Burp-UI`_


Options
-------

::

    usage: burp-ui [-h] [-v] [-d] [-V] [-c <CONFIG>] [-l <FILE>]
                   [-i <MIGRATIONSDIR>]
                   ...

    positional arguments:
      remaining

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         increase output verbosity (e.g., -vv is more verbose
                            than -v)
      -d, --debug           enable debug mode
      -V, --version         print version and exit
      -c <CONFIG>, --config <CONFIG>
                            burp-ui configuration file
      -l <FILE>, --logfile <FILE>
                            output logs in defined file
      -i <MIGRATIONSDIR>, --migrations <MIGRATIONSDIR>
                            migrations directory


Developer options
-----------------

Since v0.4.0, `Burp-UI`_ uses the new Flask's *CLI* module. This change brings
new options to help you debug your development environment:

::

    Usage: flask run [OPTIONS]

      Runs a local development server for the Flask application.

      This local server is recommended for development purposes only but it can
      also be used for simple intranet deployments.  By default it will not
      support any sort of concurrency at all to simplify debugging.  This can be
      changed with the --with-threads option which will enable basic
      multithreading.

      The reloader and debugger are by default enabled if the debug flag of
      Flask is enabled and disabled otherwise.

    Options:
      -h, --host TEXT                 The interface to bind to.
      -p, --port INTEGER              The port to bind to.
      --reload / --no-reload          Enable or disable the reloader.  By default
                                      the reloader is active if debug is enabled.
      --debugger / --no-debugger      Enable or disable the debugger.  By default
                                      the debugger is active if debug is enabled.
      --eager-loading / --lazy-loader
                                      Enable or disable eager loading.  By default
                                      eager loading is enabled if the reloader is
                                      disabled.
      --with-threads / --without-threads
                                      Enable or disable multithreading.
      --help                          Show this message and exit.


Some options are redundant with `Burp-UI`_'s one.

Example
-------

By default, the standalone server listens on *127.0.0.1* on port *5000*, if you
wish to change this, you would run something like:

::

    burp-ui -h 0.0.0.0 -p 8080


.. _Flask: http://flask.pocoo.org/
.. _burpui.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/share/burpui/etc/burpui.sample.cfg
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Burp: http://burp.grke.net/
