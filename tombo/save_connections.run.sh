#!/bin/sh

####################################################################################################
# 
# This script prepares the environment for the Sun Grid Engine batch script to run in by making a
# snapshot of the code base at the start of the run and queing the related batch script 
# 'save_connections.job.sh'.
#
# Author: Tom Close (tclose@oist.jp)
# Created: 8/6/2012
# 
####################################################################################################

JOB_NAME=save_connections
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
export PATH=/apps/DeschutterU/NEURON-7.2/x86_64/bin:/opt/mpi/gnu/openmpi-1.4.3/bin/:$PATH
export PYTHONPATH=$WORK_DIR/src:/apps/DeschutterU/NEURON-7.2/lib64/python2.4/site-packages:/apps/DeschutterU/Python-Extensions/lib64/python2.4/site-packages
export LD_LIBRARY_PATH=/opt/mpi/gnu/openmpi-1.4.3/lib/
export PARAMDIR=$WORK_DIR/Molecular_Layer/tests/set5


# Copying files across to work directory
PROJECT_DIR="$( cd "$( dirname "$0" )/../" && pwd )" # Get the project directory, by determining the folder one up from where the script resides. Relies on this script being one level down from the project root.
echo cp -PR $PROJECT_DIR/Molecular_Layer $WORK_DIR/hoc
echo cp -PR $PROJECT_DIR/NINEMLP $WORK_DIR/NINEMLP
cp -PR $PROJECT_DIR/NINEMLP $WORK_DIR/NINEMLP
cp -PR $PROJECT_DIR/Molecular_Layer $WORK_DIR/Molecular_Layer


echo ''
echo 'Compiling HOC code'
echo ''
cd $WORK_DIR/Molecular_Layer
echo nrniv -mpi -python main.py --build
echo ''
NRNIV=`which nrniv`
$NRNIV -mpi -python main.py --build

# Replace special tags in the job script with the created timestamp
sed s#WORK_DIR#$WORK_DIR#g $PROJECT_DIR/tombo/$JOB_NAME.job.sh | sed s#TIMESTAMP#$TIMESTAMP#g > $WORK_DIR/$JOB_NAME.job.sh 

# Add the job script to the que
qsub $WORK_DIR/$JOB_NAME.job.sh 

echo "The output of this job can be viewed by:"
echo less $WORK_DIR/output
