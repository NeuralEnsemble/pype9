from __future__ import division
from unittest import TestCase
from math import exp
import neo
from collections import namedtuple, defaultdict
from itertools import groupby
from operator import itemgetter
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
import ninemlcatalog
try:
    from matplotlib.pyplot import plt
except ImportError:
    pass


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


class TestBrunel2000(TestCase):

    delay = 1.5 * un.ms

    brunel_parameters = {
        "SR": {"g": 3.0, "eta": 2.0},
        "SR2": {"g": 2.0, "eta": 2.0},
        "SR3": {"g": 0.0, "eta": 2.0},
        "small_SR3": {"g": 0.0, "eta": 2.0},
        "SIfast": {"g": 6.0, "eta": 4.0},
        "AI": {"g": 5.0, "eta": 2.0},
        "SIslow": {"g": 4.5, "eta": 0.9},
        "SIslow": {"g": 4.5, "eta": 0.95}}

    simtime = 100.0
    order = 2500

    pop_names = ('Exc', 'Inh', 'Ext')

#     ref29ml_param_map = {
#         "C_m": CMem,
#         "tau_m": tauMem,
#         "tau_syn_ex": tauSyn,
#         "tau_syn_in": tauSyn,
#         "t_ref": 2.0,
#         "E_L": 0.0,
#         "V_reset": 0.0,
#         "V_m": 0.0,
#          "V_th": theta}

    dt = 0.1 * un.ms    # the resolution in ms

    BrunelNetwork = namedtuple(
        'BrunelNetwork',
        'exc inh ext espikes ispikes xspikes N_rec N_neurons CE CI')

    def setUp(self):
        self.ref_network = self._construct_ref_nest_brunel('small_SR3',
                                                           order=self.order)
        self.ref_spikes = self._simulate_ref_brunel(self.ref_network,
                                                    simtime=self.simttime)

    def test_flatten(self, **kwargs):  # @UnusedVariable
        brunel_network = ninemlcatalog.load('network/Brunel2000/AI/')
        (component_arrays,
         connection_groups) = BasePype9Network._flatten_to_arrays_and_conns(
            brunel_network)
        self.assertEqual(len(component_arrays), 3)
        self.assertEqual(len(connection_groups), 3)

    def test_nest(self, build_mode='force', case='small_SR3', plot=False,
                  **kwargs):  # @UnusedVariable @IgnorePep8
        pyNN.nest.setup(timestep=0.1, min_delay=0.1, max_delay=10.0)
        nest.ResetKernel()
        nest.SetKernelStatus(
            {"resolution": float(self.dt.value), "print_time": True,
             'local_num_threads': 1})
        network9ML = ninemlcatalog.load('network/Brunel2000/' + case)
        network_nineml = Network.from_document(network9ML)
        network = NestPype9Network(network_nineml, min_delay=0.1,
                                   max_delay=2.0, build_mode=build_mode)
        for pop_name in self.pop_names:
            network.component_array(pop_name).record('spikes')
        pyNN.nest.run(self.simtime)
        spikes = {}
        for pop_name in self.pop_names:
            spikes[pop_name] = network.component_array(pop_name).get_data()
            if plot:
                fig = plt.figure()
                fig.plot(ts1, gids, 'blue')
                plt.xlabel('Times (ms)')
                plt.ylabel('Cell Indices')
        if plot:
            plt.show()

    def test_neuron(self):
        pyNN.neuron.setup(timestep=0.1, min_delay=0.1, max_delay=10.0)

#                 self.assertEqual(network.component_array('Exc').size,
#                                  nest.GetStatus(ref_network.exc, 'size'))
#             print("Number of neurons : {0}".format(N_neurons))
#             print("Number of synapses: {0}".format(num_synapses))
#             print("       Exitatory  : {0}".format(
#                 int(CE * N_neurons) + N_neurons))
#             print("       Inhibitory : {0}".format(int(CI * N_neurons)))

    @classmethod
    def _construct_ref_nest_brunel(cls, case, order=2500):
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
        g = cls.brunel_parameters[case]["g"]
        eta = cls.brunel_parameters[case]["eta"]
        epsilon = 0.1  # connection probability

        NE = 4 * order
        NI = 1 * order
        N_neurons = NE + NI
        N_rec = order

        CE = int(epsilon * NE)  # number of excitatory synapses per neuron
        CI = int(epsilon * NI)  # number of inhibitory synapses per neuron
        C_tot = int(CI + CE)  # total number of synapses per neuron

        # Initialize the parameters of the integrate and fire neuron
        tauSyn = 0.5
        tauMem = 20.0
        CMem = 250.0
        theta = 20.0
        J = 0.1  # postsynaptic amplitude in mV

        # normalize synaptic current so that amplitude of a PSP is J
        J_unit = cls._compute_normalised_psr(tauMem, CMem, tauSyn)
        J_ex = J / J_unit
        J_in = -g * J_ex

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

        nodes_ex = nest.Create("iaf_psc_alpha", NE)
        nodes_in = nest.Create("iaf_psc_alpha", NI)

        nest.SetDefaults("poisson_generator", {"rate": p_rate})
        noise = nest.Create("poisson_generator")

        espikes = nest.Create("spike_detector")
        ispikes = nest.Create("spike_detector")
        xspikes = nest.Create("spike_detector")

        nest.SetStatus(espikes, [{"label": "brunel-py-exc",
                                  "withtime": True,
                                  "withgid": True}])

        nest.SetStatus(ispikes, [{"label": "brunel-py-in",
                                  "withtime": True,
                                  "withgid": True}])

        nest.SetStatus(xspikes, [{"label": "brunel-py-ext",
                                  "withtime": True,
                                  "withgid": True}])

        print("Connecting devices")

        nest.CopyModel(
            "static_synapse", "excitatory", {
                "weight": J_ex, "delay": float(cls.delay.value)})
        nest.CopyModel(
            "static_synapse", "inhibitory", {
                "weight": J_in, "delay": float(cls.delay.value)})

        nest.Connect(noise, nodes_ex, 'all_to_all', "excitatory")
        nest.Connect(noise, nodes_in, 'all_to_all', "excitatory")

        nest.Connect(nodes_ex[:N_rec], espikes, syn_spec="excitatory")
        nest.Connect(nodes_in[:N_rec], ispikes, syn_spec="excitatory")
        nest.Connect(noise[:N_rec], xspikes, syn_spec="excitatory")

        nest.Connect(
            range(
                NE + 1,
                NE + 1 + N_rec),
            ispikes,
            'all_to_all',
            "excitatory")
        # We now iterate over all neuron IDs, and connect the neuron to the
        # sources from our array. The first loop connects the excitatory
        # neurons and the second loop the inhibitory neurons.
        conn_params_ex = {'rule': 'fixed_indegree', 'indegree': CE}
        nest.Connect(
            nodes_ex,
            nodes_ex +
            nodes_in,
            conn_params_ex,
            "excitatory")

        conn_params_in = {'rule': 'fixed_indegree', 'indegree': CI}
        nest.Connect(
            nodes_in,
            nodes_ex +
            nodes_in,
            conn_params_in,
            "inhibitory")
        return cls.BrunelNetwork(nodes_ex, nodes_in, noise, espikes, ispikes,
                                 xspikes, N_rec, N_neurons, CE, CI)

    @classmethod
    def _simulate_ref_brunel(cls, network, simtime=1000.0):
        print("Simulating")
        nest.Simulate(simtime)
        events_ex = nest.GetStatus(network.espikes, "n_events")[0]
        events_in = nest.GetStatus(network.ispikes, "n_events")[0]
#         rate_ex = events_ex / simtime * 1000.0 / network.N_rec
#         rate_in = events_in / simtime * 1000.0 / network.N_rec
#         num_synapses = (nest.GetDefaults("excitatory")["num_connections"] +
#                         nest.GetDefaults("inhibitory")["num_connections"])
#         print("Brunel network simulation (Python)")
#         print("Number of neurons : {0}".format(network.N_neurons))
#         print("Number of synapses: {0}".format(num_synapses))
#         print("       Exitatory  : {0}".format(
#             int(network.CE * network.N_neurons) + network.N_neurons))
#         print("       Inhibitory : {0}".format(
#             int(network.CI * network.N_neurons)))
#         print("Excitatory rate   : %.2f Hz" % rate_ex)
#         print("Inhibitory rate   : %.2f Hz" % rate_in)
        spikes = defaultdict(dict)
        for pop_name in ('espikes', 'ispikes', 'xspikes'):
            events = nest.GetStatus(getattr(network, pop_name), "events")[0]
            for sender, sender_time_pairs in groupby(
                sorted(zip(events['senders'], events['times']),
                       key=itemgetter(0)), key=itemgetter(0)):
                spikes[pop_name][sender] = neo.SpikeTrain(
                    zip(*sender_time_pairs)[1], units='ms', t_stop=simtime)
        return spikes

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
                        help="Extra options that are passed to the test")
    args = parser.parse_args()
    options = dict(args.option)
    if args.tester == 'network':
        tester = TestNetwork(args.test)
    elif args.tester == 'brunel':
        tester = TestBrunel2000(args.test)
    else:
        raise Exception("Unrecognised tester '{}'".format(args.tester))
    getattr(tester, args.test)(build_mode=args.build_mode, **options)
