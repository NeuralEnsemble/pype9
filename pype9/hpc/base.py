#!/usr/bin/env python
"""
  Wraps a executable to enable that script to be submitted to an SGE cluster
  engine

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
import sys
import os.path
import argparse
from copy import copy
import time
import subprocess
import shutil
from pype9.arguments import outputpath


class HPCSubmitter(object):
    """
    This class automates the submission of MPI jobs on a SGE-powered high-
    performance computing cluster
    """

    MEAN_MEMORY_RATIO_DEFAULT = 0.8

    def __init__(self, script_path, num_processes=8, que_name='shortP',
                 max_memory='4800m', mean_memory=None, python_install_dir=None,
                 mpi_install_dir=None, neuron_install_dir=None,
                 nest_install_dir=None, sundials_install_dir=None,
                 work_dir_parent=None, output_dir_parent=None,
                 logging_dir=None):
        self.script_path = os.path.abspath(script_path)
        self.num_processes = num_processes
        self.que_name = que_name
        self.max_memory = max_memory
        if mean_memory is None:
            max_mem_in_mb = float(max_memory[:-1])
            if max_memory[-1] in ('g', 'G'):
                max_mem_in_mb *= 1000
            elif max_memory[-1] not in ('m', 'M'):
                raise Exception(
                    "Unrecognised memory unit '{}'".format(max_memory[-1]))
            mean_memory = str(int(round(max_mem_in_mb *
                                        self.MEAN_MEMORY_RATIO_DEFAULT))) + 'm'
        self.mean_memory = mean_memory
        if python_install_dir:
            self.py_dir = python_install_dir
        else:
            self.py_dir = os.environ.get('PYTHONHOME', None)
        if mpi_install_dir:
            self.mpi_dir = mpi_install_dir
        else:
            self.mpi_dir = os.environ.get('MPIHOME', None)
        if neuron_install_dir:
            self.nrn_dir = neuron_install_dir
        else:
            self.nrn_dir = os.environ.get('NRNHOME', None)
        if nest_install_dir:
            self.nest_dir = nest_install_dir
        else:
            self.nest_dir = os.environ.get('NESTHOME', None)
        if sundials_install_dir:
            self.sdials_dir = sundials_install_dir
        else:
            self.sdials_dir = os.environ.get('SUNDIALSHOME', None)
        # Import the script as a module
        self.script_name = os.path.splitext(os.path.basename(script_path))[0]
        if os.path.dirname(self.script_path):
            sys.path.insert(0, os.path.dirname(self.script_path))
        exec("import {} as script".format(self.script_name))
        sys.path.pop(0)
        self.script = script  # @UndefinedVariable
        # Place empty versions of parser and prepare_work_dir if they are not
        # provided by script
        if not hasattr(self.script, 'parser'):
            self.script.parser = argparse.ArgumentParser()
        self.script_args = copy(self.script.parser._actions)
        if not hasattr(script, 'prepare_work_dir'):  # @UndefinedVariable
            def dummy_func(src_dir, args):
                pass
            self.script.prepare_work_dir = dummy_func
        # Create work dir and set output dir path
        self._create_work_dir(work_dir_parent, output_dir_parent,
                              logging_dir)

    def _create_work_dir(self, work_dir_parent=None, output_dir_parent=None,
                         logging_dir=None, required_dirs=[],
                         dependencies=[]):
        """
        Generates unique paths for the work and output directories, creating
        the work directory in the process.

        `script_name`       -- The name of the script, used to name the
                               directories appropriately
        `work_dir`          -- The name of the
        `output_dir_parent` -- The name of the parent directory in which the
                               output directory
                               "will be created (defaults to $HOME/Output).
        `required_dirs`    -- The sub-directories that need to be copied into
                              the work directory
        """
        if output_dir_parent is None:
            output_dir_parent = os.path.join(os.environ['HOME'], 'output')
        if work_dir_parent is None:
            work_dir_parent = os.path.realpath(os.path.join(os.environ['HOME'],
                                                            'work'))
        if logging_dir is None:
            logging_dir = os.path.realpath(os.path.join(os.environ['HOME'],
                                                        'running'))
        if not os.path.exists(work_dir_parent):
            raise Exception(
                "Symbolic link to work directory is missing from your home "
                "directory (i.e. $HOME/work). A symbolic link should be "
                "created that points to an appropriate directory in your "
                "units sub-directory of '/work' "
                "(i.e. ln -s /work/<unit-name>/<user-name> $HOME/work)")
        if not work_dir_parent.startswith('/work'):
            raise Exception(
                "$HOME/work be a symbolic link to a sub-directory of the "
                "high-performance filesystem mounted at '/work' (typically "
                "/work/<unit-name>/<user-name>).")
        # Automatically generate paths
        # Unique time for distinguishing runs
        time_str = time.strftime('%Y-%m-%d-%A_%H-%M-%S', time.localtime())
        # Working directory path
        self.work_dir = os.path.join(
            work_dir_parent, self.script_name + "." + time_str + ".1")
        # Ensure that working directory is unique
        created_work_dir = False
        count = 1
        while not created_work_dir:
            try:
                created_work_dir = not os.makedirs(self.work_dir)
            except IOError as e:
                count += 1
                if count > 1000:
                    print ("Something has gone wrong, can't create directory "
                           "'{}' after 1000 attempts".format(self.work_dir))
                    raise e
                # Replace old count at the end of work directory with new count
                self.work_dir = '.'.join(
                    self.work_dir.split('.')[:-1] + [str(count)])
        self.logging_path = os.path.join(logging_dir,
                                         os.path.basename(self.work_dir))
        # Make output directory for the generated files
        os.mkdir(os.path.join(self.work_dir, 'output'))
        # Write time string to file for future reference
        with open(os.path.join(self.work_dir,
                               'output', 'time_stamp'), 'w') as f:
            f.write(time_str + '\n')
        # Determine the path for the output directory when it is copied to the
        # output directory destination
        self.output_dir = os.path.join(
            output_dir_parent, os.path.split(self.work_dir)[1])
        # os.mkdir(self.output_dir)
        # Copy snapshot of selected subdirectories to working directory
        for directory in required_dirs:
            print ("Copying '{}' sub-directory to work directory"
                   .format(directory))
            shutil.copytree(
                directory, os.path.join(self.work_dir, directory),
                symlinks=True)
        if dependencies:
            dependency_dir = os.path.join(self.work_dir, 'depend')
            os.mkdir(dependency_dir)
            for from_, to_ in dependencies:
                shutil.copytree(from_, os.path.join(dependency_dir, to_))

    def parse_arguments(self, argv=None,
                        args_to_remove=['plot', 'plot_saved']):
        if argv is None:
            argv = sys.argv[1:]
        parser = self.script.parser
        removed_args = []
        for opt in args_to_remove:
            try:
                action = next(a for a in parser._actions if a.dest == opt)
                removed_args.append((action.dest, action.default))
                parser._remove_action(action)
            except StopIteration:  # Don't worry if the action isn't present
                pass
        parser.add_argument(
            '--np', type=int, default=self.num_processes,
            help="The the number of processes to use for the simulation "
            "(default: %(default)s)")
        parser.add_argument(
            '--que_name', type=str, default=self.que_name,
            help="The the que to submit the job to (default: '%(default)s')")
        parser.add_argument(
            '--output_dir', default=None, type=str,
            help="The parent directory in which the output directory will be "
            "created  (default: $HOME/Output)")
        parser.add_argument(
            '--max_memory', type=str, default=self.max_memory,
            help="The maximum memory allocated to run the network "
            "(default: '%(default)s')")
        parser.add_argument(
            '--mean_memory', type=str, default=self.mean_memory,
            help="The average memory usage required by the program, decides "
                 "when the scheduler is able to run the job "
                 "(default: '%(default)s')")
        parser.add_argument(
            '--time_limit', type=float, default=None,
            help="The time limit after which the job will be terminated")
        parser.add_argument(
            '--jobname', type=str, default=None,
            help="Saves a file within the output directory with the "
                 "descriptive name for easy renaming of the output directory "
                 "after it is copied to its final destination, via the "
                 "command 'mv <output_dir> `cat <output_dir>/name`'")
        parser.add_argument(
            '--dry_run', action='store_true',
            help="Performs a dry run without trying to  submit the job to the "
            "cluster for testing")
        parser.add_argument(
            '--work_dir', type=str, default=None,
            help="The work directory in which to run the simulation")
        args = parser.parse_args(argv)
        self.num_processes = args.np
        self.que_name = args.que_name
        self.max_memory = args.max_memory
        self.mean_memory = args.mean_memory
        for arg in self.script_args:
            if arg.type is outputpath:
                path = getattr(args, arg.dest)
                if path:
                    basename = os.path.basename(path)
                    new_path = self.work_dir + '/output/' + basename
                    setattr(args, arg.dest, new_path)
        for name, default_val in removed_args:
            setattr(args, name, default_val)
        return args

    def submit(self, args, env=None, copy_to_output=[],
               strip_9build_from_copy=True, name=None):
        """
        Create a jobscript in the work directory and then submit it to the
        tombo que

        `override_args`  -- Override existing arguments parsed from command
                            line
        `env`            -- The required environment variables (defaults to
                            those generated by '_create_env(work_dir)')
        `copy_to_output` -- Directories to copy into the output directory
        `strip_build_from_copy` -- Removes all files and directories to be
                            copied that have the name 'build'
        `name`           -- Records a name for the run (when generating
                            multiple runs) so that the output directory can be
                            easily renamed to a more informative name after it
                            is copied to its destination via the command "mv
                            <output_dir> `cat <output_dir>/name`"
        """
        # Copy necessary files into work directory and compile if necessary
        self.script.prepare_work_dir(self, args)
        # Create command line to be run in job script from parsed arguments
        cmdline = self._create_cmdline(args)
        if not env:
            env = self._create_env(self.work_dir)
        else:
            env = copy(env)
        copy_cmd = ''
        for to_copy in copy_to_output:
            origin = self.work_dir + os.path.sep + to_copy
            if strip_9build_from_copy:
                copy_cmd += ('find {origin} -name .9build -exec rm -r {{}} \;'
                             ' 2>/dev/null\n'
                             .format(origin=origin))
            destination = self.output_dir + os.path.sep + to_copy
            base_dir = os.path.dirname(
                destination[:-1]
                if destination.endswith('/') else destination)
            copy_cmd += ("""
mkdir -p {base_dir}
cp -r {origin} {destination}
""" .format(base_dir=base_dir, origin=origin,
                destination=destination))
        # Create jobscript
        if args.time_limit:
            if (not isinstance(args.time_limit, str) or
                    len(args.time_limit.split(':')) != 3):
                raise Exception("Poorly formatted time limit string '{}' "
                                "passed to submit job".format(args.time_limit))
            time_limit_option = ("\n# Set the maximum run time\n#$ -l h_rt "
                                 "{}\n" .format(args.time_limit))
        else:
            time_limit_option = ''
        if name:
            name_cmd = "echo '{name}' > {output_dir}/name"
        else:
            name_cmd = ""
        jobscript_path = os.path.join(self.work_dir, self.script_name + '.job')
        self._write_jobscript(self, jobscript_path, args, env,
                                         name_cmd, cmdline, copy_cmd,
                                         time_limit_option)
        # Submit job
        print ("\nSubmitting job {} to que {}"
               .format(jobscript_path, self.que_name))
        if args.dry_run:
            print ("Would normally call 'qsub {}' here but '--dry_run' option "
                   "was provided" .format(jobscript_path))
        else:
            self._submit_to_que(jobscript_path)
        print ("\nA working directory has been created at {}"
               .format(self.work_dir))
        print ("Once completed the output files will be copied to {}\n"
               .format(self.output_dir))
        print ("While the job is running the output stream can be viewed by "
               "the following command:\n")
        print "less {}\n".format(self.logging_path)
        print ("After it is finished the job it can be viewed at "
               "the following command:\n")
        print "less {}\n".format(os.path.join(self.output_dir, 'log'))

    def _create_cmdline(self, args, skip_args=[]):
        cmdline = 'python {}'.format(self.script_path)
        options = ''
        for arg in self.script_args:
            name = arg.dest
            if hasattr(args, name) and name not in skip_args:
                val = getattr(args, name)
                if arg.required:
                    cmdline += ' {}'.format(val)
                else:
                    if isinstance(arg, argparse._StoreTrueAction):
                        if val:
                            options += ' --{}'.format(name)
                    elif isinstance(arg, argparse._StoreFalseAction):
                        if not val:
                            options += ' --{}'.format(name)
                    elif val is not None and val != []:
                        if isinstance(arg, argparse._AppendAction):
                            values = val
                        else:
                            values = [val]
                        for v in values:
                            options += ' --{}'.format(name)
                            if arg.nargs in ('+', '*') or arg.nargs > 1:
                                options += ' ' + ' '.join([str(i) for i in v])
                            else:
                                options += ' {}'.format(v)
        cmdline += options
        return cmdline

    def _create_env(self, work_dir):
        """
        Creates a dictionary containing the appropriate environment variables

        `work_dir` -- The work directory to set the envinroment variables for
        """
        env = os.environ.copy()
        # os.path.abspath(os.path.dirname(self.script_path)) + os.pathsep
        new_path = ''
        if self.py_dir:
            new_path += os.path.join(self.py_dir, 'bin') + os.pathsep
        if self.mpi_dir:
            new_path += os.path.join(self.mpi_dir, 'bin') + os.pathsep
        if self.nrn_dir:
            new_path += os.path.join(self.nrn_dir,
                                     'x86_64', 'bin') + os.pathsep
        if self.nest_dir:
            new_path += os.path.join(self.nest_dir, 'bin') + os.pathsep
        if self.sdials_dir:
            os.path.join(self.sdials_dir, 'bin') + os.pathsep
        env['PATH'] = new_path + env['PATH']
        new_pythonpath = os.path.join(work_dir, 'depend') + os.pathsep
        if self.nest_dir:
            new_pythonpath += (os.path.join(self.nest_dir,
                                            'lib', 'python2.7',
                                            'dist-packages') + os.pathsep)
        env['PYTHONPATH'] = new_pythonpath + os.pathsep.join(sys.path)
        new_library_path = ''
        if self.mpi_dir:
            new_library_path += os.path.join(self.mpi_dir, 'lib') + os.pathsep
        if self.nest_dir:
            new_library_path += os.path.join(self.nest_dir,
                                             'lib', 'nest') + os.pathsep
        if self.sdials_dir:
            new_library_path += os.path.join(self.sdials_dir, 'lib')
        env['NINEML_SRC_PATH'] = os.path.join(work_dir, 'src')
        return env

    def compile(self, args):
        """
        Compiles objects in the work directory that are required by the NINEML+
        network

        @param script_name: Name of the script in the 'simulate' directory
        @param work_dir: The work directory in which the network is compiled
        @param env: The required environment variables (defaults to those
                    generated by 'create_env(work_dir)')
        @param script_dir: The directory that the script is stored in
                           (default: 'simulate')
        """
        env = self._create_env(self.work_dir)
        env['NINEMLP_MPI'] = '1'
        # Remove NMODL build directory for pyNN neuron so it can be recompiled
        # in script
#         if args.simulator == 'neuron':
#             pynn_nmodl_path = os.path.join(self.work_dir, 'depend', 'pyNN',
#                                            'neuron', 'nmodl')
#             if os.path.exists(os.path.join(pynn_nmodl_path, 'x86_64')):
#                 shutil.rmtree(os.path.join(pynn_nmodl_path, 'x86_64'))
#             subprocess.check_call('cd {}; {}'
#                                   .format(pynn_nmodl_path,
#                                           path_to_exec('nrnivmodl')),
#                                   shell=True)
        cmd_line = self._create_cmdline(args, skip_args=['build'])
        cmd_line += ' --build build_only'
        print "Compiling required NINEML+ objects"
        print cmd_line
        subprocess.check_call(cmd_line, shell=True, env=env)
