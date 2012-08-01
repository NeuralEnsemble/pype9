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
# $ -pe openmpi 4

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

JOB_NAME=comparison

# Set up the correct paths 
export PATH=/apps/DeschutterU/NEURON-7.2/x86_64/bin:/opt/mpi/gnu/openmpi-1.4.3/bin/:$PATH
export PYTHONPATH=WORK_DIR/src:/apps/DeschutterU/NEURON-7.2/lib64/python2.4/site-packages:/apps/DeschutterU/Python-Extensions/lib64/python2.4/site-packages
export LD_LIBRARY_PATH=/opt/mpi/gnu/openmpi-1.4.3/lib/
export NINEMLP_SRC_PATH=WORK_DIR/src
export NINEMLP_BUILD_MODE='lazy'
export NINEMLP_MPI=1
export NRNHOME=/apps/DeschutterU/NEURON-7.2
export NRNARC=x86_64

machines="$PE_HOSTFILE"
cat $machines

echo "==============Starting mpirun===============" 

cd WORK_DIR/Molecular_Layer
time mpirun nrniv -mpi -python main.py --include_pops "['purkinje', 'granule']" --init 

cd WORK_DIR/src
time mpirun python test/comparison.py --method ninemlp

echo "==============Mpirun has ended===============" 

#mkdir -p $HOME/Data/$JOB_NAME/TIMESTAMP.$JOB_ID
#cp -v *.dat $HOME/Data/$JOB_NAME/TIMESTAMP.$JOB_ID
#cp -v *.bin $HOME/Data/$JOB_NAME/TIMESTAMP.$JOB_ID
#cp -Rv dat $HOME/Data/$JOB_NAME/TIMESTAMP.$JOB_ID

