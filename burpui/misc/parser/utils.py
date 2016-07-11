# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.parser.utils
    :platform: Unix
    :synopsis: Burp-UI configuration file parser utilities.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import os
import datetime

from copy import copy
from collections import OrderedDict
from glob import glob
from six import iteritems, viewkeys


class Option(object):
    """Object representing an option

    :param name: Option name
    :type name: str

    :param value: Option value
    :type value: str
    """
    type = None
    delim = '='
    _dirty = False

    def __init__(self, name, value=None):
        self.name = name
        self.value = value
        self._dirty = True

    def update(self, value):
        """Change the option value"""
        self._dirty = True
        self.value = value

    def clean(self):
        """Mark the option as clean"""
        self._dirty = False

    def parse(self):
        """Parse the option value"""
        return self.value

    def dump(self):
        """Return the option representation to store in configuration file"""
        return "{} {} {}".format(self.name, self.delim, self.value)

    def __repr__(self):
        """Option representation"""
        return "{} -> {}".format(self.name, self.parse())

    def __str__(self):
        """Option to string"""
        return self.dump()


class OptionStr(Option):
    """Option type String

    Example:
        server = toto
    """
    type = 'string'


class OptionInt(Option):
    """Option type Integer

    Example:
        port = 1234
    """
    type = 'integer'

    def parse(self):
        """Parse the option value"""
        return int(self.value)


class OptionBool(Option):
    """Option type Boolean

    Example:
        hardlinked_archive = 1
    """
    type = 'boolean'

    def parse(self):
        """Parse the option value"""
        try:
            return int(self.value) == 1
        except ValueError:
            return False


class OptionMulti(Option):
    """Option type Multi

    Example:
        keep = 7
        keep = 4
    """
    type = 'multi'

    def __init__(self, name, value=None):
        self.name = name
        self._dirty = True
        if value:
            self.value = [value]
        else:
            self.value = []

    def append(self, value):
        self._dirty = True
        self.value.append(value)
        return self.value

    def remove(self, value):
        self._dirty = True
        self.value.remove(value)
        return self.value

    def index(self, value):
        return self.value.index(value)

    def dump(self):
        """Return the option representation to store in configuration file"""
        ret = u''
        for val in self.value:
            ret += '{} {} {}\n'.format(self.name, self.delim, val)
        return ret.rstrip('\n')


class OptionInc(Option):
    """Option type Include

    Example:
        . incexc/windows
    """
    type = 'include'
    delim = ""

    def __init__(self, parser, name, value=None, root=None, mode='srv'):
        """
        :param parser: Parser instance
        :type parser: :class:`burpui.misc.parser.burp1.Parser`
        """
        super(OptionInc, self).__init__(name, value)
        self.parser = parser
        self.mode = mode
        self.extended = []
        self._dirty = True
        if root:
            self.root = os.path.dirname(root)
        else:
            self.root = None

    def _path_absolute(self, path):
        absolute = path
        if not path.startswith('/'):
            if self.root:
                absolute = os.path.join(self.root, path)
            elif self.mode == 'srv':
                absolute = os.path.join(self.parser.root, path)
            else:
                absolute = os.path.join(self.parser.clientconfdir, path)
        return absolute

    def extend(self):
        """Helper function for the parsing"""
        if not self._dirty and self.extended:
            return self.extended
        paths = []
        root = self._path_absolute(self.value)
        for path in glob(root):
            if self.parser._is_secure_path(path) and os.path.isfile(path) and \
                    not path.endswith('~') and not path.endswith('.back'):
                paths.append(path)
        self.clean()
        self.extended = paths
        return paths

    def parse(self):
        """Parse the option value"""
        return self.extend()

    def dump(self):
        """Return the option representation to store in configuration file"""
        if self.extend() and not self.parser.backend.enforce:
            return '. {}'.format(self.name)
        # if the include did not match anything, we can safely remove it
        return ''


class File(dict):
    """Object representing a configuration file

    :param parser: Parser object
    :type parser: :class:`burpui.misc.parser.doc.Doc`
    """
    delta = datetime.timedelta(seconds=30)
    last = datetime.datetime.now() - delta
    mtime = 0

    def __init__(self, parser, name=None, mode='srv'):
        """
        :param parser: Parser object
        :type parser: :class:`burpui.misc.parser.doc.Doc`

        :param name: File name
        :type name: str

        :param mode: Configuration type
        :type mode: str
        """
        self._dirty = False
        self.parser = parser
        self.mode = mode
        self.name = name
        self.options = OrderedDict()
        self.types = {
            'boolean': OrderedDict(),
            'integer': OrderedDict(),
            'include': OrderedDict(),
            'multi': OrderedDict(),
            'string': OrderedDict(),
        }
        try:
            if self.name:
                self.mtime = os.path.getmtime(self.name)
        except os.error:
            # try to get mtime
            pass

    @property
    def changed(self):
        now = datetime.datetime.now()
        if (now - self.last) > self.delta:
            self.last = now
            try:
                if self.name:
                    mtime = os.path.getmtime(self.name)
                else:
                    return True
            except os.error:
                return True
            oldmtime = self.mtime
            self.mtime = mtime
            return mtime != oldmtime
        if self.mtime == 0:
            return True
        return False

    def clone(self):
        cpy = File(self.parser, name=self.name, mode=self.mode)
        cpy.options = copy(self.options)
        cpy.types = copy(self.types)
        return cpy

    def clean(self):
        self._dirty = False
        for _, opt in iteritems(self.options):
            opt.clean()

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def flatten(self, typ, listed=True, parse=True):
        self._refresh_types()
        if parse:
            self.clean()
        if listed:
            return [
                {
                    'name': key,
                    'value': val.parse() if parse else val
                }
                for key, val in iteritems(self.types[typ])
            ]
        ret = OrderedDict()
        for key, val in iteritems(self.types[typ]):
            ret[key] = val.parse() if parse else val
        return ret

    @property
    def dirty(self):
        self._dirty = self._dirty or \
            any([x._dirty for _, x in iteritems(self.options)])
        return self._dirty

    @property
    def boolean(self):
        return self.flatten('boolean')

    @property
    def integer(self):
        return self.flatten('integer')

    @property
    def include(self):
        return self.flatten('include')

    @property
    def multi(self):
        return self.flatten('multi')

    @property
    def string(self):
        return self.flatten('string')

    def _refresh_types(self):
        if self._dirty:
            for key in viewkeys(self.types):
                self.types[key] = OrderedDict()

            for key, opt in iteritems(self.options):
                self.types[opt.type][key] = opt

        self._dirty = False

    def _options_for_type(self, typ):
        return getattr(self.parser, '{}_{}'.format(typ, self.mode), [])

    def _type_for_option(self, opt):
        if opt == u'.':
            return 'include'

        for typ in ['boolean', 'integer', 'multi', 'string']:
            if opt in self._options_for_type(typ):
                return typ
        return None

    def _new_opt(self, key, value=None, typ=None):
        typ = typ or self._type_for_option(key)

        if typ == 'boolean':
            return OptionBool(key, value)
        if typ == 'integer':
            return OptionInt(key, value)
        if typ == 'multi':
            opt = self.options.get(key, OptionMulti(key))
            opt.append(value)
            return opt
        if typ == 'include':
            key = value
            opt = OptionInc(
                self.parser,
                key,
                value,
                root=self.name,
                mode=self.mode
            )

        return OptionStr(key, value)

    def get(self, key, default=None):
        try:
            return self.options[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        return self.options[key]

    def __setitem__(self, key, value):
        self._dirty = True
        if key in self._options_for_type('boolean'):
            opt = OptionBool(key, value)
        elif key in self._options_for_type('integer'):
            opt = OptionInt(key, value)
        elif key in self._options_for_type('multi'):
            opt = self.options.get(key, OptionMulti(key))
            opt.append(value)
        elif key == u'.':
            key = value
            opt = OptionInc(
                self.parser,
                key,
                value,
                root=self.name,
                mode=self.mode
            )
        else:
            opt = OptionStr(key, value)
        self.options[key] = opt
        self.types[opt.type][key] = opt

    def __repr__(self):
        self._refresh_types()
        ret = u''
        for key, opts in iteritems(self.types):
            ret += '{} =>\n'.format(key)
            for _, opt in iteritems(opts):
                ret += '\t' + repr(opt) + '\n'
        return ret.rstrip('\n')

    def __str__(self):
        ret = u''
        for _, val in iteritems(self.options):
            tmp = str(val)
            if tmp:
                ret += tmp + '\n'
        return ret.rstrip('\n')

    def __len__(self):
        return len(self.options)

    def __delitem__(self, key):
        self._dirty = True
        del self.options[key]

    def clear(self):
        self._dirty = True
        return self.options.clear()

    def copy(self):
        return self.options.copy()

    def has_key(self, k):
        return k in self.options

    def update(self, *args, **kwargs):
        self._dirty = True
        return self.options.update(*args, **kwargs)

    def keys(self):
        return self.options.keys()

    def values(self):
        return self.options.values()

    def items(self):
        return self.options.items()

    def pop(self, *args):
        self._dirty = True
        return self.options.pop(*args)

    def __cmp__(self, dic):
        return cmp(self.options, dic)

    def __contains__(self, item):
        return item in self.options

    def __iter__(self):
        return iter(self.options)

    def __unicode__(self):
        return unicode(self.__repr__())


class Config(File):
    """Object representing a configuration

    A config is like a virtual file so we can reuse some methods

    :param parser: Parser object
    :type parser: :class:`burpui.misc.parser.doc.Doc`
    """

    def __init__(self, path=None, parsed=None, parser=None, mode='srv'):
        """
        :param parser: Parser object
        :type parser: :class:`burpui.misc.parser.doc.Doc`

        :param mode: Configuration type
        :type mode: str
        """
        super(Config, self).__init__(parser, mode)
        # we need an OrderedDict since the order of the configuration matters
        self.files = OrderedDict()
        self.default = path
        self.name = path
        self._dirty = True
        if path:
            if not parsed:
                self.files[path] = File(parser, path, mode=mode)
            else:
                self.files[path] = parsed
            self.files.get(path).set_name(path)

    @property
    def changed(self):
        for path, conf in iteritems(self.files):
            if conf.changed:
                return True
        return False

    def clone(self):
        default = self.get_default(True).clone()
        cpy = Config(self.name, default, self.parser, self.mode)
        for path, parsed in iteritems(self.files):
            if path == self.name:
                continue
            cpy.add_file(parsed.clone(), path)
        return cpy

    def set_default(self, path):
        self.default = path
        self.name = path
        try:
            default = self.get_default(True)
            if not self.parser and default:
                self.parser = getattr(self.get_default(), 'parser')
            if not self.mode and default:
                self.mode = getattr(self.get_default(), 'mode')
        except ValueError:
            pass

    def get_default(self, exc=False):
        if self.default:
            return self.get_file(self.default)
        if exc:
            raise ValueError('No default configuration found')
        return File(self.parser, mode=self.mode)

    def add_file(self, parsed=None, path=None):
        idx = path or self.default
        self.files[idx] = parsed or File(self.parser, mode=self.mode)
        self.files[idx].set_name(idx)
        self._dirty = True
        return self.files[idx]

    def get_file(self, path):
        ret = self.files.get(path, File(self.parser, mode=self.mode))
        return ret

    def del_file(self, path):
        self._dirty = True
        del self.files[path]

    def list_files(self):
        return self.files.keys()

    def _refresh(self):
        if self._dirty or \
                any([x.dirty
                     for _, x in iteritems(self.files)]):

            # cleanup "caches"
            self.options = OrderedDict()
            for key in viewkeys(self.types):
                self.types[key] = OrderedDict()

            # now update caches with new values
            for _, fil in iteritems(self.files):
                self.options.update(fil.options)
                fil.clean()

            for key, val in iteritems(self.options):
                self.types[val.type][key] = val

        self._dirty = False

    def _get(self, key, default=None, raw=False):
        self._refresh()
        try:
            obj = self.options[key]
        except KeyError:
            if self.parser and key in self.parser.defaults:
                obj = self._new_opt(key, self.parser.defaults[key])
            else:
                return default
        return obj if raw else obj.parse()

    def get_raw(self, key, default=None):
        return self._get(key, default, True)

    def get(self, key, default=None):
        return self._get(key, default)

    def __getitem__(self, key):
        self._refresh()
        return self.options[key]

    def __setitem__(self, key, value):
        self.get_default(True)[key] = value
        self._dirty = True

    def __repr__(self):
        self._refresh()
        ret = u''
        for key, fil in iteritems(self.files):
            ret += '>' * 5 + key + '<' * 5 + '\n'
            ret += repr(fil) + '\n'
        return ret.rstrip('\n')

    def __str__(self):
        self._refresh()
        return super(Config, self).__str__()

    def __len__(self):
        self._refresh()
        return len(self.options)

    def __delitem__(self, key):
        del self.get_default(True)[key]
        self._dirty = True

    def clear(self):
        self._dirty = True
        return self.files.clear()

    def copy(self):
        return self.files.copy()

    def has_key(self, k):
        self._refresh()
        return k in self.options

    def update(self, *args, **kwargs):
        self._dirty = True
        return self.get_default(True).update(*args, **kwargs)

    def keys(self):
        self._refresh()
        return self.options.keys()

    def values(self):
        self._refresh()
        return self.options.values()

    def items(self):
        self._refresh()
        return self.options.items()

    def pop(self, *args):
        self._dirty = True
        return self.get_default(True).pop(*args)

    def __cmp__(self, dic):
        self._refresh()
        return cmp(self.options, dic)

    def __contains__(self, item):
        self._refresh()
        return item in self.options

    def __iter__(self):
        self._refresh()
        return iter(self.options)

    def __unicode__(self):
        return unicode(repr(self))
