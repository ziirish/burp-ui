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
                  [-m <agent|server>]

   optional arguments:
     -h, --help            show this help message and exit
     -v, --verbose         increase output verbosity (e.g., -vv is more than -v)
     -d, --debug           alias for -v
     -V, --version         print version and exit
     -c <CONFIG>, --config <CONFIG>
                           configuration file
     -l <FILE>, --logfile <FILE>
                           output logs in defined file
     -m <agent|server>, --mode <agent|server>
                           application mode (server or agent)


.. _Flask: http://flask.pocoo.org/
.. _burpui.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/share/burpui/etc/burpui.sample.cfg
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Burp: http://burp.grke.net/
