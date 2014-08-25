#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import os
import unittest
import urllib2
import pprint
from flask.ext.testing import LiveServerTestCase, TestCase

sys.path.append('{0}/..'.format(os.path.join(os.path.dirname(os.path.realpath(__file__)))))

from burpui import app, bui

class BurpuiLiveTestCase(LiveServerTestCase):

	def create_app(self):
		conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../burpui.cfg')
		app.config['TESTING'] = True
		app.config['LIVESERVER_PORT'] = 5001
		app.config['CFG'] = conf
		bui.setup(conf)
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
		app.config['TESTING'] = True
		bui.cli.port = 9999
		return app

	def test_some_json(self):
		response = self.client.get('/api/clients.json')
		self.assertEquals(response.json, dict(results=[]))


if __name__ == '__main__':
	unittest.main()
