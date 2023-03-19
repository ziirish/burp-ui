# -*- coding: utf8 -*-
"""
.. module:: burpui.utils
    :platform: Unix
    :synopsis: Burp-UI utils module.

.. moduleauthor:: Ziirish <hi+burpui@ziirish.me>

"""
import datetime
import math
import os
import string
import sys
import tarfile
import zipfile
from uuid import UUID

NOTIF_OK = 0
NOTIF_WARN = 1
NOTIF_ERROR = 2
NOTIF_INFO = 3


class human_readable(int):
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
            if fmt[-1].lower() in ["b", "c", "d", "o", "x", "n", "e", "f", "g", "%"]:
                # Numeric format.
                return int(self).__format__(fmt)
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
        width = "" if fmt.find(".") == -1 else fmt[: fmt.index(".")]
        precis = fmt[:-2] if width == "" else fmt[fmt.index(".") : -2]

        # do the precision bit first, so width/alignment works with the suffix
        if float(self) == 0:
            return "{0:{1}f}".format(v, precis)
        t = ("{0:{1}f} " + mult[i] + suffix).format(v, precis)

        return "{0:{1}}".format(t, width) if width != "" else t


class BUIcompress:
    """Provides a context to generate any kind of archive supported by
    burp-ui
    """

    def __init__(self, name, archive, zip64=False):  # pragma: no cover
        self.name = name
        self.archive = archive
        self.zip64 = zip64

    def __enter__(self):
        self.arch = None
        if self.archive == "zip":
            self.arch = zipfile.ZipFile(
                self.name,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
                allowZip64=self.zip64,
            )
        elif self.archive == "tar.gz":
            self.arch = tarfile.open(self.name, "w:gz")
        elif self.archive == "tar.bz2":
            self.arch = tarfile.open(self.name, "w:bz2")
        return self

    def __exit__(self, type, value, traceback):
        self.arch.close()

    def append(self, path, arcname):
        if self.archive == "zip":
            if os.path.islink(path):
                # This is a symlink, we virtually create one in memory
                # because zipfile does not seem to support them natively
                vfile = zipfile.ZipInfo()
                vfile.filename = arcname  # That's the name of the actual file
                vfile.external_attr |= 0o120000 << int(16)  # symlink file type
                vfile.compress_type = zipfile.ZIP_STORED
                # os.readlink gives us the target of the symlink
                self.arch.writestr(vfile, os.readlink(path))
            else:
                self.arch.write(path, arcname)
        elif self.archive in ["tar.gz", "tar.bz2"]:
            self.arch.add(path, arcname=arcname, recursive=False)


def is_uuid(string):
    """Tells if a given string is a UUID"""
    try:
        val = UUID(string, version=4)
    except ValueError:
        return False

    return val.hex == string.replace("-", "")


def lookup_file(name=None, guess=True, directory=False, check=True):
    if name and isinstance(name, str):
        if os.path.isfile(name) or name == "/dev/null":
            return name
        elif directory and os.path.isdir(name):
            return name
        elif not guess:
            if check:
                raise IOError("File not found: '{}'".format(name))
            return name
    if name and isinstance(name, str):
        names = [name]
    elif name:
        names = name
    else:
        names = ["burpui.cfg", "burpui.sample.cfg"]
    roots = [
        "",
        "share/burpui",
        "/etc/burp",
        os.path.join(
            sys.prefix,
            "share",
            "burpui",
        ),
        os.path.join(
            sys.prefix,
            "local",
            "share",
            "burpui",
        ),
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..",
            "..",
            "..",
            "..",
            "share",
            "burpui",
        ),
    ]
    prefixes = ["", "etc"]
    for filename in names:
        for root in roots:
            for prefix in prefixes:
                tmp = os.path.join(root, prefix, filename)
                if directory and os.path.isdir(tmp):
                    return tmp
                elif os.path.isfile(tmp):
                    return tmp


def utc_to_local(timestamp):
    try:
        import arrow
        from tzlocal import get_localzone

        # 1487607525 -> 1487611125
        utc = arrow.get(datetime.datetime.fromtimestamp(timestamp))
        local = utc.to(str(get_localzone()))
        return local.int_timestamp
    except (TypeError, arrow.parser.ParserError, ImportError):
        return timestamp


def __(string):
    """dummy function to fake the translation"""
    return string


class ReverseProxied(object):
    """Wrap the application in this middleware and configure the
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
    """

    def __init__(self, wsgi_app, app):
        self.wsgi_app = wsgi_app
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get("HTTP_X_SCRIPT_NAME", self.app.config["BUI_PREFIX"])
        if script_name:
            if script_name.startswith("/"):
                environ["SCRIPT_NAME"] = script_name
                path_info = environ["PATH_INFO"]
                if path_info.startswith(script_name):
                    environ["PATH_INFO"] = path_info[len(script_name) :]
            else:
                self.app.warning("'prefix' must start with a '/'!")

        return self.wsgi_app(environ, start_response)


def make_list(data):
    """Ensure data is a list

    :param data: data to check

    :returns: data as list
    """
    if isinstance(data, list):
        return data
    if data is None:
        return []
    return list(data) if not isinstance(data, str) else [data]
