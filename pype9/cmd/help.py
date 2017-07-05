"""
Prints help information associated with a PyPe9 command
"""
from argparse import ArgumentParser


def argparser():
    parser = ArgumentParser(prog='pype9 help', description=__doc__)
    parser.add_argument('cmd', default=None,
                        help="Name of the command to print help information")
    return parser


# List of available cmds
def all_cmds():
    return [c for c in dir(pype9.cmd) if not c.startswith('_')]


def get_parser(cmd):
    "Get the parser associated with a given cmd"
    return getattr(pype9.cmd, cmd).argparser()


def available_cmds_message():
    return (
        "usage: pype9 <cmd> <args>\n\n"
        "available commands:\n{}""".format(
            "\n".join('    {}\n        {}'.format(c, _get_description(c))
                      for c in all_cmds())))


def _get_description(cmd):
    return get_parser(cmd).description.strip().replace('\n', '\n        ')


def run(argv):
    if not argv:
        print available_cmds_message()
    else:
        args = argparser().parse_args(argv)
        get_parser(args.cmd).print_help()


import pype9.cmd  # @IgnorePep8

if __name__ == '__main__':
    import sys
    run(sys.argv[1:])
