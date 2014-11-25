"""

  This module contains functions for building and loading NMODL mechanisms

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import os.path
import shutil
import time
import platform
import tempfile
import uuid
import subprocess as sp
from .. import BaseCodeGenerator

if 'NRNHOME' in os.environ:
    os.environ['PATH'] += (os.pathsep +
                           os.path.join(os.environ['NRNHOME'],
                                        platform.machine(), 'bin'))
else:
    try:
        if os.environ['HOME'] == '/home/tclose':
            # I apologise for this little hack (this is the path on my machine,
            # to save me having to set the environment variable in eclipse)
            os.environ['PATH'] += os.pathsep + '/opt/NEURON/nrn-7.3/x86_64/bin'
    except KeyError:
        pass


class CodeGenerator(BaseCodeGenerator):

    # BUILD_ARCHS = [platform.machine(), 'i686', 'x86_64', 'powerpc', 'umac']
    SIMULATOR_NAME = 'neuron'
    _DEFAULT_SOLVER = 'derivimplicit'
    _TMPL_PATH = os.path.join(os.path.dirname(__file__), 'jinja_templates')

    def __init__(self):
        super(CodeGenerator, self).__init__()
        # Find the path to nrnivmodl
        self.nrnivmodl_path = self._path_to_exec('nrnivmodl')
        # Work out the name of the installation directory for the compiled
        # NMODL files on the current platform
        self.specials_dir = self._get_specials_dir()

    def _extract_template_args(self, args, component, initial_state,
                               ode_method='gsl', v_threshold=None):
        raise NotImplementedError

    def _render_source_files(self, template_args, src_dir, _, verbose):
        raise NotImplementedError

    def compile_source_files(self, compile_dir, component_name, verbose):
        """
        Builds all NMODL files in a directory
        @param src_dir: The path of the directory to build
        @param build_mode: Can be one of either, 'lazy', 'super_lazy',
                           'require', 'force', or 'build_only'. 'lazy' doesn't
                           run nrnivmodl if the library is found, 'require',
                           requires that the library is found otherwise throws
                           an exception (useful on clusters that require
                           precompilation before parallelisation where the
                           error message could otherwise be confusing), 'force'
                           removes existing library if found and recompiles,
                           and 'build_only' removes existing library if found,
                           recompile and then exit
        @param verbose: Prints out verbose debugging messages
        """
        # Change working directory to model directory
        os.chdir(compile_dir)
        if verbose:
            print ("Building NEURON mechanisms in '{}' directory."
                   .format(compile_dir))
        # Run nrnivmodl command in src directory
        try:
            if not verbose:
                with open(os.devnull, "w") as fnull:
                    sp.check_call(self.nrnivmodl_path, stdout=fnull,
                                  stderr=fnull)
            else:
                sp.check_call(self.nrnivmodl_path)
        except sp.CalledProcessError as e:
            raise Exception("Compilation of NMODL files for '{}' model failed."
                            " See src directory '{}':\n "
                            .format(component_name, compile_dir, e))

    def _get_install_dir(self, build_dir, install_dir):
        if install_dir:
            raise Exception("Cannot specify custom installation directory "
                            "('{}') for NEURON simulator as it needs to be "
                            "located as a specifically named directory of the "
                            "src directory (e.g. x86_64 for 64b unix/linux)"
                            .format(install_dir))
        # return the platform-specific location of the nrnivmodl output files
        return os.path.abspath(os.path.join(build_dir, self._SRC_DIR,
                                            self.specials_dir))

    def _get_compile_dir(self, build_dir):
        """
        The compile dir is the same as the src dir for NEURON compile
        """
        return os.path.abspath(os.path.join(build_dir, self._SRC_DIR))

    def _get_specials_dir(self):
        # Create a temporary directory to run nrnivmodl in
        tmp_dir_path = os.path.join(tempfile.gettempdir(), uuid.uuid4())
        try:
            os.mkdir(tmp_dir_path)
        except IOError:
            raise Exception("Error creating temporary directory '{}'"
                            .format(tmp_dir_path))
        orig_dir = os.getcwd()
        os.chdir(tmp_dir_path)
        # Run nrnivmodl to see what build directory is created
        try:
            with open(os.devnull, "w") as fnull:
                sp.check_call(self.nrnivmodl_path, stdout=fnull, stderr=fnull)
        except sp.CalledProcessError as e:
            raise Exception("Error test running nrnivmodl".format(e))
        # Get the name of the specials directory
        try:
            specials_dir = os.listdir(tmp_dir_path)[0]
        except IndexError:
            raise Exception("Error test running nrnivmodl no build directory "
                            "created".format(e))
        # Return back to the original directory
        os.chdir(orig_dir)
        return specials_dir
