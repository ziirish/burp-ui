# -*- coding: utf8 -*-
"""
.. module:: burpui.forms
    :platform: Unix
    :synopsis: Burp-UI forms module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""

from flask_wtf import Form
from wtforms import TextField, PasswordField, BooleanField, validators


class LoginForm(Form):
    username = TextField('Username', [validators.Length(min=2, max=25)])
    password = PasswordField('Password', [validators.Required()])
    remember = BooleanField('Remember me', [validators.Optional()])
