import os
import sys
import errno
import shutil


def remove_ignore_missing(path):
    try:
        try:
            shutil.rmtree(path)
        except OSError as e:
            if e.errno == errno.ENOTDIR:  # Not a directory
                os.remove(path)
            else:
                raise
    except OSError as e:
        if e.errno != errno.ENOENT:  # Doesn't exist
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
