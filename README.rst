Build Status
------------

.. image:: http://ci.ziirish.me/projects/1/status.png?ref=master
    :target: http://ci.ziirish.me/projects/1?ref=master


Requirements
------------

Please note that currently, ``Burp-UI`` must be running on the same server that
runs the burp-server.


For LDAP authentication (optional), we need the ``simpleldap`` module that 
requires the following packages on Debian:

::

    aptitude install libsasl2-dev libldap2-dev python-dev


Then we install the module itself:

::

    pip install simpleldap


Installation
------------

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


Gunicorn
--------

``Burp-UI`` now supports `Gunicorn <http://gunicorn.org>`_ in order to handle 
multiple users simultaneously.

You need to install ``gunicorn`` and ``eventlet``:

::

    pip install eventlet
    pip install gunicorn

You will then be able to launch ``Burp-UI`` this way:

::

    gunicorn -k eventlet -w 4 'burpui:init(conf="/path/to/burpui.cfg")'


Instructions
------------

In order to make the *on the fly* restoration/download functionality work, there
you need to check a few things:

1. Provide the full path of the burp (client) binary file
2. Provide the full path of an empty directory where a temporary restoration
   will be made. This involves you have enough space left on that location on
   the server that runs ``Burp-UI``
3. Launch ``Burp-UI`` with a user that can proceed restorations and that can
   write in the directory above
4. Make sure to configure a client on the server that runs ``Burp-UI`` that can
   restore files of other clients (option *restore_client* in burp-server
   configuration)


Notes
-----

Please feel free to report any issues on my `gitlab <https://git.ziirish.me/ziirish/burp-ui/issues>`_
I have closed the *github tracker* to have a unique tracker system.


TODO
----

`Here <https://git.ziirish.me/ziirish/burp-ui/issues?label_name=todo>`_ is a non-exhaustive list of things I'd like to add.

Also note that in the future, I'd like to write a burp-client GUI.
But I didn't think yet of what to do.


Changelog
---------

* version `current <https://git.ziirish.me/ziirish/burp-ui/>`_:

  - `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.5...master>`_

* version `0.0.5 <https://git.ziirish.me/ziirish/burp-ui/commits/v0.0.5>`_:

  - Add multi-server support
  - Fix bugs
  - `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.4...v0.0.5>`_

* version `0.0.4 <https://git.ziirish.me/ziirish/burp-ui/commits/v0.0.4>`_:

  - Add the ability to download files directly from the web interface
  - `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.3...v0.0.4>`_

* version `0.0.3 <https://git.ziirish.me/ziirish/burp-ui/commits/v0.0.3>`_:

  - Add authentication
  - `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.2...v0.0.3>`_

* version `0.0.2 <https://git.ziirish.me/ziirish/burp-ui/commits/v0.0.2>`_:

  - Fix bugs
  - `Full changelog <https://git.ziirish.me/ziirish/burp-ui/compare/v0.0.1...v0.0.2>`_

* version `0.0.1 <https://git.ziirish.me/ziirish/burp-ui/commits/v0.0.1>`_:

  - Initial release


Licenses
--------

Burp-UI is released under the BSD 3-clause `License`_.

But this project is built on top of other tools listed here:

- `d3.js <http://d3js.org/>`_ (`BSD <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/d3/LICENSE>`__)
- `nvd3.js <http://nvd3.org/>`_ (`Apache <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/nvd3/LICENSE.md>`__)
- `jQuery <http://jquery.com/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/jquery/MIT-LICENSE.txt>`__)
- `jQuery-UI <http://jqueryui.com/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/jquery-ui/MIT-LICENSE.txt>`__)
- `fancytree <https://github.com/mar10/fancytree>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/fancytree/MIT-LICENSE.txt>`__)
- `bootstrap <http://getbootstrap.com/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/bootstrap/LICENSE>`__)
- `typeahead <http://twitter.github.io/typeahead.js/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/typeahead/LICENSE>`__)
- `bootswatch <http://bootswatch.com/>`_ (`MIT <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/bootstrap/bootswatch.LICENSE>`__)
- Home-made `favicon <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/images/favicon.ico>`_ based on pictures from `simpsoncrazy <http://www.simpsoncrazy.com/pictures/homer>`_

Also note that this project is made with the Awesome `Flask`_ micro-framework.


Thanks
------

Special Thanks to Graham Keeling for its great software! This project would not
exist without `Burp`_.

.. _Flask: http://flask.pocoo.org/
.. _License: https://git.ziirish.me/ziirish/burp-ui/blob/master/LICENSE
.. _Burp: http://burp.grke.org/
.. _burpui.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui.cfg

