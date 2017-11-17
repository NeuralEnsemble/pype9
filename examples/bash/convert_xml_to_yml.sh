#!/usr/bin/env bash
# An example bash script converting 9ML serialized to XML to YAML

set -e  # Stop execution in case of errors

if [ -z "$1" ]; then
	echo "Usage: convert_xml_to_yml.sh XML_FILE [OUT_DIR]"
	exit 
fi

if [ ! -z "$2" ]; then
	OUT_DIR=$2
else
	OUT_DIR=$(pwd)
fi

INPUT_PATH=$1
FNAME=$(basename $INPUT_PATH)
FNAME_BASE=${FNAME%.xml}

if [ $FNAME_BASE == $FNAME ]; then
	echo "Input XML file $INPUT_PATH needs to have '.xml' extension"
	exit
fi 

echo "pype9 convert $INPUT_PATH $OUT_DIR/$FNAME_BASE.yml"
pype9 convert --nineml_version 2 $INPUT_PATH $OUT_DIR/$FNAME_BASE.yml
