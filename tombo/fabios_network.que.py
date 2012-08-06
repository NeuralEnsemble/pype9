#!/usr/bin/env python

####################################################################################################
# 
# This script prepares the environment for the Sun Grid Engine batch script to run in by making a
# snapshot of the code base at the start of the run and queing the related batch script 
# 'fabios_network.job.sh'.
#
# Author: Tom Close (tclose@oist.jp)
# Created: 8/6/2012
# 
####################################################################################################

import os.path
import time
import shutil
import subprocess

#Name of the script to run
SCRIPT_NAME = 'fabios_network'

# Automatically generate paths
time_str = time.strftime('%Y-%m-%d(%A)_%H-%M-%S', time.localtime()) # Unique time for distinguishing runs
work_dir = os.path.join(os.environ['HOME'], 'Work', SCRIPT_NAME + "." + time_str + ".1") # Working directory path
code_dir = os.normpath(os.path.join(os.path.basename(os.path.abspath(__file__), '..'))) # Root directory of the project code

#Ensure that working directory is unique
count = 2
while os.path.exists(work_dir):
    work_dir[-1] = str(count)
    count += 1   
os.makedirs(workd_dir) 

# Copy snapshot of code directory and network description to working directory
DIRS_TO_COPY = ['src', 'xml']
for directory in DIRS_TO_COPY:
    shutil.copytree(os.path.join(code_dir,directory), os.path.join(work_dir,directory), symlinks=True)

# Set path variables
PATH ='/apps/DeschutterU/NEURON-7.2/x86_64/bin:/opt/mpi/gnu/openmpi-1.4.3/bin:/apps/python/272/bin:'
PYTHONPATH = os.path.join(work_dir, 'src')
LD_LIBRARY_PATH = '/opt/mpi/gnu/openmpi-1.4.3/lib'
NINEMLP_SRC_PATH = os.path.join(work_dir, 'src')

#Compile network
os.environ['PATH'] = PATH + os.environ['PATH']
os.environ['PYTHONPATH'] = PYTHONPATH
os.environ['LD_LIBRARY_PATH'] = LD_LIBRARY_PATH
os.environ['NINEMLP_SRC_PATH'] = NINEMLP_SRC_PATH
os.environ['NINEMLP_BUILD_MODE'] = 'compile_only'
os.environ['NINEMLP_MPI'] = 1
execfile(os.path.join(work_dir,'src', 'test', SCRIPT_NAME + '.py'))

#Create jobscript
jobscript_path = os.path.join(work_dir, 'jobscript.sh')
f = open(jobscript_path, 'w')
f.write("""#!/bin/sh

# Parse the job script using this shell
#$ -S /bin/bash

# Send stdout and stderr to the same file.
#$ -j y

# Standard output and standard error files
#$ -o {work_dir}/output
#$ -e {work_dir}/output

# Name of the queue
#$ -q longP

# use OpenMPI parallel environment with 96 processes
#$ -pe openmpi 96

# Export the following env variables:
#$ -v HOME
#$ -v PATH
#$ -v PYTHONPATH
#$ -v LD_LIBRARY_PATH
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
export NINEMLP_SRC_PATH={ninemlp_src_path}
export NINEMLP_BUILD_MODE='lazy'
export NINEMLP_MPI=1

echo "==============Starting mpirun===============" 

cd {work_dir}/src
time mpirun python test/{script_name}.py --output {work_dir}/output_activity --time 100 --start 50 --mf_rate 1000

echo "==============Mpirun has ended===============" 

""".format(script_name=SCRIPT_NAME, work_dir=work_dir, path=PATH, pythonpath=PYTHONPATH, 
           ld_library_path=LD_LIBRARY_PATH, nineml_src_path=NINEMLP_SRC_PATH))

# Submit job
subprocess.call('qsub %s' % jobscript_path)
print "The output of this job can be viewed by:"
print os.path.join(work_dir, output)
            
