import logging
import os.path
from nineml import units as un
import ctypes
from pyNN.neuron import (
    setup as pyNN_setup, run as pyNN_run, end as pyNN_end, state as pyNN_state)
from nineml.units import Quantity
from pype9.simulator.base.simulation import BaseSimulation
from pype9.simulator.neuron.cells.code_gen import CodeGenerator
from pype9.exceptions import Pype9UsageError

logger = logging.getLogger('PyPe9')


class Simulation(BaseSimulation):
    """
    This is adapted from the code for the simulation controller in PyNN for
    use with individual cell objects
    """

    _active = None
    name = 'Neuron'

    DEFAULT_MAX_DELAY = 10 * un.ms

    def __init__(self, *args, **kwargs):
        super(Simulation, self).__init__(*args, **kwargs)

    def _run(self, t_stop, callbacks=None, **kwargs):  # @UnusedVariable
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
        pyNN_run(float(Quantity(t_stop, 'ms')), callbacks=callbacks)

    def _prepare(self, **kwargs):
        "Reset the simulation and prepare it for creating new cells/networks"
        if self._min_delay is None:
            if self.num_threads() == 1:
                min_delay = self.dt * 2
            else:
                raise Pype9UsageError(
                    "Min delay needs to be set for NEST simulator if using "
                    "more than one thread")
        else:
            min_delay = self._min_delay
        if self._max_delay is None:
            if self.num_threads() == 1:
                max_delay = self.DEFAULT_MAX_DELAY
            else:
                raise Pype9UsageError(
                    "Max delay needs to be set for NEST simulator if using "
                    "more than one thread")
        else:
            max_delay = self._max_delay
        pyNN_setup(timestep=float(self.dt.in_units(un.ms)),
                   min_delay=float(min_delay.in_units(un.ms)),
                   max_delay=float(max_delay.in_units(un.ms)),
                   **kwargs)

    def _initialise(self):
        """
        Just in time initialisations that are performed before the simulation
        starts running.
        """
        if self._has_random_processes():
            self._seed_libninemlnrn()
        for cell in self._registered_cells:
            cell._initialise()
        # Initialisation of cells within PyNN arrays is handled by PyNN

    def _exit(self):
        """Final things that need to be done before the simulation exits"""
        pyNN_end()

    def mpi_rank(self):
        "The rank of the MPI node the code is running on"
        return pyNN_state.mpi_rank

    def num_processes(self):
        "The number of MPI processes"
        return pyNN_state.num_processes

    def num_threads(self):
        "The total number of threads across all MPI nodes"
        return self.num_processes()

    def _has_random_processes(self):
        for cell in self._registered_cells:
            if cell.component_class.has_random_processes:
                return True
        for array in self._registered_arrays:
            if array.component_class.has_random_processes:
                return True
        return False

    def _seed_libninemlnrn(self):
        """
        Sets the random seed used by libninemlnrn to generate random
        distributions
        """
        libninemlnrn = ctypes.CDLL(
            os.path.join(CodeGenerator.LIBNINEMLNRN_PATH, 'libninemlnrn.so'))
        libninemlnrn.nineml_seed_gsl_rng(self.seed)


def simulation(*args, **kwargs):
    return Simulation(*args, **kwargs)
