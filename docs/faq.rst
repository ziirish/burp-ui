FAQ
===

Is there a demo somewhere?
--------------------------

Yes, you can play with `Burp-UI`_ at `demo.ziirish.me`_. Credentials are:

- *admin* / *admin* to play with `Burp-UI`_ as an administrator
- *demo* / *demo* to play with `Burp-UI`_ as a regular user

How to start using Burp-UI?
---------------------------

You may find all the basic informations to get started with `Burp-UI`_ in the
`README`_ file. You can also read the `step-by-step <step-by-step.html>`_ page
to get started.

How does Burp-UI work?
----------------------

The answer depends whether you are using burp 1.x or burp 2.x. Basically,
`Burp-UI`_ tries to provide a consistent API between the *Frontend* (the UI) and
the burp server. To do so, it implements two *Backends*: burp-1 and burp-2.
You can select either of these with the `version <usage.html#versions>`__ flag
in your configuration.

You can also refer to the `Architecture <architecture.html>`__ page of the
documentation to know more about those backends.

How to configure my *firewall*?
-------------------------------

When running `Burp-UI`_ in standalone `mode <usage.html#versions>`__, the
embedded webserver listens on port **5000** on all interfaces.

The `Burp-UI`_ agents listen on port **10000** by default.

Of course those are configurable.

What are the default credentials?
---------------------------------

The default login / password is *admin* / *admin* with the
`basic <usage.html#basic>`__ authentication backend.

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
this documentation along with the `version <usage.html#versions>`__ section for
more details.

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

Burp-UI does not work anymore since I upgraded it, what can I do?
-----------------------------------------------------------------

Make sure you read the `upgrading <upgrading.html>`_ page in case some breaking
changes occurred.

How can I contribute?
---------------------

You can refer to the `contributing <contributing.html>`__ section of this
documentation.




.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Gunicorn: http://gunicorn.org/
.. _README: https://git.ziirish.me/ziirish/burp-ui/blob/master/README.rst
.. _demo.ziirish.me: https://demo.ziirish.me/
