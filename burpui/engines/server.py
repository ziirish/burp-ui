# -*- coding: utf8 -*-
"""
.. module:: burpui.server
    :platform: Unix
    :synopsis: Burp-UI server module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import logging  # noqa
import os
import re
import sys
import warnings
from datetime import timedelta

from flask import Flask

from ..config import config
from ..misc.acl.handler import ACLloader
from ..misc.audit.handler import BUIauditLoader
from ..misc.auth.handler import UserAuthHandler
from ..plugins import PluginManager
from ..tools.logging import logger

BUI_DEFAULTS = {
    "Global": {
        "port": 0,
        "bind": "",
        "ssl": False,
        "sslcert": "",
        "sslkey": "",
        "backend": "burp2",
        "auth": ["basic"],
        "acl": ["none"],
        "audit": ["none"],
        "prefix": "",
        "plugins": [],
        "demo": False,
        "dsn": "",
        "piwik_url": "",
        "piwik_script": "piwik.php",
        "piwik_id": 0,
    },
    "UI": {
        "refresh": 180,
        "liverefresh": 5,
        "ignore_labels": ["color:.*"],
        "format_labels": [r"s/^os:\s*//"],
        "default_strip": 0,
    },
    "Security": {
        "scookie": True,
        "appsecret": "random",
        "cookietime": 14,
        "sessiontime": 5,
    },
    "Production": {
        "storage": "",
        "session": "",
        "cache": "",
        "redis": "",
        "celery": False,
        "database": "",
        "limiter": False,
        "ratio": "60/minute",
        "num_proxies": 0,
        "proxy_fix_args": "{'x_proto': {num_proxies}, 'x_for': {num_proxies}, 'x_host': {num_proxies}, 'x_prefix': {num_proxies}}",
    },
    "WebSocket": {
        "enabled": True,
        "embedded": False,
        "broker": "redis",
        "url": "",
        "debug": False,
    },
    "Experimental": {
        "noserverrestore": False,
    },
}


class BUIServer(Flask):
    """
    The :class:`burpui.engines.server.BUIServer` class provides the ``Burp-UI`` server.
    """

    gunicorn = False

    def __init__(self):
        """The :class:`burpui.engines.server.BUIServer` class provides the ``Burp-UI``
        server.

        :param app: The Flask application to launch
        """
        super(BUIServer, self).__init__("burpui")
        self.init = False
        # We cannot override the Flask's logger so we use our own
        self._logger = logger
        self._logger.disabled = True
        self.conf = config
        # switch the flask config with our magic config object
        self.conf.update(self.config)
        self.config = self.conf

    def enable_logger(self, enable=True):
        """Enable or disable the logger"""
        self._logger.disabled = not enable

    @property
    def logger(self):
        """
        :rtype: :class:`logging.Logger`
        """
        return self._logger

    def setup(self, conf=None, unittest=False, cli=False):
        """The :func:`burpui.engines.server.BUIServer.setup` functions is used to setup
        the whole server by parsing the configuration file and loading the
        different backends.

        :param conf: Path to a configuration file
        :type conf: str

        :param unittest: Whether we are unittesting or not (used to avoid burp2
                         strict requirements checks)
        :type unittest: bool

        :param cli: Whether we are in cli mode or not
        :type cli: bool
        """
        self.sslcontext = None
        if not conf:
            conf = self.config["CFG"]

        if not conf:
            raise IOError("No configuration file found")

        # Raise exception if errors are encountered during parsing
        self.conf.parse(conf, BUI_DEFAULTS)
        self.conf.default_section("Global")

        self.config["BUI_BIND"] = self.conf.safe_get("bind")
        self.config["BUI_PORT"] = self.conf.safe_get("port", "integer")
        if self.config["BUI_BIND"] or self.config["BUI_PORT"]:
            warnings.warn(
                "The 'bind' and 'port' configuration options are now deprecated and "
                "have no effect on burp-ui anymore unless you use the 'burp-ui-legacy' "
                "command.\n"
                "Please use the '-h' and '-p' command line flags instead.",
                UserWarning,
            )
        self.demo = self.config["BUI_DEMO"] = self.conf.safe_get("demo", "boolean")
        self.config["BUI_DSN"] = self.conf.safe_get("dsn")
        self.config["BUI_PIWIK_URL"] = self.conf.safe_get("piwik_url")
        self.config["BUI_PIWIK_SCRIPT"] = self.conf.safe_get("piwik_script")
        self.config["BUI_PIWIK_ID"] = self.conf.safe_get("piwik_id", "integer")
        self.config["BACKEND"] = self.conf.safe_get("backend")
        # FIXME: this sucks, we need to test the burp2 backend as well!
        if unittest:
            self.config["BACKEND"] = "burp1"
        self.config["STANDALONE"] = self.config["BACKEND"] != "multi"
        self.config["BUI_SSL"] = self.conf.safe_get("ssl", "boolean")
        self.config["BUI_SSLCERT"] = self.conf.safe_get("sslcert")
        self.config["BUI_SSLKEY"] = self.conf.safe_get("sslkey")
        if (
            self.config["BUI_SSL"]
            or self.config["BUI_SSLCERT"]
            or self.config["BUI_SSLKEY"]
        ):
            warnings.warn(
                "The 'ssl', 'sslcert' and 'sslkey' configuration options are deprecated "
                "as of v0.4.0. It means they have no effect on burp-ui anymore. "
                "If you really need them, consider using the 'burp-ui-legacy' command "
                "instead.",
                UserWarning,
            )

        # TODO: remove in 0.8.0
        old_prefix = self.conf.safe_get("prefix")

        self.plugins = self.config["BUI_PLUGINS"] = self.conf.safe_get(
            "plugins", "string_lower_list"
        )
        if len(self.plugins) == 1 and self.plugins[0] == "none":
            self.plugins = self.config["BUI_PLUGINS"] = []

        self.auth = self.config["BUI_AUTH"] = self.conf.safe_get(
            "auth", "string_lower_list"
        )

        self.audit_backends = self.config["BUI_AUDIT"] = self.conf.safe_get(
            "audit", "string_lower_list"
        )

        # UI options
        self.config["REFRESH"] = self.conf.safe_get("refresh", "integer", "UI")
        self.config["LIVEREFRESH"] = self.conf.safe_get("liverefresh", "integer", "UI")
        self.config["DEFAULT_STRIP"] = self.conf.safe_get(
            "default_strip", "integer", "UI"
        )
        self.ignore_labels = self.conf.safe_get("ignore_labels", "force_list", "UI")
        format_labels = self.conf.safe_get("format_labels", "force_list", "UI")
        self.format_labels = []
        for format_label in format_labels:
            search = re.search(
                r"^s(?P<separator>.)(?P<regex>.*?)(?P=separator)(?P<replace>.*?)(?P=separator)$",
                format_label,
            )
            if search:
                self.format_labels.append(
                    (search.group("regex"), search.group("replace"))
                )

        # Production options
        self.storage = self.config["BUI_STORAGE"] = self.conf.safe_get(
            "storage", section="Production"
        )
        self.cache_db = self.config["BUI_CACHE_DB"] = self.conf.safe_get(
            "cache", section="Production"
        )
        self.session_db = self.config["BUI_SESSION_DB"] = self.conf.safe_get(
            "session", section="Production"
        )
        self.redis = self.config["BUI_REDIS"] = self.conf.safe_get(
            "redis", section="Production"
        )
        self.limiter = self.config["BUI_LIMITER"] = self.conf.safe_get(
            "limiter", "boolean_or_string", section="Production"
        )
        if isinstance(self.limiter, bool) and not self.limiter:
            self.limiter = self.config["BUI_LIMITER"] = "none"
        self.config["BUI_RATIO"] = self.conf.safe_get("ratio", section="Production")
        self.use_celery = self.config["BUI_CELERY"] = self.conf.safe_get(
            "celery", "boolean_or_string", section="Production"
        )
        self.database = self.config["SQLALCHEMY_DATABASE_URI"] = self.conf.safe_get(
            "database", "boolean_or_string", section="Production"
        )
        self.config["WITH_LIMIT"] = False
        if isinstance(self.database, bool):
            self.config["WITH_SQL"] = self.database
        else:
            self.config["WITH_SQL"] = self.database and self.database.lower() != "none"
        if isinstance(self.use_celery, bool):
            self.config["WITH_CELERY"] = self.use_celery
        else:
            self.config["WITH_CELERY"] = (
                self.use_celery and self.use_celery.lower() != "none"
            )
        self.config["NUM_PROXIES"] = self.conf.safe_get(
            "num_proxies", "integer", section="Production"
        )
        self.config["PROXY_FIX_ARGS"] = self.conf.safe_get(
            "proxy_fix_args", section="Production"
        )
        prefix = self.conf.safe_get("prefix", section="Production")
        if not prefix and old_prefix:
            # TODO: remove in a later version
            prefix = old_prefix
            warnings.warn(
                "The 'prefix' option has been moved from the '[Global]' section to the "
                "'[Production]' section",
                UserWarning,
            )
        if prefix and not prefix.startswith("/"):
            if prefix.lower() != "none":
                self.logger.warning("'prefix' must start with a '/'!")
            prefix = ""
        self.config["BUI_PREFIX"] = prefix

        # WebSocket options
        self.ws_enabled = self.config["WS_ENABLED"] = self.conf.safe_get(
            "enabled", "boolean", section="WebSocket"
        )
        self.config["WITH_WS"] = self.conf.safe_get(
            "embedded", "boolean", section="WebSocket"
        )
        self.ws_broker = self.config["BUI_WS_BROKER"] = self.conf.safe_get(
            "broker", "boolean_or_string", section="WebSocket"
        )
        self.config["WS_DEBUG"] = self.conf.safe_get(
            "debug", "boolean", section="WebSocket"
        )
        self.config["WS_URL"] = self.conf.safe_get("url", section="WebSocket")
        if self.config.get("WS_URL", "").lower() == "none" or self.config.get(
            "WITH_WS", False
        ):
            self.config["WS_URL"] = None

        # Experimental options
        self.noserverrestore = self.conf.safe_get(
            "noserverrestore", "boolean", section="Experimental"
        )

        # Security options
        self.config["BUI_SCOOKIE"] = self.conf.safe_get(
            "scookie", "boolean", section="Security"
        )
        self.config["SECRET_KEY"] = self.conf.safe_get("appsecret", section="Security")
        days = self.conf.safe_get("cookietime", "integer", section="Security") or 14
        self.config["REMEMBER_COOKIE_DURATION"] = self.config[
            "PERMANENT_SESSION_LIFETIME"
        ] = timedelta(days=days)
        self.config["REMEMBER_COOKIE_NAME"] = "remember_token"
        days = self.conf.safe_get("sessiontime", "integer", section="Security") or 5
        self.config["SESSION_INACTIVE"] = timedelta(days=days)

        self.logger.info("backend: {}".format(self.config["BACKEND"]))
        self.logger.info("listen port: {}".format(self.config["BUI_PORT"]))
        self.logger.info("bind addr: {}".format(self.config["BUI_BIND"]))
        self.logger.info("use ssl: {}".format(self.config["BUI_SSL"]))
        self.logger.info("standalone: {}".format(self.config["STANDALONE"]))
        self.logger.info("sslcert: {}".format(self.config["BUI_SSLCERT"]))
        self.logger.info("sslkey: {}".format(self.config["BUI_SSLKEY"]))
        self.logger.info("prefix: {}".format(self.config["BUI_PREFIX"]))
        self.logger.info("secure cookie: {}".format(self.config["BUI_SCOOKIE"]))
        self.logger.info(
            "cookietime: {}".format(self.config["REMEMBER_COOKIE_DURATION"])
        )
        self.logger.info("session inactive: {}".format(self.config["SESSION_INACTIVE"]))
        self.logger.info("refresh: {}".format(self.config["REFRESH"]))
        self.logger.info("liverefresh: {}".format(self.config["LIVEREFRESH"]))
        self.logger.info("auth: {}".format(self.auth))
        self.logger.info("audit: {}".format(self.audit_backends))
        self.logger.info("celery: {}".format(self.use_celery))
        self.logger.info("redis: {}".format(self.redis))
        self.logger.info("limiter: {}".format(self.limiter))
        self.logger.info("database: {}".format(self.database))
        self.logger.info("with SQL: {}".format(self.config["WITH_SQL"]))
        self.logger.info("with Celery: {}".format(self.config["WITH_CELERY"]))
        self.logger.info("with WebSocket: {}".format(self.config["WITH_WS"]))
        self.logger.info("demo: {}".format(self.config["BUI_DEMO"]))

        self.init = True
        if not cli:
            self.load_modules()

    def load_modules(self, strict=False):
        """Load the extensions"""
        self.plugin_manager = PluginManager(self, self.plugins)
        if self.plugins:
            self.plugin_manager.load_all()

        try:
            self.audit = BUIauditLoader(self)
        except ImportError as exc:
            self.logger.critical(
                f"Import Exception, module '{self.audit_backends}': {exc}"
            )
            raise exc

        if self.auth and "none" not in self.auth:
            try:
                self.uhandler = UserAuthHandler(self)
                for back, err in self.uhandler.errors.items():
                    self.logger.critical(
                        "Unable to load '{}' authentication backend:\n{}".format(
                            back, err
                        )
                    )
            except ImportError as exc:
                self.logger.critical(
                    "Import Exception, module '{0}': {1}".format(self.auth, str(exc))
                )
                raise exc
            self.acl_engine = self.config["BUI_ACL"] = self.conf.safe_get(
                "acl", "string_lower_list"
            )
            self.config["LOGIN_DISABLED"] = False
        else:
            self.config["LOGIN_DISABLED"] = True
            # No login => no ACL
            self.acl_engine = self.config["BUI_ACL"] = ["none"]
            self.auth = self.config["BUI_AUTH"] = "none"

        if self.acl_engine and "none" not in self.acl_engine:
            try:
                self.acl_handler = ACLloader(self)
            except Exception as exc:
                self.logger.critical(
                    "Import Exception, module '{0}': {1}".format(
                        self.acl_engine, str(exc)
                    )
                )
                raise exc
        else:
            self.acl_handler = False

        self.logger.info("acl: {}".format(self.acl_engine))

        backend = self.config["BACKEND"]
        if "." in backend:
            module = backend
        else:
            module = "burpui.misc.backend.{}".format(backend)

        # This is used for development purpose only
        from ..misc.backend.burp1 import Burp as BurpGeneric

        self.client = BurpGeneric(dummy=True)
        self.strict = strict
        try:
            # lookup plugins first
            mod = self.plugin_manager.get_plugin_by_name(backend)
            if mod:
                self.client = mod.Burp(self, conf=self.conf)
            else:
                # Try to load submodules from our current environment
                # first
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                mod = __import__(module, fromlist=["Burp"])
                self.client = mod.Burp(self, conf=self.conf)
        except Exception as exc:
            msg = "Failed loading backend {0}: {1}".format(module, str(exc))
            if strict:
                self.logger.critical(msg, exc_info=exc, stack_info=True)
                sys.exit(2)
            else:
                exc.args = (msg,)
                raise exc

        self.audit.logger.info("Burp-UI server started")

    @property
    def acl(self):
        """ACL module

        :returns: :class:`burpui.misc.acl.interface.BUIacl`
        """
        if self.acl_engine and "none" not in self.acl_engine:
            # refresh acl to detect config changes
            from ..misc.acl.interface import BUIacl  # noqa

            acl = self.acl_handler.acl  # type: BUIacl
            return acl
        return None

    def get_send_file_max_age(self, name):
        """Provides default cache_timeout for the send_file() functions."""
        if name:
            lname = name.lower()
            extensions = ["js", "css", "woff"]
            for ext in extensions:
                if lname.endswith(".{}".format(ext)):
                    return 3600 * 24 * 30  # 30 days
        return Flask.get_send_file_max_age(self, name)

    def manual_run(self):
        """The :func:`burpui.engines.server.BUIServer.manual_run` functions is used to
        actually launch the ``Burp-UI`` server.

        .. deprecated:: 0.4.0
           You should now run the Flask's run command.
        """
        if not self.init:
            self.setup()

        if self.config["BUI_SSL"]:
            self.sslcontext = (self.config["BUI_SSLCERT"], self.config["BUI_SSLKEY"])

        if self.sslcontext:
            self.config["SSL"] = True
            self.run(
                host=self.config["BUI_BIND"],
                port=self.config["BUI_PORT"],
                debug=self.config["DEBUG"],
                ssl_context=self.sslcontext,
            )
        else:
            self.run(
                host=self.config["BUI_BIND"],
                port=self.config["BUI_PORT"],
                debug=self.config["DEBUG"],
            )
