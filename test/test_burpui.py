#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import os
import json
import unittest
import tempfile

if sys.version_info >= (3, 0):
    from urllib.request import urlopen
else:
    from urllib2 import urlopen

from flask_testing import LiveServerTestCase, TestCase
from flask import url_for

sys.path.append('{0}/..'.format(os.path.join(os.path.dirname(os.path.realpath(__file__)))))

from burpui import init as BUIinit


class BurpuiLiveTestCase(LiveServerTestCase):

    def create_app(self):
        conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../share/burpui/etc/burpui.sample.cfg')
        bui = BUIinit(debug=12, gunicorn=False, unittest=True)
        bui.config['DEBUG'] = False
        bui.config['TESTING'] = True
        bui.config['LOGIN_DISABLED'] = True
        bui.config['LIVESERVER_PORT'] = 5001
        bui.config['CFG'] = conf
        bui.setup(conf)
        bui.login_manager.init_app(bui)
        return bui

    def setUp(self):
        print ('\nBegin Test 1\n')

    def tearDown(self):
        print ('\nTest 1 Finished!\n')

    def test_server_is_up_and_running(self):
        response = urlopen(self.get_server_url())
        self.assertEqual(response.code, 200)


class BurpuiAPIBasicHTTPTestCase(TestCase):

    def setUp(self):
        print ('\nBegin Test 2\n')

    def tearDown(self):
        print ('\nTest 2 Finished!\n')
        os.unlink(self.logfile)

    def create_app(self):
        conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test2.cfg')
        _, self.logfile = tempfile.mkstemp()
        bui = BUIinit(conf, 1, self.logfile, gunicorn=False, unittest=True)
        bui.config['DEBUG'] = False
        return bui

    def test_auth_required(self):
        response = self.client.get(url_for('api.about'))
        self.assert200(response)
        response = self.client.get(url_for('api.counters'))
        self.assert401(response)

    def test_auth_valid(self):
        import base64
        response = self.client.get(
            url_for('api.live'),
            headers={
                'Authorization': 'Basic ' + base64.b64encode(b'admin:admin').decode('utf-8')
            }
        )
        self.assert200(response)


class BurpuiAPITestCase(TestCase):

    def setUp(self):
        print ('\nBegin Test 3\n')

    def tearDown(self):
        print ('\nTest 3 Finished!\n')

    def create_app(self):
        conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test2.cfg')
        bui = BUIinit(gunicorn=False, unittest=True)
        bui.config['TESTING'] = True
        bui.config['LOGIN_DISABLED'] = True
        bui.config['CFG'] = conf
        bui.setup(conf)
        bui.login_manager.init_app(bui)
        self.bui = bui
        return bui

    def test_no_clients(self):
        response = self.client.get(url_for('api.clients_stats'))
        self.assertEquals(json.loads(response.data.decode('utf-8'))['message'], u'Cannot contact burp server at 127.0.0.1:9999')
        self.assert500(response)

    def test_server_config_parsing(self):
        response = self.client.get(url_for('api.server_settings'))
        asse = dict((
                    (
                        u'results',
                        {
                            u'common': [],
                            u'boolean': [],
                            u'integer': [],
                            u'multi': [],
                            u'includes': [],
                            u'includes_ext': [],
                            u'clients': []
                        }
                    ),
                    (u'boolean', self.bui.cli.get_parser_attr('boolean_srv')),
                    (u'string', self.bui.cli.get_parser_attr('string_srv')),
                    (u'integer', self.bui.cli.get_parser_attr('integer_srv')),
                    (u'multi', self.bui.cli.get_parser_attr('multi_srv')),
                    (u'server_doc', self.bui.cli.get_parser_attr('doc')),
                    (u'suggest', self.bui.cli.get_parser_attr('values')),
                    (u'placeholders', self.bui.cli.get_parser_attr('placeholders')),
                    (u'defaults', self.bui.cli.get_parser_attr('defaults'))))
        self.assertEquals(response.json, asse)

    def test_client_config_parsing(self):
        response = self.client.get(url_for('api.client_settings', client='toto'))
        asse = dict((
                    (
                        u'results',
                        {
                            u'common': [],
                            u'boolean': [],
                            u'integer': [],
                            u'multi': [],
                            u'includes': [],
                            u'includes_ext': [],
                            u'clients': []
                        }
                    ),
                    (u'boolean', self.bui.cli.get_parser_attr('boolean_cli')),
                    (u'string', self.bui.cli.get_parser_attr('string_cli')),
                    (u'integer', self.bui.cli.get_parser_attr('integer_cli')),
                    (u'multi', self.bui.cli.get_parser_attr('multi_cli')),
                    (u'server_doc', self.bui.cli.get_parser_attr('doc')),
                    (u'suggest', self.bui.cli.get_parser_attr('values')),
                    (u'placeholders', self.bui.cli.get_parser_attr('placeholders')),
                    (u'defaults', self.bui.cli.get_parser_attr('defaults'))))
        self.assertEquals(response.json, asse)

    def test_restore(self):
        response = self.client.post(url_for('api.restore', name='dummy', backup=1), data=dict(strip=False))
        self.assert400(response)

    def test_running_clients(self):
        response = self.client.get(url_for('api.running_clients'))
        self.assertEquals(response.json, [])

    def test_live_rendering(self):
        response = self.client.get(url_for('api.counters', client='toto'))
        self.assert404(response)
        response = self.client.get(url_for('api.counters'))
        self.assert400(response)

    def test_servers_json(self):
        response = self.client.get(url_for('api.servers_stats'))
        self.assertEquals(response.json, [])

    def test_live(self):
        response = self.client.get(url_for('api.live'))
        self.assertEquals(response.json, [])

    def test_running(self):
        response = self.client.get(url_for('api.running_backup'))
        self.assertEquals(response.json, dict(running=False))

    def test_client_tree(self):
        response = self.client.get(url_for('api.client_tree', name='toto', backup=1))
        self.assertEquals(json.loads(response.data.decode('utf-8'))['message'], u'Cannot contact burp server at 127.0.0.1:9999')
        self.assert500(response)

    def test_clients_report_json(self):
        response = self.client.get(url_for('api.clients_report'))
        self.assertEquals(json.loads(response.data.decode('utf-8'))['message'], u'Cannot contact burp server at 127.0.0.1:9999')
        self.assert500(response)

    def test_client_stat_json(self):
        response = self.client.get(url_for('api.client_stats', name='toto'))
        self.assertEquals(json.loads(response.data.decode('utf-8'))['message'], u'Cannot contact burp server at 127.0.0.1:9999')
        self.assert500(response)
        response = self.client.get(url_for('api.client_stats', name='toto', backup=1))
        self.assertEquals(json.loads(response.data.decode('utf-8'))['message'], u'Cannot contact burp server at 127.0.0.1:9999')
        self.assert500(response)

    def test_client_json(self):
        response = self.client.get(url_for('api.client_report', name='toto'))
        self.assertEquals(json.loads(response.data.decode('utf-8'))['message'], u'Cannot contact burp server at 127.0.0.1:9999')
        self.assert500(response)


class BurpuiRoutesTestCase(TestCase):

    def setUp(self):
        print ('\nBegin Test 4\n')

    def tearDown(self):
        print ('\nTest 4 Finished!\n')

    def create_app(self):
        conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test4.cfg')
        bui = BUIinit(conf, gunicorn=False, unittest=True)
        bui.config['TESTING'] = True
        bui.config['LOGIN_DISABLED'] = True
        bui.config['LIVESERVER_PORT'] = 5001
        bui.setup(conf)
        bui.login_manager.init_app(bui)
        return bui

    def test_live_monitor(self):
        response = self.client.get(url_for('view.live_monitor'), follow_redirects=True)
        assert 'Sorry, there are no running backups' in response.data.decode('utf-8')

    def test_get_clients(self):
        response = self.client.get(url_for('api.clients_stats'))
        self.assertEqual(response.json, [{u'state': u'idle', u'last': u'never', u'name': u'testclient', u'phase': None, u'percent': 0}])


class BurpuiLoginTestCase(TestCase):

    def setUp(self):
        print ('\nBegin Test 5\n')

    def tearDown(self):
        print ('\nTest 5 Finished!\n')

    def login(self, username, password):
        return self.client.post(url_for('view.login'), data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def create_app(self):
        conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../share/burpui/etc/burpui.sample.cfg')
        bui = BUIinit(conf, False, None, False, unittest=True)
        bui.config['TESTING'] = True
        bui.config['LIVESERVER_PORT'] = 5001
        bui.config['WTF_CSRF_ENABLED'] = False
        bui.cli.port = 9999
        return bui

    def test_config_render(self):
        rv = self.login('admin', 'admin')
        response = self.client.get(url_for('view.settings'))
        assert 'Burp Configuration' in response.data.decode('utf-8')

    def test_login_ok(self):
        rv = self.login('admin', 'admin')
        assert 'Logged in successfully' in rv.data.decode('utf-8')

    def test_login_ko(self):
        rv = self.login('admin', 'toto')
        assert 'Wrong username or password' in rv.data.decode('utf-8')

    def test_login_no_user(self):
        rv = self.login('toto', 'toto')
        assert 'Wrong username or password' in rv.data.decode('utf-8')


class BurpuiACLTestCase(TestCase):

    def setUp(self):
        print ('\nBegin Test 6\n')

    def tearDown(self):
        print ('\nTest 6 Finished!\n')

    def login(self, username, password):
        return self.client.post(url_for('view.login'), data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def create_app(self):
        conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test6.cfg')
        bui = BUIinit(conf, False, None, False, unittest=True)
        bui.config['TESTING'] = True
        bui.config['LIVESERVER_PORT'] = 5001
        bui.config['WTF_CSRF_ENABLED'] = False
        bui.cli.port = 9999
        return bui

    def test_login_ko(self):
        rv = self.login('admin', 'toto')
        assert 'Wrong username or password' in rv.data.decode('utf-8')

    def test_config_render(self):
        rv = self.login('admin', 'admin')
        response = self.client.get(url_for('view.settings'))
        assert 'Burp Configuration' in response.data.decode('utf-8')

    def test_config_render_ko(self):
        rv = self.login('user1', 'password')
        response = self.client.get(url_for('view.settings'))
        self.assert403(response)

    def test_cli_settings_ko(self):
        rv = self.login('user1', 'password')
        response = self.client.get(url_for('api.client_settings', client='toto'))
        self.assert403(response)


class BurpuiTestInit(TestCase):

    def setUp(self):
        print ('\nBegin Test 7\n')

    def tearDown(self):
        print ('\nTest 7 Finished!\n')
        os.unlink(self.tmpFile)

    def create_app(self):
        conf1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test7-1.cfg')
        conf2 = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test7-2.cfg')
        BUIinit(conf1, False, None, False, unittest=True)
        BUIinit(conf2, False, None, False, unittest=True)
        bui = BUIinit(None, False, None, False, unittest=True)
        bui.config['TESTING'] = True
        bui.config['LIVESERVER_PORT'] = 5001
        bui.config['WTF_CSRF_ENABLED'] = False
        bui.cli.port = 9999
        return bui

    def test_exception(self):
        _, self.tmpFile = tempfile.mkstemp()
        self.assertRaises(IOError, BUIinit, 'thisfileisnotlikelytoexist', True, self.tmpFile, False, unittest=True)
        self.assertRaises(IOError, BUIinit, 'thisfileisnotlikelytoexist', False, self.tmpFile, False, unittest=True)
        conf3 = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test7-3.cfg')
        self.assertRaises(ImportError, BUIinit, conf3, False, None, False, unittest=True)


#class BurpuiAPILoginTestCase(TestCase):
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
#        conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test7.cfg')
#        app.config['TESTING'] = True
#        app.config['LOGIN_DISABLED'] = True
#        app.config['CFG'] = conf
#        bui.setup(conf)
#        return app
#
#    def test_server_config_parsing(self):
#        rv = self.login('toto', 'toto')
#        response = self.client.get(url_for('api.server_settings', server='dummy'))
#        self.assertEquals(response.json, {u'message': u'Sorry, you don\'t have rights to access the setting panel'})
#
#    def test_client_config_parsing(self):
#        rv = self.login('toto', 'toto')
#        response = self.client.get(url_for('api.client_settings', client='toto', server='dummy'))
#        self.assertEquals(response.json, {u'message': u'Sorry, you don\'t have rights to access the setting panel'})
#
#    def test_restore(self):
#        rv = self.login('toto', 'toto')
#        response = self.client.post(url_for('api.restore', name='dummy', backup=1, server='dummy'), data=dict(strip=False))
#        self.assert500(response)


if __name__ == '__main__':
    unittest.main()
