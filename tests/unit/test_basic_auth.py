import os
import pytest
import tempfile

from flask import url_for

from burpui.app import create_app


@pytest.fixture
def app():
    conf = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../configs/test2.cfg"
    )
    _, logfile = tempfile.mkstemp()
    bui = create_app(conf, 1, logfile, gunicorn=False, unittest=True)
    bui.config["DEBUG"] = False
    return bui


def test_auth_required(client):
    response = client.get(url_for("api.about"))
    assert response.status_code == 200
    response = client.get(url_for("api.counters"))
    assert response.status_code == 401


def test_auth_valid(client):
    import base64

    response = client.get(
        url_for("api.live"),
        headers={
            "Authorization": "Basic " + base64.b64encode(b"admin:admin").decode("utf-8")
        },
    )
    assert response.status_code == 200
