# -*- coding: utf8 -*-
import inspect
import os
from collections import OrderedDict
from importlib import import_module

from flask_login import current_user

from .interface import BUIaudit
from .interface import BUIauditLogger as BUIauditLoggerInterface


class BUIauditLoader(BUIaudit):
    """See :class:`burpui.misc.audit.interface.BUIaudit`"""

    def __init__(self, app=None):
        """See :func:`burpui.misc.audit.interface.BUIaudit.__init__`

        :param app: Instance of the app we are running in
        :type app: :class:`burpui.engines.server.BUIServer`
        """
        self.app = app
        backends = []
        self.errors = {}
        if self.app.audit_backends and "none" not in self.app.audit_backends:
            me, _ = os.path.splitext(os.path.basename(__file__))
            back = self.app.audit_backends
            for au in back:
                if au == me:
                    self.app.logger.critical("Recursive import not permitted!")
                    continue
                try:
                    (modpath, _) = __name__.rsplit(".", 1)
                    mod = import_module("." + au, modpath)
                    obj = mod.BUIauditLoader(self.app)
                    backends.append(obj)
                except:
                    import traceback

                    self.errors[au] = traceback.format_exc()
        for name, plugin in self.app.plugin_manager.get_plugins_by_type(
            "audit"
        ).items():
            try:
                obj = plugin.BUIauditLoader(self.app)
                backends.append(obj)
            except:
                import traceback

                self.errors[name] = traceback.format_exc()
        backends.sort(key=lambda x: getattr(x, "priority", -1), reverse=True)
        if (
            not backends
            and self.app.audit_backends
            and "none" not in self.app.audit_backends
        ):
            raise ImportError(
                "No backend found for '{}':\n{}".format(
                    self.app.audit_backends, self.errors
                )
            )
        for name, err in self.errors.items():
            self.app.logger.error(
                "Unable to load module {}:\n{}".format(repr(name), err)
            )
        self.backends = OrderedDict()
        for obj in backends:
            self.backends[obj.name] = obj
        self._logger = BUIauditLogger(self)


class BUIauditLogger(BUIauditLoggerInterface):
    def __init__(self, loader):
        self.loader = loader

    def log(self, level, message, *args, **kwargs):
        server_log = ""
        if "server" in kwargs:
            server = kwargs["server"]
            del kwargs["server"]
            if server:
                server_log = f" on {server}"
        if current_user and not current_user.is_anonymous:
            msg = f"{current_user} -> {message}{server_log}"
        else:
            msg = f"{message}{server_log}"
        caller = ""
        stack = inspect.stack()
        exclude = [
            "audit/interface.py",
            "audit/handler.py",
        ]
        for frame in stack:
            if any(frame.filename.endswith(x) for x in exclude):
                continue
            caller = f"{frame.function} [{frame.filename}:{frame.lineno}]"
            break
        if "extra" in kwargs and isinstance(kwargs["extra"], dict):
            kwargs["extra"]["from"] = caller
        else:
            kwargs["extra"] = {"from": caller}
        for back in self.loader.backends.values():
            back.logger.log(level, msg, *args, **kwargs)
