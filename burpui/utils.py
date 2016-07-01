# -*- coding: utf8 -*-
"""
.. module:: burpui.utils
    :platform: Unix
    :synopsis: Burp-UI utils module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import os
import re
import math
import string
import sys
import codecs
import datetime
import json
import shutil
import zipfile
import tarfile
import logging
import configobj
import validate

from inspect import currentframe, getouterframes
from ._compat import PY3
from . import __version__, __release__

NOTIF_OK = 0
NOTIF_WARN = 1
NOTIF_ERROR = 2
NOTIF_INFO = 3

if PY3:
    long = int  # pragma: no cover
    basestring = str  # pragma: no cover


class human_readable(long):
    """define a human_readable class to allow custom formatting
    format specifiers supported :
        em : formats the size as bits in IEC format i.e. 1024 bits (128 bytes) = 1Kib
        eM : formats the size as Bytes in IEC format i.e. 1024 bytes = 1KiB
        sm : formats the size as bits in SI format i.e. 1000 bits = 1kb
        sM : formats the size as bytes in SI format i.e. 1000 bytes = 1KB
        cm : format the size as bit in the common format i.e. 1024 bits (128 bytes) = 1Kb
        cM : format the size as bytes in the common format i.e. 1024 bytes = 1KB

    code from: http://code.activestate.com/recipes/578323-human-readable-filememory-sizes-v2/
    """
    def __format__(self, fmt):  # pragma: no cover
        # is it an empty format or not a special format for the size class
        if fmt == "" or fmt[-2:].lower() not in ["em", "sm", "cm"]:
            if fmt[-1].lower() in ['b', 'c', 'd', 'o', 'x', 'n', 'e', 'f', 'g', '%']:
                # Numeric format.
                return long(self).__format__(fmt)
            else:
                return str(self).__format__(fmt)

        if sys.version_info >= (3, 0):
            chars = string.ascii_lowercase
        else:
            chars = string.lowercase
        # work out the scale, suffix and base
        factor, suffix = (8, "b") if fmt[-1] in chars else (1, "B")
        base = 1024 if fmt[-2] in ["e", "c"] else 1000

        # Add the i for the IEC format
        suffix = "i" + suffix if fmt[-2] == "e" else suffix

        mult = ["", "K", "M", "G", "T", "P"]

        val = float(self) * factor
        i = 0 if val < 1 else int(math.log(val, base)) + 1
        v = val / math.pow(base, i)
        v, i = (v, i) if v > 0.5 else (v * base, i - 1)

        # Identify if there is a width and extract it
        width = "" if fmt.find(".") == -1 else fmt[:fmt.index(".")]
        precis = fmt[:-2] if width == "" else fmt[fmt.index("."):-2]

        # do the precision bit first, so width/alignment works with the suffix
        if float(self) == 0:
            return "{0:{1}f}".format(v, precis)
        t = ("{0:{1}f}" + mult[i] + suffix).format(v, precis)

        return "{0:{1}}".format(t, width) if width != "" else t


if PY3:  # pragma: no cover
    class BUIlogger(logging.Logger):
        padding = 0
        """Logger class for more convenience"""
        def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
            """
            Try to guess where was call the function
            """
            cf = currentframe()
            caller = getouterframes(cf)
            cpt = 0
            size = len(caller)
            me = __file__
            if me.endswith('.pyc'):
                me = me[:-1]
            # It's easy to get the _logger parent function because it's the
            # following frame
            while cpt < size - 1:
                (_, filename, _, function_name, _, _) = caller[cpt]
                if function_name == '_logger' and filename == me:
                    cpt += 1
                    break
                cpt += 1
            cpt += self.padding
            (frame, filename, line_number, function_name, lines, index) = caller[cpt]
            return super(BUIlogger, self).makeRecord(name, level, filename, line_number, msg, args, exc_info, func=function_name, extra=extra, sinfo=sinfo)
else:
    class BUIlogger(logging.Logger):
        padding = 0
        """Logger class for more convenience"""
        def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
            """Try to guess where was call the function"""
            cf = currentframe()
            caller = getouterframes(cf)
            cpt = 0
            size = len(caller)
            me = __file__
            if me.endswith('.pyc'):
                me = me[:-1]
            # It's easy to get the _logger parent function because it's the
            # following frame
            while cpt < size - 1:
                (_, filename, _, function_name, _, _) = caller[cpt]
                if function_name == '_logger' and filename == me:
                    cpt += 1
                    break
                cpt += 1
            cpt += self.padding
            (frame, filename, line_number, function_name, lines, index) = caller[cpt]
            return super(BUIlogger, self).makeRecord(name, level, filename, line_number, msg, args, exc_info, func=function_name, extra=extra)


class BUIlogging(object):
    logger = None
    monkey = None
    padding = 0
    """Provides a generic logging method for all modules"""
    def _logger(self, level, msg, *args):
        """generic logging method so that the logging is backend-independent"""
        if self.logger and self.logger.getEffectiveLevel() <= logging.getLevelName(level.upper()):
            sav = None
            if not self.monkey:
                self.monkey = BUIlogger(__name__)
            # bui-agent overrides the _logger function so we add a padding offset
            self.monkey.padding = self.padding
            # dynamically monkey-patch the makeRecord function
            sav = self.logger.makeRecord
            self.logger.makeRecord = self.monkey.makeRecord
            self.logger.log(logging.getLevelName(level.upper()), msg, *args)
            self.logger.makeRecord = sav


class BUIcompress():
    """Provides a context to generate any kind of archive supported by burp-ui"""
    def __init__(self, name, archive, zip64=False):  # pragma: no cover
        self.name = name
        self.archive = archive
        self.zip64 = zip64

    def __enter__(self):
        self.arch = None
        if self.archive == 'zip':
            self.arch = zipfile.ZipFile(self.name, mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=self.zip64)
        elif self.archive == 'tar.gz':
            self.arch = tarfile.open(self.name, 'w:gz')
        elif self.archive == 'tar.bz2':
            self.arch = tarfile.open(self.name, 'w:bz2')
        return self

    def __exit__(self, type, value, traceback):
        self.arch.close()

    def append(self, path, arcname):
        if self.archive == 'zip':
            if os.path.islink(path):
                # This is a symlink, we virtually create one in memory
                # because zipfile does not seem to support them natively
                vfile = zipfile.ZipInfo()
                vfile.filename = arcname  # That's the name of the actual file
                vfile.external_attr |= 0o120000 << long(16)  # symlink file type
                vfile.compress_type = zipfile.ZIP_STORED
                # os.readlink gives us the target of the symlink
                self.arch.writestr(vfile, os.readlink(path))
            else:
                self.arch.write(path, arcname)
        elif self.archive in ['tar.gz', 'tar.bz2']:
            self.arch.add(path, arcname=arcname, recursive=False)


def implement(func):
    """A decorator indicating the method is implemented.

    For the agent and the 'multi' backend, we inherit the backend interface but
    we don't really implement it because we just act as a proxy.
    But maintaining the exhaustive list of methods in several places to always
    implement the same "proxy" thing was painful so I ended up cheating to
    dynamically implement those methods thanks to the __getattribute__ magic
    function.

    But sometimes we want to implement specific things, hence this decorator
    to indicate we don't want the default "magic" implementation and use the
    custom implementation instead.
    """
    func.__ismethodimplemented__ = True
    return func


def basic_login_from_request(request, app):
    """Check 'Authorization' headers and log the user in if possible.

    :param request: The input request
    :type request: :class:`flask.Request`

    :param app: The application context
    :type app: :class:`burpui.server.BUIServer`
    """
    if app.auth != 'none':
        auth = request.authorization
        if auth:
            app.logger.debug('Found user: {}'.format(auth.username))
            user = app.uhandler.user(auth.username)
            if user.active and user.login(auth.password):
                from flask_login import login_user
                login_user(user)
                app.logger.debug('Successfully logged in')
                return user
            app.logger.warning('Failed to log-in')
    return None


class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    In nginx:

    ::

        location /myprefix {
            proxy_pass http://192.168.0.1:5001;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Scheme $scheme;
            proxy_set_header X-Script-Name /myprefix;
        }


    In Apache:

    ::

        <Location /myprefix>
            ProxyPass http://192.168.0.1:5001
            ProxyPassReverse http://192.168.0.1:5001
            RequestHeader set X-Script-Name /myprefix
        </Location>


    :param wsgi_app: the WSGI application

    Inspired by: http://flask.pocoo.org/snippets/35/
    '''
    def __init__(self, wsgi_app, app):
        self.wsgi_app = wsgi_app
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', self.app.prefix)
        if script_name:
            if script_name.startswith('/'):
                environ['SCRIPT_NAME'] = script_name
                path_info = environ['PATH_INFO']
                if path_info.startswith(script_name):
                    environ['PATH_INFO'] = path_info[len(script_name):]
            else:
                self.app.warning("'prefix' must start with a '/'!")

        return self.wsgi_app(environ, start_response)


class BUIConfig(object):
    """Custom config parser"""
    logger = logging.getLogger('burp-ui')
    delta = datetime.timedelta(seconds=30)
    last = datetime.datetime.now() - delta
    mtime = 0

    def __init__(self, config, explain=False, defaults=None):
        """Wrapper around the ConfigObj class

        :param config: Configuration to parse
        :type config: str, list or File

        :param explain: Whether to explain the parsing errors or not
        :type explain: bool

        :param defaults: Default options
        :type defaults: dict
        """
        self.conf = {}
        self.conffile = config
        self.section = None
        self.defaults = defaults
        self.validator = validate.Validator()
        try:
            self.conf = configobj.ConfigObj(config, encoding='utf-8')
            self.last = datetime.datetime.now()
            self.mtime = os.path.getmtime(self.conffile)
        except configobj.ConfigObjError as exp:
            # We were unable to parse the config, maybe we need to
            # convert/update it
            self.logger.warning(
                'Unable to parse the configuration... Trying to convert it'
            )
            # if conversion is successful, give it another try
            if self._convert(config):
                # This time, if it fails, the exception will be forwarded
                try:
                    self.conf = configobj.ConfigObj(config)
                except configobj.ConfigObjError as exp2:
                    if explain:
                        self._explain(exp2)
                    else:
                        raise exp2
            else:
                self.logger.critical('Unable to convert configuration')
                if explain:
                    self._explain(exp)
                else:
                    raise exp

    @property
    def options(self):
        """ConfigObj object"""
        if (datetime.datetime.now() - self.last) > self.delta:
            self._refresh()
        return self.conf

    @property
    def id(self):
        """Conf ID to detect changes"""
        return self.mtime

    @staticmethod
    def string_lower_list(value):
        if not value:
            raise validate.VdtMissingValue('Option not found')
        if not isinstance(value, list):
            return [str(value).lower()]
        return [str(x).lower() for x in value]

    def changed(self, id):
        """Check if the conf has changed"""
        if (datetime.datetime.now() - self.last) > self.delta:
            self._refresh()
        return id != self.mtime

    def _refresh(self):
        """Refresh conf"""
        self.last = datetime.datetime.now()
        mtime = os.path.getmtime(self.conffile)
        if mtime != self.mtime:
            self.logger.debug('Configuration changed')
            self.mtime = mtime
            self.conf.reload()

    def update_defaults(self, new_defaults):
        """Add new defaults"""
        self.defaults.update(new_defaults)

    def default_section(self, section):
        """Set the default section"""
        self.section = section

    def _convert(self, config):
        """Convert an old config to a new one"""
        sav = '{}.back'.format(config)
        current_section = None

        if os.path.exists(sav):
            self.logger.error(
                'Looks like the configuration file has already been converted'
            )
            return False

        try:
            shutil.copy(config, sav)
        except IOError as exp:
            self.logger.error(str(exp))
            return False

        try:
            with codecs.open(sav, 'r', 'utf-8') as ori:
                with codecs.open(config, 'w', 'utf-8') as new:
                    # We add some headers
                    new.write('# Auto-generated file from a previous version\n')
                    new.write('# @version@ - {}\n'.format(__version__))
                    new.write('# @release@ - {}\n'.format(__release__))
                    for line in ori.readlines():
                        line = line.rstrip('\n')
                        search = re.search(r'^\s*(#?)\s*\[([^\]]+)\]\s*', line)
                        if search:
                            if not search.group(1):
                                current_section = search.group(2)
                        # if we find old style config lines, we convert them
                        elif re.match(r'^\s*\S+\s*:\s*.+$', line) and \
                                re.match(r'^\s*[^\[]', line):
                            key, val = re.split(r'\s*:\s*', line, 1)
                            # We support *objects* but we need to serialize them
                            try:
                                jsn = json.loads(val)
                                # special case, we re-format the admin value
                                if current_section == 'BASIC:ACL' and \
                                        key == 'admin' and \
                                        isinstance(jsn, list):
                                    val = ','.join(jsn)
                                elif isinstance(jsn, list) or \
                                        isinstance(jsn, dict):
                                    val = "'{}'".format(json.dumps(jsn))
                            except ValueError:
                                pass
                            line = '{} = {}'.format(key, val)

                        new.write('{}\n'.format(line))

        except IOError as exp:
            self.logger.error(str(exp))
            return False
        return True

    @staticmethod
    def _explain(exception):
        """Explain parsing errors

        :param exception: Exception object
        :type exception: :class:`configobj.ConfigObjError`
        """
        message = u'\n'
        for error in exception.errors:
            message += error.message + '\n'

        raise configobj.ConfigObjError(message.rstrip('\n'))

    def safe_get(
            self,
            key,
            cast='pass',
            section=None,
            defaults=None):
        """Safely return the asked option

        :param key: Key name
        :type key: str

        :param cast: How to cast the option
        :type cast: str

        :param section: Section name
        :type section: str

        :param defaults: Default options
        :type defaults: dict, mixed

        :returns: The value of the asked option
        """
        # The configobj validator is sooo broken. We need to workaround it...
        default_by_type = {
            'integer': 0,
            'boolean': False,
        }
        section = section or self.section
        # if the defaults argument is not a list, assume it's a single value
        if defaults and not isinstance(defaults, dict):
            defaults = {section: {key: defaults}}
        defaults = defaults or self.defaults
        if section not in self.conf:
            self.logger.warning("No '{}' section found".format(section))
            if defaults:
                return defaults.get(section, {}).get(key)
            return None

        val = self.conf.get(section).get(key)
        default = default_by_type.get(cast)
        if defaults and section in defaults and \
                key in defaults.get(section):
            default = defaults.get(section, {}).get(key)
        try:
            caster = self.validator.functions.get(cast)
            if not caster:
                try:
                    caster = getattr(self, cast)
                except AttributeError:
                    self.logger.error(
                        "'{}': no such validator".format(cast)
                    )
                    return val
            ret = caster(val)
            # special case for boolean and integer, etc.
            if ret is None:
                ret = default
            self.logger.debug(
                '[{}]:{} - found: {}, default: {} -> {}'.format(
                    section,
                    key,
                    val,
                    default,
                    ret
                )
            )
        except validate.ValidateError as exp:
            ret = default
            self.logger.warning(
                '{}\n[{}]:{} - found: {}, default: {} -> {}'.format(
                    str(exp),
                    section,
                    key,
                    val,
                    default,
                    ret
                )
            )
        return ret
