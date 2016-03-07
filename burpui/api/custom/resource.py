# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.resource
    :platform: Unix
    :synopsis: Burp-UI api custom resource module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask_restplus import Resource as ResourcePlus
from flask_login import current_user


class Resource(ResourcePlus):
    """Subclass default Resource to manage ACL"""

    def __init__(self, api=None, *args, **kwargs):
        self.username = current_user.get_id()
        self.is_admin = api.bui.acl and api.bui.acl.is_admin(self.username)
        self.cache = api.cache
        ResourcePlus.__init__(self, api, *args, **kwargs)
