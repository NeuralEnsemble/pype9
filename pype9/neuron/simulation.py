from neuron import h
import quantities as pq
import numpy
import logging
from pyNN.neuron.simulator import _State as PyNNState
from pype9.base.simulation import BaseSimulation
from pype9.neuron.cells.code_gen import CodeGenerator
import os.path
import ctypes
from binascii import hexlify

logger = logging.getLogger('PyPe9')


class Simulation(BaseSimulation, PyNNState):
    """
    This is adapted from the code for the simulation controller in PyNN for
    use with individual cell objects
    """

    instance_counter = 0

    def __init__(self):
        super(Simulation, self).__init__()
        self._time = h.Vector()

    def finalize(self):
        logger.info("Finishing up with NEURON.")
        h.quit()

    @property
    def dt(self):
        return h.dt

    @property
    def time(self):
        return pq.Quantity(self._time, 'ms')

    def run(self, simulation_time, reset=True, timestep='cvode', rtol=None,
            atol=None, random_seed=None):
        """
        Run the simulation for a certain time.
        """
        self._time.record(h._ref_t)
        if timestep == 'cvode':
            self.cvode = h.CVode()
            if rtol is not None:
                self.cvode.rtol = rtol
            if atol is not None:
                self.cvode.atol = atol
        else:
            h.dt = timestep
        if reset or not self.running:
            self.initialize()
        self.seed_rng(random_seed)
        self.running = True
        # Convert simulation time to float value in ms
        simulation_time = float(pq.Quantity(simulation_time, 'ms'))
        for _ in numpy.arange(h.dt, simulation_time + h.dt, h.dt):
            h.fadvance()
        self.tstop += simulation_time

    def reset(self):
        self.reset_cells()  # Needs to set before initialise for the init block
        h.finitialize()
        self.reset_cells()  # Just in case the voltage needs updating
        self.tstop = 0.0

    def clear(self, **kwargs):  # @UnusedVariable
        pass  # TODO: Need to look into whether it is possible to remove cells

    def seed_rng(self, seed=None):
        if seed is None:
            seed = int(hexlify(os.urandom(4)), 16)
        libninemlnrn = ctypes.CDLL(
            os.path.join(CodeGenerator.LIBNINEMLNRN_PATH, 'libninemlnrn.so'))
        libninemlnrn.nineml_seed_gsl_rng(seed)

# Make a singleton instantiation of the simulation controller
controller = _Controller()
