# -*- coding: utf8 -*-
"""
.. module:: burpui.security
    :platform: Unix
    :synopsis: Burp-UI security module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from ._compat import to_unicode, urlparse, urljoin


def sanitize_string(string, strict=True, paranoid=False):
    """Return a 'safe' version of the string (ie. remove malicious chars like
    '\n')

    :param string: String to escape
    :type string: str
    """
    if not string:
        return ""
    if paranoid:
        return to_unicode(string.encode('unicode_escape'))
    elif strict:
        return to_unicode(string).split('\n')[0]
    else:
        import re
        ret = repr(string).replace('\\\\', '\\')
        ret = re.sub(r"^u?(?P<quote>['\"])(.*)(?P=quote)$", r"\2", ret)
        return to_unicode(ret)


def basic_login_from_request(request, app):
    """Check 'Authorization' headers and log the user in if possible.

    :param request: The input request
    :type request: :class:`flask.Request`

    :param app: The application context
    :type app: :class:`burpui.server.BUIServer`
    """
    if app.auth != 'none':
        if request.headers.get('X-From-UI', False):
            return None
        auth = request.authorization
        if auth:
            from flask import session, g
            app.logger.debug('Found Basic user: {}'.format(auth.username))
            refresh = False
            if 'login' in session and session['login'] != auth.username:
                refresh = True
                session.clear()
                session['login'] = auth.username
            session['language'] = request.headers.get('X-Language', 'en')
            user = app.uhandler.user(auth.username, refresh)
            if user.active and user.login(auth.password):
                from flask_login import login_user
                from .sessions import session_manager
                login_user(user)
                if request.headers.get('X-Reuse-Session', False):
                    session_manager.store_session(
                        auth.username,
                        request.remote_addr,
                        request.headers.get('User-Agent'),
                        remember=False,
                        api=True
                    )
                else:
                    g.basic_session = True
                app.logger.debug('Successfully logged in')
                return user
            app.logger.warning('Failed to log-in')
    return None


def is_safe_url(target):
    from flask import request
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc
