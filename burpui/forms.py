# -*- coding: utf8 -*-

from flask_wtf import Form
from wtforms import TextField, PasswordField, BooleanField, validators


class LoginForm(Form):
    username = TextField('Username', [validators.Length(min=2, max=25)])
    password = PasswordField('Password', [validators.Required()])
    remember = BooleanField('Remember me', [validators.Optional()])
