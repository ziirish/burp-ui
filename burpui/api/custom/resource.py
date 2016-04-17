# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.resource
    :platform: Unix
    :synopsis: Burp-UI api custom resource module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import logging
import inspect
import json

from flask_restplus import Resource as ResourcePlus
from flask_restplus.errors import abort
from flask_login import current_user
from ..._compat import PY3

if PY3:
    basestring = str


class Resource(ResourcePlus):
    """Subclass default Resource to manage ACL"""
    logger = logging.getLogger('burp-ui')

    def __init__(self, api=None, *args, **kwargs):
        self.username = current_user.get_id()
        self.is_admin = api.bui.acl and api.bui.acl.is_admin(self.username)
        self.cache = api.cache
        ResourcePlus.__init__(self, api, *args, **kwargs)

    def abort(self, code=500, message=None, **kwargs):
        """
        Properly abort the current request

        See: :func:`~flask_restplus.errors.abort`
        """
        if message and not isinstance(message, basestring):
            try:
                message = json.dumps(message)  # pragma: no cover
            except:
                message = None
        # Add extra logs when raising abort exception
        (
            frm,
            filename,
            line_no,
            func,
            source_code,
            source_index
        ) = inspect.stack()[1]
        mod = inspect.getmodule(frm)
        self.logger.debug('Abort in {}:{}'.format(filename, line_no))
        self.logger.warning(
            '[{}] {}: {}{}'.format(
                mod.__name__,
                code,
                message,
                ' - {}'.format(kwargs) if kwargs else ''
            )
        )
        # This raises a Flask Exception
        abort(code, message, **kwargs)
