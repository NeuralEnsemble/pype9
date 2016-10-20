"""
Converts a 9ML file from one supported format to another
"""
from argparse import ArgumentParser

parser = ArgumentParser(description=__doc__)
parser.add_argument('in_file', help="9ML file to be converted")
parser.add_argument('out_file', help="Converted filename")
parser.add_argument('--nineml_version', type=str, default=None,
                    help="The version of nineml to output")


def run():
    import nineml
    args = parser.parse_args()
    doc = nineml.read(args.in_file)
    doc = doc.clone()
    kwargs = {}
    if args.nineml_version is not None:
        kwargs['version'] = args.nineml_version
    doc.write(args.out_file, **kwargs)
