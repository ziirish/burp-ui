# -*- coding: utf8 -*-

class BUIaclLoader:
    def get_acl(self):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")

class BUIacl:
    def is_admin(self, username=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")
    def clients(self, username=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")
    def is_client_allowed(self, username=None, client=None):
        raise NotImplementedError("Sorry, the current Backend does not implement this method!")
