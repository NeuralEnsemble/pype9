#!/usr/bin/env python
import os
import sys
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


# Check /usr and /usr/local to see if there is a version of libgsl and
# libgslcblas there
system_gsl = set()
for system_path in ('/usr', join('/usr', 'local')):
    system_libs = os.listdir(system_path)
    if any(l.startswith('libgsl.') or l.startswith('libgslcblas.')
           for l in system_libs):
        system_gsl.add(system_path)

# Check for the version of gsl linked to the pynestkernel
try:
    # Import NEST with suppressed NEST splash
    import nest
    cwd = os.getcwd()
    os.chdir(dirname(nest.__file__))
    if platform.platform().startswith('Darwin'):
        ldd_cmd = 'otool -L'
    else:
        ldd_cmd = 'ldd'
    ldd_out = sp.check_output('{} pynestkernel.so'.format(ldd_cmd),
                              shell=True)
    nest_gsl = set(dirname(dirname(abspath(l.split()[0]))) + sep
                       for l in ldd_out.split('\n\t') if 'libgsl' in l)
    assert nest_gsl, "NEST not linked to GSL? ldd output:\n{}".format(ldd_out)
except ImportError:
    nest_gsl = set()  # Assume they are already on system path
    print ("WARNING, Could not import NEST to determine which gsl libraries it"
           " uses")

if system_gsl:
    if nest_gsl and nest_gsl != system_gsl:
        raise Exception(
            "System GSL version found at '{}' is different from that linked "
            "to NEST at '{}'. Please specify which version you would like to "
            "use in setup.cfg in the include-dirs and link-dirs options under "
            "[build_ext]".format("', '".join(nest_gsl),
                                 "', '".join(system_gsl)))
    else:
        print ("Using system gsl version at '{}'"
               .format("', '".join(system_gsl)))
        gsl_prefixes = system_gsl
elif nest_gsl:
    print ("Using gsl version linked to NEST at '{}'"
           .format("', '".join(nest_gsl)))
    gsl_prefixes = nest_gsl
else:
    raise Exception(
        "No version of GSL found in system paths or by inspecting libs linked"
        "to NEST. Please install GNU Scientific Library if necessary and/or "
        "specify its location in setup.cfg in both include-dirs and link-dirs "
        "options of [build_ext]")


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
