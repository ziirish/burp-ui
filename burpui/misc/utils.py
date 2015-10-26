# -*- coding: utf8 -*-
"""
.. module:: burpui.misc.utils
    :platform: Unix
    :synopsis: Burp-UI utils module.

.. moduleauthor:: Ziirish <ziirish@ziirish.info>

"""
import math
import string
import sys
import inspect
import zipfile
import tarfile
import logging

from inspect import getmembers, isfunction, currentframe

if sys.version_info >= (3, 0):
    long = int  # pragma: no cover


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


if sys.version_info >= (3, 0):  # pragma: no cover
    class BUIlogger(logging.Logger):
        padding = 0
        """Logger class for more convenience"""
        def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
            """
            Try to guess where was call the function
            """
            cf = currentframe()
            caller = inspect.getouterframes(cf)
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
            caller = inspect.getouterframes(cf)
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
    def __init__(self, name, archive):  # pragma: no cover
        self.name = name
        self.archive = archive

    def __enter__(self):
        self.arch = None
        if self.archive == 'zip':
            self.arch = zipfile.ZipFile(self.name, mode='w', compression=zipfile.ZIP_DEFLATED)
        elif self.archive == 'tar.gz':
            self.arch = tarfile.open(self.name, 'w:gz')
        elif self.archive == 'tar.bz2':
            self.arch = tarfile.open(self.name, 'w:bz2')
        return self

    def __exit__(self, type, value, traceback):
        self.arch.close()

    def append(self, path, arcname):
        if self.archive == 'zip':
            self.arch.write(path, arcname)
        elif self.archive in ['tar.gz', 'tar.bz2']:
            self.arch.add(path, arcname=arcname, recursive=False)


class BUIserverException(Exception):
    """Raised in case of internal error. This exception should never reach the
    end-user.
    """
    pass
