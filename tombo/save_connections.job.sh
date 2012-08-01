#!/bin/sh

# Parse the job script using this shell
#$ -S /bin/bash

# Send stdout and stderr to the same file.
#$ -j y

# Standard output and standard error files
#$ -o WORK_DIR/output
#$ -e WORK_DIR/output

# Name of the queue
#$ -q short

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

#INCLUDED_POPS="['purkinje', 'granule']"

# Set up the correct paths 
export PATH=/apps/DeschutterU/NEURON-7.2/x86_64/bin:/opt/mpi/gnu/openmpi-1.4.3/bin/:$PATH
export PYTHONPATH=WORK_DIR/src:/apps/DeschutterU/NEURON-7.2/lib64/python2.4/site-packages:/apps/DeschutterU/Python-Extensions/lib64/python2.4/site-packages
export LD_LIBRARY_PATH=/opt/mpi/gnu/openmpi-1.4.3/lib/
export NRNHOME=/apps/DeschutterU/NEURON-7.2
export NRNARC=x86_64

machines="$PE_HOSTFILE"
cat $machines

echo "==============Starting mpirun===============" 

cd WORK_DIR/Molecular_Layer
time mpirun nrniv -mpi -python main.py --init --save_connections WORK_DIR/NINEMLP/brep/build
#--include_pops $INCLUDE_POPS 
echo "==============Mpirun has ended===============" 

