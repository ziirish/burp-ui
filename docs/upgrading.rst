.. role:: strike
    :class: strike

Upgrading
=========

This page is here to help you upgrading from previous versions of `Burp-UI`_ to
the latest version.
Each section presents major/breaking changes, new requirements and new options.
For a complete list of changes, you may refer to the
`CHANGELOG <changelog.html>`_ page.

v0.7.0
------

- **Breaking** - you now need python 3.6 or above. `Burp-UI`_ won't work on
  python 2.7 anymore.

- **Breaking** - the *single* and *version* options within the ``[Global]``
  section have been removed in favor of a new unified *backend* option. See the
  `Backends <advanced_usage.html#backends>`__ section of the documentation for
  details.

- **Breaking** - there was a bug when using burp-server >= 2.1.10 where
  timestamps where wrongly computed on the global clients view due to the fact
  timestamps have offsets since burp-server 2.1.10. The new behaviour is to
  suppose every timestamp have offset whenever we detect your current
  burp-server version is >= 2.1.10. If backups were made with an older
  burp-server, the timestamps will be wrong. You can avoid that by enabling
  the ``deep_inspection`` option in the ``[Burp]`` section (see the
  `Backend options <advanced_usage.html#options>`__ for details).
  The drawback of enabling the ``deep_inspection`` is this requires some extra
  work that may slow down burp-ui.

- **Breaking** - the authentication backends section have been renamed with the
  ``:AUTH`` suffix (so ``BASIC`` becomes ``BASIC:AUTH``, etc.).
  Please make sure you rename those sections accordingly so you won't be locked
  out.

- **Breaking** - the ``bui-agent`` will now exit when its *system* requirements
  are not met at startup time (that is: the burp-server must be up and running
  and the burp-client used by burp-ui must be able to reach the burp-server).
  A new timeout has been added though in order for ``bui-agent`` to wait for the
  burp-server to be ready.

- **Breaking** - the ``prefix`` option has been moved from the ``[Global]``
  configuration section to the ``[Production]`` one for consistency with the new
  *Production* options introduced.

v0.6.0
------

- **Breaking** - The *BASIC* ``ACL`` engine will now grant users on all agents
  if they are not explicitly defined. It means that if you have a user called
  ``example1`` with two agents (burp servers in multi-agent mode) on which you
  have respectively two clients called ``example1``, the user ``example1`` will
  be granted on both clients on the two agents. You can disable this behavior
  with the ``legacy`` option. See the
  `BASIC ACL <advanced_usage.html#basic-acl>`__ documentation for details.

- **Breaking** - A new ``[ACL]`` section has been created in order to control
  the new ACL engine behavior. See the `ACL <advanced_usage.html#acl>`__
  documentation for details.

- **Breaking** - The *Burp1* and *Burp2* configuration sections have been merged
  into one single *Burp* section. See the
  `Versions <advanced_usage.html#versions>`__ documentation for details.

- **Breaking** - The *running* backups are now displayed in ``green`` instead of
  ``blue``.

- **Breaking** - The docker postgresql image was upgraded from 9.6 to 10.1,
  you'll have to manually upgrade/migrate your data `following this
  documentation <https://github.com/tianon/docker-postgres-upgrade>`_.

- **Breaking** - The ``docker-compose.yml`` file now uses the ``version: '2'``
  format.

- **Breaking** - The old config file format with colons (:) as separator is no
  more supported.

- **New** - Plugin system to enhance ACL and Authentication backends. See the
  `Plugins <plugins.html>`__ documentation for details.

- **New** - WebSocket support for better/smarter notifications.

- **New** - Client configuration templates.

- **New** - Administration panel to manage both Authentications and
  Authorizations.

v0.5.0
------

- **Breaking** - The *standalone* option has been renamed to *single* to avoid
  confusion.

- **Breaking** - The ``bui-agent`` has now its own independent package to reduce
  dependencies, you can install it with the ``pip install burp-ui-agent``
  command. Alternatively, there is now a ``bui-agent-legacy`` command provided
  by the ``burp-ui`` package.

- **Breaking** - The database schema evolved between *v0.4.0* and *v0.5.0*. In
  order to apply these modifications, you **MUST** run the
  ``bui-manage db upgrade`` command before restarting your `Burp-UI`_
  application (if you are using celery, you must restart it too).

- **New** - The `bui-manage <manage.html>`__ tool brings two new commands:

  - ``diag`` whose documentation is available `here <manage.html#diag>`__
  - ``sysinfo`` whose documentation is available `here <manage.html#sysinfo>`__

  More details on the `Manage <manage.html>`__ and `Celery <celery.html>`__
  pages.


v0.4.0
------

- **Breaking** - Due to the use of the new Flask's embedded server, it is no
  longer possible to serve the application over SSL (HTTPS) anymore from within
  the Flask's server. You'll need to use a dedicated application server for this
  purpose such as `gunicorn <gunicorn.html>`_ or a reverse-proxy.
  The *bind* and *port* option have also been removed due to the same reason.

  Or you can use the ``python -m burpui -m legacy [--help]`` command that
  **SHOULD** be backward compatible (but note that no further support will be
  provided since it is not the Flask's default behavior anymore).

- **Breaking** - The database schema evolved between *v0.3.0* and *v0.4.0*. In
  order to apply these modifications, you **MUST** run the
  ``bui-manage db upgrade`` command before restarting your `Burp-UI`_
  application (if you are using celery, you must restart it too).

  More details on the `Manage <manage.html>`__ and `Celery <celery.html>`__
  pages.

- **Breaking** - Plain text passwords are deprecated since *v0.3.0* and are now
  disabled by default. It means you should not manually add new users in your
  burp-ui configuration anymore with ``login = password`` but you should now use
  the `bui-manage <manage.html>`__ command instead.

- **Breaking** - The default *version* setting has been set to ``2`` instead of
  ``1`` since burp-2.0.54 is now the stable release.

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
  by quotes. :strike:`*Note*: The conversion is mostly automatic, but you should
  keep an eye on it though.`

- **New** - Basic authentication backend now supports hashed passwords (*Note*:
  plain text passwords are now deprecated and the support will be dropped in
  *v0.4.0*). You can create new users with the ``bui-manage`` tool, passwords
  generated through this tool are hashed. *Note*: Starting with *v0.4.0*, plain
  text passwords will be automatically hashed.

- **New** - Local authentication backend allows you to login using local
  accounts through pam.


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Burp: http://burp.grke.org/
