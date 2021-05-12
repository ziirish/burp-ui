# -*- coding: utf8 -*-
"""
Burp-UI is a web-ui for burp backup written in python with Flask and
jQuery/Bootstrap

.. module:: burpui.logging
    :platform: Unix
    :synopsis: Burp-UI logging module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import logging


def convert_level(verbose):
    # This is already a valid level
    if logging.getLevelName(verbose) != "Level %s" % verbose and (
        not isinstance(verbose, int) or verbose > 0
    ):
        return verbose

    # The debug argument used to be a boolean so we keep supporting this format
    if isinstance(verbose, bool):
        if verbose:
            verbose = logging.DEBUG
        else:
            verbose = logging.CRITICAL
    else:
        levels = [
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            logging.DEBUG,
        ]
        if verbose >= len(levels):
            verbose = len(levels) - 1
        if not verbose:
            verbose = 0
        verbose = levels[verbose]

    return verbose


class Logger(logging.Logger):
    """
    Helper class to share our logging object across the application
    """

    app = None
    _handler = None

    def __init__(self, app=None, name=None, level=logging.NOTSET):
        """
        :param app: Application context
        :type app: flask.Flask

        :param name: Logger name
        :type name: str

        :param level: Default logging level
        :type level: int
        """
        if app and not name:  # pragma: nocover
            name = app.name
        elif not name:
            name = "burp-ui"
        logging.Logger.__init__(self, name, level)
        if app:  # pragma: nocover
            self.init_app(app)

    def init_app(self, app):
        """
        :param app: Application context
        :type app: flask.Flask
        """
        self.app = app
        config = {
            "level": app.config.get("LOG_LEVEL"),
            "logfile": app.config.get("LOG_FILE"),
        }
        self.init_logger(config)

    def init_logger(self, config):
        """
        :param config: Logger configuration
        :type config: dict
        """
        level = config.get("level", None)
        level = self.level if level is None else level
        level = convert_level(level)
        logfile = config.get("logfile")
        if self._handler is not None:
            self.removeHandler(self._handler)
        if logfile:
            handler = logging.FileHandler(logfile)
        else:
            handler = logging.StreamHandler()

        if level > logging.DEBUG:
            LOG_FORMAT = (
                "[%(asctime)s] %(levelname)s in " "%(module)s.%(funcName)s: %(message)s"
            )
        else:
            LOG_FORMAT = (
                "-" * 27
                + "[%(asctime)s]"
                + "-" * 28
                + "\n"
                + "%(levelname)s in %(module)s.%(funcName)s "
                + "[%(pathname)s:%(lineno)d]:\n"
                + "%(message)s\n"
                + "-" * 80
            )

        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))

        self.setLevel(level)
        self.addHandler(handler)
        self._handler = handler


logger = Logger()
