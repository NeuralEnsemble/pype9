import matplotlib.pyplot as plt
import logging

logger = logging.getLogger('PyPe9')


def plot(seg, dims=(10, 8), resolution=300, save=None, show=True):
    num_subplots = bool(seg.analogsignals) + bool(seg.spiketrains)
    fig, axes = plt.subplots(num_subplots, 1)
    fig.suptitle('PyPe9 Simulation Output')
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
        for i, signal in enumerate(seg.analogsignals):
            plt.plot(signal.times, signal)
            un_str = (signal.units.dimensionality.string
                      if len(units) > 1 else '')
            legend.append(signal.name + un_str if signal.name else str(i))
        plt.xlim((seg.analogsignals[0].t_start, seg.analogsignals[0].t_stop))
        plt.xlabel('Time (ms)')
        un_str = (' ({})'.format(next(iter(units)))
                  if len(units) == 1 else '')
        plt.ylabel('Analog signals{}'.format(un_str))
        plt.title("{}Analog Signals".format(plt_name), fontsize=12)
        plt.legend(legend)
    fig.set_figwidth(dims[0])
    fig.set_figheight(dims[1])
    if save is not None:
        fig.savefig(save, dpi=resolution)
        logger.info("Saved{} figure to '{}'".format(plt_name, save))
    if show:
        plt.show()
