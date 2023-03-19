# -*- coding: utf8 -*-
import logging
import re

from ...tools.logging import logger as parent_logger
from .interface import BUIaudit
from .interface import BUIauditLogger as BUIauditLoggerInterface


class BUIauditLoader(BUIaudit):
    section = name = "BASIC:AUDIT"

    logfile = None
    max_bytes = None
    rotate = None

    def __init__(self, app):
        """
        :param app: Instance of the app we are running in
        :type app: :class:`burpui.engines.server.BUIServer`
        """
        self.app = app
        self.conf = self.app.conf

        self.level = default = logging.getLevelName(self.app.logger.getEffectiveLevel())

        if self.section in self.conf.options:
            self.priority = self.conf.safe_get(
                "priority", "integer", self.section, defaults=self.section
            )
            self.level = self.conf.safe_get(
                "level", section=self.section, defaults=default
            )
            self.logfile = self.conf.safe_get("logfile", section=self.section)
            self.max_bytes = self.conf.safe_get(
                "max_bytes",
                "force_string",
                section=self.section,
                defaults="30 * 1024 * 1024",
            )
            self.rotate = self.conf.safe_get(
                "rotate", "integer", section=self.section, defaults=5
            )

        if self.max_bytes and re.match(r"(\d+\s*[+-/*]?\s*)+$", self.max_bytes):
            self.max_bytes = eval(self.max_bytes)
        else:
            self.max_bytes = 0

        if self.level != default:
            self.level = logging.getLevelName(f"{self.level}".upper())
            if not isinstance(self.level, int):
                self.level = default

        self._logger = BUIauditLogger(self)


class BUIauditLogger(BUIauditLoggerInterface):
    _logger = parent_logger.getChild("audit")  # type: logging.Logger

    def __init__(self, loader):
        self.loader = loader
        self._level = self.loader.level
        LOG_FORMAT = "[%(asctime)s] AUDIT %(levelname)s in %(from)s: %(message)s"

        if self.loader.logfile and self.loader.logfile.lower() != "none":
            from logging.handlers import RotatingFileHandler

            handler = RotatingFileHandler(
                self.loader.logfile,
                maxBytes=self.loader.max_bytes,
                backupCount=self.loader.rotate,
            )
        else:
            from logging import StreamHandler

            handler = StreamHandler()

        handler.setLevel(self.level)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))

        self._logger.setLevel(self.level)
        self._logger.addHandler(handler)

    def log(self, level, message, *args, **kwargs):
        self._logger.log(level, message, *args, **kwargs)
