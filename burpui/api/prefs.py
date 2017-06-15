# -*- coding: utf8 -*-
"""
.. module:: burpui.api.prefs
    :platform: Unix
    :synopsis: Burp-UI prefs api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from six import viewkeys
from flask import session, current_app, request
from flask_login import current_user
from werkzeug.datastructures import MultiDict

from . import api
from ..server import BUIServer  # noqa
from ..ext.i18n import LANGUAGES
from .custom import Resource

bui = current_app  # type: BUIServer
ns = api.namespace('preferences', 'Preferences methods')


@ns.route('/ui',
          endpoint='prefs_ui')
class PrefsUI(Resource):
    """The :class:`burpui.api.prefs.PrefsUI` resource allows you to
    set your UI preferences.

    This resource is part of the :mod:`burpui.api.prefs` module.
    """
    parser = ns.parser()
    parser.add_argument(
        'pageLength',
        type=int,
        required=False,
        help='Number of element per page'
    )
    parser.add_argument(
        'language',
        type=str,
        required=False,
        help='Language',
        choices=list(LANGUAGES.keys())
    )
    parser.add_argument(
        'dateFormat',
        type=str,
        required=False,
        help='Date format'
    )

    @staticmethod
    def _user_language(language):
        """Set the current user language"""
        if current_user and not current_user.is_anonymous and language:
            setattr(current_user, 'language', language)

    def _store_prefs(self, key, val):
        """Store the prefs if persistent storage is enabled"""
        if bui.config['WITH_SQL'] and not bui.config['BUI_DEMO']:
            from ..ext.sql import db
            from ..models import Pref
            pref = Pref.query.filter_by(user=current_user.name, key=key).first()
            if pref:
                if val:
                    pref.value = val
                else:
                    db.session.delete(pref)
            elif val:
                pref = Pref(current_user.name, key, val)
                db.session.add(pref)
            try:
                db.session.commit()
            except:
                db.session.rollback()

    def _update_prefs(self):
        """update prefs"""
        args = self.parser.parse_args()
        sess = session._get_current_object()
        ret = {}
        req = MultiDict()
        for loc in ['values', 'json']:
            data = getattr(request, loc, None)
            if data:
                req.update(data)
        for key in viewkeys(args):
            if key not in req:
                continue
            temp = args.get(key)
            if temp:
                if key == 'language':
                    self._user_language(temp)
                sess[key] = temp
            elif key in sess:
                del sess[key]
            ret[key] = temp
            self._store_prefs(key, temp)

        return ret

    @ns.doc(
        responses={
            200: 'Success',
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def get(self):
        """Returns a list of prefs

        **GET** method provided by the webservice.

        :returns: prefs
        """
        args = self.parser.parse_args()
        ret = {}
        sess = session
        for key in viewkeys(args):
            ret[key] = sess.get(key)
        return ret

    @ns.expect(parser, validate=True)
    @ns.doc(
        responses={
            201: 'Success',
            403: 'Not allowed',
            400: 'Missing parameters',
            404: 'Backend not found',
            500: 'Backend does not support this operation',
        },
    )
    def put(self):
        """Create prefs"""
        return self._update_prefs(), 201

    @ns.expect(parser)
    @ns.doc(
        responses={
            200: 'Success',
            403: 'Not allowed',
            400: 'Missing parameters',
            404: 'Backend not found',
            500: 'Backend does not support this operation',
        },
    )
    def delete(self):
        """Delete prefs"""
        args = self.parser.parse_args()
        sess = session
        ret = {}
        for key in viewkeys(args):
            temp = args.get(key)
            if temp:
                del sess[key]
                if bui.config['WITH_SQL']:
                    from ..ext.sql import db
                    from ..models import Pref
                    try:
                        Pref.query.filter_by(
                            user=current_user.name,
                            key=key
                        ).delete()
                        db.session.commit()
                    except:
                        db.session.rollback()
            ret[key] = sess.get(key)

        return ret

    @ns.expect(parser, validate=True)
    @ns.doc(
        responses={
            200: 'Success',
            403: 'Not allowed',
            400: 'Missing parameters',
            404: 'Backend not found',
            500: 'Backend does not support this operation',
        },
    )
    def post(self):
        """Change prefs"""
        return self._update_prefs()
