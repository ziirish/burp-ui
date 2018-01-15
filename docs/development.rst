Development
===========

If you wish to use the latest and yet unstable version
(eg. `master <https://git.ziirish.me/ziirish/burp-ui/tree/master>`__),
you can install it using ``pip`` too, but I would recommend you to use a
``virtualenv``.

To do so, run the following commands:

::

    mkdir /opt/bui-venv
    pip install virtualenv
    virtualenv /opt/bui-venv
    source /opt/bui-venv/bin/activate
    cd /tmp
    # the .tar.gz works with both python 2 and python 3
    wget https://git.ziirish.me/ziirish/burp-ui/builds/artifacts/master/download?job=build:py2 -O burp-ui_build.zip
    unzip burp-ui_build.zip
    pip install --upgrade dist/burp-ui-*.tar.gz
    # Now if you want to test the latest bui-agent run this command:
    #pip install --upgrade meta/burp-ui-agent-*.tar.gz


You can uninstall/disable this `Burp-UI`_ setup by typing ``deactivate`` and
removing the ``/opt/bui-venv`` directory.


Hacking
=======

For those of you who would like to hack on the project, I have split out the
repository to keep a copy of all the external dependencies (JS and CSS) in a git
submodule.

In order to run local debugging, you need to retrieve this git submodule.

To do so, run the following commands:

::

    git clone https://git.ziirish.me/ziirish/burp-ui.git
    cd burp-ui
    git submodule update --init


Before submitting your code, make sure the tests still run.
To do that, you can use `tox <https://tox.readthedocs.io/en/latest/>`_ like
this:

::

    pip install tox
    tox


By defaults, it will run tests against python 2.7, 3.4 and 3.6. However, you can
choose the versions specifically like this:

::

    tox -e py27


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
