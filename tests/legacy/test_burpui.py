#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import json
import unittest
import tempfile
import mockredis

# from flask_testing import LiveServerTestCase, TestCase
from mock import patch
from flask import url_for

from burpui import create_app as BUIinit


# class BurpuiTestInit(TestCase):
#
#     def setUp(self):
#         print ('\nBegin Test 7\n')
#
#     def tearDown(self):
#         print ('\nTest 7 Finished!\n')
#         os.unlink(self.tmpFile)
#         if os.path.exists('this-file-should-not-exist'):
#             os.rmdir('this-file-should-not-exist')
#
#     def create_app(self):
#         kwargs = {'verbose': 0, 'logfile': '/dev/null', 'gunicorn': False, 'unittest': True}
#         root = os.path.dirname(os.path.realpath(__file__))
#         conf1 = os.path.join(root, 'configs/test7-1.cfg')
#         conf2 = os.path.join(root, 'configs/test7-2.cfg')
#         conf4 = os.path.join(root, 'configs/test7-4.cfg')
#         conf5 = os.path.join(root, 'configs/test7-5.cfg')
#         BUIinit(conf1, **kwargs)
#         BUIinit(conf2, **kwargs)
#         BUIinit(conf4, **kwargs)
#         BUIinit(conf5, **kwargs)
#         bui = BUIinit(None, **kwargs)
#         bui.config['TESTING'] = True
#         bui.config['LIVESERVER_PORT'] = 5001
#         bui.config['WTF_CSRF_ENABLED'] = False
#         bui.client.port = 9999
#         return bui
#
#     def test_exception(self):
#         _, self.tmpFile = tempfile.mkstemp()
#         self.assertRaises(IOError, BUIinit, 'thisfileisnotlikelytoexist', True, self.tmpFile, gunicorn=False, unittest=True)
#         self.assertRaises(IOError, BUIinit, 'thisfileisnotlikelytoexist', False, self.tmpFile, gunicorn=False, unittest=True)
#         conf3 = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'configs/test7-3.cfg')
#         self.assertRaises(ImportError, BUIinit, conf3, 12, '/dev/null', gunicorn=False, unittest=True)


# class BurpuiAPILoginTestCase(TestCase):
#
#    def setUp(self):
#        print ('\nBegin Test 7\n')
#
#    def tearDown(self):
#        print ('\nTest 7 Finished!\n')
#
#    def login(self, username, password):
#        return self.client.post(url_for('view.login'), data=dict(
#            username=username,
#            password=password
#        ), follow_redirects=True)
#
#    def create_app(self):
#        conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'configs/test7.cfg')
#        app.config['TESTING'] = True
#        app.config['LOGIN_DISABLED'] = True
#        app.config['CFG'] = conf
#        bui.setup(conf, True)
#        return app
#
#    def test_server_config_parsing(self):
#        rv = self.login('toto', 'toto')
#        response = self.client.get(url_for('api.server_settings', server='dummy'))
#        self.assertEqual(response.json, {u'message': u'Sorry, you don\'t have rights to access the setting panel'})
#
#    def test_client_config_parsing(self):
#        rv = self.login('toto', 'toto')
#        response = self.client.get(url_for('api.client_settings', client='toto', server='dummy'))
#        self.assertEqual(response.json, {u'message': u'Sorry, you don\'t have rights to access the setting panel'})
#
#    def test_restore(self):
#        rv = self.login('toto', 'toto')
#        response = self.client.post(url_for('api.restore', name='dummy', backup=1, server='dummy'), data=dict(strip=False))
#        self.assert500(response)


if __name__ == '__main__':
    unittest.main()
