#!/usr/bin/env python
import os
import re
from setuptools import find_packages  # @UnresolvedImport
from os.path import dirname, join, splitext
from distutils.core import setup
from distutils.command.build import build as _build
import argparse

# Parse arguments for the compilation of libninemlnrn, the so that contains
# wrappers of GSL random distributions
parser = argparse.ArgumentParser()
parser.add_argument('--cc', type=str, default=None,
                    help=("Name of C-compiler used to compile NMODL files. "
                          "If not provided, will attempt to inspect "
                          "nrnmech_makefile"))
parser.add_argument('--gsl_prefix', type=str, default=None,
                    help=("The prefix of the GSL installation to use for "
                          "random distributions in NMODL files. If not "
                          "provided will attempt to extract it from PyNest."))
args, _ = parser.parse_known_args()


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


# # Set up the required extension to handle random number generation using GSL
# # RNG in NEURON components
# libninemlnrn = Extension(('pype9.neuron.cells.code_gen.libninemlnrn.'
#                           'libninemlnrn'),
#                          sources=['pype9/neuron/cells/code_gen/libninemlnrn/'
#                                   'nineml.cpp'],
#                          libraries=['m', 'gslcblas', 'gsl', 'c'],
#                          language="c++")

class CouldNotCompileNRNRandDistrException(Exception):
    pass


class build(_build):
    """
    Add build of libninemlnrn (for GSL random distributions in NMODL) to the
    end of the build process.
    """

    user_options = _build.user_options + [
        ('cc', None, 'Compiler to use for libninemlnrn compilation.'),
        ('gsl_prefix', None,
         'Prefix of GSL installation required for libninemlnrn compilation.')]

    def run(self):
        _build.run(self)
        print("Attempting to build libninemlnrn")
        try:
            cc = args.cc if args.cc is not None else self.get_nrn_cc()
            gsl_prefixes = ([args.gsl_prefix] if args.gsl_prefix is not None
                            else self.get_gsl_prefixes())
            import subprocess as sp
            compile_cmd = '{} -fPIC -c -o nineml.o nineml.cpp {}'.format(
                cc, ' '.join('-I{}/include'.format(p) for p in gsl_prefixes))
            link_cmd = (
                '{} -shared {} -lm -lgslcblas -lgsl -o libninemlnrn.so '
                'nineml.o -lc'.format(
                    cc, ' '.join('-L{}/lib'.format(p) for p in gsl_prefixes)))
            for cmd in (compile_cmd, link_cmd):
                print(cmd)
                p = sp.Popen(cmd, shell=True, stdin=sp.PIPE,
                             stdout=sp.PIPE, stderr=sp.STDOUT,
                             close_fds=True,
                             cwd=os.path.join(package_dir, 'neuron', 'cells',
                                              'code_gen', 'libninemlnrn'))
                stdout = p.stdout.readlines()
                result = p.wait()
                # test if nrnivmodl was successful
                if result != 0:
                    print("Unable to compile libninemlnrn extensions. "
                          "Output was:\n {}".format('  '.join([''] + stdout)))
                else:
                    print("Successfully compiled libninemlnrn extension.")
        except CouldNotCompileNRNRandDistrException as e:
            print("Unable to compile libninemlnrn: random distributions in "
                  "NMODL files will not work:\n{}".format(e))

    def get_nrn_cc(self):
        """
        Get the C compiler used to compile NMODL files

        Returns
        -------
        cc : str
            Name of the C compiler used to compile NMODL files
        """
        # Get NEURON installation directory
        print ("Attempting to import neuron in order to locate "
               "nrnmech_makefile and extract C compiler used in order to "
               "compile libninemlnrn for random distributions in NMODL.")
        try:
            import neuron
        except ImportError:
            raise CouldNotCompileNRNRandDistrException(
                "Could not import neuron package, please ensure it is "
                "installed or provide C-compiler used as an setup option")
        neuron_install_dir = os.path.abspath(
            os.path.join(neuron.h.neuronhome(), '..', '..'))
        # Search for 'nrnmech_makefile' in neuron installation directory
        print ("Searching for nrnmech_makefile in '{}' directory"
               .format(neuron_install_dir))
        nrnmech_makefile_path = None
        for pth, _, fnames in os.walk(neuron_install_dir):
            if 'nrnmech_makefile' in fnames:
                nrnmech_makefile_path = os.path.join(pth, 'nrnmech_makefile')
        if nrnmech_makefile_path is None:
            raise CouldNotCompileNRNRandDistrException(
                "Could not find nrnmech_makefile in neuron install prefix "
                "'{}'. Please specify which C-compiler to use"
                .format(neuron_install_dir))
        # Extract C-compiler used in nrnmech_makefile
        try:
            with open(nrnmech_makefile_path) as f:
                contents = f.read()
        except IOError:
            raise CouldNotCompileNRNRandDistrException(
                "Could not read nrnmech_makefile at '{}'"
                .format(nrnmech_makefile_path))
        matches = re.findall(r'\s*CC\s*=\s*(.*)', contents)
        if len(matches) != 1:
            raise CouldNotCompileNRNRandDistrException(
                "Could not extract CC variable from nrnmech_makefile at '{}'"
                .format(nrnmech_makefile_path))
        cc = matches[0]
        return cc

    def get_gsl_prefixes(self):
        """
        Get the library paths used to link GLS to PyNEST

        Returns
        -------
        lib_paths : list(str)
            List of library paths passed to the PyNEST compile
        """
        print ("Attempting to import nest in order to locate GSL install dir "
               "in order to compile libninemlnrn for random distributions in "
               "NMODL.")
        try:
            import nest
        except ImportError:
            raise CouldNotCompileNRNRandDistrException(
                "Could not import 'nest' and therefore couldn't detect GSL "
                "location. Please specify explicitly to setup.py")
        nest_depends_path = os.path.join(
            os.path.dirname(nest.__file__), 'pynestkernel.la')
        print ("Attempting to read dependency libs from '{}'"
               .format(nest_depends_path))
        try:
            with open(nest_depends_path) as f:
                contents = f.read()
        except IOError:
            raise CouldNotCompileNRNRandDistrException(
                "Could not read pynestkernel.la at '{}'"
                .format(nest_depends_path))
        matches = re.findall(r"dependency_libs='(.*)'", contents)
        if len(matches) != 1:
            raise CouldNotCompileNRNRandDistrException(
                "Could not extract dependency_libs from pynestkernel.la at "
                "'{}'".format(nest_depends_path))
        prefixes = [p[2:-3] for p in matches[0].split()
                    if p.startswith('-L') and p.endswith('lib') and 'gsl' in p]
        return prefixes


setup(
    name="pype9",
    version="0.1a",
    package_data={package_name: package_data},
    scripts=[join('bin', 'pype9')],
    packages=packages,
    author="The PyPe9 Team (see AUTHORS)",
    author_email="tom.g.close@gmail.com",
    description=("\"Python PipelinEs for 9ML (PyPe9)\" to manipulate "
                 "neuron and neuron network 9ML (http://nineml.net) models "
                 "and simulate them using well-established simulator backends,"
                 " NEURON and NEST."),
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
    install_requires=['pyNN>=0.8',
                      'diophantine>=0.1',
                      'neo>=0.3.3',
                      'matplotlib'],  # 'nineml',
    dependency_links=['http://github.com/INCF/NineMLCatalog/tarball/master#egg=package-1.0'],
    tests_require=['nose'],
    cmdclass={'build': build})
