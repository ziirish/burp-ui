# -*- coding: utf8 -*-
"""
.. module:: burpui.ext.i18n
    :platform: Unix
    :synopsis: Burp-UI external Internationalization module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask import request, session
from flask_babel import Babel
from flask_login import current_user
from ..config import config
from .._compat import to_unicode

babel = Babel()

LANGUAGES = {
    'en': to_unicode('English'),
    'fr': to_unicode('Français'),
    'es': to_unicode('Español'),
    'it': to_unicode('Italiano'),
}
config['LANGUAGES'] = LANGUAGES


@babel.localeselector
def get_locale():
    locale = None
    if current_user and not current_user.is_anonymous:
        locale = getattr(current_user, 'language', None)
    elif 'language' in session:
        locale = session.get('language', None)
    if locale not in LANGUAGES:
        locale = None
    return locale or request.accept_languages.best_match(config['LANGUAGES'].keys())
