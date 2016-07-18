# -*- coding: utf8 -*-
"""
.. module:: burpui.api.admin
    :platform: Unix
    :synopsis: Burp-UI admin api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from . import api
from .custom import fields, Resource
#  from ..exceptions import BUIserverException

from six import iteritems
from flask import current_app as bui

ns = api.namespace('admin', 'Admin methods')


@ns.route('/auth/users',
          '/auth/users/<name>',
          endpoint='auth_users')
@ns.doc(
    params={
        'name': 'Username',
    }
)
class AuthUsers(Resource):
    """The :class:`burpui.api.admin.AuthUsers` resource allows you to
    retrieve a list of users and to add/update/delete them if your
    authentication backend support those actions.

    This resource is part of the :mod:`burpui.api.admin` module.
    """
    user_fields = ns.model('Users', {
        'id': fields.String(required=True, description='User id'),
        'name': fields.String(required=True, description='User name'),
        'backend': fields.String(required=True, description='Backend name'),
    })
    parser_add = ns.parser()
    parser_add.add_argument('name', required=True, help='Username', location='values')
    parser_add.add_argument('password', required=True, help='Password', location='values')
    parser_add.add_argument('backend', required=True, help='Backend', location='values')

    parser_mod = ns.parser()
    parser_mod.add_argument('password', required=True, help='Password', location='values')
    parser_mod.add_argument('backend', required=True, help='Backend', location='values')

    parser_del = ns.parser()
    parser_del.add_argument('backend', required=True, help='Backend', location='values')

    @ns.marshal_list_with(user_fields, code=200, description='Success')
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def get(self):
        """Returns a list of users

        **GET** method provided by the webservice.

        :returns: Users
        """
        # Manage ACL
        if not bui.acl or not self.is_admin:
            self.abort(403, "Not allowed to view users list")

        try:
            handler = getattr(bui, 'uhandler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No authentication backend found")
        ret = []
        for backend in handler.backends:
            loader = backend.loader
            try:
                users = getattr(loader, 'users')
            except AttributeError:
                continue
            if users:
                if isinstance(users, list):
                    for user in users:
                        ret.append({
                            'id': backend.user(user).get_id(),
                            'name': user,
                            'backend': backend.name
                        })
                elif isinstance(users, dict):
                    for user, _ in iteritems(users):
                        ret.append({
                            'id': backend.user(user).get_id(),
                            'name': user,
                            'backend': backend.name
                        })
        return ret

    @ns.expect(parser_add)
    @ns.doc(
        responses={
            200: 'Request performed with errors',
            201: 'Success',
            403: 'Not allowed',
            400: 'Missing parameters',
            404: 'Backend not found',
            500: 'Backend does not support this operation',
        },
    )
    def put(self):
        """Create a new user"""
        args = self.parser_add.parse_args()
        # Manage ACL
        if not bui.acl or not self.is_admin:
            self.abort(403, "Not allowed to create users")

        try:
            handler = getattr(bui, 'uhandler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No authentication backend found")

        backend = None
        for back in handler.backends:
            if back.name == args['backend']:
                backend = back
                break

        if not backend:
            self.abort(404, "No authentication backend found")

        if backend.add_user is False:
            self.abort(
                500,
                "The '{}' backend does not support user creation"
                "".format(args['backend'])
            )

        success, message, code = backend.add_user(
            args['name'],
            args['password']
        )
        status = 201 if success else 200
        return [[code, message]], status

    @ns.expect(parser_del)
    @ns.doc(
        responses={
            200: 'Request performed with errors',
            201: 'Success',
            403: 'Not allowed',
            400: 'Missing parameters',
            404: 'Backend not found',
            500: 'Backend does not support this operation',
        },
    )
    def delete(self, name):
        """Delete a user"""
        args = self.parser_del.parse_args()
        # Manage ACL
        if not bui.acl or not self.is_admin:
            self.abort(403, "Not allowed to delete this user")

        try:
            handler = getattr(bui, 'uhandler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No authentication backend found")

        backend = None
        for back in handler.backends:
            if back.name == args['backend']:
                backend = back
                break

        if not backend:
            self.abort(404, "No authentication backend found")

        if backend.del_user is False:
            self.abort(
                500,
                "The '{}' backend does not support user deletion"
                "".format(args['backend'])
            )

        success, message, code = backend.del_user(
            name
        )
        status = 201 if success else 200
        return [[code, message]], status

    @ns.expect(parser_mod)
    @ns.doc(
        responses={
            200: 'Request performed with errors',
            201: 'Success',
            403: 'Not allowed',
            400: 'Missing parameters',
            404: 'Backend not found',
            500: 'Backend does not support this operation',
        },
    )
    def post(self, name):
        """Change user password"""
        args = self.parser_mod.parse_args()
        # Manage ACL
        if name != self.username or not bui.acl or not self.is_admin:
            self.abort(403, "Not allowed to modify this user")

        try:
            handler = getattr(bui, 'uhandler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No authentication backend found")

        backend = None
        for back in handler.backends:
            if back.name == args['backend']:
                backend = back
                break

        if not backend:
            self.abort(404, "No authentication backend found")

        if backend.change_password is False:
            self.abort(
                500,
                "The '{}' backend does not support user modification"
                "".format(args['backend'])
            )

        success, message, code = backend.change_password(
            name,
            args['password']
        )
        status = 201 if success else 200
        return [[code, message]], status


@ns.route('/auth/backends', endpoint='auth_backends')
class AuthBackends(Resource):
    """The :class:`burpui.api.admin.AuthBackends` resource allows you to
    retrieve a list of backends and to add/update/delete users if your
    authentication backend support those actions.

    This resource is part of the :mod:`burpui.api.admin` module.
    """
    backend_fields = ns.model('Backends', {
        'name': fields.String(required=True, description='Backend name'),
        'add': fields.Boolean(required=False, default=False, description='Support user creation'),
        'mod': fields.Boolean(required=False, default=False, description='Support user edition'),
        'del': fields.Boolean(required=False, default=False, description='Support user deletion'),
    })

    @ns.marshal_list_with(backend_fields, code=200, description='Success')
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def get(self):
        """Returns a list of backends

        **GET** method provided by the webservice.

        :returns: Backends
        """
        # Manage ACL
        if not bui.acl or not self.is_admin:
            self.abort(403, "Not allowed to view users list")

        try:
            handler = getattr(bui, 'uhandler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No authentication backend found")
        ret = []
        for backend in handler.backends:
            ret.append({
                'name': backend.name,
                'add': backend.add_user is not False,
                'del': backend.del_user is not False,
                'mod': backend.change_password is not False,
            })

        return ret
