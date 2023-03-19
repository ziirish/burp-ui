# -*- coding: utf8 -*-
"""
.. module:: burpui.api.prefs
    :platform: Unix
    :synopsis: Burp-UI prefs api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from flask import current_app, request, session
from flask_login import current_user
from werkzeug.datastructures import MultiDict

from ..engines.server import BUIServer  # noqa
from ..ext.i18n import LANGUAGES
from . import api
from .custom import Resource, fields

bui = current_app  # type: BUIServer
ns = api.namespace("preferences", "Preferences methods")


@ns.route("/ui/hide", endpoint="prefs_ui_hide")
class PrefsUIHide(Resource):
    """The :class:`burpui.api.prefs.PrefsUI` resource allows you to
    set your UI preferences.

    This resource is part of the :mod:`burpui.api.prefs` module.
    """

    parser = ns.parser()
    parser.add_argument("name", dest="client", help="Client to hide")
    parser.add_argument("agent", dest="server", help="Server to hide")

    hidden_model = ns.model(
        "HiddenModel",
        {
            "client": fields.String(description="Hidden client name"),
            "server": fields.String(description="Hidden server name"),
        },
    )

    @ns.marshal_list_with(hidden_model, description="Success", code=200)
    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
        },
    )
    def get(self):
        """Returns a list of hidden clients/servers

        **GET** method provided by the webservice.

        :returns: list
        """
        if (
            bui.config["WITH_SQL"]
            and not bui.config["BUI_DEMO"]
            and not current_user.is_anonymous
        ):
            from ..models import Hidden

            return Hidden.query.filter_by(user=current_user.name).all()
        return []

    @ns.expect(parser)
    @ns.marshal_with(hidden_model, description="Success", code=200)
    @ns.doc(
        responses={
            200: "Success, object not recorder",
            201: "Success, object recorded",
            403: "Insufficient permissions",
            500: "Internal server error",
        },
    )
    def put(self):
        """Hide a client/server

        **PUT** method provided by the webservice.

        :returns: Object to hide
        """
        ret = []
        args = self.parser.parse_args()
        if (
            bui.config["WITH_SQL"]
            and not bui.config["BUI_DEMO"]
            and not current_user.is_anonymous
        ):
            from ..ext.sql import db
            from ..models import Hidden

            client = args.get("client") or None
            server = args.get("server") or None
            hidden = Hidden.query.filter_by(
                client=client, server=server, user=current_user.name
            ).first()
            if not hidden:
                hide = Hidden(current_user.name, client, server)
                db.session.add(hide)
                try:
                    db.session.commit()
                except:  # pragma: no cover
                    db.session.rollback()
                    self.abort(500, "Internal server error")
                return hide, 201
            return hidden
        return ret

    @ns.expect(parser)
    @ns.doc(
        responses={
            204: "Success",
            403: "Insufficient permissions",
            500: "Internal server error",
        },
    )
    def delete(self):
        """Make a client/server visible again

        **DELETE** method provided by the webservice.
        """
        args = self.parser.parse_args()
        if (
            bui.config["WITH_SQL"]
            and not bui.config["BUI_DEMO"]
            and not current_user.is_anonymous
        ):
            from ..ext.sql import db
            from ..models import Hidden

            hide = Hidden.query.filter_by(
                client=(args.get("client") or None),
                server=(args.get("server") or None),
                user=current_user.name,
            ).first()
            if hide:
                db.session.delete(hide)
                try:
                    db.session.commit()
                except:  # pragma: no cover
                    db.session.rollback()
                    self.abort(500, "Internal server error")
        return None, 204


@ns.route("/ui", endpoint="prefs_ui")
class PrefsUI(Resource):
    """The :class:`burpui.api.prefs.PrefsUI` resource allows you to
    set your UI preferences.

    This resource is part of the :mod:`burpui.api.prefs` module.
    """

    parser = ns.parser()
    parser.add_argument(
        "pageLength", type=int, required=False, help="Number of element per page"
    )
    parser.add_argument(
        "language",
        type=str,
        required=False,
        help="Language",
        choices=list(LANGUAGES.keys()),
    )
    parser.add_argument("dateFormat", type=str, required=False, help="Date format")
    parser.add_argument("timezone", type=str, required=False, help="Timezone")

    @staticmethod
    def _user_language(language):
        """Set the current user language"""
        if current_user and not current_user.is_anonymous and language:
            setattr(current_user, "language", language)

    def _store_prefs(self, key, val):
        """Store the prefs if persistent storage is enabled"""
        if bui.config["WITH_SQL"] and not bui.config["BUI_DEMO"]:
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
            except:  # pragma: no cover
                db.session.rollback()

    def _update_prefs(self):
        """update prefs"""
        args = self.parser.parse_args()
        sess = session._get_current_object()
        ret = {}
        req = MultiDict()
        data = getattr(request, "values", None)
        if data:
            req.update(data)
        data = request.get_json(silent=True)
        if data:
            req.update(data)
        for key in args.keys():
            if key not in req:
                continue
            temp = args.get(key)
            if temp:
                if key == "language":
                    self._user_language(temp)
                sess[key] = temp
            elif key in sess:  # pragma: no cover
                del sess[key]
            ret[key] = temp
            self._store_prefs(key, temp)

        return ret

    @ns.doc(
        responses={
            200: "Success",
            403: "Insufficient permissions",
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
        for key in args.keys():
            ret[key] = sess.get(key)
        return ret

    @ns.expect(parser, validate=True)
    @ns.doc(
        responses={
            201: "Success",
            403: "Not allowed",
            400: "Missing parameters",
        },
    )
    def put(self):
        """Create prefs"""
        return self._update_prefs(), 201

    @ns.expect(parser)
    @ns.doc(
        responses={
            200: "Success",
            403: "Not allowed",
            400: "Missing parameters",
        },
    )
    def delete(self):
        """Delete prefs"""
        args = self.parser.parse_args()
        sess = session
        ret = {}
        for key in args.keys():
            temp = args.get(key)
            if temp:
                del sess[key]
                if bui.config["WITH_SQL"]:
                    from ..ext.sql import db
                    from ..models import Pref

                    try:
                        Pref.query.filter_by(user=current_user.name, key=key).delete()
                        db.session.commit()
                    except:  # pragma: no cover
                        db.session.rollback()
            ret[key] = sess.get(key)

        return ret

    @ns.expect(parser, validate=True)
    @ns.doc(
        responses={
            200: "Success",
            403: "Not allowed",
            400: "Missing parameters",
        },
    )
    def post(self):
        """Change prefs"""
        return self._update_prefs()
