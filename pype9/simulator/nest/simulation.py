import nineml.units as un
from pype9.simulator.base.simulation import BaseSimulation
from pyNN.nest import (
    setup as pyNN_setup, run as pyNN_run, end as pyNN_end, state as pyNN_state)
from pype9.exceptions import Pype9UsageError


class Simulation(BaseSimulation):
    """Represent the simulator state."""

    _active = None
    name = 'NEST'

    DEFAULT_MAX_DELAY = 10 * un.ms

    def __init__(self, *args, **kwargs):
        self._device_delay = kwargs.get('device_delay', None)
        self._threads_per_proc = kwargs.get('threads_per_proc', 1)
        super(Simulation, self).__init__(*args, **kwargs)

    @property
    def device_delay(self):
        if self.min_delay is not None:
            return self.min_delay
        else:
            return self.dt * 2

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
        pyNN_run(t_stop.in_units(un.ms), callbacks=callbacks)

    def _prepare(self, **kwargs):
        "Reset the simulation and prepare it for creating new cells/networks"
        if self._min_delay is None:
            if self.num_threads() == 1:
                min_delay = self.device_delay
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
                   max_delay=float(max_delay.in_units(un.ms)), **kwargs)

    def _initialise(self, **kwargs):
        """
        Just in time initialisations that are performed before the simulation
        starts running.
        """
        # Initialisation is handled by NEST

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
        return self.num_processes() * self._threads_per_proc


def simulation(*args, **kwargs):
    return Simulation(*args, **kwargs)
