#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import os
import unittest
import urllib2
import pprint
from flask.ext.testing import LiveServerTestCase, TestCase

sys.path.append('{0}/..'.format(os.path.join(os.path.dirname(os.path.realpath(__file__)))))

from burpui import app, bui, login_manager, init as BUIinit

class BurpuiLiveTestCase(LiveServerTestCase):

	def create_app(self):
		conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../burpui.cfg')
		app.config['TESTING'] = True
		app.config['LOGIN_DISABLED'] = True
		app.config['LIVESERVER_PORT'] = 5001
		app.config['CFG'] = conf
		bui.setup(conf)
		login_manager.init_app(app)
		return app

	def setUp(self):
		print '\nBegin Test 1\n'

	def tearDown(self):
		print '\nTest 1 Finished!\n'

	def test_server_is_up_and_running(self):
		response = urllib2.urlopen(self.get_server_url())
		self.assertEqual(response.code, 200)

class BurpuiTestCase(TestCase):

	def setUp(self):
		print '\nBegin Test 2\n'

	def tearDown(self):
		print '\nTest 2 Finished!\n'

	def create_app(self):
		conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../burpui.cfg')
		app.config['TESTING'] = True
		app.config['LOGIN_DISABLED'] = True
		app.config['LIVESERVER_PORT'] = 5001
		app.config['CFG'] = conf
		bui.setup(conf)
		bui.cli.port = 9999
		login_manager.init_app(app)
		return app

	def test_no_clients(self):
		response = self.client.get('/api/clients.json')
		self.assertNotEquals(response.json, dict(results=[]))

class BurpuiLoginTestCase(TestCase):

	def setUp(self):
		print '\nBegin Test 3\n'

	def tearDown(self):
		print '\nTest 3 Finished!\n'

	def login(self, username, password):
		return self.client.post('/login', data=dict(
			username=username,
			password=password
		), follow_redirects=True)

	def create_app(self):
		conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../burpui.cfg')
		BUIinit(conf, False, False)
		app.config['TESTING'] = True
		app.config['LIVESERVER_PORT'] = 5001
		app.config['WTF_CSRF_ENABLED'] = False
		bui.cli.port = 9999
		login_manager.init_app(app)
		return app

	def test_login_ok(self):
		rv = self.login('admin', 'admin')
		print rv.data
		assert 'Logged in successfully' in rv.data
	
	def test_login_ko(self):
		rv = self.login('admin', 'toto')
		assert 'Wrong username or password' in rv.data

	def test_login_no_user(self):
		rv = self.login('toto', 'toto')
		assert 'Wrong username or password' in rv.data

if __name__ == '__main__':
	unittest.main()
