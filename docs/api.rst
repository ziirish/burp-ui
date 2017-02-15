API
===

Here are the different routes provided by the application. You can implement
whatever front-end you like on top of it.

The API supports HTTP Basic authentication through the *Authorization* Header.
By default, each authorization is only valid for **one** request (ie. the
sessions are automatically revoked after each request complete). You can ask for
reusable sessions though.
Here are the HTTP headers supported:

- ``X-Reuse-Session``: set it to ``true`` to be able to reuse sessions
- ``X-Language``: set it to whatever supported language you want

Don't forget to call ``/logout`` once you're done if you choose to use reusable
sessions.

.. autoflask:: burpui._rtfd:app
        :blueprints: api
        :undoc-static:
