# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.resource
    :platform: Unix
    :synopsis: Burp-UI api custom resource module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask.ext.restplus import Resource as ResourcePlus
from flask.ext.login import current_user
from .. import api

class Resource(ResourcePlus):
    """Subclass default Resource to manage ACL"""

    def __init__(self, api=None, *args, **kwargs):
        self.username = current_user.get_id()
        self.is_admin = api.bui.acl and api.bui.acl.is_admin(self.username)
        ResourcePlus.__init__(self, api, *args, **kwargs)

