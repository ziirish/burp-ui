# -*- coding: utf8 -*-
"""
.. module:: burpui.sessions
    :platform: Unix
    :synopsis: Burp-UI sessions module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import datetime

from flask import session

try:  # noqa
    from redis import Redis  # noqa
except ImportError:  # noqa
    pass


class SessionManager(object):
    """Wrapper session to keep a track on every session"""
    backend = None  # type: Redis
    prefix = ''

    def init_app(self, app):
        """Initialize the wrapper

        :param app: Application context
        :type app: :class:`burpui.server.BUIServer`
        """
        self.app = app
        self.prefix = self.app.config.get('SESSION_KEY_PREFIX', 'session:')

    def session_expired(self):
        """Check if a session is expired"""
        if self.session_managed():
            from .ext.sql import db
            from .models import Session
            store = Session.query.filter_by(uuid=session.sid).first()
            inactive = self.app.config['SESSION_INACTIVE']
            if (store and (inactive and inactive.days > 0) and
                    (store.timestamp + inactive < datetime.datetime.utcnow())):
                session['authenticated'] = False
                db.session.delete(store)
                db.session.commit()
                return True
            elif store:
                store.refresh()
                db.session.commit()
        return False

    def session_managed(self):
        """Check if a session is manageable"""
        return self.app.storage and self.app.storage.lower() != 'default' and \
            self.app.config['WITH_SQL']

    def store_session(self, user, ip=None, ua=None, remember=False, api=False):
        """Store the session in db"""
        if self.session_managed():
            from .ext.sql import db
            from .models import Session
            store = Session(
                session.sid,
                user,
                ip,
                ua,
                remember,
                api
            )
            db.session.add(store)
            db.session.commit()

    def delete_session(self):
        """Remove the session"""
        self.delete_session_by_id(getattr(session, 'sid', None))

    def delete_session_by_id(self, id):
        """Remove a session by id"""
        if self.session_managed():
            from .ext.sql import db
            from .models import Session
            Session.query.filter_by(uuid=id).delete()
            db.session.commit()

    def get_session_username(self):
        """Return the username stored in the session"""
        if self.session_managed():
            from .models import Session
            store = Session.query.filter_by(uuid=session.sid).first()
            if store:
                return store.user
        return None

    def get_session_id(self):
        """Return the current session id"""
        if self.app.storage and self.app.storage.lower() != 'default':
            return session.sid
        return None

    def get_user_sessions(self, user):
        """Return all sessions of a given user"""
        if self.session_managed():
            from .models import Session
            sessions = Session.query.filter_by(user=user).all()
            for sess in sessions:
                if not sess.expire:
                    sess.expire = self.get_session_ttl(sess.uuid)
            return sessions
        return None

    def get_session_by_id(self, id):
        """Return a session by id"""
        if self.session_managed():
            from .models import Session
            sess = Session.query.filter_by(uuid=id).first()
            if sess and not sess.expire:
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
        if 'authenticated' in session:
            session.pop('authenticated')
        return self.invalidate_session_by_id(getattr(session, 'sid', None))

    def invalidate_session_by_id(self, id):
        """Invalidate a given session"""
        if self.session_managed() and self.backend:
            if not id:
                return True
            key = self.prefix + id
            if not hasattr(self.app.session_interface, 'serializer'):
                return False
            # if we are working on the current session that have been freshly
            # created, it's content has not been dumped yet
            dump = self.backend.get(key)
            if dump:
                sess = self.app.session_interface.serializer.loads(dump)
                if 'authenticated' in sess:
                    sess.pop('authenticated')
                ttl = self.backend.ttl(key)
                self.backend.setex(key, sess, ttl)
            # make sure to remove the current user cache
            if self.app.auth != 'none':
                handler = self.app.uhandler
                users = getattr(handler, 'users', {})
                if id in users:
                    users.pop(id)
        return True

session_manager = SessionManager()
