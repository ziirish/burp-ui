import os
from urllib.request import urlopen

import pytest
from flask import url_for

from burpui import create_app


@pytest.fixture(scope="session")
def app():
    conf = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "../../share/burpui/etc/burpui.sample.cfg",
    )
    bui = create_app(debug=12, logfile="/dev/null", gunicorn=False, unittest=True)
    bui.setup(conf, True)
    bui.config["DEBUG"] = False
    bui.config["TESTING"] = True
    bui.config["LOGIN_DISABLED"] = True
    bui.config["LIVESERVER_PORT"] = 5001
    bui.config["CFG"] = conf
    bui.login_manager.init_app(bui)
    return bui


def test_server_is_up_and_running(live_server):
    import errno
    import socket

    try:
        url = url_for("view.home", _external=True)
        response = urlopen(url)
        assert response.code == 200
    except socket.error as exp:
        if exp.errno != errno.ECONNRESET:
            raise
