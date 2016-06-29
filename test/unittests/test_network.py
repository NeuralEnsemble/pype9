from __future__ import division
from math import exp
from itertools import groupby, izip
from operator import itemgetter
import numpy
import pyNN.neuron
import pyNN.nest
import nest
from nineml.user import (
    Projection, Network, DynamicsProperties,
    Population, ComponentArray, EventConnectionGroup,
    MultiDynamicsProperties, Property, RandomDistributionProperties)
from nineml.user.projection import Connectivity
from nineml.abstraction import (
    Parameter, Dynamics, Regime, On, OutputEvent, StateVariable,
    StateAssignment, Constant, Alias)
from nineml.abstraction.ports import (
    AnalogSendPort, AnalogReceivePort, AnalogReducePort, EventSendPort,
    EventReceivePort)
from nineml import units as un
from nineml.units import ms
from nineml.values import RandomValue
from pype9.base.cells import (
    ConnectionPropertySet, DynamicsWithSynapsesProperties)
from pype9.base.network import Network as BasePype9Network
from pype9.neuron.network import Network as NeuronPype9Network
from pype9.nest.network import Network as NestPype9Network
from pype9.neuron.cells import (
    simulation_controller as simulation_contoller_neuron)
from pype9.nest.cells import (
    simulation_controller as simulation_controller_nest)
import ninemlcatalog
try:
    from matplotlib import pyplot as plt
except ImportError:
    pass
if __name__ == '__main__':
    # Import dummy test case
    from utils import DummyTestCase as TestCase  # @UnusedImport
    import nest.raster_plot
else:
    from unittest import TestCase  # @Reimport

nest_bookkeeping = (
    'element_type', 'global_id', 'local_id', 'receptor_types',
    'thread_local_id', 'frozen', 'thread', 'model',
    'archiver_length', 'recordables', 'parent', 'local', 'vp',
    'tau_minus', 'tau_minus_triplet', 't_spike', 'origin', 'stop', 'start',
    'V_min')


class TestBrunel2000(TestCase):

    timestep = 0.001
    min_delay = 0.1
    max_delay = 10.0
    delay = 1.5 * un.ms

    brunel_parameters = {
        "SR": {"g": 3.0, "eta": 2.0},
        "AI": {"g": 5.0, "eta": 2.0},
        "SIfast": {"g": 6.0, "eta": 4.0},
        "SIslow": {"g": 4.5, "eta": 0.9}}

    translations = {
        'tau_m': 'tau__cell', 'V_th': 'v_threshold__cell',
        'E_L': 'e_leak__cell', 'I_e': 0.0, 'C_m': 'Cm__cell',
        'V_reset': 'v_reset__cell', 'tau_syn_in': 'tau__psr__Inhibition',
        'tau_syn_ex': 'tau__psr__Excitation',
        't_ref': 'refractory_period__cell',
        'V_m': None}  # 'v__cell'}

    pop_names = ('Exc', 'Inh', 'Ext')
    proj_names = ('Excitation', 'Inhibition', 'External')
    conn_param_names = ['weight', 'delay']
    record_params = {'Exc': {'nineml': ['v__cell',
                                        'b__psr__Excitation',
                                        'b__psr__Inhibition',
                                        'b__psr__External'],
                             'reference': ['V_m']},
                     'Inh': {'nineml': ['v__cell',
                                        'b__psr__Excitation',
                                        'b__psr__Inhibition',
                                        'b__psr__External'],
                             'reference': ['V_m']},
                     'Ext': {'nineml': [], 'reference': []}}

    dt = timestep * un.ms    # the resolution in ms
    psth_percent_error = {'Exc': 1.0, 'Inh': 1.0, 'Ext': 1.0}
    rate_percent_error = {'Exc': 1.0, 'Inh': 1.0, 'Ext': 1.0}
    out_stdev_error = {('Exc', 'Exc'): 7.0, ('Exc', 'Inh'): 6.0,
                       ('Inh', 'Exc'): 1.5, ('Inh', 'Inh'): 5.0,
                       ('Ext', 'Exc'): 0.0, ('Ext', 'Inh'): 0.0}

    def test_population_params(self, case='AI', order=10, **kwargs):  # @UnusedVariable @IgnorePep8
        self._setup('nest')
        nml = self._construct_nineml(case, order, 'nest')
        ref = self._construct_reference(case, order)
        for pop_name in ('Exc', 'Inh'):
            params = {}
            means = {}
            stdevs = {}
            for model_ver in ('nineml', 'reference'):
                if model_ver == 'nineml':
                    inds = list(nml.component_array(pop_name).all_cells)
                else:
                    inds = getattr(ref, pop_name)
                param_names = [
                    n for n in nest.GetStatus([inds[0]])[0].keys()
                    if n not in nest_bookkeeping]
                params[model_ver] = dict(
                    izip(param_names, izip(*nest.GetStatus(inds,
                                                           keys=param_names))))
                means[model_ver] = {}
                stdevs[model_ver] = {}
                for param_name, values in params[model_ver].iteritems():
                    vals = numpy.asarray(values)
                    try:
                        means[model_ver][param_name] = numpy.mean(vals)
                    except:
                        means[model_ver][param_name] = None
                    try:
                        stdevs[model_ver][param_name] = numpy.std(vals)
                    except:
                        stdevs[model_ver][param_name] = None
            for stat_name, stat in (('mean', means),
                                    ('standard deviation', stdevs)):
                for param_name in stat['reference']:
                    nml_param_name = self.translations.get(
                        param_name, param_name + '__cell')
                    if nml_param_name is not None:  # No equivalent parameter
                        if isinstance(nml_param_name, (float, int)):
                            if stat_name == 'mean':
                                nineml_stat = nml_param_name
                            else:
                                nineml_stat = 0.0
                        else:
                            nineml_stat = stat['nineml'][nml_param_name]
                        reference_stat = stat['reference'][param_name]
                        self.assertAlmostEqual(
                            reference_stat, nineml_stat,
                            msg=("'{}' {} is not almost equal between "
                                 "reference ({}) and nineml ({})  in '{}'"
                                 .format(param_name, stat_name,
                                         reference_stat, nineml_stat,
                                         pop_name)))

    def test_connection_degrees(self, case='AI', order=500, **kwargs):  # @UnusedVariable @IgnorePep8
        self._setup('nest')
        nml = self._construct_nineml(case, order, 'nest')
        ref = self._construct_reference(case, order)
        print "constructed"
        for pop1_name, pop2_name in self.out_stdev_error:
            in_degree = {}
            out_degree = {}
            for model_ver, pop1, pop2 in [
                ('nineml', nml.component_array(pop1_name).all_cells,
                 nml.component_array(pop2_name).all_cells),
                ('reference', numpy.asarray(ref[pop1_name]),
                 numpy.asarray(ref[pop2_name]))]:
                conns = numpy.asarray(nest.GetConnections(list(pop1),
                                                          list(pop2)))
                out_degree[model_ver] = numpy.array(
                    [numpy.count_nonzero(conns[:, 0] == i) for i in pop1])
                in_degree[model_ver] = numpy.array(
                    [numpy.count_nonzero(conns[:, 1] == i) for i in pop2])
            nineml_out_mean = numpy.mean(out_degree['nineml'])
            ref_out_mean = numpy.mean(out_degree['reference'])
            self.assertEqual(
                nineml_out_mean, ref_out_mean,
                "Mean out degree of '{}' to '{}' projection ({}) doesn't "
                "match reference ({})".format(
                    pop1_name, pop2_name, nineml_out_mean, ref_out_mean))
            nineml_in_mean = numpy.mean(in_degree['nineml'])
            ref_in_mean = numpy.mean(in_degree['reference'])
            self.assertEqual(
                nineml_in_mean, ref_in_mean,
                "Mean in degree of '{}' to '{}' projection ({}) doesn't "
                "match reference ({})".format(
                    pop1_name, pop2_name, nineml_in_mean, ref_in_mean))
            nineml_in_stdev = numpy.std(in_degree['nineml'])
            ref_in_stdev = numpy.std(in_degree['reference'])
            self.assertEqual(
                nineml_in_stdev, ref_in_stdev,
                "Std. of in degree of '{}' to '{}' projection ({}) doesn't "
                "match reference ({})".format(
                    pop1_name, pop2_name, nineml_in_stdev, ref_in_stdev))
            nineml_out_stdev = numpy.std(out_degree['nineml'])
            ref_out_stdev = numpy.std(out_degree['reference'])
            percent_error = abs(nineml_out_stdev / ref_out_stdev - 1.0) * 100.0
            self.assertLessEqual(
                percent_error, self.out_stdev_error[(pop1_name, pop2_name)],
                "Std. of out degree of '{}' to '{}' projection ({}) doesn't "
                "match reference ({}) within {}% ({}%)".format(
                    pop1_name, pop2_name, nineml_out_stdev, ref_out_stdev,
                    self.out_stdev_error[(pop1_name, pop2_name)],
                    percent_error))

    def test_connection_params(self, case='AI', order=10, **kwargs):  # @UnusedVariable @IgnorePep8
        self._setup('nest')
        nml = self._construct_nineml(case, order, 'nest')
        ref = self._construct_reference(case, order)
        ref_conns = self._reference_projections(ref)
        for conn_group in nml.connection_groups:
            nml_conns = conn_group.nest_connections
            nml_params = dict(izip(
                self.conn_param_names, izip(
                    *nest.GetStatus(nml_conns, self.conn_param_names))))
            # Since the weight is constant it is set as a parameter of the
            # cell class not a connection parameter
            nml_params['weight'] = nest.GetStatus(
                list(conn_group.post.all_cells),
                'weight__pls__{}'.format(conn_group.name))
            ref_params = dict(izip(
                self.conn_param_names, izip(
                    *nest.GetStatus(ref_conns[conn_group.name],
                                    self.conn_param_names))))
            for attr in self.conn_param_names:
                ref_mean = numpy.mean(ref_params[attr])
                ref_stdev = numpy.std(ref_params[attr])
                nml_mean = numpy.mean(nml_params[attr])
                nml_stdev = numpy.std(nml_params[attr])
                self.assertAlmostEqual(
                    ref_mean, nml_mean,
                    msg=("'{}' mean is not almost equal between "
                         "reference ({}) and nineml ({})  in '{}'"
                         .format(attr, ref_mean, nml_mean, conn_group.name)))
                self.assertAlmostEqual(
                    ref_stdev, nml_stdev,
                    msg=("'{}' mean is not almost equal between "
                         "reference ({}) and nineml ({})  in '{}'"
                         .format(attr, ref_stdev, nml_stdev, conn_group.name)))

    def test_sizes(self, case='AI', order=100, **kwargs):  # @UnusedVariable @IgnorePep8
        self._setup('nest')
        nml_network = self._construct_nineml(case, order, 'nest')
        nml = dict((p.name, p.all_cells) for p in nml_network.component_arrays)
        ref = self._construct_reference(case, order)
        # Test sizes of component arrays
        for name in ('Exc', 'Inh'):
            nml_size = len(nml[name])
            ref_size = len(ref[name])
            self.assertEqual(
                nml_size, ref_size,
                "Size of '{}' component array ({}) does not match reference "
                "({})".format(name, nml_size, ref_size))
        ref_conns = self._reference_projections(ref)
        for conn_group in nml.connection_groups:
            nml_size = len(conn_group)
            ref_size = len(ref_conns[conn_group.name])
            self.assertEqual(
                nml_size, ref_size,
                "Number of connections in '{}' ({}) does not match reference "
                "({})".format(conn_group.name, nml_size, ref_size))


#     cases = ["SR", "AI", "SIfast", "SIslow"]

    def test_activity(self, case='AI', order=50, simtime=1200.0, plot=True,
                      record_size=50, record_pops=('Exc', 'Inh', 'Ext'),
                      record_states=True, record_start=1000.0, bin_width=2.5,
                      **kwargs):
        record_duration = simtime - record_start
        # Construct 9ML network
        self._setup('nest')
        nml_network = self._construct_nineml(case, order, 'nest', **kwargs)
        nml = dict((p.name, list(p.all_cells))
                   for p in nml_network.component_arrays)
        # Construct reference network
        ref = self._construct_reference(case, order)
        # Set up spike recorders for reference network
        pops = {'nineml': nml, 'reference': ref}
        spikes = {}
        multi = {}
        for model_ver in ('nineml', 'reference'):
            spikes[model_ver] = {}
            multi[model_ver] = {}
            for pop_name in record_pops:
                pop = numpy.asarray(pops[model_ver][pop_name], dtype=int)
                record_inds = numpy.asarray(numpy.unique(numpy.floor(
                    numpy.arange(start=0, stop=len(pop),
                                 step=len(pop) / record_size))), dtype=int)
                spikes[model_ver][pop_name] = nest.Create("spike_detector")
                nest.SetStatus(spikes[model_ver][pop_name],
                               [{"label": "brunel-py-" + pop_name,
                                 "withtime": True, "withgid": True}])
                nest.Connect(list(pop[record_inds]),
                             spikes[model_ver][pop_name],
                             syn_spec="excitatory")
                if record_states:
                    # Set up voltage traces recorders for reference network
                    if self.record_params[pop_name][model_ver]:
                        multi[model_ver][pop_name] = nest.Create(
                            'multimeter',
                            params={'record_from':
                                    self.record_params[pop_name][model_ver]})
                        nest.Connect(multi[model_ver][pop_name],
                                     list(pop[record_inds]))
        print "Starting simulation"
        # Simulate the network
        nest.Simulate(simtime)
        print "Finished simulation"
        rates = {'reference': {}, 'nineml': {}}
        psth = {'reference': {}, 'nineml': {}}
        for model_ver in ('reference', 'nineml'):
            for pop_name in record_pops:
                events = nest.GetStatus(spikes[model_ver][pop_name],
                                        "events")[0]
                spike_times = numpy.asarray(events['times'])
                senders = numpy.asarray(events['senders'])
                inds = spike_times > record_start
                spike_times = spike_times[inds]
                senders = senders[inds]
                rates[model_ver][pop_name] = (
                    1000.0 * len(spike_times) / record_duration)
                psth[model_ver][pop_name] = (
                    numpy.histogram(
                        spike_times,
                        bins=numpy.floor(record_duration / bin_width))[0] /
                    bin_width)
                if plot:
                    plt.figure()
                    plt.scatter(spike_times, senders)
                    plt.xlabel('Time (ms)')
                    plt.ylabel('Cell Indices')
                    plt.title("{} - {} Spikes".format(model_ver, pop_name))
                    plt.figure()
                    plt.hist(spike_times,
                             bins=numpy.floor(record_duration / bin_width))
                    plt.xlabel('Time (ms)')
                    plt.ylabel('Rate')
                    plt.title("{} - {} PSTH".format(model_ver, pop_name))
                    if record_states:
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
                                t = numpy.asarray(t)
                                v = numpy.asarray(v)
                                inds = t > record_start
                                plt.plot(t[inds] * interval, v[inds])
                                legend.append(sender)
                            plt.xlabel('Time (ms)')
                            plt.ylabel(param)
                            plt.title("{} - {} {}".format(model_ver, pop_name,
                                                          param))
                            plt.legend(legend)
        for pop_name in record_pops:
            percent_rate_error = abs(rates['nineml'][pop_name] /
                                     rates['reference'][pop_name] - 1.0) * 100
            self.assertLess(
                percent_rate_error,
                self.rate_percent_error[pop_name], message=(
                    "Rate of '{}' ({}) doesn't match reference ({}) within {}%"
                    " ({}%)".format(pop_name, rates['nineml'][pop_name],
                                    rates['reference'][pop_name],
                                    self.rate_percent_error[pop_name],
                                    percent_rate_error)))
            percent_psth_stdev_error = abs(
                numpy.std(psth['nineml'][pop_name]) /
                numpy.std(psth['reference'][pop_name]) - 1.0) * 100
            self.assertLess(
                percent_psth_stdev_error,
                self.psth_percent_error[pop_name],
                message=(
                    "Std. Dev. of PSTH for '{}' ({}) doesn't match "
                    "reference ({}) within {}% ({}%)".format(
                        pop_name,
                        numpy.std(psth['nineml'][pop_name]) / bin_width,
                        numpy.std(psth['reference'][pop_name]) / bin_width,
                        self.psth_percent_error[pop_name],
                        percent_psth_stdev_error)))
        if plot:
            plt.show()

    def test_activity_neuron(self, case='AI', order=10, simtime=100.0,
                             simulators=['nest'], **kwargs):  # simulators=['nest', 'neuron']): @IgnorePep8
        data = {}
        controllers = {'nest': simulation_controller_nest,
                       'neuron': simulation_contoller_neuron}
        # Set up recorders for 9ML network
        for simulator in simulators:
            data[simulator] = {}
            self._setup(simulator)
            network = self._construct_nineml(case, order, simulator)
            for pop in network.component_arrays:
                pop.record('spikes')
                if pop.name != 'Ext':
                    pop.record('v__cell')
            controllers[simulator].run(simtime)
            for pop in network.component_arrays:
                block = data[simulator][pop.name] = pop.get_data()
                segment = block.segments[0]
                spiketrains = segment.spiketrains
                times = []
                ids = []
                for i, spiketrain in enumerate(spiketrains):
                    times.extend(spiketrain)
                    ids.extend([i] * len(spiketrain))
                plt.figure()
                plt.scatter(times, ids)
                plt.xlabel('Times (ms)')
                plt.ylabel('Cell Indices')
                plt.title("{} - {} Spikes".format(simulator, pop.name))
                if pop.name != 'Ext':
                    traces = segment.analogsignalarrays
                    plt.figure()
                    legend = []
                    for trace in traces:
                        plt.plot(trace.times, trace)
                        legend.append(trace.name)
                        plt.xlabel('Time (ms)')
                        plt.ylabel('Membrane Voltage (mV)')
                        plt.title("{} - {} Membrane Voltage".format(simulator,
                                                                    pop.name))
                    plt.legend(legend)
        plt.show()

    def test_flatten(self, **kwargs):  # @UnusedVariable
        brunel_network = ninemlcatalog.load('network/Brunel2000/AI/')
        (component_arrays,
         connection_groups) = BasePype9Network._flatten_to_arrays_and_conns(
            brunel_network)
        self.assertEqual(len(component_arrays), 3)
        self.assertEqual(len(connection_groups), 3)

    def _setup(self, simulator):
        if simulator == 'nest':
            pyNN.nest.setup(timestep=self.timestep, min_delay=self.min_delay,
                            max_delay=self.max_delay)
        elif simulator == 'neuron':
            pyNN.neuron.setup(timestep=self.timestep, min_delay=self.min_delay,
                              ax_delay=self.max_delay)
        else:
            assert False

    def _construct_nineml(self, case, order, simulator, **kwargs):
        model = ninemlcatalog.load('network/Brunel2000/' + case).as_network(
            'Brunel_{}'.format(case))
        # rescale populations
        for pop in model.populations:
            pop.size = int(numpy.ceil((pop.size / 1000) * order))
        for proj in (model.projection('Excitation'),
                     model.projection('Inhibition')):
            props = proj.connectivity.rule_properties
            number = props.property('number')
            props.set(Property(
                number.name,
                int(numpy.ceil((number.value / 1000) * order)) * un.unitless))
        if simulator == 'nest':
            NetworkClass = NestPype9Network
        elif simulator == 'neuron':
            NetworkClass = NeuronPype9Network
        else:
            assert False
        return NetworkClass(model, **kwargs)

    def _construct_reference(self, case, order):
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

        # Parameters for asynchronous irregular firing
        g = self.brunel_parameters[case]["g"]
        eta = self.brunel_parameters[case]["eta"]
        epsilon = 0.1  # connection probability

        NE = 4 * order
        NI = 1 * order

        CE = int(epsilon * NE)  # number of excitatory synapses per neuron
        CI = int(epsilon * NI)  # number of inhibitory synapses per neuron

        # Initialize the parameters of the integrate and fire neuron
        tauSyn = 0.1
        tauMem = 20.0
        CMem = 250.0
        theta = 20.0
        J = 0.1  # postsynaptic amplitude in mV

        # normalize synaptic current so that amplitude of a PSP is J
        J_unit = self._compute_normalised_psr(tauMem, CMem, tauSyn)
        J_ex = J / J_unit
        J_in = -g * J_ex
        print "Case: {}".format(case)
        print "Reference J_ex: {}".format(J_ex)
        print "Reference J_in: {}".format(J_in)

        # threshold rate, equivalent rate of events needed to
        # have mean input current equal to threshold
        nu_th = (theta * CMem) / (J_ex * CE * exp(1) * tauMem * tauSyn)
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
        nest.SetDefaults("poisson_generator", {"rate": p_rate})

        nodes_exc = nest.Create("iaf_psc_alpha", NE)
        nodes_inh = nest.Create("iaf_psc_alpha", NI)
        nodes_ext = nest.Create('parrot_neuron', NE + NI)
        noise = nest.Create("poisson_generator")

        nest.SetStatus(nodes_exc + nodes_inh, 'V_m',
                       list(numpy.random.rand(NE + NI) * 20.0))

        nest.CopyModel(
            "static_synapse", "excitatory", {
                "weight": J_ex, "delay": float(self.delay.value)})
        nest.CopyModel(
            "static_synapse", "inhibitory", {
                "weight": J_in, "delay": float(self.delay.value)})

        nest.Connect(noise, nodes_ext)
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
        return {'Exc': nodes_exc, 'Inh': nodes_inh, 'Ext': nodes_ext}

    def _reference_projections(self, network):
        combined = (network['Exc'] + network['Inh'])
        projs = {}
        projs['External'] = nest.GetConnections(network['Ext'], combined,
                                                'excitatory')
        projs['Excitation'] = nest.GetConnections(network['Exc'], combined,
                                                  'excitatory')
        projs['Inhibition'] = nest.GetConnections(network['Inh'],
                                                  combined, 'inhibitory')
        return projs

    def _pop_params_nineml(self, network):
        raise NotImplementedError

    @classmethod
    def _compute_normalised_psr(cls, tauMem, CMem, tauSyn):
        """Compute the maximum of postsynaptic potential
           for a synaptic input current of unit amplitude
           (1 pA)"""

        a = (tauMem / tauSyn)
        b = (1.0 / tauSyn - 1.0 / tauMem)

        # time of maximum
        t_max = 1.0 / b * \
            (-nest.sli_func('LambertWm1', -exp(-1.0 / a) / a) - 1.0 / a)

        # maximum of PSP for current of unit amplitude
        return (exp(1.0) / (tauSyn * CMem * b) *
                ((exp(-t_max / tauMem) -
                  exp(-t_max / tauSyn)) / b - t_max * exp(-t_max / tauSyn)))


class TestNetwork(TestCase):

    def setUp(self):
        self.all_to_all = ninemlcatalog.load('/connectionrule/AllToAll',
                                             'AllToAll')

    def test_component_arrays_and_connection_groups(self, **kwargs):  # @UnusedVariable @IgnorePep8

        # =====================================================================
        # Dynamics components
        # =====================================================================

        cell1_cls = Dynamics(
            name='Cell',
            state_variables=[
                StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 / P1 + i_ext / P2',
                    transitions=[On('SV1 > P3', do=[OutputEvent('spike')])],
                    name='R1')],
            analog_ports=[AnalogReducePort('i_ext', dimension=un.current,
                                           operator='+'),
                          EventSendPort('spike')],
            parameters=[Parameter('P1', dimension=un.time),
                        Parameter('P2', dimension=un.capacitance),
                        Parameter('P3', dimension=un.voltage)])

        cell2_cls = Dynamics(
            name='Cell',
            state_variables=[
                StateVariable('SV1', dimension=un.voltage)],
            regimes=[
                Regime(
                    'dSV1/dt = -SV1 ^ 2 / P1 + i_ext / P2',
                    transitions=[On('SV1 > P3', do=[OutputEvent('spike')]),
                                 On('SV1 > P4',
                                    do=[OutputEvent('double_spike')])],
                    name='R1')],
            analog_ports=[AnalogReducePort('i_ext', dimension=un.current,
                                           operator='+')],
            parameters=[Parameter('P1', dimension=un.time * un.voltage),
                        Parameter('P2', dimension=un.capacitance),
                        Parameter('P3', dimension=un.voltage),
                        Parameter('P4', dimension=un.voltage)])

        exc_cls = Dynamics(
            name="Exc",
            aliases=["i := SV1"],
            regimes=[
                Regime(
                    name="default",
                    time_derivatives=[
                        "dSV1/dt = SV1/tau"],
                    transitions=[
                        On('spike', do=["SV1 = SV1 + weight"]),
                        On('double_spike', do=['SV1 = SV1 + 2 * weight'])])],
            state_variables=[
                StateVariable('SV1', dimension=un.current),
            ],
            analog_ports=[AnalogSendPort("i", dimension=un.current),
                          AnalogReceivePort("weight", dimension=un.current)],
            parameters=[Parameter('tau', dimension=un.time)])

        inh_cls = Dynamics(
            name="Inh",
            aliases=["i := SV1"],
            regimes=[
                Regime(
                    name="default",
                    time_derivatives=[
                        "dSV1/dt = SV1/tau"],
                    transitions=On('spike', do=["SV1 = SV1 - weight"]))],
            state_variables=[
                StateVariable('SV1', dimension=un.current),
            ],
            analog_ports=[AnalogSendPort("i", dimension=un.current),
                          AnalogReceivePort("weight", dimension=un.current)],
            parameters=[Parameter('tau', dimension=un.time)])

        static_cls = Dynamics(
            name="Static",
            aliases=["fixed_weight := weight"],
            regimes=[
                Regime(name="default")],
            analog_ports=[AnalogSendPort("fixed_weight",
                                         dimension=un.current)],
            parameters=[Parameter('weight', dimension=un.current)])

        stdp_cls = Dynamics(
            name="PartialStdpGuetig",
            parameters=[
                Parameter(name='tauLTP', dimension=un.time),
                Parameter(name='aLTD', dimension=un.dimensionless),
                Parameter(name='wmax', dimension=un.dimensionless),
                Parameter(name='muLTP', dimension=un.dimensionless),
                Parameter(name='tauLTD', dimension=un.time),
                Parameter(name='aLTP', dimension=un.dimensionless)],
            analog_ports=[
                AnalogSendPort(dimension=un.dimensionless, name="wsyn"),
                AnalogSendPort(dimension=un.current, name="wsyn_current")],
            event_ports=[
                EventReceivePort(name="incoming_spike")],
            state_variables=[
                StateVariable(name='tlast_post', dimension=un.time),
                StateVariable(name='tlast_pre', dimension=un.time),
                StateVariable(name='deltaw', dimension=un.dimensionless),
                StateVariable(name='interval', dimension=un.time),
                StateVariable(name='M', dimension=un.dimensionless),
                StateVariable(name='P', dimension=un.dimensionless),
                StateVariable(name='wsyn', dimension=un.dimensionless)],
            constants=[Constant('ONE_NA', 1.0, un.nA)],
            regimes=[
                Regime(
                    name="sole",
                    transitions=On(
                        'incoming_spike',
                        to='sole',
                        do=[
                            StateAssignment('tlast_post', 't'),
                            StateAssignment('tlast_pre', 'tlast_pre'),
                            StateAssignment(
                                'deltaw',
                                'P*pow(wmax - wsyn, muLTP) * '
                                'exp(-interval/tauLTP) + deltaw'),
                            StateAssignment('interval', 't - tlast_pre'),
                            StateAssignment(
                                'M', 'M*exp((-t + tlast_post)/tauLTD) - aLTD'),
                            StateAssignment(
                                'P', 'P*exp((-t + tlast_pre)/tauLTP) + aLTP'),
                            StateAssignment('wsyn', 'deltaw + wsyn')]))],
            aliases=[Alias('wsyn_current', 'wsyn * ONE_NA')])

        exc = DynamicsProperties(
            name="ExcProps",
            definition=exc_cls, properties={'tau': 1 * ms})

        inh = DynamicsProperties(
            name="ExcProps",
            definition=inh_cls, properties={'tau': 1 * ms})

        random_weight = un.Quantity(RandomValue(
            RandomDistributionProperties(
                name="normal",
                definition=ninemlcatalog.load(
                    'randomdistribution/Normal', 'NormalDistribution'),
                properties={'mean': 1.0, 'variance': 0.25})), un.nA)

        random_wmax = un.Quantity(RandomValue(
            RandomDistributionProperties(
                name="normal",
                definition=ninemlcatalog.load(
                    'randomdistribution/Normal', 'NormalDistribution'),
                properties={'mean': 2.0, 'variance': 0.5})))

        static = DynamicsProperties(
            name="StaticProps",
            definition=static_cls,
            properties={'weight': random_weight})

        stdp = DynamicsProperties(name="StdpProps", definition=stdp_cls,
                                  properties={'tauLTP': 10 * un.ms,
                                              'aLTD': 1,
                                              'wmax': random_wmax,
                                              'muLTP': 3,
                                              'tauLTD': 20 * un.ms,
                                              'aLTP': 4})

        cell1 = DynamicsProperties(
            name="Pop1Props",
            definition=cell1_cls,
            properties={'P1': 10 * un.ms,
                        'P2': 100 * un.uF,
                        'P3': -50 * un.mV})

        cell2 = DynamicsProperties(
            name="Pop2Props",
            definition=cell2_cls,
            properties={'P1': 20 * un.ms * un.mV,
                        'P2': 50 * un.uF,
                        'P3': -40 * un.mV,
                        'P4': -20 * un.mV})

        cell3 = DynamicsProperties(
            name="Pop3Props",
            definition=cell1_cls,
            properties={'P1': 30 * un.ms,
                        'P2': 50 * un.pF,
                        'P3': -20 * un.mV})

        # =====================================================================
        # Populations and Projections
        # =====================================================================

        pop1 = Population(
            name="Pop1",
            size=10,
            cell=cell1)

        pop2 = Population(
            name="Pop2",
            size=15,
            cell=cell2)

        pop3 = Population(
            name="Pop3",
            size=20,
            cell=cell3)

        proj1 = Projection(
            name="Proj1",
            pre=pop1, post=pop2, response=inh, plasticity=static,
            connectivity=self.all_to_all,
            port_connections=[
                ('pre', 'spike', 'response', 'spike'),
                ('response', 'i', 'post', 'i_ext'),
                ('plasticity', 'fixed_weight', 'response', 'weight')],
            delay=self.delay)

        proj2 = Projection(
            name="Proj2",
            pre=pop2, post=pop1, response=exc, plasticity=static,
            connectivity=self.all_to_all,
            port_connections=[
                ('pre', 'spike', 'response', 'spike'),
                ('pre', 'double_spike', 'response', 'double_spike'),
                ('response', 'i', 'post', 'i_ext'),
                ('plasticity', 'fixed_weight', 'response', 'weight')],
            delay=self.delay)

        proj3 = Projection(
            name="Proj3",
            pre=pop3, post=pop2, response=exc, plasticity=stdp,
            connectivity=self.all_to_all,
            port_connections=[
                ('pre', 'spike', 'response', 'spike'),
                ('response', 'i', 'post', 'i_ext'),
                ('plasticity', 'wsyn_current', 'response', 'weight'),
                ('pre', 'spike', 'plasticity', 'incoming_spike')],
            delay=self.delay)

        proj4 = Projection(
            name="Proj4",
            pre=pop3, post=pop1, response=exc, plasticity=static,
            connectivity=self.all_to_all,
            port_connections=[
                ('pre', 'spike', 'response', 'spike'),
                ('response', 'i', 'post', 'i_ext'),
                ('plasticity', 'fixed_weight', 'response', 'weight')],
            delay=self.delay)

        # =====================================================================
        # Construct the Network
        # =====================================================================

        network = Network(
            name="Net",
            populations=(pop1, pop2, pop3),
            projections=(proj1, proj2, proj3, proj4))

        # =====================================================================
        # Create expected dynamics arrays
        # =====================================================================

        dyn_array1 = ComponentArray(
            "Pop1", pop1.size,
            DynamicsWithSynapsesProperties(
                MultiDynamicsProperties(
                    "Pop1",
                    sub_components={
                        'cell': cell1,
                        'Proj2': MultiDynamicsProperties(
                            name='Proj2_syn',
                            sub_components={'psr': exc, 'pls': static},
                            port_connections=[
                                ('pls', 'fixed_weight', 'psr', 'weight')],
                            port_exposures=[
                                ('psr', 'i'),
                                ('psr', 'spike'),
                                ('psr', 'double_spike')]),
                        'Proj4': MultiDynamicsProperties(
                            name='Proj4_syn',
                            sub_components={'psr': exc, 'pls': static},
                            port_connections=[
                                ('pls', 'fixed_weight', 'psr', 'weight')],
                            port_exposures=[
                                ('psr', 'i'),
                                ('psr', 'spike')])},
                    port_connections=[
                        ('Proj2', 'i__psr', 'cell', 'i_ext'),
                        ('Proj4', 'i__psr', 'cell', 'i_ext')],
                    port_exposures=[
                        ('cell', 'spike'),
                        ('Proj2', 'double_spike__psr'),
                        ('Proj2', 'spike__psr'),
                        ('Proj4', 'spike__psr')]),
                connection_property_sets=[
                    ConnectionPropertySet(
                        'spike__psr__Proj2',
                        [Property('weight__pls__Proj2', random_weight)]),
                    ConnectionPropertySet(
                        'double_spike__psr__Proj2',
                        [Property('weight__pls__Proj2', random_weight)]),
                    ConnectionPropertySet(
                        'spike__psr__Proj4',
                        [Property('weight__pls__Proj4', random_weight)])]))

        dyn_array2 = ComponentArray(
            "Pop2", pop2.size,
            DynamicsWithSynapsesProperties(
                MultiDynamicsProperties(
                    "Pop2",
                    sub_components={
                        'cell': cell2,
                        'Proj1': MultiDynamicsProperties(
                            name='Proj1_syn',
                            sub_components={'psr': inh, 'pls': static},
                            port_connections=[
                                ('pls', 'fixed_weight', 'psr', 'weight')],
                            port_exposures=[
                                ('psr', 'i'),
                                ('psr', 'spike')]),
                        'Proj3': MultiDynamicsProperties(
                            name='Proj3_syn',
                            sub_components={'psr': exc, 'pls': stdp},
                            port_connections=[
                                ('pls', 'wsyn_current', 'psr', 'weight')],
                            port_exposures=[
                                ('psr', 'i'),
                                ('psr', 'spike'),
                                ('pls', 'incoming_spike')])},
                    port_connections=[
                        ('Proj1', 'i__psr', 'cell', 'i_ext'),
                        ('Proj3', 'i__psr', 'cell', 'i_ext')],
                    port_exposures=[
                        ('cell', 'spike'),
                        ('cell', 'double_spike'),
                        ('Proj1', 'spike__psr'),
                        ('Proj3', 'spike__psr'),
                        ('Proj3', 'incoming_spike__pls')]),
                connection_property_sets=[
                    ConnectionPropertySet(
                        'spike__psr__Proj1',
                        [Property('weight__pls__Proj1', random_weight)]),
                    ConnectionPropertySet(
                        'incoming_spike__pls__Proj3',
                        [Property('wmax__pls__Proj3', random_wmax)])]))

        dyn_array3 = ComponentArray(
            "Pop3", pop3.size,
            DynamicsWithSynapsesProperties(
                MultiDynamicsProperties(
                    'Pop3',
                    sub_components={'cell': cell3},
                    port_exposures=[('cell', 'spike')],
                    port_connections=[])))

        conn_group1 = EventConnectionGroup(
            'Proj1__pre__spike__synapse__spike__psr', 'Pop1',
            'Pop2', 'spike__cell', 'spike__psr__Proj1',
            Connectivity(self.all_to_all, pop1, pop2), self.delay)

        conn_group2 = EventConnectionGroup(
            'Proj2__pre__spike__synapse__spike__psr', 'Pop2',
            'Pop1', 'spike__cell', 'spike__psr__Proj2',
            Connectivity(self.all_to_all, pop2, pop1), self.delay)

        conn_group3 = EventConnectionGroup(
            'Proj2__pre__double_spike__synapse__double_spike__psr',
            'Pop2', 'Pop1', 'double_spike__cell',
            'double_spike__psr__Proj2',
            Connectivity(self.all_to_all, pop2, pop1), self.delay)

        conn_group4 = EventConnectionGroup(
            'Proj3__pre__spike__synapse__spike__psr', 'Pop3',
            'Pop2', 'spike__cell', 'spike__psr__Proj3',
            Connectivity(self.all_to_all, pop3, pop2), self.delay)

        conn_group5 = EventConnectionGroup(
            'Proj3__pre__spike__synapse__incoming_spike__pls',
            'Pop3', 'Pop2', 'spike__cell', 'incoming_spike__pls__Proj3',
            Connectivity(self.all_to_all, pop3, pop2), self.delay)

        conn_group6 = EventConnectionGroup(
            'Proj4__pre__spike__synapse__spike__psr', 'Pop3',
            'Pop1', 'spike__cell', 'spike__psr__Proj4',
            Connectivity(self.all_to_all, pop3, pop1), self.delay)

        # =====================================================================
        # Test equality between network automatically generated dynamics arrays
        # and manually generated expected one
        # =====================================================================
        (component_arrays,
         connection_groups) = BasePype9Network._flatten_to_arrays_and_conns(
            network)

        self.assertEqual(
            component_arrays['Pop1'], dyn_array1,
            "Mismatch between generated and expected dynamics arrays:\n {}"
            .format(component_arrays['Pop1'].find_mismatch(dyn_array1)))
        self.assertEqual(
            component_arrays['Pop2'], dyn_array2,
            "Mismatch between generated and expected dynamics arrays:\n {}"
            .format(component_arrays['Pop2'].find_mismatch(dyn_array2)))
        self.assertEqual(
            component_arrays['Pop3'], dyn_array3,
            "Mismatch between generated and expected dynamics arrays:\n {}"
            .format(component_arrays['Pop3'].find_mismatch(dyn_array3)))
        # =====================================================================
        # Test equality between network automatically generated connection
        # groups and manually generated expected ones
        # =====================================================================
        self.assertEqual(
            connection_groups[
                'Proj1__pre__spike__synapse__spike__psr'],
            conn_group1,
            "Mismatch between generated and expected connection groups:\n {}"
            .format(
                connection_groups['Proj1__pre__spike__synapse__spike__psr']
                .find_mismatch(conn_group1)))
        self.assertEqual(
            connection_groups['Proj2__pre__spike__synapse__spike__psr'],
            conn_group2,
            "Mismatch between generated and expected connection groups:\n {}"
            .format(
                connection_groups['Proj2__pre__spike__synapse__spike__psr']
                .find_mismatch(conn_group2)))
        self.assertEqual(
            connection_groups[
                'Proj2__pre__double_spike__synapse__double_spike__psr'],
            conn_group3,
            "Mismatch between generated and expected connection groups:\n {}"
            .format(
                connection_groups[
                    'Proj2__pre__double_spike__synapse__double_spike__psr']
                .find_mismatch(conn_group3)))
        self.assertEqual(
            connection_groups[
                'Proj3__pre__spike__synapse__spike__psr'],
            conn_group4,
            "Mismatch between generated and expected connection groups:\n {}"
            .format(
                connection_groups[
                    'Proj3__pre__spike__synapse__spike__psr']
                .find_mismatch(conn_group4)))
        self.assertEqual(
            connection_groups[
                'Proj3__pre__spike__synapse__incoming_spike__pls'],
            conn_group5,
            "Mismatch between generated and expected connection groups:\n {}"
            .format(
                connection_groups[
                    'Proj3__pre__spike__synapse__incoming_spike__pls']
                .find_mismatch(conn_group5)))
        self.assertEqual(
            connection_groups[
                'Proj4__pre__spike__synapse__spike__psr'],
            conn_group6,
            "Mismatch between generated and expected connection groups:\n {}"
            .format(
                connection_groups[
                    'Proj4__pre__spike__synapse__spike__psr']
                .find_mismatch(conn_group6)))


if __name__ == '__main__':
    import argparse
    import logging
    import sys

    pyNN_logger = logging.Logger('PyNN')
    pyNN_logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    pyNN_logger.addHandler(ch)

    parser = argparse.ArgumentParser()
    parser.add_argument('--test', type=str, default='test_compare_brunel',
                        help="Switch between different tests to run")
    parser.add_argument('--tester', type=str, default='network',
                        help="Which tester to use")
    parser.add_argument('--build_mode', type=str, default='force',
                        help="The build mode with which to construct the "
                        "network")
    parser.add_argument('--option', nargs=2, type=str, action='append',
                        default=[],
                        help="Extra options that are passed to the test")
    args = parser.parse_args()
    options = dict(args.option)
    if args.tester == 'network':
        tester = TestNetwork()
    elif args.tester == 'brunel':
        tester = TestBrunel2000()
    else:
        raise Exception("Unrecognised tester '{}'".format(args.tester))
    getattr(tester, args.test)(build_mode=args.build_mode, **options)
