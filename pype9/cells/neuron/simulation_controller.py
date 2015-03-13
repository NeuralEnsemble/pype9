from neuron import h
import quantities as pq
import weakref
import numpy
import logging

logger = logging.getLogger('PyPe9')


class _SimulationController(object):
    """
    This is adapted from the code for the simulation controller in PyNN for
    use with individual cell objects
    """

    def __init__(self):
        self.running = False
        self.registered_cells = []
        self._time = h.Vector()

    def initialize(self):
        self.running = True
        self.reset()

    def finalize(self):
        logger.info("Finishing up with NEURON.")
        h.quit()

    @property
    def time(self):
        return pq.Quantity(self._time, 'ms')

    def register_cell(self, cell):
        self.registered_cells.append(weakref.ref(cell))

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
        # Convert simulation time to float value in ms
        simulation_time = float(pq.Quantity(simulation_time, 'ms'))
        for _ in numpy.arange(h.dt, simulation_time + h.dt, h.dt):
            h.fadvance()
        self.tstop += simulation_time

    def reset(self):
        h.finitialize(-65.0)
        for cell_ref in reversed(self.registered_cells):
            if cell_ref():
                cell_ref().memb_init()
                cell_ref().reset_recordings()
            else:
                # If the cell has been deleted remove the weak reference to it
                self.registered_cells.remove(cell_ref)
        self.tstop = 0

# Make a singleton instantiation of the simulation controller
simulation_controller = _SimulationController()
del _SimulationController
