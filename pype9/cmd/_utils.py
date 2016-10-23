import os.path
from argparse import ArgumentTypeError


def existing_file(fname):
    if not os.path.isfile(fname):
        raise ArgumentTypeError(
            "'{}' does not refer to an existing file".format(fname))
    return fname
