"""
Command that compares a 9ML model with an existing version in NEURON and/or
NEST
"""
import argparse

parser = argparse.ArgumentParser(__doc__)
parser.add_argument('nineml_model', type=str, help="The 9ML model to compare")
parser.add_argument('temp', type=int, help="dummy")
parser.add_argument('--nest', type=str,
                    help="The name of the nest model to compare against")
parser.add_argument('--neuron', type=str,
                    help="The name of the NEURON model to compare against")
args = parser.parse_args()
print args.nineml_model + ', ' + str(args.temp)
