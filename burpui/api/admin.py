# -*- coding: utf8 -*-
"""
.. module:: burpui.api.admin
    :platform: Unix
    :synopsis: Burp-UI admin api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from . import api
from ..server import BUIServer  # noqa
from ..sessions import session_manager
from ..utils import NOTIF_OK
from .custom import fields, Resource
#  from ..exceptions import BUIserverException

from six import iteritems
from flask import current_app
from flask_login import current_user

bui = current_app  # type: BUIServer
ns = api.namespace('admin', 'Admin methods')

user_fields = ns.model('Users', {
    'id': fields.String(required=True, description='User id'),
    'name': fields.String(required=True, description='User name'),
    'backend': fields.String(required=True, description='Backend name'),
})
session_fields = ns.model('Sessions', {
    'uuid': fields.String(description='Session id'),
    'ip': fields.String(description='IP address'),
    'ua': fields.String(description='User-Agent'),
    'permanent': fields.Boolean(description='Remember cookie'),
    'api': fields.Boolean(description='API login'),
    'expire': fields.DateTime(description='Expiration date'),
    'timestamp': fields.DateTime(description='Last seen'),
    'current': fields.Boolean(description='Is current session', default=False)
})


@ns.route('/me', endpoint='admin_me')
class AdminMe(Resource):
    """The :class:`burpui.api.admin.AdminMe` resource allows you to
    retrieve informations about your currently logged in user.

    This resource is part of the :mod:`burpui.api.admin` module.
    """

    @ns.marshal_with(user_fields)
    def get(self):
        """Returns the current user informations

        **GET** method provided by the webservice.

        :returns: Users
        """
        return getattr(current_user, 'real', current_user)


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
    parser_add = ns.parser()
    parser_add.add_argument('username', required=True, help='Username', location='values')
    parser_add.add_argument('password', required=True, help='Password', location='values')
    parser_add.add_argument('backend', required=True, help='Backend', location='values')

    parser_mod = ns.parser()
    parser_mod.add_argument('password', required=True, help='Password', location=('values', 'json'))
    parser_mod.add_argument('backend', required=True, help='Backend', location=('values', 'json'))
    parser_mod.add_argument('old_password', required=False, help='Old password', location=('values', 'json'))

    parser_del = ns.parser()
    parser_del.add_argument('backend', required=True, help='Backend', location='values')

    @api.acl_admin_required(message="Not allowed to view users list")
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
        try:
            handler = getattr(bui, 'uhandler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No authentication backend found")
        ret = []
        for name, backend in iteritems(handler.backends):
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

    @api.disabled_on_demo()
    @api.acl_admin_required(message="Not allowed to create users")
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

        try:
            handler = getattr(bui, 'uhandler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0 or \
                args['backend'] not in handler.backends:
            self.abort(404, "No authentication backend found")

        backend = handler.backends[args['backend']]

        if backend.add_user is False:
            self.abort(
                500,
                "The '{}' backend does not support user creation"
                "".format(args['backend'])
            )

        success, message, code = backend.add_user(
            args['username'],
            args['password']
        )
        status = 201 if success else 200
        return [[code, message]], status

    @api.disabled_on_demo()
    @api.acl_admin_required(message="Not allowed to delete this user")
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

        try:
            handler = getattr(bui, 'uhandler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0 or \
                args['backend'] not in handler.backends:
            self.abort(404, "No authentication backend found")

        backend = handler.backends[args['backend']]

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

    @api.disabled_on_demo()
    @api.acl_own_or_admin(key='name', message="Not allowed to modify this user")
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

        if not self.is_admin and not args['old_password']:
            self.abort(400, "Old password required")

        try:
            handler = getattr(bui, 'uhandler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0 or \
                args['backend'] not in handler.backends:
            self.abort(404, "No authentication backend found")

        backend = handler.backends[args['backend']]

        if backend.change_password is False:
            self.abort(
                500,
                "The '{}' backend does not support user modification"
                "".format(args['backend'])
            )

        success, message, code = backend.change_password(
            name,
            args['password'],
            args.get('old_password')
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

    @api.acl_admin_required(message="Not allowed to view backends list")
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
        try:
            handler = getattr(bui, 'uhandler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No authentication backend found")
        ret = []
        for name, backend in iteritems(handler.backends):
            ret.append({
                'name': name,
                'add': backend.add_user is not False,
                'del': backend.del_user is not False,
                'mod': backend.change_password is not False,
            })

        return ret


@ns.route('/me/session',
          '/me/session/<id>',
          endpoint='user_sessions')
@ns.doc(
    params={
        'id': 'Session id',
    }
)
class MySessions(Resource):
    """The :class:`burpui.api.admin.MySessions` resource allows you to
    retrieve a list of sessions and invalidate them for the current user.

    This resource is part of the :mod:`burpui.api.admin` module.
    """

    @ns.marshal_list_with(session_fields, code=200, description='Success')
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'User not found',
        },
    )
    def get(self, id=None):
        """Returns a list of sessions

        **GET** method provided by the webservice.

        :returns: Sessions
        """
        if id:
            return session_manager.get_session_by_id(id)
        user = getattr(current_user, 'name', None)
        if not user:
            self.abort(404, 'User not found')
        return session_manager.get_user_sessions(user)

    @api.disabled_on_demo()
    @ns.doc(
        responses={
            201: 'Success',
            403: 'Insufficient permissions',
            404: 'User or session not found',
            400: 'Wrong request'
        }
    )
    def delete(self, id=None):
        """Delete a given session

        Note: ``id`` is mandatory
        """
        if not id:
            self.abort(400, 'Missing id')
        user = getattr(current_user, 'name', None)
        if not user:
            self.abort(404, 'User not found')
        store = session_manager.get_session_by_id(id)
        if not store:
            self.abort('Session not found')
        if store.user != user:
            self.abort(403, 'Insufficient permissions')
        if session_manager.invalidate_session_by_id(store.uuid):
            session_manager.delete_session_by_id(store.uuid)
        return [NOTIF_OK, 'Session {} successfully revoked'.format(id)], 201
