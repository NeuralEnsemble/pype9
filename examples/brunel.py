from __future__ import division
import sys
import ninemlcatalog
import numpy
from nineml import units as un, Property
argv = sys.argv[1:]  # Save argv before it is clobbered by the NEST init.
import pyNN.neuron  # @IgnorePep8
import pyNN.nest  # @IgnorePep8
import pype9.neuron.cells  # @IgnorePep8
import pype9.nest.cells  # @IgnorePep8
import argparse  # @IgnorePep8
import logging  # @IgnorePep8
try:
    from matplotlib import pyplot as plt
except ImportError:
    pass

pyNN_logger = logging.Logger('PyNN')

parser = argparse.ArgumentParser()
parser.add_argument('--cases', type=str, nargs='+',
                    default=['AI', 'SIFast', 'SISlow', 'SR'],
                    help="Which Brunel version(s) to run")
parser.add_argument('--order', type=int, default=10,
                    help="The scale of the network (full network order=1000)")
parser.add_argument('--simtime', type=float, default=100.0,
                    help="The length of the simulation in ms")
parser.add_argument('--timestep', type=float, default=0.1,
                    help="Simulation timestep")
parser.add_argument('--simulators', type=str, nargs='+',
                    default=['neuron', 'nest'],
                    help="Which simulators to simulate the 9ML network")
parser.add_argument('--record_v', default=False,
                    help=("Whether to record and plot the voltages"))
parser.add_argument('--build_mode', type=str, default='force',
                    help="The build mode with which to construct the "
                    "network")
parser.add_argument('--option', nargs=2, type=str, action='append',
                    default=[],
                    help="Extra options that are passed to the test")
parser.add_argument('--seed', type=int, default=None,
                    help="Random seed passed to the simulators")
args = parser.parse_args(argv)


pyNN_states = {'nest': pyNN.nest.simulator.state,
               'neuron': pyNN.neuron.simulator.state}
pyNN_setup = {'nest': pyNN.nest.setup, 'neuron': pyNN.neuron.setup}
pype9_network_classes = {'nest': pype9.nest.Network,
                         'neuron': pype9.neuron.Network}
pype9_controller = {'nest': pype9.nest.cells.simulation_controller,
                    'neuron': pype9.neuron.cells.simulation_controller}
# Set up recorders for 9ML network
rates = {}
psth = {}

# Set the random seed
numpy.random.seed(args.seed)
seeds = numpy.asarray(
    numpy.floor(numpy.random.random(len(args.simulators) * 1e5)),
    dtype=int) * 2

# Loop through each Brunel case and scale the model according to the order
models = {}
for case in args.cases:
    model = ninemlcatalog.load(
        'network/Brunel2000/' + case).as_network('Brunel_{}'.format(case))
    # Rescale loaded populations to requested order
    if args.order != 1000:
        for pop in model.populations:
            pop.size = int(numpy.ceil((pop.size / 1000) * args.order))
        for proj in (model.projection('Excitation'),
                     model.projection('Inhibition')):
            props = proj.connectivity.rule_properties
            number = props.property('number')
            props.set(Property(
                number.name,
                (int(numpy.ceil((number.value / 1000) * args.order)) *
                 un.unitless)))
    models[case] = model

# Create the network and run the simulations for each simulator
for simulator, seed in zip(args.simulators, seeds):
    # Reset the simulator
    pype9_controller[simulator].clear(rng_seed=seed)
    pyNN_setup[simulator](timestep=args.timestep, rng_seeds_seed=seed + 1)
    for case, model in models.iteritems():
        # Construct the network
        network = pype9_network_classes[simulator](model)
        # Record spikes and voltages
        for pop in network.component_arrays:
            pop.record('spikes')
            if args.record_v and pop.name != 'Ext':
                pop.record('v__cell')
        # Run the simulation
        pyNN_states[simulator].run(args.simtime)
        # Plot the results of the simulation
        for pop in network.component_arrays:
            block = pop.get_data()
            segment = block.segments[0]
            spiketrains = segment.spiketrains
            spike_times = []
            ids = []
            for i, spiketrain in enumerate(spiketrains):
                spike_times.extend(spiketrain)
                ids.extend([i] * len(spiketrain))
            plt.figure()
            plt.scatter(spike_times, ids)
            plt.xlabel('Times (ms)')
            plt.ylabel('Cell Indices')
            plt.title("{} - {} Spikes".format(simulator, pop.name))
            if args.record_v and pop.name != 'Ext':
                traces = segment.analogsignalarrays
                plt.figure()
                legend = []
                for trace in traces:
                    plt.plot(trace.times, trace)
                    legend.append(trace.name)
                    plt.xlabel('Time (ms)')
                    plt.ylabel('Membrane Voltage (mV)')
                    plt.title("{} - {} Membrane Voltage".format(
                        simulator, pop.name))
                plt.legend(legend)
