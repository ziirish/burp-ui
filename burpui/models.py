# -*- coding: utf8 -*-
"""
.. module:: burpui.models
    :platform: Unix
    :synopsis: Burp-UI DB models module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import datetime

from .ext.sql import db


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True)
    task = db.Column(db.String)
    user = db.Column(db.String, nullable=True)
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
