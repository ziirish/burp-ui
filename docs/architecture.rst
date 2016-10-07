Architecture
============

This section is a must-read in order to understand what is going on between
`Burp`_ and `Burp-UI`_.

Both projects are lead by two different people so please report your issues to
the right project.


The *Burp1* and *Burp2* backends behave slightly differently due to some changes
in the core or `Burp`_. You can refer to the `Burp`_'s `documentation
<http://burp.grke.org/docs/monitor.html>`_ for details.

Burp 1.x
--------

If you are running `Burp`_ 1.x, you **MUST** install `Burp-UI`_ on the same host
(or at least setup a `bui-agent <buiagent.html>`__ locally).
This limitation is due to the fact burp 1.x only exposes its *status port* (the
port 4972 by default) to localhost (either 127.0.0.1 or ::1).
`Burp-UI`_ then just opens a connexion to ``localhost:4972`` in order to
communicate with `Burp`_.


Here is a little illustration:

::

    +--------------------------------------------+
    |                                            |
    |               Backup server                |
    |                                            |
    +--------------------------------------------+
    |                                            |
    |                                            |
    |                                            |
    |                                            |
    |                                            |
    |                                            |
    |                                            |
    |                                            |
    | +-----------+              +------------+  |
    | |  Burp-UI  |              |    Burp    |  |
    | +-----------+              +------------+  |
    | |           |              |            |  |
    | |           |    :4972     |            |  |
    | |           +-------------->            |  |
    | |           |              |            |  |
    | |           |              |            |  |
    | +-----------+              +------------+  |
    |                                            |
    +--------------------------------------------+


Burp 2.x
--------

If you are running `Burp`_ 2.x, you can host `Burp-UI`_ on a different server,
but I don't recommend it if you wish to be able to use all the features.

The `Burp`_ 2.x *status port* has been completely reworked. It can now be
published to remote hosts, but the *status protocol* is not compatible with 1.x.

The *status port* is now accessed through a `Burp`_ client thanks to the
``-a m`` flag. The client will then take care to open the connexion with the
server securing the communication with SSL. The `Burp`_ server also supports
basic *ACL* though the ``restore_client`` option.

By default, a client will only be able to view its own reports/stats. If you
want to be able to monitor other clients, you need to be added as a
``restore_client`` for those clients (this can be done by editing the client
configuration file in the *clientconfdir* directory on the server).
Alternatively, you can add this option in the *burp-server.conf* file for this
setting to be applied globally for all the clients.


Ok, now why did I tell you all this? Well, because the `Burp-UI`_'s backend for
`Burp`_ 2.x is basically just a wrapper around ``burp -a m``.

It means that when you start `Burp-UI`_ with ``version = 2``, the command
``<burpbin> -c <bconfcli> -a m`` (where *<burpbin>* defaults to */usr/sbin/burp*
and *<bconfcli>* defaults to */etc/burp/burpui.cfg*).
Of course this command will be ran with the same permissions and privileges as
`Burp-UI`_ itself.


And here is a little illustration to summarize all this:

::

    +------------------------------------------------+
    |                                                |
    |                 Backup server                  |
    |                                                |
    +------------------------------------------------+
    |                                                |
    | +--------------------------------------------+ |
    | |                   Burp-UI                  | |
    | +--------------------------------------------+ |
    | |                                            | |
    | |                                            | |
    | |          +----------------------+          | |
    | |          |      burp -a m       |          | |
    | |          +----------+-----------+          | |
    | |                     |                      | |
    | +--------------------------------------------+ |
    |                       |                        |
    | +---------------------v----------------------+ |
    | |                                            | |
    | |                   Burp                     | |
    | |                                            | |
    | +--------------------------------------------+ |
    |                                                |
    +------------------------------------------------+


.. _Burp: http://burp.grke.org/
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
