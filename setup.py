#!/usr/bin/env python
import os
from setuptools import setup, find_packages, Extension  # @UnresolvedImport
from os.path import dirname, abspath, join, splitext


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

# Attempt to find the prefix of the gsl and gslcblas libraries
try:
    # Check for the version of gsl linked to the pynestkernel
    import nest
    import subprocess as sp
    import os.path
    import platform
    cwd = os.getcwd()
    os.chdir(dirname(nest.__file__))
    if platform.platform().startswith('Darwin'):
        cmd = 'otool -L'
    else:
        cmd = 'ldd'
    ldd_out = sp.check_output('{} pynestkernel.so', shell=True)
    gsl_prefixes = set(dirname(dirname(abspath(l.split()[0])))
                       for l in ldd_out.split('\n\t') if 'libgsl' in l)
except ImportError:
    raise Exception(
        "Could not import NEST to determine the location of GSL")


# Set up the required extension to handle random number generation using GSL
# RNG in NEURON components
libninemlnrn = Extension("libninemlnrn",
                         sources=[os.path.join('neuron', 'cells', 'code_gen',
                                               'libninemlnrn', 'nineml.cpp')],
                         libraries=['m', 'gslcblas', 'gsl', 'c'],
                         language="c++",
                         extra_compile_args=[join('-I', p, 'include')
                                             for p in gsl_prefixes],
                         extra_link_args=[join('-L', p, 'lib')
                                          for p in gsl_prefixes])

setup(
    name="pype9",
    version="0.1a",
    package_data={package_name: package_data},
    packages=packages,
    author="Thomas G. Close and Andrew P. Davison",
    # add your name here if you contribute to the code
    author_email="tom.g.close@gmail.com",
    description=("\"Python PipelinEs for 9ML (PyPe9)\" to simulate neuron and "
                 "neuron network models described in 9ML in the NEURON and "
                 "NEST simulators."),
    long_description=open("README.rst").read(),
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
    tests_require=['nose', 'ninemlcatalog']
)
