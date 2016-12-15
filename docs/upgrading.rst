Upgrading
=========

This page is here to help you upgrading from previous versions of `Burp-UI`_ to
the latest version.
Each section presents major/breaking changes, new requirements and new options.
For a complete list of changes, you may refer to the
`CHANGELOG <changelog.html>`_ page.

v0.4.0
------

- **Breaking** - Due to the use of the new Flask's embedded server, it is no
  longer possible to serve the application over SSL (HTTPS) anymore from within
  the Flask's server. You'll need to use a dedicated application server for this
  purpose such as `gunicorn <gunicorn.html>`_ or a reverse-proxy.

  Or you can use the ``python -m burpui -m legacy [--help]`` command that
  **SHOULD** be backward compatible (but note that no further support will be
  provided since it is not the Flask's default behavior anymore).
- **Breaking** - The database schema evolved between v0.3.0 and v0.4.0. In order
  to apply these modifications, you **MUST** run the ``bui-manage db upgrade``
  command before restarting your `Burp-UI`_ application (if you are using
  celery, you must restart it too).

  More details on the `Manage <manage.html>`__ and `Celery <celery.html>`__
  pages.
- **Breaking** - Plain text passwords are deprecated since v0.3.0 and are now
  disabled by default. It means you should not manually add new users in your
  burp-ui configuration anymore with ``login = password`` but you should now use
  the `bui-manage <manage.html>`__ command instead.
- **Breaking** - The default *version* setting has been set to ``2`` instead of
  ``1`` since burp-2.0.52 is now the stable release.
- **New** - The ``bui-manage`` tool can now help you setup both `Burp`_ and
  `Burp-UI`_.
- **New** - The SQL requirements have evolved, you **MUST** run
  ``pip install --upgrade "burp-ui[sql]"`` if you wish to keep using persistent
  storage.


v0.3.0
------

- **New** - ``bui-manage`` tool: This tool is used to setup database (see
  `Manage <manage.html>`__).
- **New** - ``bui-celery`` tool: This tool is used to run a celery runner (see
  `Celery <celery.html>`__).
- **Breaking** -  Configuration file format changed. Colons (:) must be replaced
  by equals (=). Besides, some settings containing spaces should be surrounded
  by quotes. *Note*: The conversion is mostly automatic, but you should keep an
  eye on it though.
- **New** - Basic authentication backend now supports hashed passwords (*Note*:
  plain text passwords are now deprecated and the support will be dropped in
  v0.4.0). You can create new users with the ``bui-manage`` tool, passwords
  generated through this tool are hashed. *Note*: Starting with v0.4.0, plain
  text passwords will be automatically hashed.
- **New** - Local authentication backend allows you to login using local
  accounts through pam.


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Burp: http://burp.grke.org/
