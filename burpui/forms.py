# -*- coding: utf8 -*-
"""
.. module:: burpui.forms
    :platform: Unix
    :synopsis: Burp-UI forms module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from .ext.i18n import LANGUAGES, get_locale

from flask_wtf import Form
from flask_babel import gettext
from wtforms import TextField, PasswordField, BooleanField, SelectField, validators


class LoginForm(Form):
    username = TextField(gettext('Username'), [validators.Length(min=2, max=25)])
    password = PasswordField(gettext('Password'), [validators.Required()])
    language = SelectField(gettext('Language'), choices=LANGUAGES.items(), default=get_locale)
    remember = BooleanField(gettext('Remember me'), [validators.Optional()])
