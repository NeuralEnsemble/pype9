"""
Simple tool for plotting the output of PyPe9 simulations using Matplotlib_.
Since Pype9 output is stored in Neo_ format, it can be used to plot generic
Neo_ files but it also includes handling of Pype9-specific annotations, such as
regime transitions.
"""
from argparse import ArgumentParser
from ._utils import existing_file, logger  # @UnusedImport


def argparser():
    parser = ArgumentParser(prog='pype9 plot',
                            description=__doc__)
    parser.add_argument('filename', type=existing_file,
                        help="Neo file outputted from a PyPe9 simulation")
    parser.add_argument('--save', type=str, default=None,
                        help="Location to save the figure to")
    parser.add_argument('--dims', type=int, nargs=2, default=(10, 8),
                        metavar=('WIDTH', 'HEIGHT'),
                        help="Dimensions of the plot")
    parser.add_argument('--hide', action='store_true',
                        help="Whether to show the plot or not")
    parser.add_argument('--resolution', type=float, default=300.0,
                        help="Resolution of the figure when it is saved")
    return parser


def run(argv):
    import neo
    from pype9.exceptions import Pype9UsageError
    from pype9.plot import plot

    args = argparser().parse_args(argv)

    segments = neo.PickleIO(args.filename).read()
    if len(segments) > 1:
        raise Pype9UsageError(
            "Expected only a single recording segment in file '{}', found {}."
            .format(args.filename, len(segments)))

    seg = segments[0]
    plot(seg, dims=args.dims, show=not args.hide, resolution=args.resolution,
         save=args.save)
