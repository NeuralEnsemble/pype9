"""
This package contains backports of modules to python 2.4 that are required for NINEML+/pyNN 
software. If possible (if the python version used is sufficient) the standard versions are preferred
by this package, with the backported versions only used if the standard versions are missing.

@author: Tom Close 
@date: 12/6/2012
"""

# Use stdlib's functools if available
try:
    import functools
except ImportError:
    import _functools as functools # Only includes 'partial', 'update_wrapper', 'wraps' functions

# Use stdlib's argparse if available
try:
    import argparse
except ImportError:
    import _argparse as argparse # Includes all functionality added in Python 2.7

#Note that _collections imports everything from the existing collections module, and adds 
#'namedtuple' if it is missing.
import _collections as collections

if 'any' not in __builtins__:
    def any(iterable): #@BuiltInFunction
        for element in iterable:
            if element:
                return True
        return False
else:
    any = __builtins__['any']

if 'all' not in __builtins__:
    def all(iterable): #@BuiltInFunction
        for element in iterable:
            if not element:
                return False
        return True
else:
    all = __builtins__['all']
