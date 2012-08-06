#!/bin/sh

####################################################################################################
# 
# This script prepares the environment for the Sun Grid Engine batch script to run in by making a
# snapshot of the code base at the start of the run and queing the related batch script 
# 'performance.job.sh'.
#
# Author: Tom Close (tclose@oist.jp)
# Created: 8/6/2012
# 
####################################################################################################

JOB_NAME=fabios_network
TIMESTAMP=`date +%a%d%b%Y_%H%M`

# Create work directory to house this snapshot of the code.
WORK_DIR=$HOME/Work/$JOB_NAME.${TIMESTAMP}

# Iterate over potential names for work directory until one doesn't exist
COUNT=2
while [ -d $WORK_DIR ]; do 
  WORK_DIR=$WORK_DIR.$COUNT
  COUNT=$(( $COUNT + 1 ))
done
echo "Creating $WORK_DIR"
mkdir -p $WORK_DIR

# Set up path variables to run build script
export PATH=/apps/DeschutterU/NEURON-7.2/x86_64/bin:/opt/mpi/gnu/openmpi-1.4.3/bin:/apps/python/272/bin:$PATH
export PYTHONPATH=$WORK_DIR/src
export LD_LIBRARY_PATH=/opt/mpi/gnu/openmpi-1.4.3/lib
export NINEMLP_SRC_PATH=$WORK_DIR/src
export NINEMLP_BUILD_MODE='compile_only'
export NINEMLP_MPI=1

# Copying files across to work directory
PROJECT_DIR="$( cd "$( dirname "$0" )/../" && pwd )" # Get the project directory, by determining the folder one up from where the script resides. Relies on this script being one level down from the project root.
echo cp -PR $PROJECT_DIR/src $WORK_DIR/src
echo cp -PR $PROJECT_DIR/NINEMLP $WORK_DIR/NINEMLP
cp -PR $PROJECT_DIR/src $WORK_DIR/src
cp -PR $PROJECT_DIR/NINEMLP $WORK_DIR/NINEMLP

echo ''
echo 'Compiling NINEML+ code'
echo ''
echo python $WORK_DIR/src/test/fabios_network.py
echo ''
python $WORK_DIR/src/test/fabios_network.py --build compile_only

# Replace special tags in the job script with the created timestamp
sed s#WORK_DIR#$WORK_DIR#g $PROJECT_DIR/tombo/$JOB_NAME.job.sh | sed s#TIMESTAMP#$TIMESTAMP#g > $WORK_DIR/$JOB_NAME.job.sh 

# Add the job script to the que
qsub $WORK_DIR/$JOB_NAME.job.sh 

echo "The output of this job can be viewed by:"
echo less $WORK_DIR/output
