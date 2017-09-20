# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.ws
    :platform: Unix
    :synopsis: Burp-UI external WebSocket module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import os
import sys

from ..config import config
from flask_socketio import SocketIO

_stdout = sys.stdout
_stderr = sys.stderr
null = open(os.devnull, 'wb')

# hide stdout and stderr messages
sys.stdout = sys.stderr = null

options = {}
if config.get('WS_ASYNC_MODE'):
    options['async_mode'] = config.get('WS_ASYNC_MODE')

socketio = SocketIO(
    message_queue=config.get('WS_MESSAGE_QUEUE'),
    manage_session=config.get('WS_MANAGE_SESSION', False),
    engineio_logger=config.get('WS_DEBUG', False),
    **options
)

# revert stdout and stderr
sys.stdout = _stdout
sys.stderr = _stderr
#null.flush()
#null.close()
