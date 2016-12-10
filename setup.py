#!/usr/bin/env python
import os
import re
import platform
import tempfile
import subprocess as sp
# from setuptools import find_packages  # @UnresolvedImport
# from os.path import dirname, join, splitext
# from distutils.core import setup
# from distutils.command.build import build as _build
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
package_dir = os.path.join(os.path.dirname(__file__), package_name)
# package_data = []
# prefix_len = len(package_dir) + 1
# for path, dirs, files in os.walk(package_dir, topdown=True):
#     package_data.extend(
#         (os.path.join(path, f)[prefix_len:] for f in files
#          if os.path.splitext(f)[1] in ('.tmpl', '.cpp') or f == 'Makefile'))
# 
# packages = [p for p in find_packages() if p != 'test']


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


class build(object):
    """
    Add build of libninemlnrn (for GSL random distributions in NMODL) to the
    end of the build process.
    """

    def run(self):
#         _build.run(self)
        print("Attempting to build libninemlnrn")
        try:
            cc = args.cc if args.cc is not None else self.get_nrn_cc()
            gsl_prefixes = ([args.gsl_prefix] if args.gsl_prefix is not None
                            else self.get_gsl_prefixes())
            compile_cmd = '{} -fPIC -c -o nineml.o nineml.cpp {}'.format(
                cc, ' '.join('-I{}/include'.format(p) for p in gsl_prefixes))
            link_cmd = (
                '{} -shared {} -lm -lgslcblas -lgsl -o libninemlnrn.so '
                'nineml.o -lc'.format(
                    cc, ' '.join('-L{}/lib'.format(p) for p in gsl_prefixes)))
            for cmd in (compile_cmd, link_cmd):
                self.run_cmd(
                    cmd,
                    work_dir=os.path.join(package_dir, 'neuron', 'cells',
                                          'code_gen', 'libninemlnrn'),
                    fail_msg="Unable to compile libninemlnrn extensions")
            print("Successfully compiled libninemlnrn extension.")
        except CouldNotCompileNRNRandDistrException as e:
            print("Unable to compile libninemlnrn: random distributions in "
                  "NMODL files will not work:\n{}".format(e))

    def run_cmd(self, cmd, work_dir, fail_msg):
        p = sp.Popen(cmd, shell=True, stdin=sp.PIPE, stdout=sp.PIPE,
                     stderr=sp.STDOUT, close_fds=True, cwd=work_dir)
        stdout = p.stdout.readlines()
        result = p.wait()
        # test if cmd was successful
        if result != 0:
            raise CouldNotCompileNRNRandDistrException(
                "{}:\n{}".format(fail_msg, '  '.join([''] + stdout)))

    def get_nrn_cc(self):
        """
        Get the C compiler used to compile NMODL files

        Returns
        -------
        cc : str
            Name of the C compiler used to compile NMODL files
        """
        # Get path to nrnivmodl
        nrnivmodl_path = self.path_to_exec('nrnivmodl')
        try:
            with open(nrnivmodl_path) as f:
                contents = f.read()
        except IOError:
            raise CouldNotCompileNRNRandDistrException(
                "Could not read nrnivmodl at '{}'"
                .format(nrnivmodl_path))
        # Execute nrnivmodl down to the point that it sets the bindir, then
        # echo it to stdout and quit
        # Get the part of nrnivmodl to run
        bash_to_run = []
        found_bindir_export = False
        for line in contents.splitlines():
            bash_to_run.append(line)
            if re.match(r'export.*bindir.*', line):
                bash_to_run.append('echo $bindir')
                found_bindir_export = True
                break
        # Write bash to file, execute and extract binary dir
        if found_bindir_export:
            _, fname = tempfile.mkstemp(text=True)
            with open(fname, 'w') as f:
                f.write('\n'.join(bash_to_run))
            bin_dir = sp.check_output('sh {}'.format(fname),
                                      shell=True).strip()
        else:
            raise CouldNotCompileNRNRandDistrException(
                "Problem parsing nrnivmodl at '{}', could not find "
                "'export {{bindir}}' line".format(nrnivmodl_path))
        nrnmech_makefile_path = os.path.join(bin_dir, 'nrnmech_makefile')
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

    def path_to_exec(self, exec_name):
        """
        Returns the full path to an executable by searching the "PATH"
        environment variable

        Parameters
        ----------
        exec_name: str
            Name of executable to search the execution path

        Returns
        -------
        return: str
            Full path to executable
        """
        if platform.system() == 'Windows':
            exec_name += '.exe'
        # Get the system path
        system_path = os.environ['PATH'].split(os.pathsep)
        # Append NEST_INSTALL_DIR/NRNHOME if present
        if 'NRNHOME' in os.environ:
            system_path.append(os.path.join(os.environ['NRNHOME'], 'bin'))
        if 'NEST_INSTALL_DIR' in os.environ:
            system_path.append(os.path.join(os.environ['NEST_INSTALL_DIR'],
                                            'bin'))
        # Check the system path for the command
        exec_path = None
        for dr in system_path:
            path = os.path.join(dr, exec_name)
            if os.path.exists(path):
                exec_path = path
                break
        if not exec_path:
            raise CouldNotCompileNRNRandDistrException(
                "Could not find executable '{}' on the system path '{}', which"
                " is required to build libninemlnrn"
                .format(exec_name, ':'.join(system_path)))
        return exec_path

b = build()

print b.get_nrn_cc()

# 
# setup(
#     name="pype9",
#     version="0.1a",
#     package_data={package_name: package_data},
#     scripts=[join('bin', 'pype9')],
#     packages=packages,
#     author="The PyPe9 Team (see AUTHORS)",
#     author_email="tom.g.close@gmail.com",
#     description=("\"Python PipelinEs for 9ML (PyPe9)\" to manipulate "
#                  "neuron and neuron network 9ML (http://nineml.net) models "
#                  "and simulate them using well-established simulator backends,"
#                  " NEURON and NEST."),
#     long_description=open(join(dirname(__file__), "README.rst")).read(),
#     license="The MIT License (MIT)",
#     keywords=("NineML pipeline computational neuroscience modeling "
#               "interoperability XML 9ML neuron nest"),
#     url="http://github.com/CNS-OIST/PyPe9",
#     classifiers=['Development Status :: 3 - Alpha',
#                  'Environment :: Console',
#                  'Intended Audience :: Science/Research',
#                  'License :: OSI Approved :: MIT',
#                  'Natural Language :: English',
#                  'Operating System :: OS Independent',
#                  'Programming Language :: Python :: 2',
#                  'Topic :: Scientific/Engineering'],
#     install_requires=['pyNN>=0.8',
#                       'diophantine>=0.1',
#                       'neo>=0.3.3',
#                       'matplotlib'],  # 'nineml',
#     dependency_links=['http://github.com/INCF/NineMLCatalog/tarball/master#egg=package-1.0'],
#     tests_require=['nose'],
#     cmdclass={'build': build})
