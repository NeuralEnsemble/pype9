#!/usr/bin/env bash
# An example bash script performing the equivalent of the simple_hh.py script
# in the 'examples/api' directory using the 'pype9' CLI tool

echo "ARGS: $@"

if [ ! -z "$1" ]; then
	OUT_DIR="$1"
else
	OUT_DIR="$HOME/.pype9/examples/"	
fi

if [ ! -z "$2" ]; then
	PLOT_OPTIONS="--hide --save $2"
else
	PLOT_OPTIONS=''	
fi

V_FNAME="$OUT_DIR/simple_hh_example-v.neo.pkl"

mkdir -p $OUT_DIR

echo "Plot options: $PLOT_OPTIONS"

pype9 simulate \
	catalog://neuron/HodgkinHuxley#PyNNHodgkinHuxleyProperties \
	nest 500.0 0.001 \
	--init_value v 65 mV \
	--init_value m 0.0 unitless \
	--init_value h 1.0 unitless \
	--init_value n 0.0 unitless \
	--record v $V_FNAME
	
pype9 plot $V_FNAME $PLOT_OPTIONS
