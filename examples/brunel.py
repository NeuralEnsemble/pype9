from __future__ import division
import sys
import os.path
from itertools import groupby
from operator import itemgetter
from collections import defaultdict
import ninemlcatalog
import numpy as np
from nineml import units as un, Property
import pyNN.neuron
import pype9.neuron
import argparse
import logging
from matplotlib import pyplot as plt
argv = sys.argv[1:]  # Save argv before it is clobbered by the NEST init.
import nest  # @IgnorePep8
import pyNN.nest  # @IgnorePep8
import pype9.nest  # @IgnorePep8


# Basic network params
min_delay = 0.1
max_delay = 10.0

# Dictionaries to look up simulator specific objects/classes
pyNN_states = {'nest': pyNN.nest.simulator.state,
               'neuron': pyNN.neuron.simulator.state}
pyNN_setup = {'nest': pyNN.nest.setup, 'neuron': pyNN.neuron.setup}
pype9_network_classes = {'nest': pype9.nest.Network,
                         'neuron': pype9.neuron.Network}


# Construct reference NEST network
def construct_reference(case, order, num_record, num_record_v, pops_to_plot,
                        timestep):
    """
    The model has been adapted from the brunel-alpha-nest.py
    model that is part of NEST.

    Copyright (C) 2004 The NEST Initiative

    NEST is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    NEST is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with NEST.  If not, see <http://www.gnu.org/licenses/>.
    This version uses NEST's Connect functions.
    """

    # Parameters used to construct the reference network
    delay = 1.5 * un.ms

    # Initialize the parameters of the integrate and fire neuron
    theta = 20.0
    J = 0.1  # postsynaptic amplitude in mV
    tauSyn = 0.1
    tauMem = 20.0
    CMem = 250.0

    epsilon = 0.1  # connection probability

    brunel_parameters = {
        "SR": {"g": 3.0, "eta": 2.0},
        "AI": {"g": 5.0, "eta": 2.0},
        "SIfast": {"g": 6.0, "eta": 4.0},
        "SIslow": {"g": 4.5, "eta": 0.9}}

    # Parameters for asynchronous irregular firing
    g = brunel_parameters[case]["g"]
    eta = brunel_parameters[case]["eta"]

    NE = 4 * order
    NI = 1 * order

    CE = int(epsilon * NE)  # number of excitatory synapses per neuron
    CI = int(epsilon * NI)  # number of inhibitory synapses per neuron
    if not CE:
        CE = 1

    def compute_normalised_psr(tauMem, CMem, tauSyn):
        """Compute the maximum of postsynaptic potential
           for a synaptic input current of unit amplitude
           (1 pA)
        """

        a = (tauMem / tauSyn)
        b = (1.0 / tauSyn - 1.0 / tauMem)

        # time of maximum
        t_max = 1.0 / b * \
            (-nest.sli_func('LambertWm1', -np.exp(-1.0 / a) / a) - 1.0 / a)

        # maximum of PSP for current of unit amplitude
        return (np.exp(1.0) / (tauSyn * CMem * b) *
                ((np.exp(-t_max / tauMem) -
                  np.exp(-t_max / tauSyn)) / b - t_max *
                 np.exp(-t_max / tauSyn)))

    # normalize synaptic current so that amplitude of a PSP is J
    J_unit = compute_normalised_psr(tauMem, CMem, tauSyn)
    J_ex = J / J_unit
    J_in = -g * J_ex

    # threshold rate, equivalent rate of events needed to
    # have mean input current equal to threshold
    nu_th = ((theta * CMem) /
             (J_ex * CE * np.exp(1) * tauMem * tauSyn))
    nu_ex = eta * nu_th
    p_rate = 1000.0 * nu_ex * CE

    neuron_params = {"C_m": CMem,
                     "tau_m": tauMem,
                     "tau_syn_ex": tauSyn,
                     "tau_syn_in": tauSyn,
                     "t_ref": 2.0,
                     "E_L": 0.0,
                     "V_reset": 0.0,
                     "V_m": 0.0,
                     "V_th": theta}

    nest.SetDefaults("iaf_psc_alpha", neuron_params)
    nodes_exc = nest.Create("iaf_psc_alpha", NE)
    nodes_inh = nest.Create("iaf_psc_alpha", NI)

    nest.SetStatus(nodes_exc + nodes_inh, 'V_m',
                   list(np.random.rand(NE + NI) * 20.0))

    nest.SetDefaults("poisson_generator", {"rate": p_rate})
    noise = nest.Create("poisson_generator")
    nodes_ext = nest.Create('parrot_neuron', NE + NI)
    nest.Connect(noise, nodes_ext)

    all_nodes = {'Exc': nodes_exc, 'Inh': nodes_inh, 'Ext': nodes_ext}

    # Set up connections

    nest.CopyModel(
        "static_synapse", "excitatory", {
            "weight": J_ex, "delay": float(delay.value)})
    nest.CopyModel(
        "static_synapse", "inhibitory", {
            "weight": J_in, "delay": float(delay.value)})

    nest.Connect(nodes_ext, nodes_exc + nodes_inh, 'one_to_one',
                 "excitatory")

    # We now iterate over all neuron IDs, and connect the neuron to the
    # sources from our array. The first loop connects the excitatory
    # neurons and the second loop the inhibitory neurons.
    conn_params_ex = {'rule': 'fixed_indegree', 'indegree': CE}
    nest.Connect(
        nodes_exc,
        nodes_exc +
        nodes_inh,
        conn_params_ex,
        "excitatory")

    conn_params_in = {'rule': 'fixed_indegree', 'indegree': CI}
    nest.Connect(
        nodes_inh,
        nodes_exc +
        nodes_inh,
        conn_params_in,
        "inhibitory")

    recorders = defaultdict(dict)
    for pop_name in pops_to_plot:
        pop = np.asarray(all_nodes[pop_name], dtype=int)
        spikes = recorders[pop_name]['spikes'] = nest.Create("spike_detector")
        nest.SetStatus(spikes, [{"label": "brunel-py-" + pop_name,
                                 "withtime": True, "withgid": True}])
        nest.Connect(list(pop[:num_record]), spikes, syn_spec="excitatory")
        if num_record_v:
            # Set up voltage traces recorders for reference network
            multi = recorders[pop_name]['V_m'] = nest.Create(
                'multimeter', params={'record_from': ['V_m'],
                                      'interval': timestep})
            nest.Connect(multi, list(pop[:num_record_v]))
    return all_nodes, recorders


pyNN_logger = logging.Logger('PyNN')

parser = argparse.ArgumentParser()
parser.add_argument('--case', type=str, nargs='+', default='AI',
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
parser.add_argument('--option', nargs=2, type=str, action='append',
                    default=[],
                    help="Extra options that are passed to the test")
parser.add_argument('--seed', type=int, default=None,
                    help="Random seed passed to the simulators")
parser.add_argument('--reference', action='store_true', default=False,
                    help="Plot a reference NEST implementation alongside")
parser.add_argument('--save_fig', type=str, default=None,
                    help=("Location to save the generated figures"))
parser.add_argument('--figsize', nargs=2, type=float, default=(10, 15),
                    help="The size of the figures")
args = parser.parse_args(argv)


if __name__ == '__main__':

    if args.save_fig is not None:
        save_path = os.path.abspath(args.save_fig)
        if not os.path.exists(save_path):
            os.mkdir(save_path)
    else:
        save_path = None

    # Get the list of populations to record and plot from
    pops_to_plot = ['Exc', 'Inh']
    if args.plot_input:
        pops_to_plot.append('Ext')

    # Set the random seed
    np.random.seed(args.seed)
    seeds = np.asarray(
        np.floor(np.random.random(len(args.simulators) * 1e5)), dtype=int)

    # Load the Brunel model corresponding to the 'case' argument from the
    # nineml catalog and scale the model according to the 'order' argument
    model = ninemlcatalog.load('network/Brunel2000/' + args.case).as_network(
        'Brunel_{}'.format(args.case))
    if args.order != 1000:
        for pop in model.populations:
            pop.size = int(np.ceil((pop.size / 1000) * args.order))
        for proj in (model.projection('Excitation'),
                     model.projection('Inhibition')):
            props = proj.connectivity.rule_properties
            number = props.property('number')
            props.set(Property(
                number.name,
                (int(np.ceil((number.value / 1000) * args.order)) *
                 un.unitless)))

    # Create dictionaries to hold the simulation results
    spikes = defaultdict(dict)
    if args.num_record_v:
        vs = defaultdict(dict)

    # Create the network for each simulator and set recorders
    networks = {}
    for simulator, seed in zip(args.simulators, seeds):
        # Reset the simulator
        pyNN_setup[simulator](min_delay=min_delay, max_delay=max_delay,
                              timestep=args.timestep, rng_seeds_seed=seed)
        # Construct the network
        networks[simulator] = pype9_network_classes[simulator](
            model, build_mode=args.build_mode)
        if args.build_mode != 'build_only':
            # Record spikes and voltages
            for pop in networks[simulator].component_arrays:
                pop[:args.num_record].record('spikes')
                if args.num_record_v and pop.name != 'Ext':
                    pop[:args.num_record_v].record('v__cell')

    if args.build_mode == 'build_only':
        exit()

    # Set of simulators to run
    simulator_to_run = set(args.simulators)

    # Create the reference simulation if required
    if args.reference:
        _, ref_recorders = construct_reference(
            args.case, args.order, args.num_record, args.num_record_v,
            pops_to_plot, args.timestep)
        simulator_to_run.add('nest')

    # Run the simulation(s)
    for simulator in simulator_to_run:
        pyNN_states[simulator].run(args.simtime)

    # Plot the results
    num_subplots = len(args.simulators) + int(args.reference)
    for pop_name in pops_to_plot:
        spike_fig, spike_subplots = plt.subplots(num_subplots, 1,
                                                 figsize=args.figsize)
        spike_fig.suptitle("{} - {} Spike Times".format(args.case, pop_name),
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
            plt.sca(spike_subplots[subplot_index])
            plt.scatter(spike_times, ids)
            plt.xlim((args.plot_start, args.simtime))
            plt.ylim((-1, len(spiketrains)))
            plt.xlabel('Times (ms)')
            plt.ylabel('Cell Indices')
            plt.title("PyPe9 {}".format(simulator.upper()), fontsize=12)
            if args.num_record_v and pop_name != 'Ext':
                traces = segment.analogsignalarrays
                legend = []
                plt.sca(v_subplots[subplot_index])
                for trace in traces:
                    plt.plot(trace.times, trace)
                plt.xlim((args.plot_start, args.simtime))
                plt.ylim([0.0, 20.0])
                plt.xlabel('Time (ms)')
                plt.ylabel('Membrane Voltage (mV)')
                plt.title("Pype9 {}".format(simulator.upper()), fontsize=12)
        if args.reference:
            events = nest.GetStatus(ref_recorders[pop_name]['spikes'],
                                    "events")[0]
            spike_times = np.asarray(events['times'])
            senders = np.asarray(events['senders'])
            inds = np.asarray(spike_times > args.plot_start, dtype=bool)
            spike_times = spike_times[inds]
            senders = senders[inds] - senders.min()
            plt.sca(spike_subplots[-1])
            plt.scatter(spike_times, senders)
            plt.xlim((args.plot_start, args.simtime))
            plt.ylim((-1, senders.max() + 1))
            plt.xlabel('Times (ms)')
            plt.ylabel('Cell Indices')
            plt.title("Ref. NEST", fontsize=12)
            if args.num_record_v:
                events, interval = nest.GetStatus(
                    ref_recorders[pop_name]['V_m'], ["events", 'interval'])[0]
                sorted_vs = sorted(zip(events['senders'], events['times'],
                                       events['V_m']), key=itemgetter(0))
                legend = []
                plt.sca(v_subplots[-1])
                for sender, group in groupby(sorted_vs, key=itemgetter(0)):
                    _, t, v = zip(*group)
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
    print "done"
