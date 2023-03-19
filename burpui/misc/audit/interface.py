# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.audit.interface
    :platform: Unix
    :synopsis: Burp-UI audit interface.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import logging
from abc import ABCMeta, abstractmethod


class BUIauditLogger(object, metaclass=ABCMeta):
    """The :class:`burpui.misc.audit.interface.BUIauditLogger` class defines the audit
    Logger interface.
    """

    _level = -1

    @property
    def level(self):
        return self._level

    def debug(self, message, *args, **kwargs):
        if logging.DEBUG >= self.level:
            self.log(logging.DEBUG, message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        if logging.INFO >= self.level:
            self.log(logging.INFO, message, *args, **kwargs)

    def warn(self, message, *args, **kwargs):
        if logging.WARN >= self.level:
            self.log(logging.WARN, message, *args, **kwargs)

    warning = warn

    def err(self, message, *args, **kwargs):
        if logging.ERROR >= self.level:
            self.log(logging.ERROR, message, *args, **kwargs)

    error = err

    def critical(self, message, *args, **kwargs):
        if logging.CRITICAL >= self.level:
            self.log(logging.CRITICAL, message, *args, **kwargs)

    @abstractmethod
    def log(self, level, message, *args, **kwargs):
        pass


class BUIaudit(object, metaclass=ABCMeta):
    """The :class:`burpui.misc.audit.interface.BUIaudit` class defines the audit
    interface.

    :param app: Instance of the app we are running in
    :type app: :class:`burpui.engines.server.BUIServer`
    """

    priority = 0

    name = None
    _logger = None

    def __init__(self, app):
        self.app = app

    @property
    def logger(self) -> BUIauditLogger:
        """:rtype: class:`BUIauditLogger`"""
        return self._logger
