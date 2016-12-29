# -*- coding: utf8 -*-
"""
.. module:: burpui.forms
    :platform: Unix
    :synopsis: Burp-UI forms module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from .ext.i18n import LANGUAGES, get_locale

from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as __
from wtforms import TextField, PasswordField, BooleanField, SelectField, validators


class LoginForm(FlaskForm):
    username = TextField(__('Username'), [validators.Length(min=2, max=25)])
    password = PasswordField(__('Password'), [validators.Required()])
    language = SelectField(__('Language'), choices=LANGUAGES.items(), default=get_locale)
    remember = BooleanField(__('Remember me'), [validators.Optional()])
