# -*- coding: utf8 -*-
"""
.. module:: misc
    :platform: Unix
    :synopsis: Burp-UI misc api module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
from burpui.api import api
from burpui.misc.backend.interface import BUIserverException
from flask.ext.restful import reqparse, Resource
from flask.ext.login import current_user, login_required
from flask import jsonify, render_template, make_response, abort


@api.resource('/api/render-live-template',
              '/api/<server>/render-live-template',
              '/api/render-live-template/<name>',
              '/api/<server>/render-live-template/<name>',
              endpoint='api.render_live_tpl')
class RenderLiveTpl(Resource):
    """
    The :class:`burpui.api.misc.RenderLiveTpl` resource allows you to
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
        """
        API: render_live_tpl
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
            abort(500)
        # Manage ACL
        if (api.bui.acl and
            (not api.bui.acl.is_client_allowed(current_user.name, name, server) or
             not api.bui.acl.is_admin(current_user.name))):
            abort(403)
        if isinstance(api.bui.cli.running, dict):
            if server and name not in api.bui.cli.running[server]:
                abort(404)
            else:
                found = False
                for k, a in api.bui.cli.running.iteritems():
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
