Burp-UI
=======

.. image:: https://git.ziirish.me/ziirish/burp-ui/badges/master/build.svg
    :target: https://git.ziirish.me/ziirish/burp-ui/pipelines
    :alt: Build Status

.. image:: https://git.ziirish.me/ziirish/burp-ui/badges/master/coverage.svg
    :target: https://git.ziirish.me/ziirish/burp-ui/pipelines
    :alt: Test coverage

.. image:: https://readthedocs.org/projects/burp-ui/badge/?version=latest
    :target: https://readthedocs.org/projects/burp-ui/?badge=latest
    :alt: Documentation Status

.. contents::

Introduction
------------

Screenshots
^^^^^^^^^^^

.. image:: https://git.ziirish.me/ziirish/burp-ui/raw/master/docs/_static/burp-ui.gif
    :target: https://git.ziirish.me/ziirish/burp-ui/blob/master/docs/_static/burp-ui.gif

Demo
^^^^

A screenshot is worth a thousand words, but a Demo is worth a thousand
screenshots.
You can now play with ``Burp-UI`` at
`demo.burp-ui.org <https://demo.burp-ui.org/>`_

Credentials:

- *admin* / *admin* to play with ``Burp-UI`` as an administrator
- *demo* / *demo* to play with ``Burp-UI`` as a regular user

What's that?
^^^^^^^^^^^^

Let me introduce you ``Burp-UI``. It is a web-based UI to manage your
burp-servers.
You can view different reports about burp-servers, burp-clients, backups, etc.
``Burp-UI`` allows you to perform *online* restorations and to edit/manage
your burp-server's configuration files.

Who are you?
^^^^^^^^^^^^

I'm `Ziirish <http://ziirish.info>`__, a French *DevOps* who loves `Burp`_ and
who'd like to help its adoption by providing it a nice and powerful interface.
If you like my work, you can:

* Thank me by sending me an email or writing nice comments
* Buy me a beer or some fries (or both!)
* Make a donation on my `Paypal <http://ziirish.info>`__

Documentation
-------------

The documentation is hosted on `readthedocs <https://readthedocs.org>`_ at the
following address: `burp-ui.readthedocs.io`_

FAQ
---

A `FAQ`_ is available with the documentation.

Community
---------

Please refer to the `Contributing`_ page.

Notes
-----

Feel free to report any issues on my `gitlab
<https://git.ziirish.me/ziirish/burp-ui/issues>`_.

I have closed the *github tracker* to have a unique tracker system.

Also please, read the `Contributing`_ page before reporting any issue to make
sure we have all the informations to help you.

See also
--------

Starting with burp-ui v0.3.0, I introduced you `burp_server_report
<https://github.com/pablodav/burp_server_reports>`_
a project lead by Pablo Estigarribia.

Pablo also contributed to other interesting projects to automate burp and burp-ui
deployments through Ansible:

- `burpui_server <https://galaxy.ansible.com/CoffeeITWorks/burpui_server/>`_
- `burp2_server <https://galaxy.ansible.com/CoffeeITWorks/burp2_server/>`_

@qm2k contributed some scripts/config to tweak your setup. You can found them here:

- `burp-ui_integration <https://github.com/qm2k/burp-ui_integration>`_
- `burp_integration <https://github.com/qm2k/burp_integration>`_

Licenses
--------

``Burp-UI`` is released under the BSD 3-clause `License`_.

But this project is built on top of other tools. Here is a non exhaustive list:

- `d3.js <http://d3js.org/>`_
- `nvd3.js <http://nvd3.org/>`_
- `jQuery <http://jquery.com/>`_
- `jQuery-UI <http://jqueryui.com/>`_
- `fancytree <https://github.com/mar10/fancytree>`_
- `bootstrap <http://getbootstrap.com/>`_
- `typeahead <http://twitter.github.io/typeahead.js/>`_
- `bootswatch <http://bootswatch.com/>`_ theme ``Slate``
- `angular-bootstrap-switch <https://github.com/frapontillo/angular-bootstrap-switch>`_
- `angular.js <https://angularjs.org/>`_
- `angular-ui-select <https://github.com/angular-ui/ui-select>`_
- `AngularStrap <http://mgcrea.github.io/angular-strap/>`_
- `lodash <https://github.com/lodash/lodash>`_
- `DataTables <http://datatables.net/>`_
- Home-made `favicon <https://git.ziirish.me/ziirish/burp-ui/blob/master/burpui/static/images/favicon.ico>`_ based on pictures from `simpsoncrazy <http://www.simpsoncrazy.com/pictures/homer>`_

Also note that this project is made with the Awesome `Flask`_ micro-framework.

Thanks
------

Thank you all for your feedbacks and bug reports. Those are making the project
moving forward.

Thank you to the `Flask`_ developers and community.

Special Thanks to Graham Keeling for his great piece of software! This project
would not exist without `Burp`_.


.. _Flask: http://flask.pocoo.org/
.. _License: https://git.ziirish.me/ziirish/burp-ui/blob/master/LICENSE
.. _Burp: http://burp.grke.org/
.. _burpui.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/share/burpui/etc/burpui.sample.cfg
.. _burp-ui.readthedocs.io: https://burp-ui.readthedocs.io/en/latest/
.. _FAQ: https://burp-ui.readthedocs.io/en/latest/faq.html
.. _Contributing: https://burp-ui.readthedocs.io/en/latest/contributing.html
