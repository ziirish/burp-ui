#!/usr/bin/env python
# -*- coding: utf8 -*-
import pytest
import sys
import os
import tempfile
import shutil

sys.path.append('{0}/..'.format(os.path.join(os.path.dirname(os.path.realpath(__file__)))))

from burpui import create_app as BUIinit  # noqa
from burpui.misc.parser.burp1 import Parser  # noqa

PWD = os.path.dirname(os.path.realpath(__file__))

@pytest.fixture
def app():
    conf = os.path.join(PWD, 'configs/test_api_prefs.cfg')
    bui = BUIinit(conf, logfile='/dev/null', gunicorn=False, unittest=True)
    bui.config['TESTING'] = True
    bui.config['SECRET_KEY'] = 'nyan'
    bui.config['WTF_CSRF_ENABLED'] = False
    with bui.app_context():
        from burpui.ext.sql import db
        from burpui.models import lazy_loading
        lazy_loading()
        db.create_all()
        db.session.commit()
    yield bui

@pytest.fixture
def parser(app):
    tmpdir = tempfile.mkdtemp()
    shutil.copytree(os.path.join(PWD, 'burp'), tmpdir)
    confsrv = os.path.join(tmpdir, 'burp-server.conf')
    confcli = os.path.join(tmpdir, 'burp.conf')
    parser = Parser(app)
    parser.init_app(confsrv, confcli)

    yield parser

    shutil.rmtree(tmpdir)
