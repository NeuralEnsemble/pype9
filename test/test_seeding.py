from __future__ import division
from itertools import chain
import ninemlcatalog
import numpy
import logging
import sys
from nineml import units as un, Property
from pype9.simulate.neuron import (
    CellMetaClass as NeuronCellMetaClass, Network as NeuronNetwork,
    Simulation as NeuronSimulation)
from pype9.simulate.nest import (
    CellMetaClass as NESTCellMetaClass, Network as NESTNetwork,
    Simulation as NESTSimulation)
from pype9.simulate.neuron import Simulation
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport

logger = logging.getLogger('PyPe9')
logger.setLevel(logging.INFO)
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
        brunel_model.population('Ext').cell['rate'] = 300 / un.s
        for Network, Simulation in (
            (NeuronNetwork, NeuronSimulation),
                (NESTNetwork, NESTSimulation)):
            with Simulation(dt=0.01 * un.ms, seed=1) as sim:
                network1 = Network(brunel_model)
                network1.component_array('Ext').record('spike_output')
                print "Sim 1 - prop: {}, dyn: {}, global: {}".format(
                    sim.all_properties_seeds, sim.all_dynamics_seeds,
                    sim.global_seed)
                sim.run(20 * un.ms)
            ext1_spikes = network1.component_array(
                'Ext').recording('spike_output')
            exc1_conns = network1.connection_group('Excitation').get(
                ['weight', 'delay'], 'list')
            with Simulation(dt=0.01 * un.ms, seed=1) as sim:
                network2 = Network(brunel_model)
                network2.component_array('Ext').record('spike_output')
                print "Sim 2 - prop: {}, dyn: {}, global: {}".format(
                    sim.all_properties_seeds, sim.all_dynamics_seeds,
                    sim.global_seed)
                sim.run(20 * un.ms)
            ext2_spikes = network2.component_array(
                'Ext').recording('spike_output')
            exc2_conns = network2.connection_group('Excitation').get(
                ['weight', 'delay'], 'list')
            with Simulation(dt=0.01 * un.ms, seed=2) as sim:
                network3 = Network(brunel_model)
                network3.component_array('Ext').record('spike_output')
                print "Sim 3 - prop: {}, dyn: {}, global: {}".format(
                    sim.all_properties_seeds, sim.all_dynamics_seeds,
                    sim.global_seed)
                sim.run(20 * un.ms)
            ext3_spikes = network3.component_array(
                'Ext').recording('spike_output')
            exc3_conns = network3.connection_group('Excitation').get(
                ['weight', 'delay'], 'list')
            with Simulation(dt=0.01 * un.ms, properties_seed=1) as sim:
                network4 = Network(brunel_model)
                network4.component_array('Ext').record('spike_output')
                print "Sim 4 - prop: {}, dyn: {}, global: {}".format(
                    sim.all_properties_seeds, sim.all_dynamics_seeds,
                    sim.global_seed)
                sim.run(20 * un.ms)
            ext4_spikes = network4.component_array(
                'Ext').recording('spike_output')
            exc4_conns = network4.connection_group('Excitation').get(
                ['weight', 'delay'], 'list')
            self.assertEqual(exc1_conns, exc2_conns,
                             "Network External connections not the same "
                             "despite using the same seed")
            self.assertEqual(list(chain(*ext1_spikes.spiketrains)),
                             list(chain(*ext2_spikes.spiketrains)),
                             "Network Exc spikes not the same despite using "
                             "the same seed")
            self.assertNotEqual(exc1_conns, exc3_conns,
                                "Network External connections the same despite"
                                " using different seeds")
            self.assertNotEqual(list(chain(*ext1_spikes.spiketrains)),
                                list(chain(*ext3_spikes.spiketrains)),
                                "Network Exc spikes the same despite using "
                                "different  seeds")
            self.assertEqual(exc1_conns, exc4_conns,
                             "Network 4 External connections different despite"
                             " using the same properties seeds")
            self.assertNotEqual(list(chain(*ext1_spikes.spiketrains)),
                                list(chain(*ext4_spikes.spiketrains)),
                                "Network Exc spikes the same despite using "
                                "different seeds:\n{}\n{}".format(
                                    list(chain(*ext1_spikes.spiketrains)),
                                    list(chain(*ext4_spikes.spiketrains))))

    def _load_brunel(self, case, order):
        model = ninemlcatalog.load('network/Brunel2000/' + case).as_network(
            'Brunel_{}'.format(case))
        # Don't clone so that the url is not reset
        model = model.clone()
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


if __name__ == '__main__':
    tester = TestSeeding()
    if sys.argv[1] == 'array':
        tester.test_component_array_seed()
    elif sys.argv[1] == 'network':
        tester.test_network_seed()
    else:
        assert False
