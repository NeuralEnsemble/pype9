"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
import os
import errno


def remove_ignore_missing(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def ensure_camel_case(name):
    if len(name) < 2:
        raise Exception("The name ('{}') needs to be at least 2 letters long"
                        "to enable the capitalized version to be different "
                        "from upper case version".format(name))
    if name == name.lower() or name == name.upper():
        name = name.title()
    return name
