"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
import os
import sys
import errno


def remove_ignore_missing(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def add_lib_path(path):
    if (sys.platform.startswith('linux') or
        sys.platform in ['os2', 'os2emx', 'cygwin', 'atheos',
                         'ricos']):
        lib_path_key = 'LD_LIBRARY_PATH'
    elif sys.platform == 'darwin':
        lib_path_key = 'DYLD_LIBRARY_PATH'
    elif sys.platform == 'win32':
        lib_path_key = 'PATH'
    if lib_path_key in os.environ:
        os.environ[lib_path_key] += os.pathsep + path
    else:
        os.environ[lib_path_key] = path


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()
