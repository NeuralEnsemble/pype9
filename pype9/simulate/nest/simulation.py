import nineml.units as un
from pype9.simulate.common.simulation import Simulation as BaseSimulation
from pyNN.nest import (
    setup as pyNN_setup, run as pyNN_run, state as pyNN_state, end as pyNN_end)
from pype9.exceptions import Pype9UsageError


class Simulation(BaseSimulation):
    """Represent the simulator state."""

    _active = None
    name = 'NEST'

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
        callbacks : function
            A function callback to allow the update of external objects (e.g.
            progress bar) during the simulation.
        """
        pyNN_run(float(t_stop.in_units(un.ms)), callbacks=callbacks)

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
                   max_delay=float(max_delay.in_units(un.ms)),
                   grng_seed=self.global_seed,
                   rng_seeds=self.all_dynamics_seeds, **kwargs)

    def mpi_rank(self):
        "The rank of the MPI node the code is running on"
        return pyNN_state.mpi_rank

    def num_processes(self):
        "The number of MPI processes"
        return pyNN_state.num_processes

    def num_threads(self):
        "The total number of threads across all MPI nodes"
        return self.num_processes() * self._threads_per_proc

    @classmethod
    def quit(cls):
        "Gracefully quit the simulator"
        pyNN_end()
