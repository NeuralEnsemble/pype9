#!/usr/bin/env python
"""
Wraps a executable to enable that script to be submitted to an SGE cluster engine
"""
import sys
import os.path
import argparse
from copy import copy
import time
import subprocess
import shutil


class SGESubmitter(object):
    """
    This class automates the submission of MPI jobs on a SGE-powered high-performance computing 
    cluster
    """

    def __init__(self, script_path, np=8, que_name='short', max_memory='3g', virtual_memory='2g',
                 python_install_dir=None, mpi_install_dir=None,  neuron_install_dir=None, 
                 nest_install_dir=None, sundials_install_dir=None, work_dir_parent=None, 
                 output_dir_parent=None):
        self.script_path = os.path.abspath(script_path)
        self.np = np
        self.que_name = que_name
        self.max_memory = max_memory
        self.virtual_memory = virtual_memory
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
        
        if os.path.dirname(self.script_path):
            sys.path.append(os.path.dirname(self.script_path))
        self.script_name = os.path.splitext(os.path.basename(script_path))[0]
        exec("import {} as script".format(self.script_name))
        self.script = script
        # Place empty versions of parser and prepare_work_dir if they are not provided by script
        if not hasattr(self.script, 'parser'):
            self.script.parser = argparse.ArgumentParser()
        self.script_args = copy(self.script.parser._actions)
        if not hasattr(script, 'prepare_work_dir'):
            def dummy_func(src_dir, args):
                pass
            self.script.prepare_work_dir = dummy_func
        # Create work dir and set output dir path
        self._create_work_dir(work_dir_parent, output_dir_parent)

    def _create_work_dir(self, work_dir_parent=None, output_dir_parent=None, required_dirs=[], 
                         dependencies=[]):
        """
        Generates unique paths for the work and output directories, creating the work directory in the 
        process.
        
        `script_name`       -- The name of the script, used to name the directories appropriately
        `work_dir`          -- The name of the 
        `output_dir_parent` -- The name of the parent directory in which the output directory """ \
                               "will be created (defaults to $HOME/Output)."
        "`required_dirs`    -- The sub-directories that need to be copied into the work directory"
        if not output_dir_parent:
            output_dir_parent = os.path.join(os.environ['HOME'], 'output')
        work_dir_parent = os.path.realpath(os.path.join(os.environ['HOME'], 'work'))
        if not os.path.exists(work_dir_parent):
            raise Exception("Symbolic link to work directory is missing from your home directory "
                            "(i.e. $HOME/work). A symbolic link should be created that points to "
                            "an appropriate directory in your units sub-directory of '/work' "
                            "(i.e. ln -s /work/<unit-name>/<user-name> $HOME/work)")
        if not work_dir_parent.startswith('/work'):
            raise Exception("$HOME/work be a symbolic link to a sub-directory of the "
                            "high-performance filesystem mounted at '/work' (typically "
                            "/work/<unit-name>/<user-name>).")
        # Automatically generate paths
        # Unique time for distinguishing runs
        time_str = time.strftime('%Y-%m-%d-%A_%H-%M-%S', time.localtime())
        # Working directory path
        self.work_dir = os.path.join(work_dir_parent, self.script_name + "." + time_str + ".1")
        # Ensure that working directory is unique
        created_work_dir = False
        count = 1
        while not created_work_dir:
            try:
                created_work_dir = not os.makedirs(self.work_dir)
            except IOError as e:
                count += 1
                if count > 1000:
                    print "Something has gone wrong, can't create directory '{}' after 1000 " \
                          "attempts".format(self.work_dir)
                    raise e
                # Replace old count at the end of work directory with new count
                self.work_dir = '.'.join(self.work_dir.split('.')[:-1] + [str(count)])
        # Make output directory for the generated files
        os.mkdir(os.path.join(self.work_dir, 'output'))
        # Write time string to file for future reference
        with open(os.path.join(self.work_dir, 'output', 'time_stamp'), 'w') as f:
            f.write(time_str + '\n')
        # Determine the path for the output directory when it is copied to the output directory destination
        self.output_dir = os.path.join(output_dir_parent, os.path.split(self.work_dir)[1])
        # Copy snapshot of selected subdirectories to working directory
        for directory in required_dirs:
            print "Copying '{}' sub-directory to work directory".format(directory)
            shutil.copytree(directory, os.path.join(work_dir, directory), symlinks=True)
        if dependencies:
            dependency_dir = os.path.join(work_dir, 'depend')
            os.mkdir(dependency_dir)
            for from_, to_ in dependencies:
                shutil.copytree(from_, os.path.join(dependency_dir, to_))
    
    def parse_arguments(self, argv, remove_options_from_script=('plot','output','disable_mpi')):
        parser = self.script.parser
        for opt in remove_options_from_script:
            try:
                parser._remove_action(next(a for a in parser._actions if a.dest == opt))
            except StopIteration:
                pass
        parser.add_argument('--np', type=int, default=self.np,
                        help="The the number of processes to use for the simulation "
                             "(default: %(default)s)")
        parser.add_argument('--que_name', type=str, default=self.que_name,
                            help="The the que to submit the job to (default: '%(default)s')")
        parser.add_argument('--output_dir', default=None, type=str,
                            help="The parent directory in which the output directory will be created "
                                 "(default: $HOME/Output)")
        parser.add_argument('--max_memory', type=str, default=self.max_memory,
                            help="The maximum memory allocated to run the network "
                                 "(default: '%(default)s')")
        parser.add_argument('--virtual_memory', type=str, default=self.virtual_memory,
                            help="The average memory usage required by the program, decides when "
                                  "the scheduler is able to run the job (default: '%(default)s')")
        parser.add_argument('--time_limit', type=float, default=None,
                            help="The time limit after which the job will be terminated")
        parser.add_argument('--jobname', type=str, default=None,
                            help="Saves a file within the output directory with the descriptive name"
                                 " for easy renaming of the output directory after it is copied to "
                                 "its final destination, via the command "
                                 "'mv <output_dir> `cat <output_dir>/name`'")
        parser.add_argument('--dry_run', action='store_true',
                            help="Performs a dry run without trying to  submit the job to the "
                                 "cluster for testing")
        parser.add_argument('--work_dir', type=str, default=None,
                            help="The work directory in which to run the simulation")
        args = parser.parse_args(argv)
        self.np = args.np
        self.que_name = args.que_name
        self.max_memory = args.max_memory
        self.virtual_memory = args.virtual_memory
        return args

    def submit(self, args, env=None, copy_to_output=[], strip_9build_from_copy=True,
               name=None, dry_run=False):
        """
        Create a jobscript in the work directory and then submit it to the tombo que
        
        `override_args`  -- Override existing arguments parsed from command line
        `env`            -- The required environment variables (defaults to those generated by '_create_env(work_dir)')    
        `copy_to_output` -- Directories to copy into the output directory
        `strip_build_from_copy` -- Removes all files and directories to be copied that have the name 'build'
        `name`           -- Records a name for the run (when generating multiple runs) so that the output directory can be easily renamed to a more informative name after it is copied to its destination via the command "mv <output_dir> `cat <output_dir>/name`"
        """
        # Copy necessary files into work directory and compile if necessary
        self.script.prepare_work_dir(self.work_dir, args)
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
                copy_cmd += 'find {origin} -name .9build -exec rm -r {{}} \; 2>/dev/null\n'.\
                          format(origin=origin)
            destination = self.output_dir + os.path.sep + to_copy
            base_dir = os.path.dirname(destination[:-1] if destination.endswith('/') else destination)
            copy_cmd += (
"""
mkdir -p {base_dir}
cp -r {origin} {destination}
"""
                         .format(base_dir=base_dir, origin=origin, destination=destination))
        # Create jobscript
        if args.time_limit:
            if type(args.time_limit) != str or len(args.time_limit.split(':')) != 3:
                raise Exception("Poorly formatted time limit string '{}' passed to submit job"
                                .format(args.time_limit))
            time_limit_option = ("\n# Set the maximum run time\n#$ -l h_rt {}\n"
                                 .format(args.time_limit))
        else:
            time_limit_option = ''
        if name:
            name_cmd = "echo '{name}' > {output_dir}/name"
        else:
            name_cmd = ""
        jobscript_path = os.path.join(self.work_dir, self.script_name + '.job')
        with open(jobscript_path, 'w') as f:
            f.write(
"""#!/usr/bin/env sh
    
# Parse the job script using this shell
#$ -S /bin/bash

# Send stdout and stderr to the same file.
#$ -j y

# Standard output and standard error files
#$ -o {work_dir}/output_stream
#$ -e {work_dir}/output_stream

# Name of the queue
#$ -q {que_name}

# use OpenMPI parallel environment with {np} processes
#$ -pe openmpi {np}
{time_limit}
# Set the memory limits for the script
#$ -l h_vmem={max_memory}
#$ -l virtual_free={virtual_memory}

# Export the following env variables:
#$ -v HOME
#$ -v PATH
#$ -v PYTHONPATH
#$ -v LD_LIBRARY_PATH
#$ -v NINEMLP_SRC_PATH
#$ -v NINEMLP_MPI
#$ -v BREP_DEVEL
#$ -v PARAMDIR
#$ -v VERBOSE

###################################################
### Copy the model to all machines we are using ###
###################################################

# Set up the correct paths 
export PATH={path}:$PATH
export PYTHONPATH={pythonpath}
export LD_LIBRARY_PATH={ld_library_path}

echo "============== Starting mpirun ===============" 

cd {work_dir}
{cmdline}

echo "============== Mpirun has ended =============="

echo "Copying files to output directory '{output_dir}'"
cp -r {work_dir}/output {output_dir}
cp {jobscript_path} {output_dir}/job
cp {work_dir}/output_stream {output_dir}/output
{name_cmd}
{copy_cmd}

echo "============== Done ===============" 
"""
            .format(work_dir=self.work_dir, args=args, path=env['PATH'], np=self.np, 
                    que_name=self.que_name, max_memory = self.max_memory, 
                    virtual_memory=self.virtual_memory, pythonpath=env['PYTHONPATH'], 
                    ld_library_path=env['LD_LIBRARY_PATH'], cmdline=cmdline, 
                    output_dir=self.output_dir, name_cmd=name_cmd, copy_cmd=copy_cmd, 
                    jobscript_path=jobscript_path, time_limit=time_limit_option))
        # Submit job
        print "Submitting job '{}' to que '{}'".format(jobscript_path, self.que_name)
        if dry_run:
            print ("Would normally call 'qsub {}' here but 'dry_run' option was provided"
                   .format(jobscript_path))
        else:
            subprocess.check_call('qsub {}'.format(jobscript_path), shell=True)
        print "Your job '{}' has been submitted".format(jobscript_path)
        print "The output stream can be viewed by:"
        print "less {}".format(os.path.join(self.work_dir, 'output_stream'))
        print ("Once completed the output files (including the output stream and job script) of "
               "this job will be copied to: {}".format(self.output_dir))
    
    def _create_cmdline(self, args):
        cmdline = 'time mpirun python {}'.format(self.script_path)
        options = ' --output {}/output/'.format(self.work_dir)
        for arg in self.script_args:
            name = arg.dest
            if hasattr(args, name):
                val = getattr(args, name)
                if arg.required:
                        cmdline += ' {}'.format(val)
                else:
                    if val is not False:
                        options += ' --{}'.format(name)
                        if val is not True:
                            options += ' {}'.format(val)
        cmdline += options
        return cmdline

    def _create_env(self, work_dir):
        """
        Creates a dictionary containing the appropriate environment variables
        
        `work_dir` -- The work directory to set the envinroment variables for
        """
        env = os.environ.copy()
        new_path = '' #os.path.abspath(os.path.dirname(self.script_path)) + os.pathsep
        if self.py_dir:
            new_path += os.path.join(self.py_dir, 'bin') + os.pathsep
        if self.mpi_dir:
            new_path += os.path.join(self.mpi_dir, 'bin') + os.pathsep
        if self.nrn_dir:
            new_path += os.path.join(self.nrn_dir, 'x86_64', 'bin') + os.pathsep
        if self.nest_dir:
            new_path += os.path.join(self.nest_dir, 'bin') + os.pathsep
        if self.sdials_dir:
            os.path.join(self.sdials_dir, 'bin') + os.pathsep
        env['PATH'] = new_path + env['PATH']
        new_pythonpath = os.path.join(work_dir, 'depend') + os.pathsep
        if self.nest_dir:
            new_pythonpath += (os.path.join(self.nest_dir, 'lib', 'python2.7', 'dist-packages') +
                               os.pathsep)
        env['PYTHONPATH'] = new_pythonpath + os.pathsep.join(sys.path)
        new_library_path = ''
        if self.mpi_dir:
            new_library_path += os.path.join(self.mpi_dir, 'lib') + os.pathsep
        if self.nest_dir:
            new_library_path += os.path.join(self.nest_dir, 'lib', 'nest') + os.pathsep
        if self.sdials_dir:
            new_library_path += os.path.join(self.sdials_dir, 'lib')
        env['NINEML_SRC_PATH'] = os.path.join(work_dir, 'src')
        return env


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception("At least one argument (the script name to submit to the que) should be "
                        "passed to que_sge.py")
    submitter = SGESubmitter(sys.argv[1])
    args = submitter.parse_arguments(sys.argv[2:])
    submitter.submit(args)
