import logging
import os.path
from nineml import units as un
import ctypes
from pyNN.neuron import (
    setup as pyNN_setup, run as pyNN_run, end as pyNN_end, state as pyNN_state)
from pyNN.neuron.simulator import initializer as pyNN_initializer
from pype9.simulate.common.simulation import Simulation as BaseSimulation
from pype9.simulate.neuron.cells.code_gen import CodeGenerator
from pype9.exceptions import Pype9UsageError

logger = logging.getLogger('PyPe9')


class Simulation(BaseSimulation):
    """
    This is adapted from the code for the simulation controller in PyNN for
    use with individual cell objects
    """

    _active = None
    name = 'Neuron'

    class _DummyID(object):

        def __init__(self, cell):
            self._cell = cell

    DEFAULT_MAX_DELAY = 10 * un.ms

    def __init__(self, *args, **kwargs):
        super(Simulation, self).__init__(*args, **kwargs)
        self._has_random_processes = False

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

    def _initialize(self):
        """
        Just in time initialisations that are performed before the simulation
        starts running.
        """
        if self._has_random_processes:
            self._seed_libninemlnrn()
        super(Simulation, self)._initialize()

    def mpi_rank(self):
        "The rank of the MPI node the code is running on"
        return pyNN_state.mpi_rank

    def num_processes(self):
        "The number of MPI processes"
        return pyNN_state.num_processes

    def num_threads(self):
        "The total number of threads across all MPI nodes"
        return self.num_processes()

    def register_cell(self, cell):
        super(Simulation, self).register_cell(cell)
        # The initial states of NMODL mechanism need to be set twice before and
        # after h.finitialize is called in order to set states that may be
        # required in the NET_RECEIVE block before finitialize and to set the
        # state variables in preparation for the simulation. Since the PyNN
        # initializer is called after finitialize, and the super method before,
        # so we make sure the cell is registered with both, when it is in
        # a PyNN population and independent.
        pyNN_initializer.register(self._DummyID(cell))
        if cell.component_class.is_random:
            self._has_random_processes = True

    def register_array(self, array):
        super(Simulation, self).register_array(array)
        if array.component_class.is_random:
            self._has_random_processes = True
        # The initial states of NMODL mechanism need to be set twice before and
        # after h.finitialize is called in order to set states that may be
        # required in the NET_RECEIVE block before finitialize and to set the
        # state variables in preparation for the simulation. Since the PyNN
        # initializer is called after finitialize, and the super method before,
        # so we make sure the cell is registered with both, when it is in
        # a PyNN population and independent.
        for id_ in array:
            self._registered_cells.append(id_._cell)

    def _seed_libninemlnrn(self):
        """
        Sets the random seed used by libninemlnrn to generate random
        distributions.
        """
        # Could be performed in __enter__ along with the setting of other seeds
        # but there is a problem loading the library with ctypes before it has
        # been loaded by the required mod files, so it is delayed until
        # initialisation
        libninemlnrn = ctypes.CDLL(
            os.path.join(CodeGenerator.LIBNINEMLNRN_PATH, 'libninemlnrn.so'))
        libninemlnrn.nineml_seed_gsl_rng(self.dynamics_seed)

    @classmethod
    def quit(cls):
        "Gracefully quit the simulator"
        pyNN_end()
