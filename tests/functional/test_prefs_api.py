#!/usr/bin/env python
# -*- coding: utf8 -*-
from flask import url_for


def login(client, username, password):
    url = url_for('view.login')
    return client.post(url, data=dict(
        username=username,
        password=password,
        language='en'
    ), follow_redirects=True)


def logout(client):
    return client.get('view.logout', follow_redirects=True)


def test_prefs_hide(client, app):
    login(client, 'admin', 'admin')
    URL = url_for('api.prefs_ui_hide')

    response = client.get(URL)
    assert response.json == []

    response = client.put(URL, data=dict(name='test', agent=None))
    assert response.status_code == 201
    assert response.json == {'client': 'test', 'server': None}

    response = client.put(URL, data=dict(name='test', agent=None))
    assert response.status_code == 200

    response = client.delete(URL, data=dict(name='test', agent=None))
    assert response.status_code == 204

    response = client.get(URL)
    assert response.json == []

    app.config['WITH_SQL'] = False
    response = client.get(URL)
    assert response.json == []
    response = client.put(URL, data=dict(name='test', agent=None))
    assert response.status_code == 200
    assert response.json == []
    app.config['WITH_SQL'] = True

    logout(client)


def test_prefs(client, app):
    login(client, 'admin', 'admin')
    URL = url_for('api.prefs_ui')

    response = client.get(URL)
    assert response.json == {'language': 'en', 'dateFormat': None, 'pageLength': None}

    response = client.put(URL, data=dict(language='fr', dateFormat='llll', pageLength=25))
    assert response.status_code == 201
    assert response.json == {'language': 'fr', 'dateFormat': 'llll', 'pageLength': 25}

    response = client.post(URL, data=dict(language='en'))
    assert response.status_code == 200
    assert response.json == {'language': 'en'}

    response = client.delete(URL, data=dict(pageLength=25))
    assert response.status_code == 200
    assert response.json == {'language': 'en', 'dateFormat': 'llll', 'pageLength': None}

    logout(client)
