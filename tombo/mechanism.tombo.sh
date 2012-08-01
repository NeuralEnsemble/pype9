#!/bin/bash 

export PATH=/apps/DeschutterU/NEURON-7.2/x86_64/bin:/opt/mpi/gnu/openmpi-1.4.3/bin/:$PATH
export PYTHONPATH=/apps/DeschutterU/NEURON-7.2/lib64/python2.4/site-packages:/apps/DeschutterU/Python-Extensions/lib64/python2.4/site-packages:/home/t/tclose/cerebellar/src
export LD_LIBRARY_PATH=/opt/mpi/gnu/openmpi-1.4.3/lib/
export NRNHOME=/apps/DeschutterU/NEURON-7.2
export NINEMLP_MPI=1

python ../src/test/batch/test_granule_mechs.py
