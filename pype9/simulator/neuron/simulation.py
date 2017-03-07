from neuron import h
import logging
import os.path
import ctypes
from pype9.simulator.base.simulation import BaseSimulation
from pype9.simulator.neuron.cells.code_gen import CodeGenerator

logger = logging.getLogger('PyPe9')


class Simulation(BaseSimulation):
    """
    This is adapted from the code for the simulation controller in PyNN for
    use with individual cell objects
    """

    _active = None

    def __init__(self, *args, **kwargs):
        super(Simulation, self).__init__(*args, **kwargs)
        self._time = h.Vector()

    def seed_rng(self, seed=None):
        libninemlnrn = ctypes.CDLL(
            os.path.join(CodeGenerator.LIBNINEMLNRN_PATH, 'libninemlnrn.so'))
        libninemlnrn.nineml_seed_gsl_rng(seed)

    def run(self, t_stop):  # @UnusedVariable
        """
        Run the simulation until time 't'. Typically won't be called explicitly
        as the __exit__ function will run the simulation until t_stop. However,
        it may be required if a state needs to be updated mid-way through the
        simulation.

        Parameters
        ----------
        t_stop : nineml.Quantity (time)
            The time to run the simulation until
        """

    def _prepare(self):
        "Reset the simulation and prepare it for creating new cells/networks"

    def _initialise(self):
        """
        Just in time initialisations that are performed before the simulation
        starts running.
        """

    def mpi_rank(self):
        "The rank of the MPI node the code is running on"

    def num_processes(self):
        "The number of MPI processes"

    def num_threads(self):
        "The total number of threads across all MPI nodes"

#     def finalize(self):
#         logger.info("Finishing up with NEURON.")
#         h.quit()
#
#     @property
#     def dt(self):
#         return h.dt
#
#     @property
#     def time(self):
#         return pq.Quantity(self._time, 'ms')
#
#     def run(self, simulation_time, reset=True, timestep='cvode', rtol=None,
#             atol=None, random_seed=None):
#         """
#         Run the simulation for a certain time.
#         """
#         self._time.record(h._ref_t)
#         if timestep == 'cvode':
#             self.cvode = h.CVode()
#             if rtol is not None:
#                 self.cvode.rtol = rtol
#             if atol is not None:
#                 self.cvode.atol = atol
#         else:
#             h.dt = timestep
#         if reset or not self.running:
#             self.initialize()
#         self.seed_rng(random_seed)
#         self.running = True
#         # Convert simulation time to float value in ms
#         simulation_time = float(pq.Quantity(simulation_time, 'ms'))
#         for _ in numpy.arange(h.dt, simulation_time + h.dt, h.dt):
#             h.fadvance()
#         self.tstop += simulation_time
#
#     def reset(self):
#         self.reset_cells()  # Needs to set before initialise for the init block
#         h.finitialize()
#         self.reset_cells()  # Just in case the voltage needs updating
#         self.tstop = 0.0
#
#     def clear(self, **kwargs):  # @UnusedVariable
#         pass  # TODO: Need to look into whether it is possible to remove cells


def simulation(*args, **kwargs):
    return Simulation(*args, **kwargs)
