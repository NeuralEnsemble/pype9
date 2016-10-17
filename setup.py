#!/usr/bin/env python
import os
from setuptools import setup, find_packages, Extension  # @UnresolvedImport
# from setuptools.command.install import install
from os.path import dirname, abspath, join, splitext, sep
import subprocess as sp
import platform


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

# Attempt to find the prefix of the gsl and gslcblas libraries used by NEST


# Check /usr/local to see if there is a version of libgsl and libgslcblas there
usr_local_libs = os.listdir(join('/usr', 'local'))
if (bool(1 for l in usr_local_libs if l.startswith('libgsl.')) and
        bool(1 for l in usr_local_libs if l.startswith('libgslcblas.'))):
    gsl_prefixes = []  # Assume they are already on system path
else:
    # Check for the version of gsl linked to the pynestkernel
    try:
        import nest
        cwd = os.getcwd()
        os.chdir(dirname(nest.__file__))
        if platform.platform().startswith('Darwin'):
            ldd_cmd = 'otool -L'
        else:
            ldd_cmd = 'ldd'
        ldd_out = sp.check_output('{} pynestkernel.so'.format(ldd_cmd),
                                  shell=True)
        gsl_prefixes = set(dirname(dirname(abspath(l.split()[0]))) + sep
                           for l in ldd_out.split('\n\t') if 'libgsl' in l)
        assert gsl_prefixes, ("NEST not linked to GSL? ldd output:\n{}"
                              .format(ldd_out))
    except ImportError:
        raise Exception("Could not find gsl libraries in /usr/local or import "
                        "NEST to determine the location of the GSL it uses")


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
