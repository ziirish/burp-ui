# -*- coding: utf8 -*-
"""
.. module:: burpui.api.backup
    :platform: Unix
    :synopsis: Burp-UI backup api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from . import api
from ..server import BUIServer  # noqa
from .custom import Resource
from ..exceptions import BUIserverException

from flask import current_app

bui = current_app  # type: BUIServer
ns = api.namespace('backup', 'Backup methods')


@ns.route('/server-backup/<name>',
          '/<server>/server-backup/<name>',
          methods=['GET', 'DELETE'],
          endpoint='is_server_backup')
@ns.route('/do-server-backup/<name>',
          '/<server>/do-server-backup/<name>',
          methods=['PUT'],
          endpoint='server_backup')
@ns.doc(
    params={
        'server': 'Which server to collect data from when in multi-agent mode',
        'name': 'Client name',
    },
)
class ServerBackup(Resource):
    """The :class:`burpui.api.backup.ServerBackup` resource allows you to
    prepare a server-initiated backup.

    This resource is part of the :mod:`burpui.api.backup` module.
    """
    @ns.doc(
        responses={
            200: 'Success',
            400: 'Missing parameter',
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def get(self, server=None, name=None):
        """Tells if a 'backup' file is present

        **GET** method provided by the webservice.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :returns: True if the file is found
        """
        if not name:
            self.abort(400, 'Missing options')
        # Manage ACL
        if (bui.acl and
                (not bui.acl.is_client_allowed(self.username,
                                               name,
                                               server) and not
                 self.is_admin)):
            self.abort(403, 'You are not allowed to access this client')
        try:
            return {'is_server_backup': bui.client.is_server_backup(name, server)}
        except BUIserverException as e:
            self.abort(500, str(e))

    @ns.doc(
        responses={
            200: 'Success',
            400: 'Missing parameter',
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def delete(self, server=None, name=None):
        """Remove the 'backup' file if present

        **DELETE** method provided by the webservice.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :returns: Status message (success or failure)
        """
        if not name:
            self.abort(400, 'Missing options')
        # Manage ACL
        if (bui.acl and
                (not bui.acl.is_client_allowed(self.username,
                                               name,
                                               server) and not
                 self.is_admin)):
            self.abort(403, 'You are not allowed to cancel a backup for this client')
        try:
            return bui.client.cancel_server_backup(name, server)
        except BUIserverException as e:
            self.abort(500, str(e))

    @ns.doc(
        responses={
            201: 'Success',
            400: 'Missing parameter',
            403: 'Insufficient permissions',
            500: 'Internal failure',
        },
    )
    def put(self, server=None, name=None):
        """Schedule a server-initiated backup

        **PUT** method provided by the webservice.

        :param server: Which server to collect data from when in multi-agent
                       mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :returns: Status message (success or failure)
        """
        json = []
        # Check params
        if not name:
            self.abort(400, 'Missing options')
        # Manage ACL
        if (bui.acl and
                (not bui.acl.is_client_allowed(self.username,
                                               name,
                                               server) and not
                 self.is_admin)):
            self.abort(
                403,
                'You are not allowed to schedule a backup for this client'
            )
        try:
            json = bui.client.server_backup(name, server)
            return json, 201
        except BUIserverException as e:
            self.abort(500, str(e))
