# -*- coding: utf8 -*-
"""
.. module:: burpui.config
    :platform: Unix
    :synopsis: Burp-UI config module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import codecs
import os
import re

import configobj
import validate

from .tools.logging import logger


class BUIConfig(dict):
    """Custom config parser"""

    logger = logger
    mtime = 0

    def __init__(self, config=None, defaults=None):
        """Wrapper around the ConfigObj class

        :param config: Configuration to parse
        :type config: str, list or File

        :param defaults: Default options
        :type defaults: dict
        """
        if defaults is not None:
            self.defaults = defaults
        if config:
            self.parse(config, defaults)

    def parse(self, config, defaults=None):
        """Parse the conf

        :param config: Configuration to parse
        :type config: str, list or File

        :param defaults: Default options
        :type defaults: dict
        """
        self.conf = {}
        self.conffile = config
        self.section = None
        if defaults is not None or not hasattr(self, "defaults"):
            self.defaults = defaults
        self.validator = validate.Validator()
        try:
            self.conf = configobj.ConfigObj(config, encoding="utf-8")
            self.mtime = os.path.getmtime(self.conffile)
        except configobj.ConfigObjError as exp:
            # We were unable to parse the config
            self.logger.critical("Unable to parse configuration")
            raise exp

    @property
    def options(self):
        """ConfigObj object"""
        self._refresh()
        return self.conf

    @property
    def id(self):
        """Conf ID to detect changes"""
        return self.mtime

    @staticmethod
    def string_lower_list(value):
        if not value:
            raise validate.VdtMissingValue("No value for this option")
        if not isinstance(value, list):
            return [str(value).lower()]
        return [str(x).lower() for x in value]

    @staticmethod
    def force_string(value):
        if not value:
            raise validate.VdtMissingValue("No value for this option")
        if not isinstance(value, list):
            return str(value)
        return ",".join(value)

    def boolean_or_string(self, value):
        if not value:
            raise validate.VdtMissingValue("No value for this option")
        try:
            caster = self.validator.functions.get("boolean")
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
        if not self.section_exists(section):
            # look for the section in the comments
            conffile = self.options.filename
            source = source or conffile
            ori = []
            with codecs.open(source, "r", "utf-8", errors="ignore") as config:
                ori = [x.rstrip("\n") for x in config.readlines()]
            if ori:
                with codecs.open(conffile, "w", "utf-8", errors="ignore") as config:
                    found = False
                    for line in ori:
                        if re.match(r"^\s*(#|;)+\s*\[{}\]".format(section), line):
                            config.write("[{}]\n".format(section))
                            found = True
                        else:
                            config.write("{}\n".format(line))

                    if not found:
                        config.write("[{}]\n".format(section))
                ret = False
        return ret

    def section_exists(self, section):
        """Check whether a section exists or not"""
        return section in self.options

    def rename_section(self, old_section, new_section, source=None):
        """Rename a given section"""
        ret = False
        if not self.section_exists(old_section):
            return ret
        conffile = self.options.filename
        source = source or conffile
        ori = []
        with codecs.open(source, "r", "utf-8", errors="ignore") as config:
            ori = [x.rstrip("\n") for x in config.readlines()]
        if ori:
            with codecs.open(conffile, "w", "utf-8", errors="ignore") as config:
                for line in ori:
                    if re.match(r"^\s*(#|;)*\s*\[{}\]".format(old_section), line):
                        config.write(
                            "{}\n".format(line.replace(old_section, new_section))
                        )
                        ret = True
                    else:
                        config.write("{}\n".format(line))
        return ret

    def _rename_option_full(self, orig_option, dest_option, orig_section, dest_section):
        """Rename a given option and possibly moves it to another section
        :return: True if the option have been successfully renamed/moved
        :rtype: bool

        :raises ValueError: if the ``orig_section`` does not exist
        :raises KeyError: if the ``orig_option`` does not exist in the ``orig_section``
        """
        if not self.section_exists(orig_section):
            raise ValueError("No such section: {}".format(orig_section))

        orig = self.conf[orig_section]
        if orig_option not in orig:
            raise KeyError(
                "No such option in the [{}] section: {}".format(
                    orig_section, orig_option
                )
            )

        # adding the new section if it is missing
        if orig_section != dest_section and not self.lookup_section(dest_section):
            self._refresh(True)

        dest = self.conf[dest_section]
        comments = orig.comments[orig_option]
        inline_comments = orig.inline_comments[orig_option]

        # copy value and comments from orig to dest
        dest[dest_option] = orig[orig_option]
        dest.comments[dest_option] = comments
        dest.inline_comments[dest_option] = inline_comments

        # remove orig key
        del orig[orig_option]

        # save
        self.conf.write()
        return True

    def rename_option(self, orig_option, dest_option, section):
        """Rename a given option"""
        # this is useless
        if orig_option == dest_option:
            return False
        return self._rename_option_full(orig_option, dest_option, section, section)

    def move_option(self, option, orig_section, dest_section):
        """Move an option to another section, if you need to rename the option use the
        _rename_option_full function instead"""
        # useless
        if orig_section == dest_section:
            return False
        return self._rename_option_full(option, option, orig_section, dest_section)

    def changed(self, id):
        """Check if the conf has changed"""
        # don't use delta for cases where we run several gunicorn workers
        self._refresh()
        return id != self.mtime

    def _refresh(self, force=False):
        """Refresh conf"""
        mtime = os.path.getmtime(self.conffile)
        if mtime != self.mtime or force:
            self.logger.debug("Configuration changed")
            self.mtime = mtime
            self.conf.reload()

    def update_defaults(self, new_defaults):
        """Add new defaults"""
        self.defaults.update(new_defaults)

    def default_section(self, section):
        """Set the default section"""
        self.section = section

    def safe_get(self, key, cast="pass", section=None, defaults=None):
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
            "integer": 0,
            "boolean": False,
        }
        section = section or self.section
        # if the defaults argument is not a dict, assume it's a single value
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
        if defaults and section in defaults and key in defaults.get(section):
            default = defaults.get(section, {}).get(key)
        try:
            caster = self.validator.functions.get(cast)
            if not caster:
                try:
                    caster = getattr(self, cast)
                except AttributeError:
                    self.logger.error("'{}': no such validator".format(cast))
                    return val
            if cast == "force_list" and val is None:
                val = []
            ret = caster(val)
            # special case for boolean and integer, etc.
            if ret is None:
                ret = default
            self.logger.debug(
                "[{}]:{} - found: {}, default: {} -> {}".format(
                    section, key, val, default, ret
                )
            )
        except validate.ValidateError as exp:
            ret = default
            self.logger.info(
                "{}\n[{}]:{} - found: {}, default: {} -> {}".format(
                    str(exp), section, key, val, default, ret
                )
            )
        return ret


config = BUIConfig()
