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
parser.add_argument('--show', action='store_true',
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
    if seg.spiketrains:
        plt.subplot(num_subplots, 1, 1)
        spiketrains = seg.spiketrains
        spike_times = []
        ids = []
        for i, spiketrain in enumerate(spiketrains):
            spike_times.extend(spiketrain)
            ids.extend([i] * len(spiketrain))
        plt.sca(subplots[0])
        plt.scatter(spike_times, ids)
        plt.xlim((args.plot_start, args.simtime))
        plt.ylim((-1, len(spiketrains)))
        plt.xlabel('Times (ms)')
        plt.ylabel('Cell Indices')
        plt.title("PyPe9{} Spike Trains".format(
            ' ' + seg.name if seg.name else ''), fontsize=12)
    if seg.analogsignals:
        legend = []
        plt.sca(num_subplots)
        units = []
        for i, trace in enumerate(seg.analogsignals):
            plt.plot(trace.times, trace)
            units.append(trace.units)
            legend.append(trace.name if trace.name else str(i))
        plt.xlim((args.plot_start, args.simtime))
        plt.xlabel('Time (ms)')
        plt.ylabel('')
        plt.title("Pype9{} Analog Signals".format(
            ' ' + seg.name if seg.name else ''), fontsize=12)
