FAQ
===

Is there a demo somewhere?
--------------------------

Yes, you can play with `Burp-UI`_ at `demo.burp-ui.org`_. Credentials are:

- *admin* / *admin* to play with `Burp-UI`_ as an administrator
- *demo* / *demo* to play with `Burp-UI`_ as a regular user

How to start using Burp-UI?
---------------------------

You may find all the basic informations to get started with `Burp-UI`_ in the
`README`_ file and in this documentation. You can also read the
`step-by-step <step-by-step.html>`_ page for some detailed use-cases.

How does Burp-UI work?
----------------------

The answer depends whether you are using burp 1.x or burp 2.x. Basically,
`Burp-UI`_ tries to provide a consistent API between the *Frontend* (the UI) and
the burp server. To do so, it implements two *Backends*: burp-1 and burp-2.
You can select either of these with the `version <advanced_usage.html#versions>`__
flag in your configuration.

You can also refer to the `Architecture <architecture.html>`__ page of the
documentation to know more about those backends.

How to configure my *firewall*?
-------------------------------

When running `Burp-UI`_ in single `mode <advanced_usage.html#versions>`__, the
embedded webserver listens on port **5000** on all interfaces.

The `Burp-UI`_ agents listen on port **10000** by default.

Of course those are configurable.

What are the default credentials?
---------------------------------

The default login / password is *admin* / *admin* with the
`basic <advanced_usage.html#basic>`__ authentication backend.

How does the online restoration feature work?
---------------------------------------------

The online restoration feature works the same way as if you were running the
burp client yourself.
It means `Burp-UI`_ runs the following command:

::

    burp -a r -b <number> -C <client name> -r <regex> -d /tmp/XXX -c <bconfcli>


It then generates an archive based on the restored files.

Because of this workflow, and especially the use of the ``-C`` flag you need to
tell your burp-server the client used by `Burp-UI`_ can perform a restoration
for a different client.
You can refer to the `restoration <installation.html#restoration>`__ section of
this documentation along with the `version <advanced_usage.html#versions>`__
section for more details.

What does the server-initiated restoration feature do and how to make it work?
------------------------------------------------------------------------------

This feature asks the server to perform a restoration on the client the next
time it sees it.

In order for this feature to work, your client **MUST** allows the server to do
that. You have to set ``server_can_restore = 1`` (which is the default value) in
your client configuration file (usually */etc/burp/burp.conf*).

How can I start Burp-UI as a daemon?
------------------------------------

There are several *init scripts* provided by some users available
`here <https://git.ziirish.me/ziirish/burp-ui/tree/master/contrib>`__.

.. note:: I do not (and cannot) support these scripts. Only the `Gunicorn`_ way
          is supported.

The recommended way to run `Burp-UI`_ in production is to use `Gunicorn`_. You
can refer to the `gunicorn <gunicorn.html#daemon>`__ section of this
documentation for more details.

How to setup a reverse-proxy in front of Burp-UI?
-------------------------------------------------

The only way to run `Burp-UI`_ behind a reverse-proxy is to use `Gunicorn`_.
You can refer to the `gunicorn <gunicorn.html#reverse-proxy>`__ section of this
documentation for more details.

Why don't I see all my clients using the burp-2 backend?
--------------------------------------------------------

Starting with burp 2, you cannot see all the client through the status port
unless you tell burp a particular client can see other clients statistics.
See the `general instructions <installation.html#burp-2>`_ for more details.

Are there any known issues?
---------------------------

There is a `known issue <introduction.html#known-issues>`__ section in this
documentation.

I cannot find the ``bui-agent`` command anymore, where is it?
-------------------------------------------------------------

Since *v0.5.0*, the `bui-agent <buiagent.html>`_ has it's own package in order
to reduce requirements. The agent does not need the Flask requirements and so
on. You can now install it with the ``pip install burp-ui-agent`` command.
Alternatively, there is now a ``bui-agent-legacy`` provided by the ``burp-ui``
package.

See the `upgrading <upgrading.html#v0-5-0>`__ section for more details.

Why using redis?
----------------

Redis may be used for several things:

- store the sessions server side (by default sessions are stored client side in
  a secure cookie)
- cache some data
- monitor API usage for the rate limiter

All of these features are totally optional.
Redis is also used by celery to interact between Burp-UI and the asynchronous
worker.

Why using SQL?
--------------

The SQL database is currently used to keep a track of several meta-data.
Since *v0.5.0*, the SQL database is able to store user preferences.
Again, it is totally optional to use it.

Why using Celery?
-----------------

Celery is used to run some asynchronous jobs such as reports computations or
online restorations.

Computing reports asynchronously allows faster answer especially when you manage
several dozens of clients.

Burp-UI does not seem to understand the *bind* and *port* options anymore, what should I do?
--------------------------------------------------------------------------------------------

Since *v0.4.0*, the new Flask development server is used when running in
*single* mode. The *bind* and *port* options are not read anymore.
You can either run `Burp-UI`_ with the ``-- -h x.x.x.x -p yyyy`` flags or use
the legacy launcher ``python -m burpui -m legacy [--help]``.
See the `upgrading <upgrading.html#v0-4-0>`__ page for details.

Burp-UI does not work anymore since I upgraded it, what can I do?
-----------------------------------------------------------------

Make sure you read the `upgrading <upgrading.html>`__ page in case some breaking
changes occurred.

I am getting errors while restoring large files (>3GB), what should I do?
-------------------------------------------------------------------------

The default *zip* module does not support large files by default. You can either
enable large file support by setting ``zip64 = true`` in the ``[Experimental]``
section.
Alternatively, you can choose an other compression module by selecting an other
extension while proceeding the restoration.

I see a lot of *cannot spawn burp process* errors, what can I do?
-----------------------------------------------------------------

This error means `Burp-UI`_ is not able to communicate with the burp server.
You should check your logs (both `Burp-UI`_'s and burp server's) to understand
what is wrong.
If you are using `Gunicorn`_, it is possible you reached the limit of *status
children*. You can safely increase the ``max_status_children`` setting in your
*burp-server.conf* file to 15 (the default is 5).
You can also check your *status port* is open and/or accessible by your client.
To do so, you can run the ``burp -a m`` command.

How can I contribute?
---------------------

You can refer to the `contributing <contributing.html>`__ section of this
documentation.




.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Gunicorn: http://gunicorn.org/
.. _README: https://git.ziirish.me/ziirish/burp-ui/blob/master/README.rst
.. _demo.burp-ui.org: https://demo.burp-ui.org/
