"""
Converts a 9ML file from one supported format to another
"""
from argparse import ArgumentParser
from ._utils import nineml_document, logger

parser = ArgumentParser(prog='pype9 convert',
                        description=__doc__)
parser.add_argument('in_file', type=nineml_document,
                    help="9ML file to be converted")
parser.add_argument('out_file', help="Converted filename")
parser.add_argument('--nineml_version', type=str, default=None,
                    help="The version of nineml to output")


def run(argv):
    args = parser.parse_args(argv)

    doc = args.in_file.clone()
    kwargs = {}
    if args.nineml_version is not None:
        kwargs['version'] = args.nineml_version
    doc.write(args.out_file, **kwargs)
    logger.info("Converted '{}' to '{}'".format(args.in_file, args.out_file))
