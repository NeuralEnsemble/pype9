"""
Converts a 9ML file from one supported format to another
"""
import nineml
from argparse import ArgumentParser

parser = ArgumentParser(__doc__)
parser.add_argument('in_file', help="9ML file to be converted")
parser.add_argument('out_file', help="Converted filename")
parser.add_argument('--nineml_version', type=str, default=None,
                    help="The version of nineml to output")
args = parser.parse_args()

if __name__ == '__main__':
    doc = nineml.read(args.in_file)
    kwargs = {}
    if args.nineml_version is not None:
        kwargs['version'] = args.nineml_version
    doc.write(args.out_file, **kwargs)
