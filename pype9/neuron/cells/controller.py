from neuron import h
import quantities as pq
import numpy
import logging
from pype9.base.cells.controller import SimulationController

logger = logging.getLogger('PyPe9')


class _SimulationController(SimulationController):
    """
    This is adapted from the code for the simulation controller in PyNN for
    use with individual cell objects
    """

    instance_counter = 0

    def __init__(self):
        super(_SimulationController, self).__init__()
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
            atol=None):
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
        self.running = True
        # Convert simulation time to float value in ms
        simulation_time = float(pq.Quantity(simulation_time, 'ms'))
        for _ in numpy.arange(h.dt, simulation_time + h.dt, h.dt):
            h.fadvance()
        self.tstop += simulation_time

    def reset(self):
        h.finitialize(-65.0)
        self.reset_cells()
        self.tstop = 0.0

# Make a singleton instantiation of the simulation controller
simulation_controller = _SimulationController()
