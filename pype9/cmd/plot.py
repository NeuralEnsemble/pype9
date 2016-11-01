"""
Convenient script for plotting the output of PyPe9 simulations (actually not
9ML specific as the signals are stored in Neo format)
"""
from argparse import ArgumentParser

parser = ArgumentParser(description=__doc__)
parser.add_argument('filename', help="9ML file to be converted")
parser.add_argument('--name', type=str, action='append', default=None,
                    help="Name of the signal within the file to plot")
parser.add_argument('--save', type=str, default=None,
                    help="Location to save the figure to")
parser.add_argument('--hide', action='store_true',
                    help="Whether to show the plot or not")


def run(argv):
    import neo
    import matplotlib.pyplot as plt
    from pype9.exceptions import Pype9UsageError

    args = parser.parse_args(argv)

    data = neo.PickleIO(args.filename).read()
    if len(data.segments) > 1:
        raise Pype9UsageError(
            "Expected only a single recording segment in file '{}', found {}."
            .format(args.filename, len(data.segments)))

    seg = data.segments[0]
    num_subplots = bool(seg.analogsignals) + bool(seg.spiketrains)
    fig, subplots = plt.subplots(num_subplots, 1)
    fig.title('PyPe9 simulation output')
    plt_name = ' ' + seg.name if seg.name else ''
    if seg.spiketrains:
        plt.subplot(num_subplots, 1, 1)
        spike_times = []
        ids = []
        for i, spiketrain in enumerate(seg.spiketrains):
            if args.name is None or spiketrain.name in args.name:
                spike_times.extend(spiketrain)
                ids.extend([i] * len(spiketrain))
        plt.sca(subplots[0])
        plt.scatter(spike_times, ids)
        plt.xlim((seg.spiketrains[0].t_start, seg.spiketrains[0].t_stop))
        plt.ylim((-1, len(seg.spiketrains)))
        plt.xlabel('Times (ms)')
        plt.ylabel('Cell Indices')
        plt.title("PyPe9{} Spike Trains".format(plt_name), fontsize=12)
    if seg.analogsignals:
        legend = []
        plt.sca(num_subplots)
        units = set(s.units for s in seg.analogsignals)
        for i, signal in enumerate(seg.analogsignals):
            if args.name is None or spiketrain.name in args.name:
                plt.plot(signal.times, signal)
                un_str = (signal.units.dimensionality.string
                          if len(units) > 1 else '')
                legend.append(signal.name + un_str if signal.name else str(i))
        plt.xlim((seg.analogsignals[0].t_start, seg.analogsignals[0].t_stop))
        plt.xlabel('Time (ms)')
        un_str = (' ({})'.format(next(iter(units)).dimensionality.string)
                  if len(units) == 1 else '')
        plt.ylabel('Analog signals{}'.format(un_str))
        plt.title("Pype9{} Analog Signals".format(plt_name), fontsize=12)
    if args.save is not None:
        fig.savefig(args.save)
        print "Saved{} figure to '{}'".format(plt_name, args.save)
    if not args.hide:
        plt.show()
