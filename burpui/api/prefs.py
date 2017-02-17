# -*- coding: utf8 -*-
"""
.. module:: burpui.api.prefs
    :platform: Unix
    :synopsis: Burp-UI prefs api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from six import viewkeys
from flask import session

from . import api
from .custom import Resource
#  from ..exceptions import BUIserverException

ns = api.namespace('preferences', 'Preferences methods')


@ns.route('/ui',
          endpoint='prefs_ui')
class PrefsUI(Resource):
    """The :class:`burpui.api.prefs.PrefsUI` resource allows you to
    set your UI preferences.

    This resource is part of the :mod:`burpui.api.prefs` module.
    """
    parser = ns.parser()
    parser.add_argument('pageLength', type=int, required=False, help='Number of element per page', location='values')

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

    @ns.expect(parser)
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
        args = self.parser.parse_args()
        sess = session
        ret = {}
        for key in viewkeys(args):
            temp = args.get(key)
            if temp:
                sess[key] = temp
                ret[key] = temp

        return ret, 201

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
            ret[key] = sess.get(key)

        return ret

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
    def post(self):
        """Change prefs"""
        args = self.parser.parse_args()
        sess = session
        ret = {}
        for key in viewkeys(args):
            temp = args.get(key)
            if temp:
                sess[key] = temp
                ret[key] = temp

        return ret
