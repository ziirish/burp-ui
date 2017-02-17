Running
=======

There are several ways to run `Burp-UI`_. You can either use the embedded
Flask's `development server <http://flask.pocoo.org/docs/0.12/server/>`_ or you
can use any of the `deployement options <http://flask.pocoo.org/docs/0.12/deploying/>`_
provided by Flask.

.. note:: I personaly focus on ``gunicorn`` support for production deployments


Sandboxing
----------

If you want to play with `Burp-UI`_ to *PoC* it or if you are going to be the
only user, you can absolutely use the embedded server.
If you plan to run `Burp-UI`_ in production, then you should go with
`Gunicorn`_.

Option 1
^^^^^^^^

You can run the embedded server with the following command:

::

    burp-ui


By default, the server listens on *localhost:5000*. You can easily change this
by adding the ``-- -h x.x.x.x -p yyyy`` options. See `here <installation.html#developer-options>`_
for details.

Option 2
^^^^^^^^

Prior to v0.4.0, you could specify the *bind* and *port* option within the
`Burp-UI`_ configuration file.
You can still use this behavior by running:

::

    python -m burpui -m legacy [--help]


Production
----------

Like I said earlier, I recommend using `Gunicorn`_ for production deployments.
You can refer to the dedicated `gunicorn <gunicorn.html>`__ page of this
documentation to know everything on how to `Burp-UI`_ through `Gunicorn`_.


Going further
-------------

Please refer to the `advanced usage <advanced_usage.html>` page for details on
how to use/customize `Burp-UI`_.


.. _Burp-UI: https://git.ziirish.me/ziirish/burp-ui
.. _Gunicorn: http://gunicorn.org/
