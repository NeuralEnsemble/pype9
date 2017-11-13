#!/usr/bin/env bash
# An example bash script performing the equivalent of the simple_hh.py script
# in the 'examples/api' directory using the 'pype9' CLI tool

if [ -z "$1" ]; then
	PLOT_OPTIONS="--hide --save $1"
else
	PLOT_OPTIONS=''	
fi

V_FNAME=~/.pype9/examples/simple_hh_example-v.neo.pkl

pype9 simulate \
	ninemlcatalog://neuron/HodgkinHuxley#PyNNHodgkinHuxleyProperties \
	nest 500.0 0.001 \
	--init_value v 65 mV \
	--init_value m 0.0 unitless \
	--init_value h 1.0 unitless \
	--init_value n 0.0 unitless \
	--record v $V_FNAME
	
pype9 plot $V_FNAME $PLOT_OPTIONS
