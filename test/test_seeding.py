from __future__ import division
from unittest import TestCase
import ninemlcatalog
from copy import deepcopy
import numpy
from nineml import units as un, Property
from pype9.simulator.neuron import (
    CellMetaClass as NeuronCellMetaClass, Network as NeuronNetwork,
    Simulation as NeuronSimulation)
from pype9.simulator.nest import (
    CellMetaClass as NESTCellMetaClass, Network as NESTNetwork,
    Simulation as NESTSimulation)
from pype9.simulator.neuron import Simulation
import logging
import sys

logger = logging.getLogger('PyPe9')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class TestSeeding(TestCase):

    def test_cell_seed(self):
        poisson_model = ninemlcatalog.load('input/Poisson#Poisson')
        for CellMetaClass, Simulation in (
            (NeuronCellMetaClass, NeuronSimulation),
                (NESTCellMetaClass, NESTSimulation)):
            Poisson = CellMetaClass(poisson_model, name='PoissonTest')
            rate = 300 / un.s
            t_next = 0.0 * un.s
            with Simulation(dt=0.01 * un.ms, seed=1) as sim:
                poisson1 = Poisson(rate=rate, t_next=t_next)
                poisson1.record('spike_output')
                sim.run(100 * un.ms)
            poisson1_spikes = poisson1.recording('spike_output')
            with Simulation(dt=0.01 * un.ms, seed=1) as sim:
                poisson2 = Poisson(rate=rate, t_next=t_next)
                poisson2.record('spike_output')
                sim.run(100 * un.ms)
            poisson2_spikes = poisson2.recording('spike_output')
            with Simulation(dt=0.01 * un.ms, seed=2) as sim:
                poisson3 = Poisson(rate=rate, t_next=t_next)
                poisson3.record('spike_output')
                sim.run(100 * un.ms)
            poisson3_spikes = poisson3.recording('spike_output')
            self.assertEqual(list(poisson1_spikes), list(poisson2_spikes),
                             "Poisson spike train not the same despite using "
                             "the same seed")
            self.assertNotEqual(list(poisson1_spikes), list(poisson3_spikes),
                                "Poisson spike train the same despite using "
                                "different  seeds")

    def test_network_seed(self):
        brunel_model = self._load_brunel('AI', 1)
        for Network, Simulation in (
            (NeuronNetwork, NeuronSimulation),
                (NESTNetwork, NESTSimulation)):
            with Simulation(dt=0.01 * un.ms, seed=1) as sim:
                network1 = Network(brunel_model)
                network1.component_array('Exc').record('spike_output')
                sim.run(20 * un.ms)
            exc1_spikes = network1.component_array(
                'Exc').recording('spike_output')
            with Simulation(dt=0.01 * un.ms, seed=1) as sim:
                network2 = Network(brunel_model)
                network2.component_array('Exc').record('spike_output')
                sim.run(20 * un.ms)
            exc2_spikes = network2.component_array(
                'Exc').recording('spike_output')
            with Simulation(dt=0.01 * un.ms, seed=2) as sim:
                network3 = Network(brunel_model)
                network3.component_array('Exc').record('spike_output')
                sim.run(20 * un.ms)
            exc3_spikes = network3.component_array(
                'Exc').recording('spike_output')
            self.assertEqual(list(exc1_spikes.spiketrains[0]),
                             list(exc2_spikes.spiketrains[0]),
                             "Network Exc spikes not the same despite using "
                             "the same seed")
            self.assertNotEqual(list(exc1_spikes.spiketrains[0]),
                                list(exc3_spikes.spiketrains[0]),
                                "Network Exc spikes the same despite using "
                                "different  seeds")

    def _load_brunel(self, case, order):
        model = ninemlcatalog.load('network/Brunel2000/' + case).as_network(
            'Brunel_{}'.format(case))
        # Don't clone so that the url is not reset
        model = deepcopy(model)
        scale = order / model.population('Inh').size
        # rescale populations
        for pop in model.populations:
            pop.size = int(numpy.ceil(pop.size * scale))
        for proj in (model.projection('Excitation'),
                     model.projection('Inhibition')):
            props = proj.connectivity.rule_properties
            number = props.property('number')
            props.set(Property(
                number.name,
                int(numpy.ceil(float(number.value) * scale)) * un.unitless))
        return model
