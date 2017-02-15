Installation
============

`Burp-UI`_ is written in Python with the `Flask`_ micro-framework.
The easiest way to install `Burp-UI`_ is to use ``pip``.

::

    pip install burp-ui


You can setup various parameters in the `burpui.cfg`_ file.
This file can be specified with the ``-c`` flag or should be present in
``/etc/burp/burpui.cfg``.
By default `Burp-UI`_ ships with a sample file located in
``$INSTALLDIR/share/burpui/etc/burpui.sample.cfg``.
(*$INSTALLDIR* defaults to */usr/local* when using pip **outside** a
virtualenv)

.. note::
    It is advised to copy the sample configuration in ``/etc/burp/burpui.cfg``
    and to edit this file so that it is not overwritten on every upgrade.

Then you can run ``burp-ui``: ``burp-ui``

By default, ``burp-ui`` listens on localhost on port 5000.

You can then point your browser to http://127.0.0.1:5000/

Upgrade
-------

In order to upgrade `Burp-UI`_ to the latest stable version, you can run the
following command:

::

   pip install --upgrade burp-ui


.. note::
    If you encounter any issue after upgrading to the latest stable release,
    make sure you read the `upgrading <upgrading.html>`__ page.

Debian Wheezy
-------------

The version of ``pip`` available on *Debian Wheezy* does not support all the
features needed to build and install the latest `Burp-UI`_ version.

Instead, you may want to run the following command either to install it from
scratch or to upgrade your current version to the latest one:

::

    easy_install --upgrade burp-ui


.. _Flask: http://flask.pocoo.org/
.. _burpui.cfg: https://git.ziirish.me/ziirish/burp-ui/blob/master/share/burpui/etc/burpui.sample.cfg
.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Burp: http://burp.grke.net/
