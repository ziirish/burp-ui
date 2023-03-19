import os

import pytest
from flask import url_for

from burpui.app import create_app


@pytest.fixture
def app():
    conf = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../configs/test2.cfg"
    )
    bui = create_app(logfile="/dev/null", gunicorn=False, unittest=True)
    bui.setup(conf, True)
    bui.config["TESTING"] = True
    bui.config["LOGIN_DISABLED"] = True
    bui.config["CFG"] = conf
    bui.config["SECRET_KEY"] = "nyan"
    bui.login_manager.init_app(bui)
    return bui


def login(client, username, password):
    return client.post(
        url_for("view.login"),
        data=dict(username=username, password=password, language="en"),
        follow_redirects=True,
    )


def test_no_clients(client):
    response = client.get(url_for("api.clients_stats"))
    assert response.json["message"] == "Cannot contact burp server at 127.0.0.1:9999"
    assert response.status_code == 500


def test_server_config_parsing(client, app):
    login(client, "admin", "admin")
    response = client.get(url_for("api.server_settings"))
    asse = dict(
        (
            (
                "results",
                {
                    "common": [],
                    "boolean": [],
                    "integer": [],
                    "multi": [],
                    "pair": [],
                    "includes": [],
                    "includes_ext": [],
                    "hierarchy": [
                        {
                            "children": [],
                            "title": "null",
                            "dir": "/dev",
                            "full": "/dev/null",
                            "name": "null",
                            "parent": None,
                        }
                    ],
                    "raw": "",
                },
            ),
            ("boolean", app.client.get_parser_attr("boolean_srv")),
            ("string", app.client.get_parser_attr("string_srv")),
            ("integer", app.client.get_parser_attr("integer_srv")),
            ("multi", app.client.get_parser_attr("multi_srv")),
            ("pair", app.client.get_parser_attr("pair_associations")),
            ("advanced", app.client.get_parser_attr("advanced_type")),
            ("server_doc", app.client.get_parser_attr("doc")),
            ("suggest", app.client.get_parser_attr("values")),
            ("placeholders", app.client.get_parser_attr("placeholders")),
            ("defaults", app.client.get_parser_attr("defaults")),
        )
    )
    assert response.json == asse


def test_client_config_parsing(client, app):
    login(client, "admin", "admin")
    response = client.get(url_for("api.client_settings", client="toto"))
    asse = dict(
        (
            (
                "results",
                {
                    "common": [],
                    "boolean": [],
                    "integer": [],
                    "multi": [],
                    "includes": [],
                    "includes_ext": [],
                    "hierarchy": [],
                    "templates": [],
                    "raw": None,
                },
            ),
            ("boolean", app.client.get_parser_attr("boolean_cli")),
            ("string", app.client.get_parser_attr("string_cli")),
            ("integer", app.client.get_parser_attr("integer_cli")),
            ("multi", app.client.get_parser_attr("multi_cli")),
            ("server_doc", app.client.get_parser_attr("doc")),
            ("suggest", app.client.get_parser_attr("values")),
            ("placeholders", app.client.get_parser_attr("placeholders")),
            ("defaults", app.client.get_parser_attr("defaults")),
        )
    )
    assert response.json == asse


def test_restore(client):
    response = client.post(
        url_for("api.restore", name="dummy", backup=1), data=dict(strip=False)
    )
    assert response.status_code == 400


def test_running_clients(client):
    response = client.get(url_for("api.running_clients"))
    assert response.json == []


def test_live_rendering(client):
    response = client.get(url_for("api.counters", client="toto"))
    assert response.status_code == 404
    response = client.get(url_for("api.counters"))
    assert response.status_code == 400


def test_servers_json(client):
    response = client.get(url_for("api.servers_stats"))
    assert response.json == []


def test_live(client):
    response = client.get(url_for("api.live"))
    assert response.json == []


def test_running(client):
    response = client.get(url_for("api.running_backup"))
    assert response.json == dict(running=False)


def test_client_tree(client):
    response = client.get(url_for("api.client_tree", name="toto", backup=1))
    assert response.json["message"] == "Cannot contact burp server at 127.0.0.1:9999"
    assert response.status_code == 500


def test_clients_report_json(client):
    response = client.get(url_for("api.clients_report"))
    assert response.json["message"] == "Cannot contact burp server at 127.0.0.1:9999"
    assert response.status_code == 500


def test_client_stat_json(client):
    response = client.get(url_for("api.client_stats", name="toto"))
    assert response.json["message"] == "Cannot contact burp server at 127.0.0.1:9999"
    assert response.status_code == 500
    response = client.get(url_for("api.client_stats", name="toto", backup=1))
    assert response.json["message"] == "Cannot contact burp server at 127.0.0.1:9999"
    assert response.status_code == 500


def test_client_json(client):
    response = client.get(url_for("api.client_report", name="toto"))
    assert response.json["message"] == "Cannot contact burp server at 127.0.0.1:9999"
    assert response.status_code == 500
