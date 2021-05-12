# -*- coding: utf8 -*-
"""
.. module:: burpui.api.custom.resource
    :platform: Unix
    :synopsis: Burp-UI api custom resource module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import inspect
import json

from flask_restx import Resource as ResourcePlus
from flask_restx.errors import abort

from ...tools.logging import logger


class Resource(ResourcePlus):
    """Subclass default Resource to manage ACL"""

    # by default, we require valid login for all routes. This can be disabled
    # per resource
    login_required = True

    logger = logger

    def abort(self, code=500, message=None, **kwargs):
        """
        Properly abort the current request

        See: :func:`~flask_restx.errors.abort`
        """
        if message and not isinstance(message, str):
            try:
                message = json.dumps(message)  # pragma: no cover
            except:
                message = None
        # Add extra logs when raising abort exception
        (frm, filename, line_no, func, source_code, source_index) = inspect.stack()[1]
        mod = inspect.getmodule(frm)
        self.logger.debug("Abort in {}:{}".format(filename, line_no))
        self.logger.warning(
            "[{}] {}: {}{}".format(
                mod.__name__, code, message, " - {}".format(kwargs) if kwargs else ""
            )
        )
        # This raises a Flask Exception
        abort(code, message, **kwargs)
