# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.i18n
    :platform: Unix
    :synopsis: Burp-UI external Internationalization module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask import request
from flask_babel import Babel
from flask_login import current_user
from ..config import config

babel = Babel()

LANGUAGES = {
    'en': 'English',
    'fr': 'Français',
}
config['LANGUAGES'] = LANGUAGES


@babel.localeselector
def get_locale():
    locale = None
    if current_user and not current_user.is_anonymous:
        locale = getattr(current_user, 'language', None)
    return locale or request.accept_languages.best_match(config['LANGUAGES'].keys())
