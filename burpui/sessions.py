# -*- coding: utf8 -*-
"""
.. module:: burpui.sessions
    :platform: Unix
    :synopsis: Burp-UI sessions module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import datetime
import re
import uuid

from flask import request, session

# used for completion
try:
    from redis import Redis  # noqa
except ImportError:  # pragma: no cover
    pass

try:
    from flask_session import Session as DummySessionImport  # noqa

    WITH_FLASK_SESSION = True
except ImportError:
    WITH_FLASK_SESSION = False


class SessionManager(object):
    """Wrapper session to keep a track on every session"""

    backend = None  # type: Redis
    prefix = ""

    def init_app(self, app):
        """Initialize the wrapper

        :param app: Application context
        :type app: :class:`burpui.engines.server.BUIServer`
        """
        self.app = app
        self.prefix = self.app.config.get("SESSION_KEY_PREFIX", "session:")

    def session_expired(self):
        """Check if the current session has expired"""
        if self.session_managed():
            return self.session_expired_by_id(self.get_session_id())
        return False

    def session_expired_by_id(self, id):
        """Check if a session has expired"""
        if self.session_managed():
            from .ext.sql import db
            from .models import Session

            store = Session.query.filter_by(uuid=id).first()
            inactive = self.app.config["SESSION_INACTIVE"]
            if (
                store
                and (inactive and inactive.days > 0)
                and (store.timestamp + inactive < datetime.datetime.utcnow())
            ):
                if id == self.get_session_id():
                    self.invalidate_current_session()
                else:
                    self.invalidate_session_by_id(id)
                try:
                    db.session.delete(store)
                    db.session.commit()
                except:
                    db.session.rollback()
                    return False
                return True
            elif store:
                ip = self.anonym_ip(request.remote_addr)
                store.refresh(ip)
        return False

    def session_managed(self):
        """Check if a session is manageable"""
        return (
            self.app.storage
            and self.app.storage.lower() != "default"
            and self.app.config["WITH_SQL"]
            and WITH_FLASK_SESSION
        )

    def anonym_ip(self, ip):
        """anonymize ip address while running the demo"""
        # Do nothing if not in demo mode
        if self.app.config["BUI_DEMO"]:
            if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                spl = ip.split(".")
                ip = "{}.x.x.x".format(spl[0])
            else:
                spl = ip.split(":")
                for mem in spl:
                    if mem:
                        ip = "::{}:x:x".format(mem)
                        break
        return ip

    def store_session(self, user, ip=None, ua=None, remember=False, api=False):
        """Store the session in db"""
        if self.session_managed():
            from .ext.sql import db
            from .models import Session

            id = self.get_session_id()
            Session.query.filter_by(uuid=id).delete()
            ip = self.anonym_ip(ip)
            store = Session(id, user, ip, ua, remember, api)
            try:
                db.session.add(store)
                db.session.commit()
            except:
                db.session.rollback()
            session["persistent"] = remember

    def session_import_from(self, old_id):
        """Import session from a given id"""
        self.session_update_id(old_id, self.get_session_id())

    def session_update_id(self, old_id, new_id):
        """Import session from a given id"""
        if self.session_managed():
            from .ext.sql import db
            from .models import Session

            old_session = Session.query.filter_by(uuid=old_id).first()
            if old_session:
                old_session.uuid = new_id
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
                session["persistent"] = old_session.permanent

    def session_in_db(self):
        """Tell if the current session exists in db"""
        if self.session_managed():
            from .models import Session

            id = self.get_session_id()
            return Session.query.filter_by(uuid=id).first() is not None
        # don't need to store it since it is not managed anyway
        return True

    def delete_session(self, commit=True):
        """Remove the session"""
        self.delete_session_by_id(getattr(session, "sid", None), commit)

    def delete_session_by_id(self, id, commit=True):
        """Remove a session by id"""
        if self.session_managed():
            from .ext.sql import db
            from .models import Session

            try:
                Session.query.filter_by(uuid=id).delete()
                if commit:
                    db.session.commit()
            except:
                if commit:
                    db.session.rollback()

    def bulk_session_delete_by_id(self, bucket):
        """Remove all sessions matching the bucket IDs"""
        if self.session_managed():
            from .ext.sql import db
            from .models import Session

            try:
                Session.query.filter(Session.uuid.in_(bucket)).delete(
                    synchronize_session=False
                )
                db.session.commit()
            except:
                db.session.rollback()

    def commit(self):
        if self.session_managed():
            from .ext.sql import db

            try:
                db.session.commit()
            except:
                db.session.rollback()

    def get_session_username(self):
        """Return the username stored in the current session"""
        return self.get_session_username_by_id(self.get_session_id())

    def get_session_username_by_id(self, id):
        """Return the username stored in the session"""
        if self.session_managed():
            from .models import Session

            store = Session.query.filter_by(uuid=id).first()
            if store:
                return store.user
        return None

    def get_session_id(self):
        """Return the current session id"""
        if self.app.storage and self.app.storage.lower() != "default":
            return getattr(session, "sid", str(uuid.uuid4()))
        return None

    def get_expired_sessions(self, maxret=-1, count=False):
        """Return all expired sessions"""
        if self.session_managed():
            from .models import Session

            inactive = self.app.config["SESSION_INACTIVE"]
            if inactive and inactive.days > 0:
                limit = datetime.datetime.utcnow() - inactive
                query = Session.query.filter(Session.timestamp <= limit)
                if count:
                    return query.count()
                if maxret < 0:
                    return query.all()
                else:
                    return query.limit(maxret)
        return [] if not count else 0

    def get_expired_sessions_count(self):
        return self.get_expired_sessions(count=True)

    def get_user_sessions(self, user):
        """Return all sessions of a given user"""
        if self.session_managed():
            from .models import Session

            sessions = Session.query.filter_by(user=user).all()
            curr = self.get_session_id()
            for sess in sessions:
                if sess.uuid == curr:
                    sess.current = True
                if not sess.expire:
                    inactive = self.app.config["SESSION_INACTIVE"]
                    if inactive and inactive.days > 0:
                        sess.expire = sess.timestamp + inactive
                    else:
                        sess.expire = self.get_session_ttl(sess.uuid)
            return sessions
        return []

    def get_session_by_id(self, id):
        """Return a session by id"""
        if self.session_managed():
            from .models import Session

            sess = Session.query.filter_by(uuid=id).first()
            curr = self.get_session_id()
            if sess and not sess.expire:
                if sess.uuid == curr:
                    sess.current = True
                if not sess.expire:
                    inactive = self.app.config["SESSION_INACTIVE"]
                    if inactive and inactive.days > 0:
                        sess.expire = sess.timestamp + inactive
                    else:
                        sess.expire = self.get_session_ttl(sess.uuid)
            return sess
        return None

    def get_session_ttl(self, id):
        """Return the time to live of a given session"""
        if self.session_managed() and self.backend:
            key = self.prefix + id
            ttl = self.backend.ttl(key)
            return datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        return 0

    def invalidate_current_session(self):
        """Ivalidate current session"""
        id = getattr(session, "sid", None)
        session.clear()
        # simulate a logout to clear cookies
        session["remember"] = "clear"
        return self.invalidate_session_by_id(id, False)

    def invalidate_session_by_id(self, id, recurse=True):
        """Invalidate a given session"""
        if self.session_managed() and self.backend:
            if not id:
                return True
            try:
                if id == self.get_session_id() and recurse:
                    return self.invalidate_current_session()
            except RuntimeError:
                # in case we are invoked through celery we will never
                # work on the current session
                pass
            key = self.prefix + id
            if not hasattr(self.app.session_interface, "serializer"):
                return False
            # if we are working on the current session that have been freshly
            # created, its content has not been dumped yet
            dump = self.backend.get(key)
            if dump:
                sess = self.app.session_interface.serializer.loads(dump)
                sess.clear()
                sess["remember"] = "clear"
                ttl = self.backend.ttl(key)
                val = self.app.session_interface.serializer.dumps(dict(sess))
                self.backend.setex(name=key, value=val, time=ttl)
            # make sure to remove the current user cache
            if self.app.auth != "none":
                handler = self.app.uhandler
                users = getattr(handler, "users", {})
                user = self.get_session_username_by_id(id)
                if user and user in users:
                    users.pop(user)
                if id in users:
                    users.pop(id)
        return True


session_manager = SessionManager()
