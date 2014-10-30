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
    os.environ['PATH'] += os.pathsep + \
        os.path.join(os.environ['NRNHOME'], platform.machine(), 'bin')
else:
    try:
        if os.environ['HOME'] == '/home/tclose':
            # I apologise for this little hack (this is the path on my machine,
            # to save me having to set the environment variable in eclipse)
            os.environ['PATH'] += os.pathsep + '/opt/NEURON/nrn-7.3/x86_64/bin'
    except KeyError:
        pass


class CodeGenerator(BaseCodeGenerator):

    #BUILD_ARCHS = [platform.machine(), 'i686', 'x86_64', 'powerpc', 'umac']
    SIMULATOR_NAME = 'neuron'
    _DEFAULT_SOLVER = 'derivimplicit'
    _TMPL_PATH = os.path.join(os.path.dirname(__file__), 'jinja_templates')

    def __init__(self):
        super(CodeGenerator, self).__init__()
        # Find the path to nrnivmodl
        self.nrnivmodl_path = self._path_to_exec('nrnivmodl')
        # Work out the name of the installation directory for the compiled
        # mode files on the current platform
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
        # Get the name of the build directory and save it in the builder
        try:
            self.install_dir = os.listdir(tmp_dir_path)[0]
        except IndexError:
            raise Exception("Error test running nrnivmodl no build directory "
                            "created".format(e))
        # Return back to the original directory
        os.chdir(orig_dir)

    def generate(self, celltype_name, nineml_path, install_dir=None,
                 build_dir=None, method='derivimplicit',
                 build_mode='lazy', silent_build=False, kinetics=[]):
        """
        Generates and builds the required NMODL files for a given NCML cell
        class

        @param celltype_name [str]: Name of the celltype to be built
        @param nineml_path [str]: Path to the NCML file from which the NMODL
                                  files will be compiled and built
        @param install_dir [str]: Path to the directory where the NMODL files
                                  will be generated and compiled
        @param build_dir [str]: Used to set the default 'install_dir'
                                       path
        @param method [str]: The method option to be passed to the NeMo
                             interpreter command
        @param kinetics [list(str)]: A list of ionic components to be generated
                                     using the kinetics option
        """
        # Save original working directory to reinstate it afterwards (just to
        # be polite)
        orig_dir = os.getcwd()
        # Determine the paths for the src, build and install directories
        (default_install_dir,
         params_dir, _, _) = self.get_build_paths(nineml_path, celltype_name,
                                                  self._SIMULATOR_BUILD_NAME,
                                                  build_dir)
        if not install_dir:
            install_dir = default_install_dir
        if build_mode in ('force', 'build_only'):
            shutil.rmtree(install_dir, ignore_errors=True)
            shutil.rmtree(params_dir, ignore_errors=True)
        elif build_mode in ('compile_only', 'require'):
            if (not os.path.exists(install_dir) or
                not os.path.exists(params_dir)):
                raise Exception("Prebuilt installation directory '{install}'"
                                "and/or python parameters directory '{params}'"
                                "are not present, which are required for "
                                "'require' or 'compile_only' build options"
                                .format(install=install_dir,
                                        params=params_dir))
        try:
            if not os.path.exists(install_dir):
                os.makedirs(install_dir)
            if not os.path.exists(params_dir):
                os.makedirs(params_dir)
        except IOError as e:
            raise Exception("Could not create a required neuron build "
                            "directory, check the required permissions or "
                            "specify a different  parent build directory -> {}"
                            .format(e))
        # Get the stored modification time of the previous build if it exists
        install_mtime_path = os.path.join(install_dir, self._TIME_OF_EDIT_FILE)
        params_mtime_path = os.path.join(params_dir, self._TIME_OF_EDIT_FILE)
        if os.path.exists(install_mtime_path):
            with open(install_mtime_path) as f:
                prev_install_mtime = f.readline()
        else:
            prev_install_mtime = ''
        if os.path.exists(params_mtime_path):
            with open(params_mtime_path) as f:
                prev_params_mtime = f.readline()
        else:
            prev_params_mtime = ''
        # Get the modification time of the source NCML file for comparison with
        # the build directory
        ncml_mtime = time.ctime(os.path.getmtime(nineml_path))
        rebuilt = False
        if ((ncml_mtime != prev_install_mtime
             or ncml_mtime != prev_params_mtime) and
            build_mode != 'compile_only'):
            nemo_cmd = ("{nemo_path} {nineml_path} -p --pyparams={params} "
                        "--nmodl={output} --nmodl-method={method} "
                        "--nmodl-kinetic={kinetics}"
                        .format(nemo_path=self._path_to_exec('nemo'),
                                nineml_path=os.path.normpath(nineml_path),
                                output=os.path.normpath(install_dir),
                                params=params_dir, kinetics=','.join(kinetics),
                                method=method))
            try:
                sp.check_call(nemo_cmd, shell=True)
            except sp.CalledProcessError as e:
                raise Exception("Error while compiling NCML description into "
                                "NMODL code -> {}".format(e))
            # Build mode is set to 'force' because the mod files have been
            # regenerated
            with open(install_mtime_path, 'w') as f:
                f.write(ncml_mtime)
            with open(params_mtime_path, 'w') as f:
                f.write(ncml_mtime)
            rebuilt = True
        if rebuilt or build_mode == 'compile_only':
            self.compile_nmodl(install_dir, build_mode='force',
                               silent=silent_build)
        # Switch back to original dir
        os.chdir(orig_dir)
        # Load the parameter name translations from the params dir
        component_translations = self.load_component_translations(
                                                   celltype_name, params_dir)
        return install_dir, component_translations

    def _get_install_dir(self, build_dir, install_dir):
        if install_dir:
            raise Exception("Cannot specify custom installation directory "
                            "('{}') for NEURON simulator as it needs to be "
                            "located as a specifically named directory of the "
                            "src directory"
                            .format(install_dir))
        # return the platform-specific location of the nrnivmodl output files
        return os.path.abspath(os.path.join(build_dir, self._SRC_DIR,
                                            self.install_dir))

    def generate_source_files(self, src_dir, compile_dir, install_dir,
                              celltype_name=None, silent=False):
        raise NotImplementedError

    def compile_source_files(self, src_dir, compile_dir, install_dir, #@UnusedVariable @IgnorePep8
                             celltype_name, silent=False):
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
        os.chdir(src_dir)
        print "Building mechanisms in '{}' directory.".format(src_dir)
        # Run nrnivmodl command in src directory
        try:
            if silent:
                with open(os.devnull, "w") as fnull:
                    sp.check_call(self.nrnivmodl_path, stdout=fnull,
                                  stderr=fnull)
            else:
                sp.check_call(self.nrnivmodl_path)
        except sp.CalledProcessError as e:
            raise Exception("Compilation of NMODL files for '{}' model failed."
                            " See src directory '{}':\n "
                            .format(celltype_name, src_dir, e))
