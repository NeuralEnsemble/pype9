import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
import quantities as pq
import logging
from itertools import izip

logger = logging.getLogger('PyPe9')


def plot(seg, dims=(10, 8), resolution=300, save=None, show=True,
         regime_alpha=0.05, regime_linestyle=':'):
    num_subplots = bool(seg.analogsignals) + bool(seg.spiketrains)
    fig, axes = plt.subplots(num_subplots, 1)
    fig.suptitle('PyPe9 Simulation Output')
    fig.set_figwidth(dims[0])
    fig.set_figheight(dims[1])
    # Set the dimension of the figure
    plt_name = seg.name + ' ' if seg.name else ''
    if seg.spiketrains:
        spike_times = []
        ids = []
        for i, spiketrain in enumerate(seg.spiketrains):
            spike_times.extend(spiketrain)
            ids.extend([i] * len(spiketrain))
        plt.sca(axes[0] if num_subplots > 1 else axes)
        plt.scatter(spike_times, ids)
        plt.xlim((seg.spiketrains[0].t_start, seg.spiketrains[0].t_stop))
        plt.ylim((-1, len(seg.spiketrains)))
        plt.xlabel('Times (ms)')
        plt.ylabel('Cell Indices')
        plt.title("{}Spike Trains".format(plt_name), fontsize=12)
    if seg.analogsignals:
        legend = []
        plt.sca(axes[-1] if num_subplots > 1 else axes)
        units = set(s.units.dimensionality.string for s in seg.analogsignals)
        # Plot signals
        for i, signal in enumerate(seg.analogsignals):
            un_str = (signal.units.dimensionality.string
                      if len(units) > 1 else '')
            label = signal.name + un_str if signal.name else str(i)
            line, = plt.plot(signal.times, signal, label=label)
            legend.append(line)
        # Plot regime epochs (if present)
        for epocharray in seg.epocharrays:
            # Map labels to colours
            labels = set(epocharray.labels)
            # Remove the mode epoch
            mode = mode_epoch(epocharray)
            labels.remove(mode)
            label_colours = dict((l, plt.gca()._get_lines.get_next_color())
                                 for l in labels)
            label_colours[mode] = None
            for label, start, duration in izip(epocharray.labels,
                                               epocharray.times,
                                               epocharray.durations):
                if label_colours[label] is not None:
                    end = start + duration
                    plt.axvspan(start, end, facecolor=label_colours[label],
                                alpha=regime_alpha)
                    plt.axvline(start, linestyle=regime_linestyle,
                                color='gray', linewidth=0.5)
                    plt.axvline(end, linestyle=regime_linestyle, color='gray',
                                linewidth=0.5)
            for label, colour in label_colours.iteritems():
                if colour is None:
                    colour = 'white'
                legend.append(
                    mpatches.Patch(facecolor=colour, edgecolor='grey',
                                   label=label + ' regime', linewidth=0.5,
                                   linestyle=regime_linestyle))
        plt.xlim((seg.analogsignals[0].t_start, seg.analogsignals[0].t_stop))
        plt.xlabel('Time (ms)')
        un_str = (' ({})'.format(next(iter(units)))
                  if len(units) == 1 else '')
        plt.ylabel('Analog signals{}'.format(un_str))
        plt.title("{}Analog Signals".format(plt_name), fontsize=12)
        plt.legend(handles=legend)
    if save is not None:
        fig.savefig(save, dpi=resolution)
        logger.info("Saved{} figure to '{}'".format(plt_name, save))
    if show:
        plt.show()


def mode_epoch(epocharray):
    total_durations = defaultdict(lambda: 0.0 * pq.s)
    for label, duration in izip(epocharray.labels,
                                epocharray.durations):
        total_durations[label] += duration
    max_duration = 0.0
    max_label = None
    for label, total_duration in total_durations.iteritems():
        if total_duration > max_duration:
            max_label = label
    return max_label
