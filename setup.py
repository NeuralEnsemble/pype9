#!/usr/bin/env python
import os
from setuptools import setup, find_packages, Extension  # @UnresolvedImport
from os.path import dirname, join, splitext


# Generate the package data
package_name = 'pype9'
package_dir = join(dirname(__file__), package_name)
package_data = []
prefix_len = len(package_dir) + 1
for path, dirs, files in os.walk(package_dir, topdown=True):
    package_data.extend(
        (join(path, f)[prefix_len:] for f in files
         if splitext(f)[1] in ('.tmpl', '.cpp') or f == 'Makefile'))

packages = [p for p in find_packages() if p != 'test']

# Set up the required extension to handle random number generation using GSL
# RNG in NEURON components
libninemlnrn = Extension("libninemlnrn",
                       sources=[join(package_dir, 'neuron', 'cells',
                                     'code_gen', 'libninemlnrn',
                                     'nineml.cpp')],
                       libraries=['m', 'gslcblas', 'gsl', 'c'],
                       language="c++")

setup(
    name="pype9",
    version="0.1a",
    package_data={package_name: package_data},
    packages=packages,
    author="The PyPe9 Team (see AUTHORS)",
    author_email="tom.g.close@gmail.com",
    description=("\"Python PipelinEs for 9ML (PyPe9)\" to simulate neuron and "
                 "neuron network models described in 9ML with the NEURON and "
                 "NEST simulators."),
    long_description=open(join(dirname(__file__), "README.rst")).read(),
    license="The MIT License (MIT)",
    keywords=("NineML pipeline computational neuroscience modeling "
              "interoperability XML 9ML neuron nest"),
    url="http://github.com/CNS-OIST/PyPe9",
    classifiers=['Development Status :: 3 - Alpha',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: MIT',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Topic :: Scientific/Engineering'],
    install_requires=['pyNN', 'diophantine', 'neo'],  # 'nineml',
    tests_require=['nose', 'ninemlcatalog'],
    ext_modules=[libninemlnrn])
