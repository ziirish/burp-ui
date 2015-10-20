# -*- coding: utf8 -*-
"""
.. module:: burpui.api
   :platform: Unix
   :synopsis: Burp-UI api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>


"""
import os
import re
import sys

from flask.ext.restful import Api
from importlib import import_module


class ApiWrapper(Api):
    bui = None
    loaded = False

    def init_bui(self, bui):
        self.bui = bui

    def load_all(self):
        # hack to automatically import api modules
        if not self.loaded:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            self.loaded = True
            for f in os.listdir(__path__[0]):
                name, ext = os.path.splitext(f)
                if (os.path.isfile(os.path.join(__path__[0], f)) and
                        ext == '.py' and
                        name not in ['__init__', '.', '..']):
                    mod = '.'+name
                    import_module(mod, 'burpui.api')


api = ApiWrapper()
api.load_all()
