# -*- coding: utf8 -*-
"""
.. module:: client
    :platform: Unix
    :synopsis: Burp-UI client api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
from burpui.api import api
from burpui.misc.backend.interface import BUIserverException
from flask.ext.restful import reqparse, Resource
from flask.ext.login import current_user, login_required
from flask import jsonify


@api.resource('/api/client-tree.json/<name>/<int:backup>',
              '/api/<server>/client-tree.json/<name>/<int:backup>',
              endpoint='api.client_tree')
class ClientTree(Resource):
    """
    The :class:`burpui.api.client.ClientTree` resource allows you to
    retrieve a list of files in a given backup.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    A mandatory ``GET`` parameter called ``root`` is used to know what path we
    are working on.
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)
        self.parser.add_argument('root', type=str)

    @login_required
    def get(self, server=None, name=None, backup=None):
        """
        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "results": [
                {
                  "date": "2015-05-21 14:54:49",
                  "gid": "0",
                  "inodes": "173",
                  "mode": "drwxr-xr-x",
                  "name": "/",
                  "parent": "",
                  "size": "12.0KiB",
                  "type": "d",
                  "uid": "0"
                }
              ]
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :param backup: The backup we are working on
        :type backup: int

        :returns: The *JSON* described above.
        """
        if not server:
            server = self.parser.parse_args()['server']
        j = []
        if not name or not backup:
            return jsonify(results=j)
        root = self.parser.parse_args()['root']
        try:
            if (api.bui.acl and
                    (not api.bui.acl.is_admin(current_user.name) and not
                     api.bui.acl.is_client_allowed(current_user.name,
                                                   name,
                                                   server))):
                raise BUIserverException('Sorry, you are not allowed to view this client')
            j = api.bui.cli.get_tree(name, backup, root, agent=server)
        except BUIserverException as e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        return jsonify(results=j)


@api.resource('/api/client-stat.json/<name>',
              '/api/<server>/client-stat.json/<name>',
              '/api/client-stat.json/<name>/<int:backup>',
              '/api/<server>/client-stat.json/<name>/<int:backup>',
              endpoint='api.client_stats')
class ClientStats(Resource):
    """
    The :class:`burpui.api.client.ClientStats` resource allows you to
    retrieve a statistics on a given backup for a given client.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, server=None, name=None, backup=None):
        """
        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "results": {
                "dir": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 394,
                  "scanned": 394,
                  "total": 394,
                  "unchanged": 0
                },
                "duration": 5,
                "efs": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 0,
                  "scanned": 0,
                  "total": 0,
                  "unchanged": 0
                },
                "encrypted": true,
                "end": 1422189124,
                "files": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 0,
                  "scanned": 0,
                  "total": 0,
                  "unchanged": 0
                },
                "files_enc": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 1421,
                  "scanned": 1421,
                  "total": 1421,
                  "unchanged": 0
                },
                "hardlink": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 0,
                  "scanned": 0,
                  "total": 0,
                  "unchanged": 0
                },
                "meta": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 0,
                  "scanned": 0,
                  "total": 0,
                  "unchanged": 0
                },
                "meta_enc": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 0,
                  "scanned": 0,
                  "total": 0,
                  "unchanged": 0
                },
                "number": 1,
                "received": 1679304,
                "softlink": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 1302,
                  "scanned": 1302,
                  "total": 1302,
                  "unchanged": 0
                },
                "special": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 0,
                  "scanned": 0,
                  "total": 0,
                  "unchanged": 0
                },
                "start": 1422189119,
                "total": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 3117,
                  "scanned": 3117,
                  "total": 3117,
                  "unchanged": 0
                },
                "totsize": 5345361,
                "vssfooter": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 0,
                  "scanned": 0,
                  "total": 0,
                  "unchanged": 0
                },
                "vssfooter_enc": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 0,
                  "scanned": 0,
                  "total": 0,
                  "unchanged": 0
                },
                "vssheader": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 0,
                  "scanned": 0,
                  "total": 0,
                  "unchanged": 0
                },
                "vssheader_enc": {
                  "changed": 0,
                  "deleted": 0,
                  "new": 0,
                  "scanned": 0,
                  "total": 0,
                  "unchanged": 0
                },
                "windows": "false"
              }
            }


        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :param backup: The backup we are working on
        :type backup: int

        :returns: The *JSON* described above.
        """
        if not server:
            server = self.parser.parse_args()['server']
        j = []
        if not name:
            err = [[1, 'No client defined']]
            return jsonify(notif=err)
        if (api.bui.acl and not
                api.bui.acl.is_client_allowed(current_user.name,
                                              name,
                                              server)):
            err = [[2, 'You don\'t have rights to view this client stats']]
            return jsonify(notif=err)
        if backup:
            try:
                j = api.bui.cli.get_backup_logs(backup, name, agent=server)
            except BUIserverException as e:
                err = [[2, str(e)]]
                return jsonify(notif=err)
        else:
            try:
                cl = api.bui.cli.get_client(name, agent=server)
            except BUIserverException as e:
                err = [[2, str(e)]]
                return jsonify(notif=err)
            err = []
            for c in cl:
                try:
                    j.append(api.bui.cli.get_backup_logs(c['number'], name, agent=server))
                except BUIserverException as e:
                    temp = [2, str(e)]
                    if temp not in err:
                        err.append(temp)
            if err:
                return jsonify(notif=err)
        return jsonify(results=j)


@api.resource('/api/client.json/<name>',
              '/api/<server>/client.json/<name>',
              endpoint='api.client_report')
class ClientReport(Resource):
    """
    The :class:`burpui.api.client.ClientReport` resource allows you to
    retrieve a list of backups for a given client.

    This resource is part of the :mod:`burpui.api.client` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)

    @login_required
    def get(self, server=None, name=None):
        """
        **GET** method provided by the webservice.

        The *JSON* returned is:
        ::

            {
              "results": [
                {
                  "date": "2015-01-25 13:32:00",
                  "deletable": true,
                  "encrypted": true,
                  "number": "1"
                }
              ]
            }

        The output is filtered by the :mod:`burpui.misc.acl` module so that you
        only see stats about the clients you are authorized to.

        :param server: Which server to collect data from when in multi-agent mode
        :type server: str

        :param name: The client we are working on
        :type name: str

        :returns: The *JSON* described above.
        """
        if not server:
            server = self.parser.parse_args()['server']
        try:
            if (api.bui.acl and (
                    not api.bui.acl.is_admin(current_user.name) and
                    not api.bui.acl.is_client_allowed(current_user.name,
                                                      name,
                                                      server))):
                raise BUIserverException('Sorry, you cannot access this client')
            j = api.bui.cli.get_client(name, agent=server)
        except BUIserverException as e:
            err = [[2, str(e)]]
            return jsonify(notif=err)
        return jsonify(results=j)
