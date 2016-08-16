Contributing
============

Contributions are welcome. You can help in any way you want, for instance by
opening issues on the `bug tracker
<https://git.ziirish.me/ziirish/burp-ui/issues>`__, sending patches, etc.

There is also a dedicated website. Currently it only hosts a `Discourse
<http://www.discourse.org/>`__ instance where you can discuss with each other.
No need to create another account, the one you use in the `bug tracker
<https://git.ziirish.me/ziirish/burp-ui/issues>`__ can be imported
automatically!

Feel free to use it and post your tips and remarks.

The address is: `https://burpui.ziirish.me/ <https://burpui.ziirish.me/>`__

You can financially support the project if you find it useful or if you would
like to sponsor a feature. Details on my `website <https://ziirish.info/>`__.


Issues / Bugs
-------------

If you find any issue while using ``Burp-UI`` please report it on the `bug
tracker <https://git.ziirish.me/ziirish/burp-ui/issues>`__.
All issues should contain the used command line to reproduce the problem, the
debug output and both versions of burp and ``Burp-UI`` you are using.

You can get those informations using the following commands:

::

        $ /usr/sbin/burp -v
        burp-1.4.40
        $ burp-ui -V -v
        burp-ui: v0.1.0.dev (90deb82c7b0be35f1a70bb073c9926b5947c6a85)
        $ burp-ui -v


Optionally your python version and your OS might be useful as well.


Questions
---------

Ask questions in the `discussion forum <https://burpui.ziirish.me/>`__. Do not
use the issue tracker for this purpose.

``Burp-UI`` has extensive online documentation please read the `doc
<https://burp-ui.readthedocs.io/en/latest/>`__.


Troubleshooting
---------------

In case you encounter troubles with ``Burp-UI``, you should run it with the
``-vvvv`` flag and paste the relevant output within your bug-report.
Please also give the version of ``burp`` **AND** ``Burp-UI``.
Since v0.0.6 you can use the ``-V`` or ``--version`` flag in order to get your
version number.


Merge / Pull requests
---------------------

I would like you to use `gitlab <https://git.ziirish.me/>`__ for your Merge
requests in order to take advantage of the automated tests I have been working
on.
You can login/register on my personal gitlab server with your github account.


Development
-----------

You will find any development information on the
`developer guide <developer.html>`_ page.
