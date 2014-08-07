#!/usr/bin/env python
# -*- coding: utf8 -*-
import os

from flask import Flask
from flask.ext.login import LoginManager
from burpui.server import Server as BurpUI

app = Flask(__name__)
app.config['CFG'] = os.path.join(app.root_path, 'burpui.cfg')
app.secret_key = 'VpgOXNXAgcO81xFPyWj07ppN6kExNZeCDRShseNzFKV7ZCgmW2/eLn6xSlt7pYAVBj12zx2Vv9Kw3Q3jd1266A=='
app.jinja_env.globals.update(isinstance=isinstance,list=list)

bui = BurpUI(app)

login_manager = LoginManager()
login_manager.init_app(app)

import burpui.routes
