import os
import pytest

from flask import url_for

from burpui.app import create_app


def mock_status(query='\n', timeout=None, agent=None):
    answers = {
        '': ['testclient  2   i   0'],
        '\n': ['testclient  2   i   0'],
    }
    return answers.get(query, [])


@pytest.fixture
def app(mocker):
    mocker.patch('socket.socket')
    conf = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../configs/test4.cfg')
    bui = create_app(conf, logfile='/dev/null', gunicorn=False, unittest=True)
    bui.setup(conf, True)
    bui.config['TESTING'] = True
    bui.config['LIVESERVER_PORT'] = 5001
    bui.config['SECRET_KEY'] = 'toto'
    bui.config['WTF_CSRF_ENABLED'] = False
    bui.login_manager.init_app(bui)
    return bui


def login(client, username, password):
    return client.post(url_for('view.login'), data=dict(
        username=username,
        password=password,
        language='en'
    ), follow_redirects=True)


def test_get_clients(client, mocker):
    mocker.patch('burpui.misc.backend.burp1.Burp.status', side_effect=mock_status)
    login(client, 'admin', 'admin')
    response = client.get(url_for('api.clients_stats'))
    assert sorted(response.json, key=lambda k: k['name']) == sorted([{u'state': u'idle', u'last': u'never', u'name': u'testclient', u'phase': None, u'percent': 0, u'labels': []}], key=lambda k: k['name'])


#    def test_live_monitor(self):
#        with patch('burpui.misc.backend.burp1.Burp.status', side_effect=mock_status):
#            response = self.client.get(url_for('view.live_monitor'), follow_redirects=True)
#            assert 'Sorry, there are no running backups' in response.data.decode('utf-8')
