#!/usr/bin/env python
from __future__ import print_function
import os
from setuptools import find_packages  # @UnresolvedImport
from distutils.core import setup


# Generate the package data
package_name = 'pype9'
package_dir = os.path.join(os.path.dirname(__file__), package_name)
package_data = []
prefix_len = len(package_dir) + 1
for path, dirs, files in os.walk(package_dir, topdown=True):
    package_data.extend(
        (os.path.join(path, f)[prefix_len:] for f in files
         if os.path.splitext(f)[1] in ('.tmpl', '.cpp') or f == 'Makefile'))

# Filter unittests from packages
packages = [p for p in find_packages() if not p.startswith('test.')]


setup(
    name="pype9",
    version="0.1a0",
    package_data={package_name: package_data},
    scripts=[os.path.join('scripts', 'pype9')],
    packages=packages,
    author="The PyPe9 Team (see AUTHORS)",
    author_email="tom.g.close@gmail.com",
    description=("\"Python PipelinEs for 9ML (PyPe9)\" to manipulate "
                 "neuron and neuron network 9ML (http://nineml.net) models "
                 "and simulate them using well-established simulator backends,"
                 " NEURON and NEST."),
    long_description=open(os.path.join(os.path.dirname(__file__),
                                       "README.rst")).read(),
    license="The MIT License (MIT)",
    keywords=("NineML pipeline computational neuroscience modeling "
              "interoperability XML YAML JSON HDF5 9ML neuron nest"),
    url="http://readthedocs.io/pype9",
    classifiers=['Development Status :: 3 - Alpha',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: MIT',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Topic :: Scientific/Engineering'])
