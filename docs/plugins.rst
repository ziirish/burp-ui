Plugins
=======

Since *v0.6.0*, you can write your own external plugins.
For now, only *authentication* and *acl* plugins are supported.

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
        priority = 1000

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

ACL
---

You will find here a fully working example of an external *acl* plugin.
Please refer to the `ACL API <acl.html>`_ page for more details.

.. code-block:: python
    :linenos:

        from burpui.misc.acl import interface

        __type__ = 'acl'

        class ACLloader(interface.BUIaclLoader):
            name = 'CUSTOM:ACL'
            priority = 1000

            def __init__(self, app):
                self.app = app
                self.admin = 'toto'
                self._acl = CustomACL(self)

            @property
            def acl(self):
                return self._acl

            @property
            def grants(self):
                return None

            @property
            def groups(self):
                return None


        class CustomACL(interface.BUIacl):

            def __init__(self, loader):
                self.loader = loader

            def is_admin(self, username=None):
                if not username:
                    return False
                return username == self.loader.admin

            def is_moderator(self, username=None):
                if not username:
                    return False
                return username == self.loader.admin

            def is_client_rw(self, username=None, client=None, server=None):
                if not username:
                    return False
                return username == self.loader.admin

            def is_client_allowed(self, username=None, client=None, server=None):
                if not username:
                    return False
                return username == self.loader.admin

            def is_server_rw(self, username=None, server=None):
                if not username:
                    return False
                return username == self.loader.admin

            def is_server_allowed(self, username=None, server=None):
                if not username:
                    return False
                return username == self.loader.admin


Line 1 is mandatory since you must implement the *acl* interface in order for
your plugin to work.

Line 3 ``__type__ = 'acl'`` defines a *acl* plugin.

Line 6 defines your *acl* backend name.

The rest of the code is just a minimal implementation of the *acl* interface.

This plugin defines a hardcoded admin user: *toto* which will be granted admin
rights through the whole application.

You can put this code in a file called *custom_acl.py*, save this file in
*/etc/burp/plugins* for instance, and set ``plugins = /etc/burp/plugins``.
The plugin will be automatically loaded.

.. note:: This is just an example, do not run this particular plugin in production!


ACL engine has built-in ``Groups`` support, to take full advantage of this
feature, it is recommended to use the ``global_grants`` object as shown bellow:

.. code-block:: python
    :linenos:

        from burpui.misc.acl.grants import global_grants
        from burpui.misc.acl import interface

        from six import iteritems

        __type__ = 'acl'

        class ACLloader(interface.BUIaclLoader):
            name = 'CUSTOM2:ACL'
            priority = 1001

            _groups = {
                'gp1': {
                    'grants': 'server1, server2',
                    'members': ['user1'],
                },
            }

            def __init__(self, app):
                self.app = app
                self.admin = 'toto'
                for gname, content in iteritems(self._groups):
                    global_grants.set_group(gname, content['members'])
                    global_grants.set_grant(gname, content['grants'])
                self._acl = global_grants

            @property
            def acl(self):
                return self._acl

            @property
            def grants(self):
                return self.acl.grants

            @property
            def groups(self):
                return self._groups


You can omit either the ``global_grants.set_grant`` or the
``global_grants.set_group`` part if you like. For instance to define the grants
of a given group using another ACL backend, and using your plugin to manage
groups membership.
