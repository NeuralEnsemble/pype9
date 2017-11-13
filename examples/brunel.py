from __future__ import division
from __future__ import print_function
from builtins import zip
import os.path
from itertools import groupby
from operator import itemgetter
from collections import defaultdict
import ninemlcatalog
import nest
import numpy as np
from nineml import units as un, Property
from nineml.user import Initial
import argparse
import logging
import matplotlib
from pyNN.utility import SimulationProgressBar
import sys
argv = sys.argv[1:]
from pype9.mpi import is_mpi_master  # @IgnorePep8
from pype9.utils.testing import ReferenceBrunel2000  # @IgnorePep8


pyNN_logger = logging.Logger('PyNN')

parser = argparse.ArgumentParser()
parser.add_argument('--case', type=str, default='AI',
                    help=("Which Brunel network parameterisation to run, "
                          "one of 'AI', 'SIFast', 'SISlow' or 'SR'"))
parser.add_argument('--order', type=int, default=10,
                    help="The scale of the network (full network order=1000)")
parser.add_argument('--simtime', type=float, default=100.0,
                    help="The length of the simulation in ms")
parser.add_argument('--timestep', type=float, default=0.001,
                    help="Simulation timestep")
parser.add_argument('--num_record', type=int, default=50,
                    help=("The number of cells in each population to record."
                          "All cells will be recorded if num_record > "
                          "len(population)."))
parser.add_argument('--num_record_v', type=int, default=0,
                    help=("The number of cells in each population to record "
                          "the voltage from"))
parser.add_argument('--simulators', type=str, nargs='+',
                    default=['neuron', 'nest'],
                    help="Which simulators to simulate the 9ML network")
parser.add_argument('--plot_start', type=float, default=0.0,
                    help=("The time to start plotting from"))
parser.add_argument('--build_mode', type=str, default='lazy',
                    help=("The build mode with which to construct the network."
                          " 'lazy' will only regenerate and compile the "
                          "source files if the network has changed, whereas "
                          "'force' will always rebuild the network"))
parser.add_argument('--plot_input', action='store_true',
                    help=("Plots the external Poisson input in addition to the"
                          "excitatory and inhibitory cells"))
parser.add_argument('--seed', type=int, default=None,
                    help="Random seed passed to the simulators")
parser.add_argument('--reference', action='store_true', default=False,
                    help="Plot a reference NEST implementation alongside")
parser.add_argument('--save_fig', type=str, default=None,
                    help=("Location to save the generated figures"))
parser.add_argument('--figsize', nargs=2, type=float, default=(10, 15),
                    help="The size of the figures")
parser.add_argument('--progress_bar', action='store_true', default=False,
                    help=("Show a progress bar for the simulation time (Can "
                          "cause difficulties in some displays)"))
parser.add_argument('--input_rate', type=float, default=None,
                    help="Override the input rate for debugging purposes")
parser.add_argument('--no_init_v', action='store_true',
                    help="Don't initialise the membrane voltage")
args = parser.parse_args(argv)

if not args.simulators and not args.reference:
    raise Exception("No simulations requested "
                    "(see --simulators and --reference options)")

if args.save_fig is not None:
    matplotlib.use('pdf')
    save_path = os.path.abspath(args.save_fig)
    if not os.path.exists(save_path) and is_mpi_master():
        os.mkdir(save_path)
else:
    save_path = None
# Needs to be imported after the args.save_fig argument is parsed to
# allow the backend to be set
from matplotlib import pyplot as plt  # @IgnorePep8

simulations = {}
pype9_network_classes = {}
if 'neuron' in args.simulators:
    from pype9.simulate.neuron import (
        Simulation as SimulationNEURON, Network as NetworkNEURON) # @IgnorePep8
    simulations['neuron'] = SimulationNEURON
    pype9_network_classes['neuron'] = NetworkNEURON
if 'nest' in args.simulators or args.reference:
    from pype9.simulate.nest import (
        Simulation as SimulationNEST, Network as NetworkNEST) # @IgnorePep8
    simulations['nest'] = SimulationNEST
    pype9_network_classes['nest'] = NetworkNEST

# Get the list of populations to record and plot from
pops_to_plot = ['Exc', 'Inh']
if args.plot_input:
    pops_to_plot.append('Ext')

# Set the random seed
np.random.seed(args.seed)
seeds = np.asarray(
    np.floor(np.random.random(len(args.simulators)) * 1e5), dtype=int)

# Load the Brunel model corresponding to the 'case' argument from the
# nineml catalog and scale the model according to the 'order' argument
model = ninemlcatalog.load('network/Brunel2000/' + args.case).as_network(
    'Brunel_{}'.format(args.case))
scale = args.order / model.population('Inh').size
if scale != 1.0:
    for pop in model.populations:
        pop.size = int(np.ceil(pop.size * scale))
    for proj in (model.projection('Excitation'),
                 model.projection('Inhibition')):
        props = proj.connectivity.rule_properties
        number = props.property('number')
        props.set(Property(
            number.name,
            int(np.ceil(float(number.value * scale))) * un.unitless))

if args.input_rate is not None:
    props = model.population('Ext').cell
    props.set(Property(
        'rate', args.input_rate * un.Hz))

if args.no_init_v:
    for pop_name in ('Exc', 'Inh'):
        props = model.population(pop_name).cell
        props.set(Initial('v', 0.0 * un.V))

# Create dictionaries to hold the simulation results
spikes = defaultdict(dict)
if args.num_record_v:
    vs = defaultdict(dict)

# Create the network for each simulator and set recorders
networks = {}
for simulator, seed in zip(args.simulators, seeds):
    # Reset the simulator
    with simulations[simulator](min_delay=ReferenceBrunel2000.min_delay,
                                max_delay=ReferenceBrunel2000.max_delay,
                                dt=args.timestep * un.ms, seed=seed) as sim:
        # Construct the network
        print("Constructing the network in {}".format(simulator.upper()))
        networks[simulator] = pype9_network_classes[simulator](
            model, build_mode=args.build_mode)
        print("Finished constructing the network in {}".format(
            simulator.upper()))
        # Record spikes and voltages
        for pop in networks[simulator].component_arrays:
            pop[:args.num_record].record('spikes')
            if args.num_record_v and pop.name != 'Ext':
                pop[:args.num_record_v].record('v__cell')

        # Create the reference simulation if required
        if simulator == 'nest' and args.reference:
            print("Constructing the reference NEST implementation")
            if args.no_init_v:
                init_v = {'Exc': 0.0, 'Inh': 0.0}
            else:
                init_v = None
            ref = ReferenceBrunel2000(
                args.case, args.order, override_input=args.input_rate,
                init_v=init_v)
            ref.record(num_record=args.num_record,
                       num_record_v=args.num_record_v,
                       to_plot=pops_to_plot, timestep=args.timestep)

        # Run the simulation(s)
        print("Running the simulation in {}".format(simulator.upper()))
        if args.progress_bar:
            kwargs = {'callbacks': [
                SimulationProgressBar(args.simtime / 77, args.simtime)]}
        else:
            kwargs = {}
        sim.run(args.simtime * un.ms)

if is_mpi_master():
    # Plot the results
    print("Plotting the results")
    num_subplots = len(args.simulators) + int(args.reference)
    for pop_name in pops_to_plot:
        spike_fig, spike_subplots = plt.subplots(num_subplots, 1,
                                                 figsize=args.figsize)
        spike_fig.suptitle("{} - {} Spike Times".format(args.case,
                                                        pop_name),
                           fontsize=14)
        if args.num_record_v:
            v_fig, v_subplots = plt.subplots(num_subplots, 1,
                                             figsize=args.figsize)
            v_fig.suptitle("{} - {} Membrane Voltage".format(args.case,
                                                             pop_name),
                           fontsize=14)
        for subplot_index, simulator in enumerate(args.simulators):
            # Get the recordings for the population
            pop = networks[simulator].component_array(pop_name)
            block = pop.get_data()
            segment = block.segments[0]
            # Plot the spike trains
            spiketrains = segment.spiketrains
            spike_times = []
            ids = []
            for i, spiketrain in enumerate(spiketrains):
                spike_times.extend(spiketrain)
                ids.extend([i] * len(spiketrain))
            plt.sca(spike_subplots[subplot_index]
                    if num_subplots > 1 else spike_subplots)
            plt.scatter(spike_times, ids)
            plt.xlim((args.plot_start, args.simtime))
            plt.ylim((-1, len(spiketrains)))
            plt.xlabel('Times (ms)')
            plt.ylabel('Cell Indices')
            plt.title("PyPe9 {}".format(simulator.upper()), fontsize=12)
            if args.num_record_v and pop_name != 'Ext':
                traces = segment.analogsignalarrays
                legend = []
                plt.sca(v_subplots[subplot_index]
                        if num_subplots > 1 else v_subplots)
                for trace in traces:
                    plt.plot(trace.times, trace)
                plt.xlim((args.plot_start, args.simtime))
                plt.ylim([0.0, 20.0])
                plt.xlabel('Time (ms)')
                plt.ylabel('Membrane Voltage (mV)')
                plt.title("Pype9 {}".format(simulator.upper()),
                          fontsize=12)
        if args.reference:
            events = nest.GetStatus(ref.recorders[pop_name]['spikes'],
                                    "events")[0]
            spike_times = np.asarray(events['times'])
            senders = np.asarray(events['senders'])
            inds = np.asarray(spike_times > args.plot_start, dtype=bool)
            spike_times = spike_times[inds]
            senders = senders[inds]
            if len(senders):
                senders -= senders.min()
                max_y = senders.max() + 1
            else:
                max_y = args.num_record
            plt.sca(spike_subplots[-1]
                    if num_subplots > 1 else spike_subplots)
            plt.scatter(spike_times, senders)
            plt.xlim((args.plot_start, args.simtime))
            plt.ylim((-1, max_y))
            plt.xlabel('Times (ms)')
            plt.ylabel('Cell Indices')
            plt.title("Ref. NEST", fontsize=12)
            if args.num_record_v and pop_name != 'Ext':
                events, interval = nest.GetStatus(
                    ref.recorders[pop_name]['V_m'],
                    ["events", 'interval'])[0]
                sorted_vs = sorted(zip(events['senders'], events['times'],
                                       events['V_m']), key=itemgetter(0))
                legend = []
                plt.sca(v_subplots[-1] if num_subplots > 1 else v_subplots)
                for sender, group in groupby(sorted_vs, key=itemgetter(0)):
                    _, t, v = list(zip(*group))
                    t = np.asarray(t)
                    v = np.asarray(v)
                    inds = t > args.plot_start
                    plt.plot(t[inds], v[inds])
                plt.xlim((args.plot_start, args.simtime))
                plt.ylim([0.0, 20.0])
                plt.xlabel('Time (ms)')
                plt.ylabel('Membrane Voltage (mV)')
                plt.title("Ref. NEST", fontsize=12)
        if save_path is not None:
            spike_fig.savefig(os.path.join(save_path,
                                           '{}_spikes'.format(pop_name)))
            if args.num_record_v:
                v_fig.savefig(os.path.join(save_path,
                                           '{}_v'.format(pop_name)))
    if save_path is None:
        plt.show()
    print("done")
