Development
===========

If you wish to use the latest and yet unstable version
(eg. `master <https://git.ziirish.me/ziirish/burp-ui/tree/master>`__),
you can install it using ``pip`` too, but I would recommend you to use a
``virtualenv``.
In order to build `Burp-UI`_ you will need `bower <http://bower.io/>`_.

To do so, run the following commands:

::

    mkdir /opt/bui-venv
    pip install virtualenv
    virtualenv /opt/bui-venv
    source /opt/bui-venv/bin/activate
    pip install git+https://git.ziirish.me/ziirish/burp-ui.git


You can uninstall/disable this `Burp-UI`_ setup by typing ``deactivate`` and
removing the ``/opt/bui-venv`` directory.


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
