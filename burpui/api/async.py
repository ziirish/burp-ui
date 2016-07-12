# -*- coding: utf8 -*-
"""
.. module:: burpui.api.async
    :platform: Unix
    :synopsis: Burp-UI async api module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
from . import api
from .custom import Resource

from flask import current_app as bui

ns = api.namespace('async', 'Asynchronous methods')
celery = api.celery


@ns.route('/archive/<name>/<int:backup>',
          '/<server>/archive/<name>/<int:backup>',
          endpoint='async_restore')
class AsyncRestore(Resource):
    """The :class:`burpui.api.restore.AsyncRestore` resource allows you to
    perform a file restoration.

    This resource is part of the :mod:`burpui.api.restore` module.

    The following parameters are supported:
    - ``list``: list of files/directories to restore
    - ``strip``: number of elements to strip in the path
    - ``format``: returning archive format
    - ``pass``: password to use for encrypted backups
    """
    parser = ns.parser()
    parser.add_argument('pass', help='Password to use for encrypted backups', nullable=True)
    parser.add_argument('format', required=False, help='Returning archive format', choices=('zip', 'tar.gz', 'tar.bz2'), default='zip', nullable=True)
    parser.add_argument('strip', type=int, help='Number of elements to strip in the path', default=0, nullable=True)
    parser.add_argument('list', required=True, help='List of files/directories to restore', nullable=False)

    def __init__(self):
        gunicorn = bui.gunicorn
        if gunicorn:
            return
