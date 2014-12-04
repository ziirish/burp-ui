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

class BurpuiAPITestCase(TestCase):

	def setUp(self):
		print '\nBegin Test 2\n'
	
	def tearDown(self):
		print '\nTest 2 Finished!\n'
	
	def create_app(self):
		conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test2.cfg')
		app.config['TESTING'] = True
		app.config['LOGIN_DISABLED'] = True
		app.config['CFG'] = conf
		bui.setup(conf)
		login_manager.init_app(app)
		return app

	def test_no_clients(self):
		response = self.client.get('/api/clients.json')
		self.assertEquals(response.json, {u'notif':[[2, u'Cannot contact burp server at 127.0.0.1:9999']]})
	
	def test_config_parsing(self):
		response = self.client.get('/api/server-config')
		self.assertEquals(response.json, dict(results=[],
												 boolean=bui.cli.get_parser_attr('boolean'),
												 string=bui.cli.get_parser_attr('string'),
												 integer=bui.cli.get_parser_attr('integer'),
												 multi=bui.cli.get_parser_attr('multi'),
												 server_doc=bui.cli.get_parser_attr('server_doc'),
												 suggest=bui.cli.get_parser_attr('values_server'),
												 placeholders=bui.cli.get_parser_attr('placeholders'),
												 defaults=bui.cli.get_parser_attr('defaults_server')))
	
	def test_restore(self):
		response = self.client.post('/api/restore/dummy/1', data=dict(strip=False))
		self.assert500(response)
	
	def test_running_clients(self):
		response = self.client.get('/api/running-clients.json')
		self.assertEquals(response.json, dict(results=[]))
	
	def test_live_rendering(self):
		response = self.client.get('/api/render-live-template/toto')
		self.assert404(response)
		response = self.client.get('/api/render-live-template')
		self.assert500(response)

	def test_servers_json(self):
		response = self.client.get('/api/servers.json')
		self.assertEquals(response.json, dict(results=[]))

	def test_live(self):
		response = self.client.get('/api/live.json')
		self.assertEquals(response.json, dict(results=[]))
	
	def test_running(self):
		response = self.client.get('/api/running.json')
		self.assertEquals(response.json, dict(results=False))
	
	def test_client_tree(self):
		response = self.client.get('/api/client-tree.json/toto/1')
		self.assertEquals(response.json, {u'notif':[[2, u'Cannot contact burp server at 127.0.0.1:9999']]})
	
	def test_clients_report_json(self):
		response = self.client.get('/api/clients-report.json')
		self.assertEquals(response.json, {u'notif':[[2, u'Cannot contact burp server at 127.0.0.1:9999']]})
	
	def test_client_stat_json(self):
		response = self.client.get('/api/client-stat.json/toto')
		self.assertEquals(response.json, {u'notif':[[2, u'Cannot contact burp server at 127.0.0.1:9999']]})
		response = self.client.get('/api/client-stat.json/toto/1')
		self.assertEquals(response.json, {u'notif':[[2, u'Cannot contact burp server at 127.0.0.1:9999']]})
	
	def test_client_json(self):
		response = self.client.get('/api/client.json/toto')
		self.assertEquals(response.json, {u'notif':[[2, u'Cannot contact burp server at 127.0.0.1:9999']]})

class BurpuiRoutesTestCase(TestCase):

	def setUp(self):
		print '\nBegin Test 3\n'

	def tearDown(self):
		print '\nTest 3 Finished!\n'

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
	
	def test_config_render(self):
		response = self.client.get('/settings')
		assert 'Burp Configuration' in response.data
	
	def test_live_monitor(self):
		response = self.client.get('/live-monitor', follow_redirects=True)
		assert 'Sorry, there are no running backups' in response.data

class BurpuiLoginTestCase(TestCase):

	def setUp(self):
		print '\nBegin Test 4\n'

	def tearDown(self):
		print '\nTest 4 Finished!\n'

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
		assert 'Logged in successfully' in rv.data
	
	def test_login_ko(self):
		rv = self.login('admin', 'toto')
		assert 'Wrong username or password' in rv.data

	def test_login_no_user(self):
		rv = self.login('toto', 'toto')
		assert 'Wrong username or password' in rv.data

if __name__ == '__main__':
	unittest.main()
