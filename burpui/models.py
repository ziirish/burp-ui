# -*- coding: utf8 -*-
import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True)
    task = db.Column(db.String)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expire = db.Column(db.DateTime, nullable=True)

    def __init__(self, uuid, task, expire=None):
        self.task = task
        self.uuid = uuid
        if expire:
            self.expire = datetime.datetime.utcnow() + expire

    def __repr__(self):
        return '<Task {}({})>'.format(self.task, self.uuid)
