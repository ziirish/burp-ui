# -*- coding: utf8 -*-
"""
.. module:: burpui.models
    :platform: Unix
    :synopsis: Burp-UI DB models module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import datetime

from .ext.sql import db
from flask import current_app, session
from .server import BUIServer  # noqa

app = current_app  # type: BUIServer


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(256), unique=True)
    task = db.Column(db.String(256))
    user = db.Column(db.String(256), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expire = db.Column(db.DateTime, nullable=True)

    def __init__(self, uuid, task, user=None, expire=None):
        self.task = task
        self.uuid = uuid
        self.user = user
        if expire is not None:
            self.expire = datetime.datetime.utcnow() + expire

    def __repr__(self):
        return '<Task {} ({})>'.format(self.task, self.uuid)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(256), unique=True)
    user = db.Column(db.String(256))
    ip = db.Column(db.String(256), nullable=True)
    ua = db.Column(db.String(2048), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expire = db.Column(db.DateTime, nullable=True)
    permanent = db.Column(db.Boolean)
    api = db.Column(db.Boolean)

    def __init__(self, uuid, user, ip=None, ua=None,
                 permanent=False, api=False):
        self.uuid = uuid
        self.user = user
        self.ip = ip
        self.ua = ua
        self.permanent = permanent
        self.api = api
        if self.permanent:
            self.expire = datetime.datetime.utcnow() + \
                app.permanent_session_lifetime

    def refresh(self, ip=None):
        self.timestamp = datetime.datetime.utcnow()
        if ip:
            self.ip = ip
        if self.permanent:
            self.expire = datetime.datetime.utcnow() + \
                app.permanent_session_lifetime
            if 'remember' not in session:
                session['remember'] = 'set'
        db.session.commit()

    def __repr__(self):
        return '<Session {} ({}, {}, {})>'.format(
            self.uuid,
            self.user,
            self.ip,
            self.ua
        )


class Pref(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(256))
    key = db.Column(db.String(256), nullable=False)
    value = db.Column(db.String(256))

    def __init__(self, user, key, value=None):
        self.user = user
        self.key = key
        self.value = value

    def __repr__(self):
        return '<Pref {}: {} = {}>'.format(
            self.user,
            self.key,
            self.value
        )
