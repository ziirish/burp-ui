Badges
======

.. image:: https://ci.ziirish.me/projects/1/status.png?ref=master
    :target: https://ci.ziirish.me/projects/1?ref=master
    :alt: Build Status

.. image:: https://readthedocs.org/projects/burp-ui/badge/?version=latest
    :target: https://readthedocs.org/projects/burp-ui/?badge=latest
    :alt: Documentation Status

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
``Burp-UI`` allows you to perform *on-the-fly* restorations and to edit/manage
your burp-server's configuration files.

It is actually an improvement of the burp status monitor (``burp -c /etc/burp/burp-server.conf -a s``).

In order to work properly, you must be running ``Burp-UI`` on the same host that
runs your burp-server (because the burp status port only listen on *localhost*).
If you don't want to, I developed a ``bui-agent`` that allows you to *proxify*
external commands to your burp status port.


Who are you?
------------

I'm `Ziirish <http://ziirish.info>`__, a French sysadmin who loves `Burp`_ and
who'd like to help its adoption by providing it a nice and powerful interface.
If you like my work, you can:

* Thank me by sending me an email or writing nice comments
* Buy me a beer or some fries (or both!)
* Make a donation on my `Paypal <http://ziirish.info>`__


Documentation
=============

The documentation is hosted on `readthedocs <https://readthedocs.org>`_ at the
following address: `burp-ui.readthedocs.org <https://burp-ui.readthedocs.org/en/latest/>`_


Community
=========

Please refer to the `Contributing <https://burp-ui.readthedocs.org/en/latest/contributing.html>`_ page.


Notes
=====

Please feel free to report any issues on my `gitlab <https://git.ziirish.me/ziirish/burp-ui/issues>`_.
I have closed the *github tracker* to have a unique tracker system.


TODO
====

`Here <https://git.ziirish.me/ziirish/burp-ui/issues?label_name=todo>`_ is a
non-exhaustive list of things I'd like to add.


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
.. _burpui.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/share/burpui/etc/burpui.sample.cfg
