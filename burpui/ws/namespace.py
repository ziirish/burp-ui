# -*- coding: utf8 -*-
"""
.. module:: burpui.ws.namespace
    :platform: Unix
    :synopsis: Burp-UI WebSocket namespace module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask import current_app, request
from flask_socketio import Namespace, emit

from ..server import BUIServer  # noqa

bui = current_app  # type: BUIServer


class BUINamespace(Namespace):
    def on_connect(self):
        sid = request.sid
        # if current_user.is_authenticated:
        bui.logger.debug('Someone just connected! {}'.format(sid))
        # else:
        #    bui.logger.debug('Illegal connection')
        #    disconnect()
        #    return False

    def on_disconnect(self):
        sid = request.sid
        bui.logger.debug('Someone just disconnected! {}'.format(sid))

    def on_echo(self, data):
        emit('reply', data, namespace='/ws')
        bui.logger.debug('Got message: {}'.format(data))
