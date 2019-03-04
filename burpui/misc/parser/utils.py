# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.parser.utils
    :platform: Unix
    :synopsis: Burp-UI configuration file parser utilities.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>
"""
import os
import re
import codecs
import shutil

from copy import copy
from hashlib import md5
from collections import OrderedDict
from glob import glob
from six import iteritems, viewkeys

from ...utils import NOTIF_ERROR, NOTIF_OK, NOTIF_WARN
from ...security import sanitize_string
from ...datastructures import MultiDict


RESET_IDENTIFIER = '_reset_bui_CUSTOM'
BEGIN_TEMPLATES = 'BURP-UI TEMPLATES'
END_TEMPLATES = 'END TEMPLATES'


class Option(object):
    """Object representing an option

    :param name: Option name
    :type name: str

    :param value: Option value
    :type value: str
    """
    type = None
    delim = '='
    reset_delim = ':='
    _dirty = False
    idx = -1

    def __init__(self, name, value=None):
        self.name = name
        self.value = value
        self._dirty = True
        # is there a special := syntax for this option
        self._is_reset = []

    @property
    def dirty(self):
        return self._dirty

    def is_reset(self):
        """Check if a special ':=' syntax is required based on the value"""
        if self.idx < 0 or not self._is_reset:
            return False
        if self.idx >= len(self._is_reset):
            self.idx = len(self._is_reset) - 1
        return self._is_reset[self.idx]

    def set_reset(self, value=False):
        """Mark this value as requiring a special ':=' syntax"""
        self._is_reset.append('{}'.format(value).lower() == 'true')
        self.idx += 1

    def set_resets(self, resets):
        self._is_reset = resets

    def get_resets(self):
        return self._is_reset

    def get_reset(self):
        """Return the reset list/flag"""
        return self.is_reset()

    def update(self, value):
        """Change the option value"""
        self._dirty = True
        self.value = value
        self._is_reset = []

    def clean(self):
        """Mark the option as clean"""
        self._dirty = False

    def parse(self):
        """Parse the option value"""
        return self.value

    def dump(self):
        """Return the option representation to store in configuration file"""
        delim = self.delim
        if self.is_reset():
            delim = self.reset_delim
        return "{} {} {}".format(self.name, delim, self.value)

    def __repr__(self):
        """Option representation"""
        return "{} -> {}".format(self.name, self.parse())

    def __str__(self):
        """Option to string"""
        return self.dump()

    def __eq__(self, other):
        other_name = getattr(other, 'name', None)
        other_value = getattr(other, 'value', None)
        return self.name == other_name and self.value == other_value


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
        try:
            return int(self.value)
        except (ValueError, TypeError):
            return 0


class OptionBool(Option):
    """Option type Boolean

    Example:
        hardlinked_archive = 1
    """
    type = 'boolean'

    def __init__(self, name, value=None):
        self.name = name
        self.value = self._format_value(value)
        self._dirty = True
        self._is_reset = []

    def update(self, value):
        """Change the option value"""
        self._dirty = True
        self.value = self._format_value(value)
        self._is_reset = []

    def _format_value(self, value):
        if self._parse(value):
            return 1
        return 0

    @staticmethod
    def _parse(value):
        try:
            if not value:
                return False
            elif value is True:
                return True
            elif '{}'.format(value).lower() == 'true':
                return True
            # any string will raise the ValueError
            return int(value) == 1
        except ValueError:
            return False

    def parse(self):
        """Parse the option value"""
        return self._parse(self.value)


class OptionInc(Option):
    """Option type Include

    Example:
        . incexc/windows
    """
    type = 'include'
    delim = ""

    def __init__(self, parser, name, value=None, root=None, mode='srv', template=False):
        """
        :param parser: Parser instance
        :type parser: :class:`burpui.misc.parser.burp1.Parser`
        """
        super(OptionInc, self).__init__(name, value)
        self.parser = parser
        self.mode = mode
        self.is_template = template
        self.extended = []
        self._is_reset = []
        self._dirty = True
        self._glob = False
        self._glob_dir = None
        self._glob_mtime = -1
        if root:
            self.root = os.path.dirname(root)
        else:
            self.root = None

    @property
    def dirty(self):
        return self._dirty or self._glob_changed

    def _path_absolute(self, path):
        absolute = path
        if not os.path.isabs(path):
            if self.root:
                absolute = os.path.join(self.root, path)
            elif self.mode == 'srv':
                absolute = os.path.join(self.parser.root, path)
            else:
                absolute = os.path.join(self.parser.clientconfdir, path)
        return absolute

    @property
    def _glob_changed(self):
        if not self._glob or not self._glob_dir:
            return False
        mtime = os.path.getmtime(self._glob_dir)
        return mtime != self._glob_mtime

    def extend(self):
        """Helper function for the parsing"""
        if not self._dirty and self.extended and not self._glob_changed:
            return self.extended
        paths = []
        root = self._path_absolute(self.value)
        for path in glob(root):
            if self.parser._is_secure_path(path) and os.path.isfile(path) and \
                    not path.endswith('~') and not path.endswith('.back'):
                paths.append(path)
        # more than one match mean we have a glob, for sure
        if len(paths) > 1 or (len(paths) == 1 and paths[0] != root):
            self._glob = True
            self._glob_dir = os.path.dirname(root)
            self._glob_mtime = os.path.getmtime(self._glob_dir)
        else:
            self._glob = False
        self.clean()
        self.extended = paths
        return paths

    def parse(self):
        """Parse the option value"""
        return self.extend()

    def dump(self):
        """Return the option representation to store in configuration file"""
        if self.extend() and not self.parser.backend.enforce:
            name = self.name or ''
            if self.is_template and name.startswith('../'):
                name = str(name[3:])
            return '. {}'.format(name)
        # if the include did not match anything, we can safely remove it
        return ''


class OptionTpl(Option):
    """Option type Template

    Example:
        . .buitemplates/windows
    """
    type = 'template'
    delim = ""

    def __init__(self, parser, name, value=None):
        """
        :param parser: Parser instance
        :type parser: :class:`burpui.misc.parser.burp1.Parser`
        """
        super(OptionTpl, self).__init__(name, value)
        self.parser = parser
        self.extended = False
        self._dirty = True
        if name:
            self._id = name.split(os.path.sep)[-1]
        else:
            self._id = ''

    @property
    def dirty(self):
        return self._dirty

    def _path_absolute(self, path):
        absolute = path
        if not os.path.isabs(path):
            absolute = os.path.join(self.parser.clientconfdir, path)
        return absolute

    def extend(self):
        """Helper function for the parsing"""
        if not self._dirty and self.extended:
            return self.extended
        path = self._path_absolute(self.value)
        self.clean()
        self.extended = path
        return path

    def parse(self):
        """Parse the option value"""
        return self.extend()

    def dump(self):
        """Return the option representation to store in configuration file"""
        if self.extend() and not self.parser.backend.enforce:
            return '. {}'.format(self.name)
        # if the include did not match anything, we can safely remove it
        return ''


option_for_type = {
    'integer': OptionInt,
    'string': OptionStr,
    'boolean': OptionBool,
    'include': OptionInc,
}


class OptionMulti(Option):
    """Option type Multi

    Example:
        keep = 7
        keep = 4
    """
    type = 'multi'

    def __init__(self, parser, name, value=None):
        self.parser = parser
        self.name = name
        self._dirty = True
        self._is_reset = []
        self.content_type = self.parser.advanced_type.get(name, 'string')
        self.associate = getattr(self.parser, 'pair_associations', {}).get(self.name)
        self._init_value(value)
        self.idx = len(self.value) - 1

    def _init_value(self, value):
        if value:
            container = self._obj_for_type()
            if not isinstance(value, list):
                value = container(self.name, value)
                self.value = [value]
            else:
                self.value = [container(self.name, x) for x in value]
        else:
            self.value = []

    def _obj_for_type(self):
        return option_for_type.get(self.content_type, OptionStr)

    def _wrap_object(self, value):
        container = self._obj_for_type()
        return container(self.name, value)

    def append(self, value, reset=None):
        self._dirty = True
        if isinstance(value, list):
            for v in value:
                self.value.append(self._wrap_object(v))
        else:
            self.value.append(self._wrap_object(value))
        if reset is not None:
            self.set_reset(reset)
        return self.value

    def update(self, value):
        """Change the option value"""
        self._dirty = True
        self._init_value(value)
        self._is_reset = []

    def remove(self, value):
        idx = self.value(value)
        del self.value[idx]
        self._dirty = True
        return self.value

    def index(self, value):
        for i, x in enumerate(self):
            if x == value:
                return i
        raise ValueError('{} is not in list'.format(value))

    def len(self):
        return len(self.value)

    def dump(self, start=0, strict=True):
        """Return the option representation to store in configuration file"""
        ret = u''
        if start > len(self.value):
            return ret
        res = [self.dump_index(i, strict) for i in range(start, len(self.value))]
        ret = u'\n'.join(res)
        return ret.rstrip('\n')

    def dump_index(self, index, strict=True):
        if index >= len(self.value):
            return ''
        val = self.value[index]
        delim = self.delim
        self.idx = index
        if self.is_reset():
            delim = self.reset_delim
        return '{} {} {}'.format(self.name, delim, sanitize_string('{}'.format(val.parse()), strict))

    def parse(self):
        return [x.parse() for x in self.value]

    def get_reset(self):
        return self._is_reset

    def __len__(self):
        return len(self.value)

    def __getitem__(self, ii):
        return self.value[ii].parse()

    def __delitem__(self, ii):
        del self.value[ii]
        self._dirty = True

    def __setitem__(self, ii, val):
        self.value[ii] = self._wrap_object(val)
        self._dirty = True

    def insert(self, ii, val):
        self.value.insert(ii, self._wrap_object(val))

    def __iter__(self):
        for x in self.value:
            yield x.parse()


class OptionPair(Option, dict):
    """Option type Pair

    Example:
        port = 4971
        max_children = 5
    """
    type = 'pair'

    def __init__(self, parser, name, value=None):
        self.parser = parser
        self.name = name
        self.association = getattr(self.parser, 'pair_associations', {}).get(self.name)
        self._dirty = True
        self._init_value(name, value)
        # is there a special := syntax for this option
        self._is_reset = []

    def _init_value(self, name, value):
        self.value = {}
        if value:
            value = OptionMulti(self.parser, name, value)
            self.value[name] = value

    def append(self, name, value):
        self._dirty = True
        if name != self.name:
            self.association = name
        if name in self.value:
            self.value[name].append(value)
        else:
            self.value[name] = OptionMulti(self.parser, name, value)
        return self.value

    def update(self, name, value):
        """Change the option value"""
        self._dirty = True
        self._init_value(name, value)
        self._is_reset = []

    def remove(self, name, value):
        self._dirty = True
        try:
            self.value.get(name, []).remove(value)
        except ValueError:
            pass
        return self.value

    def index(self, name, value):
        try:
            return self.value.get(name, []).index(value)
        except ValueError:
            return -1

    def len(self, name):
        if name in self.value:
            return self.value[name].len()
        return -1

    def dump(self, start=0, strict=True):
        """Return the option representation to store in configuration file"""
        ret = u''
        try:
            self_length = len(self.value[self.name])
        except KeyError:
            self_length = -1
        try:
            associate_length = len(self.value[self.association])
        except KeyError:
            associate_length = -1
        if start >= self_length and start >= associate_length:
            return ret
        for idx in range(start, max(self_length, associate_length)):
            v1 = self.dump_index(self.name, idx, strict)
            v2 = self.dump_index(self.association, idx, strict)
            if v1:
                ret += '{}\n'.format(v1)
            if v2:
                ret += '{}\n'.format(v2)
        return ret.rstrip('\n')

    def dump_index(self, name, index, strict):
        length = self.len(name)
        try:
            length = len(self.value[name])
        except KeyError:
            length = -1
        if index >= length:
            return u''
        return self.value.get(name).dump_index(index, strict)

    def parse(self, key=None):
        if key:
            if key not in self.value:
                return []
            return self.value[key].parse()
        ret = {}
        for key, opts in iteritems(self.value):
            ret[key] = opts.parse()
        return ret

    def __setitem__(self, key, item):
        self.append(key, item)

    def __getitem__(self, key):
        return self.value.get(key, OptionMulti(self.parser, key))

    def get(self, key, default=None):
        try:
            return self.value[key]
        except KeyError:
            if default:
                return default
            return OptionMulti(self.parser, key)

    def __len__(self):
        return len(self.value)

    def __delitem__(self, key):
        del self.value[key]

    def clear(self):
        self.value.clear()

    def copy(self):
        return self.value.copy()

    def has_key(self, key):
        return key in self.value

    def keys(self):
        return self.value.keys()

    def values(self):
        return self.value.values()

    def items(self):
        return self.value.items()

    def pop(self, *args):
        return self.value.pop(*args)

    def __contains__(self, item):
        return item in self.value

    def __iter__(self):
        return iter(self.value)


class File(dict):
    """Object representing a configuration file

    :param parser: Parser object
    :type parser: :class:`burpui.misc.parser.doc.Doc`
    """
    md5 = None
    mtime = 0

    def __init__(self, parser, name=None, mode='srv', parent=None, is_template=False):
        """
        :param parser: Parser object
        :type parser: :class:`burpui.misc.parser.doc.Doc`

        :param name: File name
        :type name: str

        :param mode: Configuration type
        :type mode: str
        """
        # _dirty is used to know if the object changed
        self._dirty = False
        # _changed is used to know if the file changed since last read
        self._changed = True
        # _parsing_templates is used to know if we are currently parsing templates
        self._parsing_templates = False
        # cache the content of the file
        self._raw = []
        self._raw_data = MultiDict()
        self._data = MultiDict()
        self._is_template = is_template
        self.parser = parser
        self.mode = mode
        self.name = name
        self.parent = parent
        self.updated = []
        self.associations = set()
        self.reset = {}
        self.options = OrderedDict()
        self.types = {
            'boolean': OrderedDict(),
            'integer': OrderedDict(),
            'include': OrderedDict(),
            'multi': OrderedDict(),
            'pair': OrderedDict(),
            'string': OrderedDict(),
            'template': OrderedDict(),
        }
        if self.name:
            self.parse()

    @property
    def changed(self):
        for key, val in iteritems(self.types['include']):
            if val.dirty:
                self._changed = True
                return self._changed
        for key, val in iteritems(self.types['template']):
            if val.dirty:
                self._changed = True
                return self._changed
        try:
            if self.name:
                mtime = os.path.getmtime(self.name)
            else:
                self._changed = True
                return True
        except os.error:
            self._changed = True
            return True
        if mtime != self.mtime:
            self._changed = self._md5 != self.md5
            return self._changed
        self._changed = mtime != self.mtime
        return self._changed

    def _ret_data(self, raw=True):
        if raw:
            ret = self._raw_data
        else:
            ret = self._data
        if ret and not self.dirty:
            return ret
        ret.clear()
        for key, val in iteritems(self.options):
            if isinstance(val, OptionMulti) and not raw:
                ret.setlist(key, val.parse())
            elif isinstance(val, OptionPair) and not raw:
                ret.setlist(key, val.parse(key))
            else:
                ret[key] = val if raw else val.parse()
        return ret

    @property
    def raw_data(self):
        return self._ret_data()

    @property
    def data(self):
        return self._ret_data(False)

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
        self.parse()

    def flatten(self, typ, listed=True, parse=True):
        self._refresh_types()
        if listed:
            return [
                {
                    'name': key,
                    'value': opt.parse() if parse else opt,
                    'reset': opt.get_reset()
                }
                for key, opt in iteritems(self.types[typ])
            ]
        ret = OrderedDict()
        if typ in self.types:
            for key, opt in iteritems(self.types[typ]):
                ret[key] = opt.parse() if parse else opt
        return ret

    def flatten_obj(self, name, obj, parse=True):
        return {
            'name': name,
            'value': obj.parse() if parse else obj,
            'reset': obj.get_reset()
        }

    @property
    def dirty(self):
        if not self._dirty:
            self._dirty = any([x.dirty for _, x in iteritems(self.options)])
        return self._dirty

    @property
    def boolean(self):
        return self.flatten('boolean')

    @property
    def integer(self):
        return self.flatten('integer')

    @property
    def pair(self):
        return self.flatten('pair')

    @property
    def include(self):
        return self.flatten('include')

    @property
    def template(self):
        ret = []
        for tpl in self.flatten('template', parse=False):
            ret.append({
                'value': tpl['name'],
                'name': tpl['value']._id,
            })
        return ret

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
                if key not in self.associations:
                    self.types[opt.type][key] = opt

        self._dirty = False

    def _options_for_type(self, typ):
        return getattr(self.parser, '{}_{}'.format(typ, self.mode), [])

    def _type_for_option(self, opt):
        if opt == u'.':
            return 'include'

        for typ in ['boolean', 'integer', 'multi', 'string', 'pair']:
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
            opt = self.options.get(key, OptionMulti(self.parser, key))
            opt.append(value)
            return opt
        if typ == 'pair':
            return OptionPair(self.parser, key, value)
        if typ == 'include':
            key = value
            return OptionInc(
                self.parser,
                key,
                value,
                root=self.name,
                mode=self.mode,
                template=self._is_template
            )

        return OptionStr(key, value)

    @property
    def _md5(self):
        """Compute the md5sum of the file"""
        hash_md5 = md5()
        try:
            with open(self.name, "rb") as bfile:
                for chunk in iter(lambda: bfile.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except IOError:
            return None

    def get(self, key, default=None):
        try:
            if key in self._options_for_type('pair'):
                return self.options[key].get(key)
            return self.options[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        if key in self._options_for_type('pair'):
            return self.options[key].get(key)
        return self.options[key]

    def __setitem__(self, key, value):
        self._dirty = True
        if key in self._options_for_type('boolean'):
            opt = OptionBool(key, value)
        elif key in self._options_for_type('integer'):
            opt = OptionInt(key, value)
        elif key in self._options_for_type('multi'):
            opt = self.options.get(key, OptionMulti(self.parser, key))
            opt.append(value)
        elif key in self._options_for_type('pair'):
            association = self.parser.pair_associations.get(key)
            if key not in self.options and association not in self.options:
                self.associations.add(association)
                opt = OptionPair(self.parser, key)
            elif association in self.options:
                opt = self.options.get(association)
            else:
                opt = self.options.get(key)
            opt.append(key, value)
        elif key == u'.':
            key = value
            if self._parsing_templates:
                opt = OptionTpl(self.parser, key, value)
            else:
                opt = OptionInc(
                    self.parser,
                    key,
                    value,
                    root=self.name,
                    mode=self.mode,
                    template=self._is_template
                )
                if self._is_template and key.startswith('../'):
                    key = str(key[3:])
        else:
            opt = OptionStr(key, value)
        self.options[key] = opt
        if key not in self.associations:
            self.types[opt.type][key] = opt

    def __repr__(self):
        self._refresh_types()
        ret = u''
        for key, opts in iteritems(self.types):
            ret += '{} =>\n'.format(key)
            for key2, opt in iteritems(opts):
                if key2 in self.associations:
                    continue
                ret += '\t' + repr(opt) + '\n'
        return ret.rstrip('\n')

    def __str__(self):
        ret = u''
        for key, val in iteritems(self.options):
            if key in self.associations:
                continue
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
        for key in self.types.keys():
            self.types[key].clear()
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

    @property
    def raw(self):
        if self._raw and not self._changed and not self.changed:
            return self._raw
        if not self.name:
            return self._raw
        try:
            with codecs.open(self.name, 'r', 'utf-8', errors='ignore') as fil:
                self._raw = [x.rstrip('\n') for x in fil.readlines()]
        except IOError:
            return self._raw

        self._changed = False
        self.mtime = os.path.getmtime(self.name)
        self.md5 = self._md5
        return self._raw

    def _dump_resets(self):
        ret = {}
        for key, val in iteritems(self.options):
            resets = val.get_resets()
            if resets:
                ret[key] = resets
        return ret

    def _write_key(self, fil, key, data, index=None, dry=False):
        strict = 'regex' not in key
        if not dry:
            self._changed = True

        # special case
        if key == '.':
            val = sanitize_string(data)
            if self._is_template and not val.startswith('../'):
                val = '../{}'.format(val)
            fil.write('. {}\n'.format(val))
            return val

        if index is not None and index >= 0:
            if key not in self.updated:
                val = data.getlist(key)
                if key in self:
                    self[key].update(val)
                else:
                    self[key] = val
                self.updated.append(key)
                if key in self.reset:
                    self[key].set_resets(self.reset[key])
            fil.write('{}\n'.format(self[key].dump_index(index, strict)))
            return None

        if key in getattr(self.parser, 'multi_{}'.format(self.mode)) or \
                key in getattr(self.parser, 'pair_{}'.format(self.mode), []):
            if key not in self.updated:
                val = data.getlist(key)
                if key in self:
                    self[key].update(val)
                else:
                    self[key] = val
                self.updated.append(key)
                if key in self.reset:
                    self[key].set_resets(self.reset[key])
            val = self[key]
            fil.write('{}\n'.format(self[key].dump(strict=strict)))
            return None

        if key not in self.updated:
            if key in self.parser.boolean_srv or key in self.parser.boolean_cli:
                val = data.get(key)
            else:
                val = sanitize_string(str(data.get(key)), strict)
            if key in self:
                self[key].update(val)
            else:
                self[key] = val
            self.updated.append(key)
            if key in self.reset:
                self[key].set_resets(self.reset[key])

        if dry:
            ret = self[key].parse()
            if index is not None:
                return ret[index]
            return ret
        fil.write('{}\n'.format(self[key]))

    def parse(self, force=False):
        """Parse the current config"""
        if not self._changed and not self.changed and not force:
            return

        self.clear()
        for line in self.raw:
            if re.match(r'^\s*#', line):
                if BEGIN_TEMPLATES in line:
                    self._parsing_templates = True
                if END_TEMPLATES in line:
                    self._parsing_templates = False
                continue
            res = re.search(r'\s*([^=\s]+)\s*(:)?=?\s*(.*)$', line)
            if res:
                key = res.group(1)
                reset = res.group(2)
                val = res.group(3)
                if key == u'compression':
                    val = val.replace('zlib', 'gzip')
                elif key == u'ssl_compression':
                    val = val.replace('gzip', 'zlib')
                self[key] = val
                if key in self:
                    try:
                        self[key].set_reset(reset is not None)
                    except AttributeError:
                        pass

        self._dirty = False

    def _store(self, data, dest=None, insecure=False):
        """Store the config"""
        dest = dest or self.name
        if not dest:
            return [[NOTIF_ERROR, 'No file defined!']]

        dirname = os.path.dirname(dest)
        filename = os.path.basename(dest)
        if dirname and not os.path.exists(dirname):
            try:
                os.makedirs(dirname, 0o755)
            except OSError as exp:
                return [[NOTIF_WARN, str(exp)]]

        if not insecure:
            self.reset = {}
            ref = os.path.join(dirname, '.{}.bui.init.back~'.format(filename))
            bak = os.path.join(dirname, '.{}.back~'.format(filename))

            if not os.path.isfile(ref) and os.path.isfile(dest):
                try:
                    shutil.copy(dest, ref)
                except IOError as exp:
                    return [[NOTIF_ERROR, str(exp)]]
            elif os.path.isfile(dest):
                try:
                    shutil.copy(dest, bak)
                except IOError as exp:
                    return [[NOTIF_ERROR, str(exp)]]
        else:
            self.reset = self._dump_resets()

        def _make_it_bool(array):
            return ['{}'.format(x).lower() == 'true' for x in array]

        errs = []

        for key in data.keys():
            if key in self.parser.files:
                dat = data.get(key)
                if not os.path.isfile(dat):
                    typ = 'strings'
                    if key in getattr(self.parser, 'multi_{}'.format(self.mode)):
                        typ = 'multis'
                    elif key in getattr(self.parser, 'boolean_{}'.format(self.mode)):
                        typ = 'bools'
                    elif key in getattr(self.parser, 'integer_{}'.format(self.mode)):
                        typ = 'integers'
                    # highlight the wrong parameters
                    errs.append([
                        NOTIF_ERROR,
                        "Sorry, the file '{}' does not exist".format(dat),
                        key,
                        typ
                    ])
            elif key.endswith(RESET_IDENTIFIER):
                target = key.replace(RESET_IDENTIFIER, '')
                if target in getattr(self.parser, 'multi_{}'.format(self.mode)):
                    self.reset[target] = _make_it_bool(data.getlist(key))
                else:
                    self.reset[target] = data.get(key)

        if errs and not insecure:
            return errs

        orig = self.raw
        oldkeys = [self._get_line_key(x) for x in orig]
        newkeys = list(set(viewkeys(data)) - set(oldkeys))

        multi_index_map = {}
        pair_index_map = {}
        already_multi = set()
        already_pair = set()
        already_file = []
        written = []
        self.updated = []

        def _lookup_option(key, val, start=0, strict=True, comment=True):
            """returns a list of tuples (idx, line)"""
            # re.match implies /^.../
            reg = r'\s*{}\s*:?=?'.format(key)
            if comment:
                reg = r'\s*#*{}'.format(reg)
            if strict:
                reg = r'{}\s*{}$'.format(reg, val)
            start = min(start, len(orig))
            for idx, line in enumerate(orig[start:], start):
                if re.match(reg, line.rstrip('\n')):
                    return idx, line
            return -1, None

        def _is_key_after(key, start=0):
            """checks if a key is present in the following lines"""
            idx, _ = _lookup_option(key, None, start, False)
            return idx != -1

        def _dump(line, comment=None, raw=False):
            if raw:
                fil.write('{}\n'.format(line))
                return
            lead = ''
            if comment:
                lead = '#'
            fil.write('{}{}\n'.format(lead, line))

        try:
            with codecs.open(dest, 'w', 'utf-8', errors='ignore') as fil:
                # f.write('# Auto-generated configuration using Burp-UI\n')
                data_keys = list(data.keys())
                if 'templates' in data:
                    _dump(' {}'.format(BEGIN_TEMPLATES), True)
                    tpls = data.getlist('templates')
                    for tpl in tpls:
                        self._write_key(fil, '.', tpl)
                    _dump(' {}'.format(END_TEMPLATES), True)
                skip_line = False
                for idx, line in enumerate(orig):
                    if self._line_is_comment(line) and BEGIN_TEMPLATES in line:
                        skip_line = True
                    if self._line_is_comment(line) and END_TEMPLATES in line:
                        skip_line = False
                        continue
                    if skip_line:
                        continue
                    key = self._get_line_key(line, False)
                    if (self._line_removed(line, data_keys) and
                            not self._line_is_comment(line) and
                            not self._line_is_file_include(line)):
                        # The line was removed, we comment it
                        _dump(line, comment=True)
                    elif self._line_is_file_include(line):
                        # The line is a file inclusion, we check if the line
                        # was already present
                        ori = self._include_get_file(line)
                        if self._is_template and ori.startswith('../'):
                            ori = str(ori[3:])
                        if ori in data.getlist('includes_ori') and \
                                ori not in already_file:
                            idx = data.getlist('includes_ori').index(ori)
                            inc = data.getlist('includes')[idx]
                            self._write_key(fil, '.', inc)
                            already_file.append(inc)
                        else:
                            if not insecure:
                                comment = not self._line_is_comment(line)
                                _dump(line, comment=comment)
                            else:
                                _dump(line)

                    elif key in data_keys:
                        # The line is still present or has been un-commented,
                        # rewrite it with eventual changes
                        multi = key in getattr(self.parser, 'multi_{}'.format(self.mode))
                        pair = key in getattr(self.parser, 'pair_{}'.format(self.mode), [])
                        if pair and key not in pair_index_map:
                            pair_index_map[key] = 0
                        if multi and key not in multi_index_map:
                            multi_index_map[key] = 0
                        if key in written:
                            _dump(line, comment=(not self._line_is_comment(line)))
                        else:
                            if multi:
                                length = len(self[key]) if key in self else -1
                                if key not in already_multi and \
                                        (key not in self or
                                         (key in self and
                                          length > multi_index_map[key])):
                                    self._write_key(
                                        fil,
                                        key,
                                        data,
                                        multi_index_map[key]
                                    )
                                    multi_index_map[key] += 1
                                else:
                                    _dump(line, comment=(not self._line_is_comment(line)))
                                    continue
                                if len(self[key]) == multi_index_map[key]:
                                    already_multi.add(key)
                                    continue
                                # dump the rest of the multi if there are no
                                # more keys in the conf
                                if not _is_key_after(key, idx + 1):
                                    rest = self[key].dump(multi_index_map[key])
                                    if rest:
                                        fil.write('{}\n'.format(rest))
                                    multi_index_map[key] = length
                                    already_multi.add(key)
                            elif pair:
                                length = len(self[key]) if key in self else -1
                                if key not in already_pair and \
                                        (key not in self or
                                         (key in self and
                                          length > pair_index_map[key])):
                                    self._write_key(
                                        fil,
                                        key,
                                        data,
                                        pair_index_map[key]
                                    )
                                    pair_index_map[key] += 1
                                else:
                                    _dump(line, comment=(not self._line_is_comment(line)))
                                    continue
                                if len(self[key]) == pair_index_map[key]:
                                    already_pair.add(key)
                                    continue
                                # dump the rest of the pair if there are no more
                                # keys in the conf
                                if not _is_key_after(key, idx + 1):
                                    rest = self[key].dump(pair_index_map[key])
                                    if rest:
                                        fil.write('{}\n'.format(rest))
                                    pair_index_map[key] = length
                                    already_pair.add(key)
                            else:
                                # The line was a comment and there was a further
                                # matching setting, so we just jump to the
                                # following
                                if self._line_is_comment(line) and \
                                        _lookup_option(key, None, idx + 1, False):
                                    _dump(line, raw=True)
                                    continue

                                val = self._write_key(
                                    fil,
                                    key,
                                    data,
                                    dry=True
                                )
                                lookup, _ = _lookup_option(key, val, idx + 1)
                                # The same option is here later, skip the
                                # current one
                                if lookup != -1:
                                    _dump(line, raw=True)
                                    continue

                                written.append(key)
                                self._write_key(
                                    fil,
                                    key,
                                    data
                                )
                    else:
                        _dump(line, comment=(key in written and not self._line_is_comment(line)))

                # write the rest of the multi settings
                for key, idx in iteritems(multi_index_map):
                    if key not in already_multi and idx < self[key].len():
                        fil.write('{}\n'.format(self[key].dump(idx)))
                # write the rest of the pair settings
                for key, idx in iteritems(pair_index_map):
                    if key not in already_pair and idx < self[key].len():
                        fil.wrrite('{}\n'.format(self[key].dump(idx)))
                # Write the rest of file inclusions
                if 'includes' in data:
                    for inc in data.getlist('includes'):
                        if inc not in already_file:
                            self._write_key(fil, '.', inc)
                # Write the new keys
                for key in newkeys:
                    if key.endswith(RESET_IDENTIFIER):
                        continue
                    if key not in written and key not in already_multi and \
                            key not in already_pair and \
                            key not in ['includes', 'includes_ori', 'templates']:
                        self._write_key(
                            fil,
                            key,
                            data,
                        )

        except Exception as exp:
            return [[NOTIF_ERROR, str(exp)]]

        self.parse(True)

        return [[NOTIF_OK, 'Configuration successfully saved.']]

    def store(self, dest=None, insecure=False):
        """Store the current conf object"""
        data = self.data
        return self._store(data, dest, insecure)

    def store_data(self, data, insecure=False):
        """Store the conf given a object data"""
        return self._store(data, insecure=insecure)

    @staticmethod
    def _line_is_comment(line):
        """Check whether a given line is a comment or not"""
        if not line:
            return False
        return line.startswith('#')

    @staticmethod
    def _line_is_file_include(line):
        """Check whether a given line is a file inclusion or not"""
        if not line:
            return False
        return line.startswith('.') or re.match(r'^#+\s*\.', line) is not None

    @staticmethod
    def _include_get_file(line):
        """Return the path of the included file(s)"""
        if not line:
            return None
        _, fil = re.split(r'\s+', line, 1)
        return fil

    @staticmethod
    def _get_line_key(line, ignore_comments=True):
        """Return the key of a given line"""
        if not line:
            return ''
        if '=' not in line:
            return line
        (key, _) = re.split(r'\s*:?=\s*', line, 1)
        if not ignore_comments:
            key = key.strip('# ')
        return key.strip()

    @staticmethod
    def _line_removed(line, keys):
        """Check whether a given line has been removed in the updated version"""
        if not line:
            return False
        (key, _) = re.split(r'\s+|:?=', line, 1)
        key = key.strip()
        return key not in keys


class Config(File):
    """Object representing a configuration

    A config is like a virtual file so we can reuse some methods

    :param parser: Parser object
    :type parser: :class:`burpui.misc.parser.doc.Doc`
    """

    def __init__(self, path=None, parser=None, mode='srv'):
        """
        :param parser: Parser object
        :type parser: :class:`burpui.misc.parser.doc.Doc`

        :param mode: Configuration type
        :type mode: str
        """
        # we need an OrderedDict since the order of the configuration matters
        self.files = OrderedDict()
        self._tree = []
        self.default = path
        self.name = path
        self._includes = []
        self._templates = []
        self._is_template = False
        self._dirty = True
        if path:
            self.files[path] = File(parser, path, mode=mode)
        super(Config, self).__init__(parser, path, mode)

    @property
    def changed(self):
        for path, conf in iteritems(self.files):
            if conf.changed:
                return True
        return False

    def _parse(self):

        orig = self.files.copy()
        for root, conf in iteritems(orig):
            conf.parse()
            for key, val in iteritems(conf.flatten('include', False)):
                for path in val:
                    if not os.path.isabs(path):
                        path = os.path.join(os.path.dirname(root), path)
                    self.add_file(path, root)
                    self._includes.append(path)
            for key, path in iteritems(conf.flatten('template', False)):
                if not os.path.isabs(path):
                    path = os.path.join(os.path.dirname(root), path)
                self.add_file(path, root)
                self._templates.append(path)

        # recursively parse the conf
        if orig != self.files:
            self._parse()

    def parse(self, force=False):
        if not self.changed and not force:
            return

        del self._includes[:]
        del self._templates[:]
        self._parse()

        removed = []
        orig = self.files
        for path, conf in iteritems(orig):
            if conf.parent and ((conf.name not in self._includes and
               conf.name not in self._templates) or conf.name in removed):
                removed.append(path)
                self.del_file(path)

    @property
    def tree(self):
        if not self.changed and not self.dirty and self._tree:
            return self._tree

        # make sure to refresh files list
        self.parse(True)

        def __new_node(name, parent=None):
            dirname = os.path.dirname(name)
            basename = os.path.basename(name)
            return {
                'name': basename,
                'title': basename,
                'full': name,
                'dir': dirname,
                'parent': parent,
                'children': []
            }

        self._tree[:]
        dflt = self.get_default(True)
        temp = {}

        # retrieve the offset of the default conf
        offset = 0
        for idx, (path, _) in enumerate(iteritems(self.files)):
            if path == dflt.name:
                offset = idx
                break

        for idx, (top, conf) in enumerate(iteritems(self.files)):
            if idx < offset:
                continue
            if idx > offset:
                break
            node = __new_node(conf.name)
            for key, val in iteritems(conf.flatten('include', False)):
                for path in val:
                    if not os.path.isabs(path):
                        path = os.path.join(os.path.dirname(top), path)
                    node['children'].append(__new_node(path, node['full']))
            temp[conf.name] = node
        self._tree = [x for _, x in iteritems(temp)]
        return self._tree

    def store(self, conf=None, dest=None, insecure=False):
        ret = []
        if conf and conf in self.files:
            return self.files[conf].store(dest, insecure)
        for name, conf in iteritems(self.files):
            ret += conf.store(insecure=insecure)
        return ret

    def store_data(self, conf, data, insecure=False):
        return self.get_file(conf).store_data(data, insecure)

    def clone(self):
        cpy = Config(self.name, self.parser, self.mode)
        for path, parsed in iteritems(self.files):
            if path == self.name:
                continue
            cpy.add_file(path)
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

    def add_file(self, path=None, parent=None):
        idx = path or self.default
        if idx not in self.files:
            self.files[idx] = File(self.parser, idx, self.mode, parent, self._is_template)
            self._dirty = True
        return self.files[idx]

    def get_file(self, path):
        ret = self.files.get(path, File(self.parser, path, mode=self.mode))
        ret.parse()
        return ret

    def del_file(self, path):
        self._dirty = True
        del self.files[path]

    def list_files(self):
        return self.files.keys()

    def set_template(self, val):
        self._is_template = val

    def _refresh(self):
        if self._dirty or \
                any([x.dirty
                     for _, x in iteritems(self.files)]):

            # cleanup "caches"
            self.options.clear()
            del self.options
            self.options = OrderedDict()
            for key in viewkeys(self.types):
                del self.types[key]
                self.types[key] = OrderedDict()

            # now update caches with new values
            for _, fil in iteritems(self.files):
                self.options.update(fil.options)
                self.associations = self.associations.union(fil.associations)
                # FIXME: find a way to cache efficiently
                # fil.clean()

            for key, val in iteritems(self.options):
                if key not in self.associations:
                    self.types[val.type][key] = val

        self._dirty = False

    def _get(self, key, default=None, raw=False):
        self._refresh()
        try:
            if key in self._options_for_type('pair'):
                obj = self.options[key].get(key)
            else:
                obj = self.options[key]
        except KeyError:
            if default:
                return default
            if self.parser and key in self.parser.defaults:
                obj = self._new_opt(key, self.parser.defaults[key])
            else:
                return None
        return obj if raw else obj.parse()

    def get_raw(self, key, default=None):
        return self._get(key, default, True)

    def get(self, key, default=None):
        return self._get(key, default)

    def getlist(self, key):
        obj = self._get(key, raw=True)
        if not obj:
            return []
        if isinstance(obj, OptionMulti):
            return obj.parse()
        else:
            return [obj.parse()]

    def __getitem__(self, key):
        self._refresh()
        if key in self._options_for_type('pair'):
            return self.options[key].get(key)
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
