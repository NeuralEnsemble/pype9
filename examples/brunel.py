from __future__ import division
import sys
from itertools import groupby
from operator import itemgetter
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

pyNN_logger = logging.Logger('PyNN')

parser = argparse.ArgumentParser()
parser.add_argument('--cases', type=str, nargs='+',
                    default=['AI', 'SIFast', 'SISlow', 'SR'],
                    help="Which Brunel version(s) to run")
parser.add_argument('--order', type=int, default=10,
                    help="The scale of the network (full network order=1000)")
parser.add_argument('--simtime', type=float, default=100.0,
                    help="The length of the simulation in ms")
parser.add_argument('--timestep', type=float, default=0.001,
                    help="Simulation timestep")
parser.add_argument('--simulators', type=str, nargs='+',
                    default=['neuron', 'nest'],
                    help="Which simulators to simulate the 9ML network")
parser.add_argument('--record_v', action='store_true', default=False,
                    help=("Whether to record and plot the voltages"))
parser.add_argument('--build_mode', type=str, default='force',
                    help="The build mode with which to construct the "
                    "network")
parser.add_argument('--option', nargs=2, type=str, action='append',
                    default=[],
                    help="Extra options that are passed to the test")
parser.add_argument('--seed', type=int, default=None,
                    help="Random seed passed to the simulators")
parser.add_argument('--reference', action='store_true', default=False,
                    help="Plot a reference NEST implementation alongside")
args = parser.parse_args(argv)


# Construct reference NEST network
def construct_reference(case, order):
    """
    The model in this file has been adapted from the brunel-alpha-nest.py
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
    return all_nodes


pyNN_states = {'nest': pyNN.nest.simulator.state,
               'neuron': pyNN.neuron.simulator.state}
pyNN_setup = {'nest': pyNN.nest.setup, 'neuron': pyNN.neuron.setup}
pype9_network_classes = {'nest': pype9.nest.Network,
                         'neuron': pype9.neuron.Network}
# Set up recorders for 9ML network
rates = {}
psth = {}

# Set the random seed
np.random.seed(args.seed)
seeds = np.asarray(
    np.floor(np.random.random(len(args.simulators) * 1e5)), dtype=int)

# Loop through each Brunel case and scale the model according to the order
models = {}
for case in args.cases:
    model = ninemlcatalog.load(
        'network/Brunel2000/' + case).as_network('Brunel_{}'.format(case))
    # Rescale loaded populations to requested order
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
    models[case] = model

# Create the network and run the simulations for each simulator
for simulator, seed in zip(args.simulators, seeds):
    # Reset the simulator
    pyNN_setup[simulator](timestep=args.timestep, rng_seeds_seed=seed)
    for case, model in models.iteritems():
        # Construct the network
        network = pype9_network_classes[simulator](model)
        # Record spikes and voltages
        for pop in network.component_arrays:
            pop.record('spikes')
            if args.record_v and pop.name != 'Ext':
                pop.record('v__cell')
        if args.reference:
            ref_nodes = construct_reference(case, args.order)
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
        if args.reference:
            for pop_name in network.component_array_names:
                events = nest.GetStatus(spikes[model_ver][pop_name],
                                        "events")[0]
                spike_times = np.asarray(events['times'])
                senders = np.asarray(events['senders'])
                inds = np.asarray(spike_times > record_start, dtype=bool)
                spike_times = spike_times[inds]
                senders = senders[inds]
                plt.figure()
                plt.scatter(spike_times, senders)
                plt.xlabel('Time (ms)')
                plt.ylabel('Cell Indices')
                plt.title("Reference - {} Spikes".format(pop_name))
                if args.record_v:
                    for param in self.record_params[pop_name][model_ver]:
                        events, interval = nest.GetStatus(
                            multi[model_ver][pop_name], ["events",
                                                         'interval'])[0]
                        sorted_vs = sorted(zip(events['senders'],
                                               events['times'],
                                               events[param]),
                                           key=itemgetter(0))
                        plt.figure()
                        legend = []
                        for sender, group in groupby(sorted_vs,
                                                     key=itemgetter(0)):
                            _, t, v = zip(*group)
                            t = np.asarray(t)
                            v = np.asarray(v)
                            inds = t > record_start
                            plt.plot(t[inds] * interval, v[inds])
                            legend.append(sender)
                        plt.xlabel('Time (ms)')
                        plt.ylabel(param)
                        plt.title("{} - {} {}".format(model_ver, pop_name,
                                                      param))
                        plt.legend(legend)
