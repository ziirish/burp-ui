import os
import burpui
import unittest
import urllib2
import pprint
from flask.ext.testing import LiveServerTestCase, TestCase

class BurpuiLiveTestCase(LiveServerTestCase):

	def create_app(self):
		burpui.app.config['TESTING'] = True
		burpui.app.config['LIVESERVER_PORT'] = 5001
		return burpui.app

#	def setUp(self):

#	def tearDown(self):
#		print 'Test Finished!\n'

	def test_server_is_up_and_running(self):
		response = urllib2.urlopen(self.get_server_url())
		self.assertEqual(response.code, 200)

class BurpuiTestCase(TestCase):

	def create_app(self):
		burpui.app.config['TESTING'] = True
		burpui.burpport = 9999
		return burpui.app

	def test_some_json(self):
		response = self.client.get('/api/clients.json')
		self.assertEquals(response.json, dict(results=[]))


if __name__ == '__main__':
	unittest.main()
