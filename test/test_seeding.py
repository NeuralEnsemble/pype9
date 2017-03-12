from unittest import TestCase
import ninemlcatalog
from nineml import units as un
from pype9.simulator.neuron import CellMetaClass
from pype9.simulator.neuron import Simulation


class TestSeeding(TestCase):

    def test_seed(self):
        poisson_model = ninemlcatalog.load('//input/Poisson#Poisson')
        Poisson = CellMetaClass(poisson_model, name='PoissonTest')
        with Simulation(dt=0.01 * un.ms, seed=1) as sim:
            poisson1 = Poisson(rate=300 / un.s)
            poisson1.set_state({'t_next': 5 * un.ms})
            poisson1.record('spike_output')
            sim.run(100 * un.ms)
        cell1_rec = cell.recording('spike_output')
