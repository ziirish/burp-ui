import os
import pytest

from flask import url_for

from burpui.app import create_app


@pytest.fixture
def app():
    conf = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "../../share/burpui/etc/burpui.sample.cfg",
    )
    bui = create_app(conf, False, "/dev/null", gunicorn=False, unittest=True)
    bui.config["TESTING"] = True
    bui.config["LIVESERVER_PORT"] = 5001
    bui.config["WTF_CSRF_ENABLED"] = False
    bui.client.port = 9999
    return bui


def login(client, username, password):
    return client.post(
        url_for("view.login"),
        data=dict(username=username, password=password, language="en"),
        follow_redirects=True,
    )


def test_config_render(client):
    login(client, "admin", "admin")
    response = client.get(url_for("view.settings"))
    assert "Burp Server Configuration" in response.data.decode("utf-8")


def test_login_ok(client):
    rv = login(client, "admin", "admin")
    assert "Logged in successfully" in rv.data.decode("utf-8")


def test_login_ko(client):
    rv = login(client, "admin", "toto")
    assert "Wrong username or password" in rv.data.decode("utf-8")


def test_login_no_user(client):
    rv = login(client, "toto", "toto")
    assert "Wrong username or password" in rv.data.decode("utf-8")
