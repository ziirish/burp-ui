# -*- coding: utf8 -*-
"""
.. module:: burpui.forms
    :platform: Unix
    :synopsis: Burp-UI forms module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask_babel import lazy_gettext as __
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, validators

from .ext.i18n import LANGUAGES, get_locale


class LoginForm(FlaskForm):
    username = StringField(__("Username"), [validators.DataRequired()])
    password = PasswordField(__("Password"), [validators.DataRequired()])
    language = SelectField(
        __("Language"), choices=list(LANGUAGES.items()), default=get_locale
    )
    remember = BooleanField(__("Remember me"), [validators.Optional()])
