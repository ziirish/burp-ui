FAQ
===

How to start using Burp-UI?
---------------------------

You may find all the basic informations to get started with `Burp-UI`_ in the
`README`_ file.

How to configure my *firewall*?
-------------------------------

When running `Burp-UI`_ in standalone `mode <usage.html#versions>`__, the
embedded webserver listens on port **5000** on all interfaces.

The `Burp-UI`_ agents listens on port **10000** by default.

What are the default credentials?
---------------------------------

The default login / password is *admin* / *admin* with the
`basic <usage.html#basic>`__ authentication backend.

How does the online restoration feature works?
----------------------------------------------

The online restoration feature works the same way as if you were running the
burp client yourself.
It means `Burp-UI`_ runs the following command:

::

    burp -a r -b <number> -C <client name> -r <regex> -d /tmp/XXX -c <bconfcli>


It then generates an archive based on the restored files.

Because of this workflow, and especially the use of the *-C* flag you need to
tell your burp-server the client used by `Burp-UI`_ can perform a restoration
for a different client.
You can refer to the `restoration <installation.html#restoration>`__ section of
this documentation along with the `version <usage.html#version>`__ section for
more details.

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

There is a `known issue <contributing.html#known-issues>`__ section in this
documentation.

How can I contribute?
---------------------

You can refer to the `contributing <contributing.html>`__ section of this
documentation.




.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Gunicorn: http://gunicorn.org/
.. _README: https://git.ziirish.me/ziirish/burp-ui/blob/master/README.rst
