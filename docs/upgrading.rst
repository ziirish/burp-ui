Upgrading
=========

This page is here to help you upgrading from previous versions of `Burp-UI`_ to
the latest version.
Each section presents major/breaking changes, new requirements and new options.
For a complete list of changes, you may refer to the
`CHANGELOG <changelog.html>`_ page.

v0.3.0
------

- **New** - ``bui-manage`` tool: This tool is used to setup database (see
  `Manage <manage.html>`_)
- **New** - ``bui-celery`` tool: This tool is used to run a celery runner (see
  `Celery <celery.html>`_)
- **Breaking** -  Configuration file format changed. Colons (:) must be replaced
  by equals (=). Besides, some settings containing spaces should be surrounded
  by quotes
- **New** - Basic authentication backend now support hashed passwords (*Note*:
  plain text passwords are now deprecated and the support will be dropped in
  v0.4.0). You can create new users with the ``bui-manage`` tool, passwords
  generated through this tool are hashed.
- **New** - Local authentication backend allows you to login using local
  accounts through pam


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
