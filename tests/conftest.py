#!/usr/bin/env python
# -*- coding: utf8 -*-
import pytest
import sys
import os

sys.path.append('{0}/..'.format(os.path.join(os.path.dirname(os.path.realpath(__file__)))))

from burpui import create_app as BUIinit


@pytest.fixture
def app():
    conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'configs/test_api_prefs.cfg')
    bui = BUIinit(conf, logfile='/dev/null', gunicorn=False, unittest=True)
    bui.config['TESTING'] = True
    bui.config['SECRET_KEY'] = 'nyan'
    with bui.app_context():
        from burpui.ext.sql import db
        from burpui.models import lazy_loading
        lazy_loading()
        db.create_all()
        db.session.commit()
    yield bui
