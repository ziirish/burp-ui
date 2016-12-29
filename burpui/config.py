# -*- coding: utf8 -*-
"""
.. module:: burpui.config
    :platform: Unix
    :synopsis: Burp-UI config module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import os
import re
import json
import codecs
import shutil
import datetime
import logging
import configobj
import validate

from .desc import __version__, __release__


class BUIConfig(dict):
    """Custom config parser"""
    logger = logging.getLogger('burp-ui')
    delta = datetime.timedelta(seconds=30)
    last = datetime.datetime.now() - delta
    mtime = 0

    def __init__(self, config=None, explain=False, defaults=None):
        """Wrapper around the ConfigObj class

        :param config: Configuration to parse
        :type config: str, list or File

        :param explain: Whether to explain the parsing errors or not
        :type explain: bool

        :param defaults: Default options
        :type defaults: dict
        """
        if config:
            self.parse(config, explain, defaults)

    def parse(self, config, explain=False, defaults=None):
        """Parse the conf

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
            raise validate.VdtMissingValue('No value for this option')
        if not isinstance(value, list):
            return [str(value).lower()]
        return [str(x).lower() for x in value]

    @staticmethod
    def force_string(value):
        if not value:
            raise validate.VdtMissingValue('No value for this option')
        if not isinstance(value, list):
            return str(value)
        return ','.join(value)

    def boolean_or_string(self, value):
        if not value:
            raise validate.VdtMissingValue('No value for this option')
        try:
            caster = self.validator.functions.get('boolean')
            return caster(value)
        except validate.VdtTypeError:
            return value

    def lookup_section(self, section, source=None):
        """Lookup for a given section. If the section is not found in the conf,
        we try to search it in the comments to uncomment it.
        If it is missing from the conf and the comments, we append it in the
        conf.
        """
        ret = True
        if section not in self.options:
            # look for the section in the comments
            conffile = self.options.filename
            source = source or conffile
            ori = []
            with codecs.open(source, 'r', 'utf-8', errors='ignore') as config:
                ori = [x.rstrip('\n') for x in config.readlines()]
            if ori:
                with codecs.open(conffile, 'w', 'utf-8', errors='ignore') as config:
                    found = False
                    for line in ori:
                        if re.match(r'^\s*(#|;)+\s*\[{}\]'.format(section),
                                    line):

                            config.write('[{}]\n'.format(section))
                            found = True
                        else:
                            config.write('{}\n'.format(line))

                    if not found:
                        config.write('[{}]\n'.format(section))
                ret = False
        return ret

    def changed(self, id):
        """Check if the conf has changed"""
        if (datetime.datetime.now() - self.last) > self.delta:
            self._refresh()
        return id != self.mtime

    def _refresh(self, force=False):
        """Refresh conf"""
        self.last = datetime.datetime.now()
        mtime = os.path.getmtime(self.conffile)
        if mtime != self.mtime or force:
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
            with codecs.open(sav, 'r', 'utf-8', errors='ignore') as ori:
                with codecs.open(config, 'w', 'utf-8', errors='ignore') as new:
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


config = BUIConfig()
