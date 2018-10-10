#!/usr/bin/env python
# -*- coding: utf8 -*-
import pytest

from flask import url_for

def login(client, username, password):
    url = url_for('view.login')
    return client.post(url, data=dict(
        username=username,
        password=password,
        language='en'
    ), follow_redirects=True)


def test_prefs_hide(client):
    rv = login(client, 'admin', 'admin')
    URL = url_for('api.prefs_ui_hide')
    response = client.get(URL)
    assert response.json == []
    response = client.put(URL, data=dict(name='test', agent=None))
    assert response.json == {'client': 'test', 'server': None}
