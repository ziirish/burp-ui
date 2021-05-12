import os
import pytest
import mockredis

from flask import url_for

from burpui.app import create_app


class MyMockRedis(mockredis.MockRedis):
    def setex(self, name, time, value):
        return super(MyMockRedis, self).set(name, value, ex=time)


def mock_redis_client(**kwargs):
    return MyMockRedis()


@pytest.fixture()
def app(mocker):
    mocker.patch("redis.StrictRedis", mockredis.mock_strict_redis_client)
    mocker.patch("redis.Redis", mock_redis_client)
    conf = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../configs/test8.cfg"
    )
    bui = create_app(conf, False, "/dev/null", gunicorn=False, unittest=True)
    bui.config["TESTING"] = True
    bui.config["LIVESERVER_PORT"] = 5001
    bui.config["WTF_CSRF_ENABLED"] = False
    bui.config["LOGIN_DISABLED"] = False
    bui.client.port = 9999
    with bui.app_context():
        from burpui.app import create_db
        from burpui.ext.sql import db
        from burpui.models import Session, Task  # noqa

        bui.config["WITH_SQL"] = True
        create_db(bui, True)
        db.create_all()
        db.session.commit()
    yield bui
    if os.path.exists("this-file-should-not-exist"):
        os.rmdir("this-file-should-not-exist")


def login(client, username, password):
    return client.post(
        url_for("view.login"),
        data=dict(username=username, password=password, language="en", remember=False),
        follow_redirects=True,
    )


def logout(client):
    return client.get(url_for("view.logout"), follow_redirects=True)


def test_login_and_revoke_session(client):
    login(client, "admin", "admin")
    response = client.get(url_for("api.admin_me"))
    assert response.json == {"id": "admin", "name": "admin", "backend": "BASIC:AUTH"}
    sess = client.get(url_for("api.user_sessions"))
    assert len(sess.json) > 0
    assert "uuid" in sess.json[0]
    delete = client.delete(url_for("api.user_sessions", id=sess.json[0]["uuid"]))
    assert delete.status_code == 201

    logout(client)
    response = client.get(url_for("api.admin_me"))
    assert response.status_code == 401


def test_current_session(app):
    #        with self.app.test_client() as c:
    #            with c.session_transaction() as sess:
    #                sess['authenticated'] = True

    from burpui.sessions import session_manager
    from burpui.ext.sql import db
    from burpui.models import Session
    from datetime import datetime

    session_manager.store_session("toto")
    assert session_manager.session_expired() is False
    sess = Session.query.filter_by(uuid=session_manager.get_session_id()).first()
    sess.timestamp = datetime.utcfromtimestamp(0)
    db.session.commit()
    assert session_manager.session_expired() is True
