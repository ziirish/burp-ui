import os

import pytest
from flask import url_for

from burpui.app import create_app


@pytest.fixture
def app():
    conf = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../configs/test6.cfg"
    )
    bui = create_app(conf, False, "/dev/null", gunicorn=False, unittest=True)
    bui.config["TESTING"] = True
    bui.config["LIVESERVER_PORT"] = 5001
    bui.config["WTF_CSRF_ENABLED"] = False
    bui.client.port = 9999
    return bui


def login(client, username, password, headers=None):
    return client.post(
        url_for("view.login"),
        data=dict(username=username, password=password, language="en"),
        headers=headers,
        follow_redirects=True,
    )


def logout(client):
    return client.get(url_for("view.logout"), follow_redirects=True)


def test_login_ko(client):
    rv = login(client, "admin", "toto")
    assert "Wrong username or password" in rv.data.decode("utf-8")
    logout(client)


def test_config_render(client):
    login(client, "admin", "admin")
    response = client.get(url_for("view.settings"))
    assert "Burp Server Configuration" in response.data.decode("utf-8")
    logout(client)


def test_admin_api(client):
    login(client, "admin", "admin")
    response = client.get(url_for("api.auth_users"))
    response2 = client.get(url_for("api.auth_backends"))
    assert sorted(response.json, key=lambda k: k["name"]) == sorted(
        [
            {"id": "admin", "name": "admin", "backend": "BASIC:AUTH"},
            {"id": "user1", "name": "user1", "backend": "BASIC:AUTH"},
        ],
        key=lambda k: k["name"],
    )
    assert sorted(response2.json, key=lambda k: k["name"]) == sorted(
        [
            {
                "add": True,
                "del": True,
                "name": "BASIC:AUTH",
                "description": "Uses the Burp-UI configuration file to load its rules.",
                "priority": 100,
                "type": "authentication",
                "mod": True,
            }
        ],
        key=lambda k: k["name"],
    )


def test_change_password(client):
    login(client, "user1", "password")
    response = client.post(
        url_for("api.auth_users", name="user1"),
        data={"backend": "BASIC:AUTH", "old_password": "plop", "password": "toto"},
        headers={"X-Language": "en"},
    )
    assert response.status_code == 200


def test_config_render_ko(client):
    login(client, "user1", "password")
    response = client.get(url_for("view.settings"))
    assert response.status_code == 403
    logout(client)


def test_cli_settings_ko(client):
    login(client, "user1", "password")
    response = client.get(url_for("api.client_settings", client="toto"))
    assert response.status_code == 403
    logout(client)


def test_api_403(client):
    response = client.get(
        url_for("api.client_settings", client="toto"), headers={"X-From-UI": True}
    )
    assert response.status_code == 403


def test_api_401(client):
    response = client.get(url_for("api.client_settings", client="toto"))
    assert response.status_code == 401
