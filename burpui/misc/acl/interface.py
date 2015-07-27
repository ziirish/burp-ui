# -*- coding: utf8 -*-


class BUIaclLoader:
    @property
    def acl(self):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")


class BUIacl:
    def is_admin(self, username=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def clients(self, username=None, server=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def servers(self, username=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

    def is_client_allowed(self, username=None, client=None, server=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")
