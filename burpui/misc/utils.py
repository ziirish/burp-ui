# -*- coding: utf8 -*-

"""
The following code is used to convert bytes to be human readable.
It was found on the Internet...
"""

import math
import string
import sys
import inspect
import zipfile
import tarfile

if sys.version_info >= (3, 0):
    long = int


class human_readable(long):
    """ define a human_readable class to allow custom formatting
        format specifiers supported :
            em : formats the size as bits in IEC format i.e. 1024 bits (128 bytes) = 1Kib
            eM : formats the size as Bytes in IEC format i.e. 1024 bytes = 1KiB
            sm : formats the size as bits in SI format i.e. 1000 bits = 1kb
            sM : formats the size as bytes in SI format i.e. 1000 bytes = 1KB
            cm : format the size as bit in the common format i.e. 1024 bits (128 bytes) = 1Kb
            cM : format the size as bytes in the common format i.e. 1024 bytes = 1KB

        code from: http://code.activestate.com/recipes/578323-human-readable-filememory-sizes-v2/
    """
    def __format__(self, fmt):
        # is it an empty format or not a special format for the size class
        if fmt == "" or fmt[-2:].lower() not in ["em", "sm", "cm"]:
            if fmt[-1].lower() in ['b', 'c', 'd', 'o', 'x', 'n', 'e', 'f', 'g', '%']:
                # Numeric format.
                return long(self).__format__(fmt)
            else:
                return str(self).__format__(fmt)

        # work out the scale, suffix and base
        factor, suffix = (8, "b") if fmt[-1] in string.lowercase else (1, "B")
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


def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        return sys.exc_info()[2].tb_frame.f_back


class BUIlogging(object):
    def _logger(self, level, *args):
        if self.app:
            logs = {
                'info': self.app.logger.info,
                'error': self.app.logger.error,
                'debug': self.app.logger.debug,
                'warning': self.app.logger.warning
            }
            if level in logs:
                """
                Try to guess where was call the function
                """
                cf = currentframe()
                (frame, filename, line_number, function_name, lines, index) = inspect.getouterframes(cf)[1]
                if cf is not None:
                    cf = cf.f_back
                    """
                    Ugly hack to reformat the message
                    """
                    ar = list(args)
                    if isinstance(ar[0], str):
                        ar[0] = filename + ':' + str(cf.f_lineno) + ' => ' + ar[0]
                    else:
                        ar = [filename + ':' + str(cf.f_lineno) + ' => {0}'.format(ar)]
                    args = tuple(ar)
                logs[level](*args)


class BUIcompress():
    def __init__(self, name, archive):
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
