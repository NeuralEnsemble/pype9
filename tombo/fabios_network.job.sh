#!/bin/sh

# Parse the job script using this shell
#$ -S /bin/bash

# Send stdout and stderr to the same file.
#$ -j y

# Standard output and standard error files
#$ -o WORK_DIR/output
#$ -e WORK_DIR/output

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

JOB_NAME=fabios_network

# Set up the correct paths 
export PATH=/apps/DeschutterU/NEURON-7.2/x86_64/bin:/opt/mpi/gnu/openmpi-1.4.3/bin/:/apps/python/272/bin:$PATH
export PYTHONPATH=WORK_DIR/src
export LD_LIBRARY_PATH=/opt/mpi/gnu/openmpi-1.4.3/lib/:/apps/python/272/lib
export NINEMLP_SRC_PATH=WORK_DIR/src
export NINEMLP_BUILD_MODE='lazy'
export NINEMLP_MPI=1

echo "==============Starting mpirun===============" 

cd WORK_DIR/src
time mpirun python test/fabios_network.py --output WORK_DIR/fabios_network.out --time 100 --start 50 --mf_rate 1000

echo "==============Mpirun has ended===============" 

