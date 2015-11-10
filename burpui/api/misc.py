# -*- coding: utf8 -*-
"""
.. module:: burpui.api.misc
    :platform: Unix
    :synopsis: Burp-UI misc api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
# This is a submodule we can also use "from ..api import api"
from . import api
from ..misc.utils import BUIserverException

from future.utils import iteritems
from flask.ext.restful import reqparse, Resource, abort
from flask.ext.login import current_user, login_required
from flask import render_template, make_response

import time


@api.resource('/api/render-live-template',
              '/api/<server>/render-live-template',
              '/api/render-live-template/<name>',
              '/api/<server>/render-live-template/<name>',
              endpoint='api.render_live_tpl')
class RenderLiveTpl(Resource):
    """The :class:`burpui.api.misc.RenderLiveTpl` resource allows you to
    render the *live view* template of a given client.

    This resource is part of the :mod:`burpui.api.api` module.

    An optional ``GET`` parameter called ``server`` is supported when running
    in multi-agent mode.
    A mandatory ``GET`` parameter called ``name`` is used to know what client we
    are working on.
    """

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('server', type=str)
        self.parser.add_argument('name', type=str)

    @login_required
    def get(self, server=None, name=None):
        """API: render_live_tpl
        :param name: the client name if any. You can also use the GET parameter
        'name' to achieve the same thing
        :returns: HTML that should be included directly into the page
        """
        if not server:
            server = self.parser.parse_args()['server']
        if not name:
            name = self.parser.parse_args()['name']
        # Check params
        if not name:
            abort(400, message='No client name provided')
        # Manage ACL
        if (api.bui.acl and
            (not api.bui.acl.is_client_allowed(current_user.get_id(), name, server) or
             not api.bui.acl.is_admin(current_user.get_id()))):
            abort(403)
        # refresh cache if 30 seconds elapsed since last refresh
        if not api.bui.cli.refresh or (time.time() - api.bui.cli.refresh > 30):
            api.bui.cli.is_one_backup_running()
        if isinstance(api.bui.cli.running, dict):
            if server and name not in api.bui.cli.running[server]:
                abort(404)
            else:
                found = False
                for (k, a) in iteritems(api.bui.cli.running):
                    found = found or (name in a)
                if not found:
                    abort(404)
        else:
            if name not in api.bui.cli.running:
                abort(404)
        try:
            counters = api.bui.cli.get_counters(name, agent=server)
        except BUIserverException:
            counters = []
        response = make_response(render_template('live-monitor-template.html', cname=name, counters=counters, server=server))
        response.headers['content-type'] = 'text/html'
        return response
