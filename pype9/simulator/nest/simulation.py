from nineml.units import Quantity
from pype9.simulator.base.simulation import BaseSimulation
from pyNN.nest import (
    setup as pyNN_setup, run as pyNN_run, end as pyNN_end, state as pyNN_state)


class Simulation(BaseSimulation):
    """Represent the simulator state."""

    _active = None

    def __init__(self, *args, **kwargs):
        super(Simulation, self).__init__(*args, **kwargs)
        self._device_delay = kwargs.get('device_delay', None)
        self._threads_per_proc = kwargs.get('threads_per_proc', 1)

    @property
    def device_delay(self):
        if self.min_delay is None:
            return self.min_delay
        else:
            return self.dt

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
        pyNN_setup(timestep=self.dt, min_delay=self.min_delay,
                   max_delay=self.max_delay, **kwargs)

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
