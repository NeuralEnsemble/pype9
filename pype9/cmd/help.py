"""
Prints help information associated with a PyPe9 command
"""
from argparse import ArgumentParser

parser = ArgumentParser(description=__doc__)
parser.add_argument('cmd', default=None,
                    help="Name of the command to print help information")


# List of available cmds
def all_cmds():
    return dir(pype9.cmd)


def get_parser(cmd):
    "Get the parser associated with a given cmd"
    return getattr(pype9.cmd, cmd).parser


def available_cmds_message():
    return ("\nAvailable PyPe9 commands:\n\n{}".format(
            "\n".join('  {} - {}'.format(c, get_parser(c).description)
                      for c in all_cmds())))


def run(argv):
    if not argv:
        print available_cmds_message()
    else:
        args = parser.parse_args(argv)
        get_parser(args.cmd).print_help()


import pype9.cmd  # @IgnorePep8
