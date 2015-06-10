Build Status
============

.. image:: https://ci.ziirish.me/projects/1/status.png?ref=master
    :target: https://ci.ziirish.me/projects/1?ref=master

Introduction
============

Screenshots
-----------

.. image:: https://raw.githubusercontent.com/ziirish/burp-ui/master/pictures/burp-ui.gif
    :target: https://git.ziirish.me/ziirish/burp-ui/blob/master/pictures/burp-ui.gif


What's that?
------------

Let me introduce you ``Burp-UI``. It is a web-based UI to manage your
burp-servers.
You can view different reports about burp-servers, burp-clients, backups, etc.
``Burp-UI`` allows you to perform *on-the-fly* restorations and should allow
you to edit/manage your burp-server's conf file very soon.

It is actually an improvement of the burp status monitor (``burp -c /etc/burp/burp-server.conf -a s``).

It currently supports only the burp-1.x branch but it is totally modular so
supporting burp-2.x won't be a big deal.
So in order to work properly, you must be running ``Burp-UI`` on the same host
that runs your burp-server (because the burp status port only listen on
*localhost*).
If you don't want to, I developed a ``bui-agent`` that allows you to *proxify*
external commands to your burp status port.


Who are you?
------------

I'm `Ziirish <http://ziirish.info>`_, a French sysadmin who loves `Burp`_ and
would like to help its adoption by providing it a nice and powerful interface.
If you like my work, you can:

* Thank me by sending me an email or writing a nice comment
* Buy me a beer or some fries or both!
* Make a donation on my Paypal


Contributing
============

Contributions are welcome. You can help in any way you want, for instance by
opening issues on the `bug tracker <https://git.ziirish.me/ziirish/burp-ui/issues>`__,
sending patches, etc.
There is also a dedicated website. Currently it only hosts a `Discourse <http://www.discourse.org/>`__
instance where you ca discuss with each other.
Feel free to use it and post your tips and remarks.
The address is: `http://burpui.ziirish.me/ <http://burpui.ziirish.me/>`__


Requirements
============

Please note that currently, ``Burp-UI`` must be running on the same server that
runs the burp-server.


For LDAP authentication (optional), we need the ``simpleldap`` module that
requires the following packages on Debian:

::

    aptitude install libsasl2-dev libldap2-dev python-dev


Then we install the module itself:

::

    pip install simpleldap


If you would like to use SSL, you will need the ``python-openssl`` package.
On Debian:

::

    aptitude install python-openssl


Installation
============

``Burp-UI`` is written in Python with the `Flask`_ micro-framework.
The easiest way to install Flask is to use ``pip``.

On Debian, you can install ``pip`` with the following command:

::

    aptitude install python-pip


Once ``pip`` is installed, you can install ``Burp-UI`` this way:

::

    pip install burp-ui


You can setup various parameters in the `burpui.cfg`_ file.
This file can be specified with the ``-c`` flag or should be present in
``/etc/burp/burpui.cfg``.
By default ``Burp-UI`` ships with a default file located in
``$BURPUIDIR/../share/burpui/etc/burpui.cfg``.

Then you can run ``burp-ui``: ``burp-ui``

By default, ``burp-ui`` listens on all interfaces (including IPv6) on port 5000.

You can then point your browser to http://127.0.0.1:5000/

Instructions
------------

In order to make the *on the fly* restoration/download functionality work, you
need to check a few things:

1. Provide the full path of the burp (client) binary file
2. Provide the full path of an empty directory where a temporary restoration
   will be made. This involves you have enough space left on that location on
   the server that runs ``Burp-UI``
3. Launch ``Burp-UI`` with a user that can proceed restorations and that can
   write in the directory above
4. Make sure to configure a client on the server that runs ``Burp-UI`` that can
   restore files of other clients (option *restore_client* in burp-server
   configuration)


Development
===========

If you wish to use the latest and yet unstable version (eg. `master <https://git.ziirish.me/ziirish/burp-ui/tree/master>`__),
you can install it using ``pip`` too, but I would recommend you to use a
``virtualenv``.

To do so, run the following commands:

::

    mkdir /opt/bui-venv
    pip install virtualenv
    virtualenv /opt/bui-venv
    source /opt/bui-venv/bin/activate
    pip install git+https://git.ziirish.me/ziirish/burp-ui.git


You can uninstall/disable this ``Burp-UI`` setup by typing ``deactivate`` and
removing the ``/opt/bui-venv`` directory.


Gunicorn
========

Starting from v0.0.6, ``Burp-UI`` supports `Gunicorn <http://gunicorn.org>`_ in
order to handle multiple users simultaneously.

You need to install ``gunicorn`` and ``eventlet``:

::

    pip install eventlet
    pip install gunicorn

You will then be able to launch ``Burp-UI`` this way:

::

    gunicorn -k eventlet -w 4 'burpui:init(conf="/path/to/burpui.cfg")'


When using ``gunicorn``, the command line options are not available. Instead,
run the ``Burp-UI`` ``init`` method directly. Here are the parameters you can
play with:

- conf: Path to the ``Burp-UI`` configuration file
- debug: Whether to run ``Burp-UI`` in debug mode or not to get some extra logging
- logfile: Path to a logfile in order to log ``Burp-UI`` internal messages

Options
=======

::

    Usage: burp-ui [options]

    Options:
      -h, --help            show this help message and exit
      -v, --verbose         verbose output
      -d, --debug           verbose output (alias)
      -V, --version         print version and exit
      -c CONFIG, --config=CONFIG
                            configuration file
      -l FILE, --logfile=FILE
                            output logs in defined file


Troubleshooting
===============

In case you encounter troubles with ``Burp-UI``, you should run it with the
``-d`` flag and paste the relevant output within your bug-report.
Please also give the version of ``burp`` AND ``Burp-UI``.
Since v0.0.6 you can use the ``-V`` or ``--version`` flag in order to get your
version number.


Notes
=====

Please feel free to report any issues on my `gitlab <https://git.ziirish.me/ziirish/burp-ui/issues>`_.
I have closed the *github tracker* to have a unique tracker system.


TODO
====

`Here <https://git.ziirish.me/ziirish/burp-ui/issues?label_name=todo>`_ is a
non-exhaustive list of things I'd like to add.

Also note that in the future, I'd like to write a burp-client GUI.
But I didn't think yet of what to do.

Known Issues
============

1. SSL issue

My new SSL certificate seem to be unknown on older systems like debian wheezy.
Thus, you may have some SSL failure while trying to clone my repository.
In order to fix this error, you can run the following command as root that will
add my certificate in your trust list:

::

   echo -n | openssl s_client -showcerts -connect git.ziirish.me:443 -servername git.ziirish.me 2>/dev/null | sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' >>/etc/ssl/certs/ca-certificates.crt

2. SSH issue

People that would like to clone the repository over SSH will face an
authentication failure even if they added a valid SSH key in their user
settings.
The reason is I only have *one* public IP address so I must use port
redirections to have multiple SSH instances running.
To fix the issue, you should configure your SSH client by adding the following
lines in your ``~/.ssh/config`` file:

::

   Host git.ziirish.me
      Port 2222



Licenses
========

``Burp-UI`` is released under the BSD 3-clause `License`_.

But this project is built on top of other tools listed here:

- `d3.js <http://d3js.org/>`_ (`BSD <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/d3/LICENSE>`__)
- `nvd3.js <http://nvd3.org/>`_ (`Apache <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/nvd3/LICENSE.md>`__)
- `jQuery <http://jquery.com/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/jquery/MIT-LICENSE.txt>`__)
- `jQuery-UI <http://jqueryui.com/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/jquery-ui/MIT-LICENSE.txt>`__)
- `fancytree <https://github.com/mar10/fancytree>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/fancytree/MIT-LICENSE.txt>`__)
- `bootstrap <http://getbootstrap.com/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/bootstrap/LICENSE>`__)
- `typeahead <http://twitter.github.io/typeahead.js/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/typeahead/LICENSE>`__)
- `bootswatch <http://bootswatch.com/>`_ theme ``Slate`` (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/bootstrap/bootswatch.LICENSE>`__)
- `angular-bootstrap-switch <https://github.com/frapontillo/angular-bootstrap-switch>`_ (`Apache <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/angular-bootstrap-switch/LICENSE>`__)
- `angular.js <https://angularjs.org/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/angularjs/LICENSE>`__)
- `angular-ui-select <https://github.com/angular-ui/ui-select>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/angular-ui-select/LICENSE>`__)
- `AngularStrap <http://mgcrea.github.io/angular-strap/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/angular-strap/LICENSE.md>`__)
- `lodash <https://github.com/lodash/lodash>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/lodash/LICENSE.txt>`__)
- `DataTables <http://datatables.net/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/DataTables/LICENSE.txt>`__)
- Home-made `favicon <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/images/favicon.ico>`_ based on pictures from `simpsoncrazy <http://www.simpsoncrazy.com/pictures/homer>`_

Also note that this project is made with the Awesome `Flask`_ micro-framework.


Thanks
======

Special Thanks to Graham Keeling for its great software! This project would not
exist without `Burp`_.

.. _Flask: http://flask.pocoo.org/
.. _License: https://git.ziirish.me/ziirish/burp-ui/blob/master/LICENSE
.. _Burp: http://burp.grke.org/
.. _burpui.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui.cfg
