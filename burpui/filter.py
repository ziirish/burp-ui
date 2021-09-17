# -*- coding: utf8 -*-
"""
.. module:: burpui.filter
    :platform: Unix
    :synopsis: Burp-UI filter module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""


class BUIMask(object):
    """Mask client/servers based on user preferences or user ACL"""

    def init_app(self, app):
        """Initialize the mask

        :param app: Application context
        :type app: :class:`burpui.engines.server.BUIServer`
        """
        self.app = app

    @property
    def is_user_pref(self):
        return self.app.config["WITH_SQL"]

    def has_filters(self, current_user):
        if not current_user.is_anonymous and current_user.acl.is_admin():
            if self.is_user_pref:
                return self.query_user(current_user.name)
            return False
        return True

    def query_user(self, username):
        from .models import Hidden

        return Hidden.query.filter_by(user=username).first()

    def query_hidden(self, username):
        from .models import Hidden

        return (
            Hidden.query.filter_by(user=username)
            .with_entities(Hidden.client, Hidden.server)
            .all()
        )

    def hidden_clients(self, username):
        if not self.is_user_pref:
            return []
        return self.query_hidden(username)

    def hidden_servers(self, username):
        if not self.is_user_pref:
            return []
        hidden = self.query_hidden(username)
        return [server for client, server in hidden if not client]

    def is_client_allowed(self, current_user, client=None, server=None):
        if self.app.auth == "none":
            return True
        if current_user.is_anonymous:
            return False
        if self.has_filters(current_user) and self.is_user_pref:
            hidden = self.hidden_clients(current_user.name)
            if (client, server) in hidden:
                return False
        if current_user.acl.is_admin():
            return True
        return current_user.acl.is_client_allowed(client, server)

    def is_client_rw(self, current_user, client, server=None):
        if self.app.auth == "none":
            return True
        if current_user.is_anonymous:
            return False
        if self.has_filters(current_user) and self.is_user_pref:
            hidden = self.hidden_clients(current_user.name)
            if (client, server) in hidden:
                return False
        if current_user.acl.is_admin():
            return True
        return current_user.acl.is_client_rw(client, server)

    def is_server_allowed(self, current_user, server):
        if self.app.auth == "none":
            return True
        if current_user.is_anonymous:
            return False
        if self.has_filters(current_user) and self.is_user_pref:
            hidden = self.hidden_servers(current_user.name)
            if server in hidden:
                return False
        if current_user.acl.is_admin():
            return True
        return current_user.acl.is_server_allowed(server)

    def is_server_rw(self, current_user, server):
        if self.app.auth == "none":
            return True
        if current_user.is_anonymous:
            return False
        if self.has_filters(current_user) and self.is_user_pref:
            hidden = self.hidden_servers(current_user.name)
            if server in hidden:
                return False
        if current_user.acl.is_admin():
            return True
        return current_user.acl.is_server_rw(server)


mask = BUIMask()
