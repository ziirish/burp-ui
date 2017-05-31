Plugins
=======

Since *v0.6.0*, you can write your own external plugins.
For now, only *authentication* plugins are supported.

Authentication
--------------

You will find here a fully working example of an external *authentication*
plugin.
Please refer to the `Auth API <auth.html>`_ page for more details.

.. code-block:: python
    :linenos:

    from burpui.misc.auth import interface

    __type__ = 'auth'

    class UserHandler(interface.BUIhandler):
        name = 'CUSTOM'

        def __init__(self, app):
            self.users = {
                'toto': CustomUser('toto', 'toto'),
                'tata': CustomUser('tata', 'tata'),
                'titi': CustomUser('titi', 'titi'),
                'tutu': CustomUser('tutu', 'tutu'),
            }

        def user(self, name):
            return self.users.get(name, None)

        @property
        def loader(self):
            return self

    class CustomUser(interface.BUIuser):
        def __init__(self, name, password):
            self.name = self.id = name
            self.password = password

        def login(self, passwd):
            self.authenticated = passwd == self.password
            return self.authenticated


Line 1 is mandatory since you must implement the *auth* interface in order for
your plugin to work.
Line 3 ``__type__ = 'auth'`` defines a *auth* plugin.
Line 6 defines your *auth* backend name.
The rest of the code is just a minimal implementation of the *auth* interface.
This plugin defines four hardcoded users: *toto*, *tata*, *titi*, *tutu* with
respectively the same passwords as their username.

You can put this code in a file called *custom.py*, save this file in
*/etc/burp/plugins* for instance, and set ``plugins = /etc/burp/plugins``.
The plugin will be automatically loaded.

.. note:: This is just an example, do not run this particular plugin in production!
