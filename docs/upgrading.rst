Upgrading
=========

This page is here to help you upgrading from previous versions of `Burp-UI`_ to
the latest version.
Each section presents major/breaking changes, new requirements and new options.
For a complete list of changes, you may refer to the
`CHANGELOG <changelog.html>`_ page.

v0.4.0
------

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
  ``1`` since burp-2.0.52 should become the stable release by the end of the
  year.
- **New** - The ``bui-manage`` tool can now help you setup both `Burp`_ and
  `Burp-UI`_.


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
