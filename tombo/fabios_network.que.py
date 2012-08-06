#!/usr/bin/env python

####################################################################################################
# This script prepares the environment for the Sun Grid Engine batch script to run in by making a
# snapshot of the code base at the start of the run, generating a jobscript and sending it to the job que
#
# Author: Tom Close (tclose@oist.jp)
# Created: 6/8/2012
# 
####################################################################################################

import sys

if float(sys.version[0:3]) < 2.7:
    raise Exception("This script requires python version 2.7 or greater (try adding '/apps/python/272/bin' to your PATH variable if running on tombo)")

import os.path
import time
import shutil
import subprocess
import argparse

parser = argparse.ArgumentParser(description='A script to ')
parser.add_argument('--simulator', type=str, default='neuron',
                                           help="simulator for NINEML+ (either 'neuron' or 'nest')")
parser.add_argument('--mf_rate', type=float, default=1, help='Mean firing rate of the Mossy Fibres')
parser.add_argument('--time', type=float, default=2000.0, help='The run time of the simulation (ms)')
parser.add_argument('--start_input', type=float, default=1000, help='The start time of the mossy fiber stimulation')
parser.add_argument('--min_delay', type=float, default=0.0005, help='The minimum synaptic delay in the network')
parser.add_argument('--timestep', type=float, default=0.00005, help='The timestep used for the simulation')
parser.add_argument('--stim_seed', default=None, help='The seed passed to the stimulated spikes')
parser.add_argument('--num_processes', type=int, default=96, help='The the number of processes to use for the simulation')
args = parser.parse_args()

np = args.num_processes

if not args.stim_seed:
    stim_seed = long(time.time() * 256)
else:
    stim_seed = int(args.stim_seed)
    
#Name of the script to run
SCRIPT_NAME = 'fabios_network'

# Automatically generate paths
time_str = time.strftime('%Y-%m-%d-%A_%H-%M-%S', time.localtime()) # Unique time for distinguishing runs
work_dir = os.path.join(os.environ['HOME'], 'Work', SCRIPT_NAME + "." + time_str + ".1") # Working directory path
code_dir = os.path.abspath(os.path.join(os.path.basename(__file__), '..')) # Root directory of the project code

#Ensure that working directory is unique
created_directory=False
count = 1
while not created_directory:
    try:
        os.makedirs(work_dir) 
        created_directory=True
    except IOError as e:
        count += 1
        if count > 1000:
            print "Something has gone wrong, can't create directory '%s', maybe check permissions" % work_dir
            raise e
        work_dir[-1] = str(count)

# Copy snapshot of code directory and network description to working directory
DIRS_TO_COPY = ['src', 'xml']
for directory in DIRS_TO_COPY:
    shutil.copytree(os.path.join(code_dir,directory), os.path.join(work_dir,directory), symlinks=True)

# Set path variables
PATH ='/apps/python/272/bin:/apps/DeschutterU/NEURON-7.2/x86_64/bin:/opt/mpi/gnu/openmpi-1.4.3/bin'
PYTHONPATH = os.path.join(work_dir, 'src')
LD_LIBRARY_PATH = '/opt/mpi/gnu/openmpi-1.4.3/lib'
NINEMLP_SRC_PATH = os.path.join(work_dir, 'src')

#Compile network
os.environ['PATH'] = PATH + os.pathsep + os.environ['PATH']
sys.path.append(PYTHONPATH)
os.environ['LD_LIBRARY_PATH '] = LD_LIBRARY_PATH 
os.environ['NINEMLP_SRC_PATH'] = NINEMLP_SRC_PATH
os.environ['NINEMLP_BUILD_MODE'] = 'compile_only'
os.environ['NINEMLP_MPI'] = '1'

print "Compiling required objects"
try:
    execfile(os.path.join(work_dir,'src', 'test', SCRIPT_NAME + '.py'))
except SystemExit:
    pass

#Create jobscript
jobscript_path = os.path.join(work_dir, SCRIPT_NAME + '.job.sh')
f = open(jobscript_path, 'w')
f.write("""#!/usr/bin/env sh

# Parse the job script using this shell
#$ -S /bin/bash

# Send stdout and stderr to the same file.
#$ -j y

# Standard output and standard error files
#$ -o {work_dir}/output
#$ -e {work_dir}/output

# Name of the queue
#$ -q longP

# use OpenMPI parallel environment with {np} processes
#$ -pe openmpi {np}

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
time mpirun python test/{script_name}.py --output {work_dir}/output_activity --time {time} --start_input {start_input} --mf_rate {mf_rate} --min_delay {min_delay} --simulator {simulator} --timestep {timestep} --stim_seed {stim_seed}

echo "==============Mpirun has ended===============" 

""".format(script_name=SCRIPT_NAME, work_dir=work_dir, path=PATH, pythonpath=PYTHONPATH, 
  ld_library_path=LD_LIBRARY_PATH, ninemlp_src_path=NINEMLP_SRC_PATH, mf_rate=args.mf_rate, start_input=args.start_input, time=args.time, min_delay=args.min_delay, simulator=args.simulator, timestep=args.timestep, stim_seed=stim_seed, np=np))
f.close()

# Submit job
print "Submitting job %s" % jobscript_path
subprocess.call('qsub %s' % jobscript_path, shell=True)
print "The output of this job can be viewed by:"
print "less " + os.path.join(work_dir, 'output')
            
