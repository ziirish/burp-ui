# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.ws
    :platform: Unix
    :synopsis: Burp-UI external WebSocket module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask_socketio import SocketIO

from ..config import config

options = {}
options["async_mode"] = config.get("WS_ASYNC_MODE", "gevent")

#    engineio_logger=config.get('WS_DEBUG', False),
socketio = SocketIO(
    message_queue=config.get("WS_MESSAGE_QUEUE"),
    manage_session=config.get("WS_MANAGE_SESSION", False),
    engineio_logger=False,
    **options
)
