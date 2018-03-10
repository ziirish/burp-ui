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
grant_fields = ns.model('Grants', {
    'id': fields.String(required=True, description='Grant id'),
    'grant': fields.String(required=True, description='Grant content'),
    'backend': fields.String(required=True, description='Backend name'),
})
group_fields = ns.model('Groups', {
    'id': fields.String(required=True, description='Group id'),
    'grant': fields.String(required=True, description='Group grant content'),
    'members': fields.List(fields.String, required=True, description='Group members'),
    'backend': fields.String(required=True, description='Backend name'),
})
group_members_fields = ns.model('GroupMembers', {
    'members': fields.List(fields.String, required=True, description='Group members'),
    'grant': fields.String(required=True, description='Group grant content'),
})
moderator_members_fields = ns.model('ModeratorMembers', {
    'members': fields.List(fields.String, required=True, description='Moderator members'),
    'grant': fields.String(required=True, description='Moderator grant content'),
})
admin_members_fields = ns.model('AdminMembers', {
    'members': fields.List(fields.String, required=True, description='Admin members'),
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

        :returns: User
        """
        ret = getattr(current_user, 'real', current_user)
        return ret


@ns.route('/acl/admin/<backend>',
          '/acl/admin/<backend>/<member>',
          endpoint='acl_admins')
@ns.doc(
    params={
        'backend': 'ACL backend',
        'member': 'Admin member',
    }
)
class AclAdmins(Resource):
    """The :class:`burpui.api.admin.AclAdmins` resource allows you to
    retrieve a list of admins and add/delete them if your
    acl backend support those actions.

    This resource is part of the :mod:`burpui.api.admin` module.
    """
    parser = ns.parser()
    parser.add_argument('memberName', required=False, help='Moderator member', location='values')

    @api.acl_admin_or_moderator_required(message="Not allowed to view admins list")
    @ns.marshal_with(admin_members_fields, code=200, description='Success')
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def get(self, backend):
        """Returns a list of admin users

        **GET** method provided by the webservice.

        :returns: Members
        """
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        if backend not in handler.backends:
            self.abort(404, "No acl backend '{}' found".format(backend))
        ret = {}
        loader = handler.backends[backend]
        ret = {
            'members': loader.admins
        }
        return ret

    @api.acl_admin_required(message="Not allowed to add admin members")
    @ns.expect(parser)
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def put(self, backend, member=None):
        """Add a member as admin

        **PUT** method provided by the webservice.
        """
        args = self.parser.parse_args()
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        if backend not in handler.backends:
            self.abort(404, "No acl backend '{}' found".format(backend))

        loader = handler.backends[backend]

        member = member or args['memberName']

        if loader.add_admin is False:
            self.abort(
                500,
                "The '{}' backend does not support moderator member addition"
                "".format(backend)
            )

        success, message, code = loader.add_admin(
            member
        )
        status = 201 if success else 200
        return [[code, message]], status

    @api.acl_admin_required(message="Not allowed to remove admin members")
    @ns.expect(parser)
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def delete(self, backend, member=None):
        """Remove an admin member

        **DELETE** method provided by the webservice.
        """
        args = self.parser.parse_args()
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        if backend not in handler.backends:
            self.abort(40422, "No acl backend '{}' found".format(backend))

        loader = handler.backends[backend]

        member = member or args['memberName']

        if loader.del_admin is False:
            self.abort(
                500,
                "The '{}' backend does not support admin member deletion"
                "".format(backend)
            )

        success, message, code = loader.del_admin(
            member
        )
        status = 201 if success else 200
        return [[code, message]], status


@ns.route('/acl/moderator/<backend>',
          '/acl/moderator/<backend>/<member>',
          endpoint='acl_moderators')
@ns.doc(
    params={
        'backend': 'ACL backend',
        'member': 'Moderator member',
    }
)
class AclModerators(Resource):
    """The :class:`burpui.api.admin.AclModerators` resource allows you to
    retrieve a list of moderators and add/delete them if your
    acl backend support those actions.

    This resource is part of the :mod:`burpui.api.admin` module.
    """
    parser = ns.parser()
    parser.add_argument('memberName', required=False, help='Moderator member', location='values')

    parser_mod = ns.parser()
    parser_mod.add_argument('grants', required=False, help='Moderator grants', location='values')

    @api.acl_admin_or_moderator_required(message="Not allowed to view moderators list")
    @ns.marshal_with(moderator_members_fields, code=200, description='Success')
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def get(self, backend):
        """Returns a list of moderator users

        **GET** method provided by the webservice.

        :returns: Members
        """
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        if backend not in handler.backends:
            self.abort(404, "No acl backend '{}' found".format(backend))
        ret = {}
        loader = handler.backends[backend]
        ret = {
            'members': loader.moderators,
            'grant': loader.moderator
        }
        return ret

    @api.acl_admin_or_moderator_required(message="Not allowed to add moderator members")
    @ns.expect(parser)
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def put(self, backend, member=None):
        """Add a member as moderator

        **PUT** method provided by the webservice.
        """
        args = self.parser.parse_args()
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        if backend not in handler.backends:
            self.abort(404, "No acl backend '{}' found".format(backend))

        loader = handler.backends[backend]

        member = member or args['memberName']

        if loader.add_moderator is False:
            self.abort(
                500,
                "The '{}' backend does not support moderator member addition"
                "".format(backend)
            )

        success, message, code = loader.add_moderator(
            member
        )
        status = 201 if success else 200
        return [[code, message]], status

    @api.acl_admin_or_moderator_required(message="Not allowed to remove moderator members")
    @ns.expect(parser)
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def delete(self, backend, member=None):
        """Remove a moderator member

        **DELETE** method provided by the webservice.
        """
        args = self.parser.parse_args()
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        if backend not in handler.backends:
            self.abort(404, "No acl backend '{}' found".format(backend))

        loader = handler.backends[backend]

        member = member or args['memberName']

        if loader.del_moderator is False:
            self.abort(
                500,
                "The '{}' backend does not support moderator member deletion"
                "".format(backend)
            )

        success, message, code = loader.del_moderator(
            member
        )
        status = 201 if success else 200
        return [[code, message]], status

    @api.acl_admin_or_moderator_required(message="Not allowed to update moderator grants")
    @ns.expect(parser_mod)
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def post(self, backend):
        """Update moderator grants

        **POST** method provided by the webservice.
        """
        args = self.parser.parse_args()
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        if backend not in handler.backends:
            self.abort(404, "No acl backend '{}' found".format(backend))

        loader = handler.backends[backend]

        grants = args['grants']

        if loader.mod_moderator is False:
            self.abort(
                500,
                "The '{}' backend does not support moderator grants edition"
                "".format(backend)
            )

        success, message, code = loader.mod_moderator(
            grants
        )
        status = 201 if success else 200
        return [[code, message]], status


@ns.route('/acl/group/<name>/<backend>',
          '/acl/group/<name>/<backend>/<member>',
          endpoint='acl_group_members')
@ns.doc(
    params={
        'name': 'Group name',
        'backend': 'ACL backend',
        'member': 'Group member',
    }
)
class AclGroup(Resource):
    """The :class:`burpui.api.admin.AclGroup` resource allows you to
    retrieve a list of members in a given group and add/delete them if your
    acl backend support those actions.

    This resource is part of the :mod:`burpui.api.admin` module.
    """
    parser = ns.parser()
    parser.add_argument('memberName', required=False, help='Group member', location='values')

    @api.acl_admin_or_moderator_required(message="Not allowed to view groups list")
    @ns.marshal_with(group_members_fields, code=200, description='Success')
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def get(self, name, backend):
        """Returns a list of users in a giver group

        **GET** method provided by the webservice.

        :returns: Members
        """
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        if backend not in handler.backends:
            self.abort(404, "No acl backend '{}' found".format(backend))
        ret = {}
        loader = handler.backends[backend]
        groups = loader.groups
        gname = '@{}'.format(name)
        if groups and gname in groups:
            ret = {
                'members': groups[gname].get('members', []),
                'grant': groups[gname].get('grants', '')
            }
        return ret

    @api.acl_admin_or_moderator_required(message="Not allowed to add member in group")
    @ns.expect(parser)
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def put(self, name, backend, member=None):
        """Add a member in a given group

        **PUT** method provided by the webservice.
        """
        args = self.parser.parse_args()
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        if backend not in handler.backends:
            self.abort(404, "No acl backend '{}' found".format(backend))

        loader = handler.backends[backend]

        member = member or args['memberName']

        if loader.add_group_member is False:
            self.abort(
                500,
                "The '{}' backend does not support group member addition"
                "".format(backend)
            )

        success, message, code = loader.add_group_member(
            name,
            member
        )
        status = 201 if success else 200
        return [[code, message]], status

    @api.acl_admin_or_moderator_required(message="Not allowed to remove member in group")
    @ns.expect(parser)
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def delete(self, name, backend, member=None):
        """Remove a member from a given group

        **DELETE** method provided by the webservice.
        """
        args = self.parser.parse_args()
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        if backend not in handler.backends:
            self.abort(404, "No acl backend '{}' found".format(backend))

        loader = handler.backends[backend]

        member = member or args['memberName']

        if loader.del_group_member is False:
            self.abort(
                500,
                "The '{}' backend does not support group member deletion"
                "".format(backend)
            )

        success, message, code = loader.del_group_member(
            name,
            member
        )
        status = 201 if success else 200
        return [[code, message]], status


@ns.route('/acl/groups',
          '/acl/groups/<name>',
          endpoint='acl_groups')
@ns.doc(
    params={
        'name': 'Group name',
    }
)
class AclGroups(Resource):
    """The :class:`burpui.api.admin.AclGroups` resource allows you to
    retrieve a list of groups and to add/update/delete them if your
    acl backend support those actions.

    This resource is part of the :mod:`burpui.api.admin` module.
    """
    parser_add = ns.parser()
    parser_add.add_argument('group', required=True, help='Group name', location='values')
    parser_add.add_argument('grant', required=True, help='Group grant content', location='values')
    parser_add.add_argument('backend', required=True, help='Backend', location='values')

    parser_mod = ns.parser()
    parser_mod.add_argument('grant', required=True, help='Group grant content', location='values')
    parser_mod.add_argument('backend', required=True, help='Backend', location='values')

    parser_del = ns.parser()
    parser_del.add_argument('backend', required=True, help='Backend', location='values')

    @api.acl_admin_or_moderator_required(message="Not allowed to view groups list")
    @ns.marshal_list_with(group_fields, code=200, description='Success')
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def get(self):
        """Returns a list of group

        **GET** method provided by the webservice.

        :returns: Groups
        """
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        ret = []
        for _, loader in iteritems(handler.backends):
            groups = loader.groups
            if groups:
                for name, group in iteritems(groups):
                    ret.append({
                        'id': name.lstrip('@'),
                        'grant': group.get('grants', ''),
                        'members': group.get('members', []),
                        'backend': loader.name
                    })
        return ret

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(message="Not allowed to create groups")
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
        """Create a new group"""
        args = self.parser_add.parse_args()

        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0 or \
                args['backend'] not in handler.backends:
            self.abort(404, "No acl backend found")

        loader = handler.backends[args['backend']]

        if loader.add_group is False:
            self.abort(
                500,
                "The '{}' backend does not support group creation"
                "".format(args['backend'])
            )

        success, message, code = loader.add_group(
            args['group'],
            args['grant']
        )
        status = 201 if success else 200
        return [[code, message]], status

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(message="Not allowed to delete this group")
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
        """Delete a group"""
        args = self.parser_del.parse_args()

        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0 or \
                args['backend'] not in handler.backends:
            self.abort(404, "No acl backend found")

        loader = handler.backends[args['backend']]

        if loader.del_group is False:
            self.abort(
                500,
                "The '{}' backend does not support group deletion"
                "".format(args['backend'])
            )

        success, message, code = loader.del_group(
            name
        )
        status = 201 if success else 200
        return [[code, message]], status

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(message="Not allowed to modify this group")
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
        """Change a group"""
        args = self.parser_mod.parse_args()

        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0 or \
                args['backend'] not in handler.backends:
            self.abort(404, "No acl backend found")

        loader = handler.backends[args['backend']]

        if loader.mod_group is False:
            self.abort(
                500,
                "The '{}' backend does not support group modification"
                "".format(args['backend'])
            )

        success, message, code = loader.mod_group(
            name,
            args['grant']
        )
        status = 201 if success else 200
        return [[code, message]], status


@ns.route('/acl/grants',
          '/acl/grants/<name>',
          endpoint='acl_grants')
@ns.doc(
    params={
        'name': 'Grant name',
    }
)
class AclGrants(Resource):
    """The :class:`burpui.api.admin.AclGrants` resource allows you to
    retrieve a list of grants and to add/update/delete them if your
    acl backend support those actions.

    This resource is part of the :mod:`burpui.api.admin` module.
    """
    parser_add = ns.parser()
    parser_add.add_argument('grant', required=True, help='Grant name', location='values')
    parser_add.add_argument('content', required=True, help='Grant content', location='values')
    parser_add.add_argument('backend', required=True, help='Backend', location='values')

    parser_mod = ns.parser()
    parser_mod.add_argument('content', required=True, help='Grant content', location='values')
    parser_mod.add_argument('backend', required=True, help='Backend', location='values')

    parser_del = ns.parser()
    parser_del.add_argument('backend', required=True, help='Backend', location='values')

    @api.acl_admin_or_moderator_required(message="Not allowed to view grants list")
    @ns.marshal_list_with(grant_fields, code=200, description='Success')
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'No backend found',
        },
    )
    def get(self):
        """Returns a list of grants

        **GET** method provided by the webservice.

        :returns: Grants
        """
        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No acl backend found")
        ret = []
        for _, loader in iteritems(handler.backends):
            grants = loader.grants
            if grants:
                for name, grant in iteritems(grants):
                    ret.append({
                        'id': name,
                        'grant': grant,
                        'backend': loader.name
                    })
        return ret

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(message="Not allowed to create grants")
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
        """Create a new grant"""
        args = self.parser_add.parse_args()

        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0 or \
                args['backend'] not in handler.backends:
            self.abort(404, "No acl backend found")

        loader = handler.backends[args['backend']]

        if loader.add_grant is False:
            self.abort(
                500,
                "The '{}' backend does not support grant creation"
                "".format(args['backend'])
            )

        success, message, code = loader.add_grant(
            args['grant'],
            args['content']
        )
        status = 201 if success else 200
        return [[code, message]], status

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(message="Not allowed to delete this grant")
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
        """Delete a grant"""
        args = self.parser_del.parse_args()

        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0 or \
                args['backend'] not in handler.backends:
            self.abort(404, "No acl backend found")

        loader = handler.backends[args['backend']]

        if loader.del_grant is False:
            self.abort(
                500,
                "The '{}' backend does not support grant deletion"
                "".format(args['backend'])
            )

        success, message, code = loader.del_grant(
            name
        )
        status = 201 if success else 200
        return [[code, message]], status

    @api.disabled_on_demo()
    @api.acl_admin_or_moderator_required(message="Not allowed to modify this grant")
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
        """Change a grant"""
        args = self.parser_mod.parse_args()

        try:
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0 or \
                args['backend'] not in handler.backends:
            self.abort(404, "No acl backend found")

        loader = handler.backends[args['backend']]

        if loader.mod_grant is False:
            self.abort(
                500,
                "The '{}' backend does not support grant modification"
                "".format(args['backend'])
            )

        success, message, code = loader.mod_grant(
            name,
            args['content']
        )
        status = 201 if success else 200
        return [[code, message]], status


@ns.route('/acl/backends', endpoint='acl_backends')
class AclBackends(Resource):
    """The :class:`burpui.api.admin.AclBackends` resource allows you to
    retrieve a list of ACL backends with their capabilities.

    This resource is part of the :mod:`burpui.api.admin` module.
    """
    backend_fields = ns.model('AclBackends', {
        'name': fields.String(required=True, description='Backend name'),
        'add_grant': fields.Boolean(required=False, default=False, description='Support grant creation'),
        'mod_grant': fields.Boolean(required=False, default=False, description='Support grant edition'),
        'del_grant': fields.Boolean(required=False, default=False, description='Support grant deletion'),
        'add_group': fields.Boolean(required=False, default=False, description='Support group creation'),
        'mod_group': fields.Boolean(required=False, default=False, description='Support group edition'),
        'del_group': fields.Boolean(required=False, default=False, description='Support group deletion'),
        'add_group_member': fields.Boolean(required=False, default=False, description='Support group member addition'),
        'del_group_member': fields.Boolean(required=False, default=False, description='Support group member deletion'),
        'add_moderator': fields.Boolean(required=False, default=False, description='Support moderator creation'),
        'mod_moderator': fields.Boolean(required=False, default=False, description='Support moderator edition'),
        'del_moderator': fields.Boolean(required=False, default=False, description='Support moderator deletion'),
        'add_admin': fields.Boolean(required=False, default=False, description='Support admin creation'),
        'del_admin': fields.Boolean(required=False, default=False, description='Support admin deletion'),
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
            handler = getattr(bui, 'acl_handler')
        except AttributeError:
            handler = None

        if not handler or len(handler.backends) == 0:
            self.abort(404, "No authentication backend found")
        ret = []
        for name, backend in iteritems(handler.backends):
            back = {}
            back['name'] = name
            for method in ['add_grant', 'del_grant', 'mod_grant', 'add_group', 'del_group', 'mod_group', 'add_group_member', 'del_group_member', 'add_moderator', 'del_moderator', 'mod_moderator', 'add_admin', 'del_admin']:
                back[method] = getattr(backend, method, False) is not False
            ret.append(back)

        return ret


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
    parser_mod.add_argument('password', required=True, help='Password', location='values')
    parser_mod.add_argument('backend', required=True, help='Backend', location='values')
    parser_mod.add_argument('old_password', required=False, help='Old password', location='values')

    parser_del = ns.parser()
    parser_del.add_argument('backend', required=True, help='Backend', location='values')

    @api.acl_admin_or_moderator_required(message="Not allowed to view users list")
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
    @api.acl_admin_or_moderator_required(message="Not allowed to create users")
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
    @api.acl_admin_or_moderator_required(message="Not allowed to delete this user")
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
        is_admin = True

        if not current_user.is_anonymous:
            is_admin = current_user.acl.is_admin()

        if not is_admin and not args['old_password']:
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


@ns.route('/session/<user>',
          '/session/<user>/<uuid:id>',
          endpoint='other_sessions')
@ns.doc(
    params={
        'user': 'User to get sessions from',
        'id': 'Session id',
    }
)
class OtherSessions(Resource):
    """The :class:`burpui.api.admin.OtherSessions` resource allows you to
    retrieve a list of sessions for a given user.

    This resource is part of the :mod:`burpui.api.admin` module.
    """

    @ns.marshal_list_with(session_fields, code=200, description='Success')
    @ns.doc(
        responses={
            403: 'Insufficient permissions',
            404: 'User not found',
        },
    )
    def get(self, user=None, id=None):
        """Returns a list of sessions

        **GET** method provided by the webservice.

        :returns: Sessions
        """
        if id:
            return session_manager.get_session_by_id(str(id))
        if not user:
            self.abort(404, 'User not found')
        return session_manager.get_user_sessions(user)


@ns.route('/me/session',
          '/me/session/<uuid:id>',
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
            return session_manager.get_session_by_id(str(id))
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
        store = session_manager.get_session_by_id(str(id))
        if not store:
            self.abort('Session not found')
        if store.user != user:
            self.abort(403, 'Insufficient permissions')
        if session_manager.invalidate_session_by_id(store.uuid):
            session_manager.delete_session_by_id(store.uuid)
        return [NOTIF_OK, 'Session {} successfully revoked'.format(id)], 201
