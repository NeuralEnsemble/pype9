from abc import ABCMeta, abstractmethod
from nineml import units as un
import numpy
import time
from pype9.exceptions import Pype9UsageError, Pype9NoActiveSimulationError
import logging
from pyNN.random import NumpyRNG

logger = logging.getLogger('PyPe9')


class Simulation(object):
    """
    Base class of all simulation classes that prepares and runs the simulator
    kernel. All simulator objects must be created within the context of a
    Simulation instance.

    .. code-block:: python

        with Simulation(dt=0.1 * un.ms, seed=12345) as sim:
            # Design simulation here

    The simulation is advanced using the ``run`` method

    .. code-block:: python

       with Simulation(dt=0.1 * un.ms, seed=12345) as sim:
            # Create simulator objects here
            sim.run(100.0 * un.ms)

    After the simulation context exits all objects in the simulator backend are
    destroyed (unless an exception is thrown) and only recordings can be
    reliably accessed from the "dead" Pype9 objects.

    Parameters
    ----------
    dt : nineml.Quantity (time)
        The resolution of the simulation
    t_start : nineml.Quantity (time)
        The time to start the simulation from
    seed : int | None
        The seed with which to construct the cell/network properties.
        NB: This seed will only reproduce constant results if the number
        of MPI nodes is constant
    properties_seed : int | None
        The seed used for random number generator used to set properties and
        generate connectivity. If not provided it will be derived from the
        'seed' argument.
        NB: This seed will only reproduce constant results if the number
        of MPI nodes is constant
    min_delay : nineml.Quantity (time) | None
        The minimum delay in the network. If None the min delay will be
        calculated from the first network to be created (if a single cell
        then it will be the same as the timestep)
    max_delay : nineml.Quantity (time) | None
        The maximum delay in the network. If None the max delay will be
        calculated from the first network to be created (if a single cell
        then it will be the same as the timestep)
    options : dict(str, object)
        Options passed to the simulator-specific methods
    """

    __metaclass__ = ABCMeta

    max_seed = 2 ** 32 - 1

    def __init__(self, dt, t_start=0.0 * un.s, seed=None, properties_seed=None,
                 min_delay=1 * un.ms, max_delay=10 * un.ms, **options):
        self._check_units('dt', dt, un.time)
        self._check_units('t_start', dt, un.time)
        self._check_units('min_delay', dt, un.time, allow_none=True)
        self._check_units('max_delay', dt, un.time, allow_none=True)
        self._dt = dt
        self._t_start = t_start
        self._t = t_start
        self._min_delay = min_delay if min_delay > dt else dt
        self._max_delay = max_delay if max_delay > dt else dt
        self._options = options
        self._registered_cells = None
        self._registered_arrays = None
        if seed is not None and (seed < 0 or seed > self.max_seed):
            raise Pype9UsageError(
                "Provided seed {} is out of range, must be between (0 and {})"
                .format(seed, self.max_seed))
        self._base_seed = seed
        if properties_seed is not None and (properties_seed < 0 or
                                            properties_seed > self.max_seed):
            raise Pype9UsageError(
                "Provided structure seed {} is out of range, must be between "
                "(0 and {})".format(seed, self.max_seed))
        self._base_properties_seed = properties_seed

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, type_, value, traceback):  # @UnusedVariable
        self.deactivate(kill_cells=(type_ is None))

    def activate(self):
        if self.__class__._active is not None:
            raise Pype9UsageError(
                "Cannot enter context of multiple {} simulations at the same "
                "time".format(self.__class__.name))
        self._set_seeds()
        self._running = False
        self._prepare()
        self._registered_cells = []
        self._registered_arrays = []
        self.__class__._active = self

    def deactivate(self, kill_cells=True):
        t_stop = self.t
        self.__class__._active = None
        if kill_cells:
            for cell in self._registered_cells:
                cell._kill(t_stop)
            for array in self._registered_arrays:
                array._kill(t_stop)
        else:
            logger.warning(
                "Not killing cells as an uncaught exception was thrown")
        self._registered_cells = None
        self._registered_arrays = None

    @property
    def dt(self):
        return self._dt

    @property
    def t(self):
        return self._t

    @property
    def t_start(self):
        return self._t_start

    @property
    def min_delay(self):
        return self._min_delay

    @property
    def max_delay(self):
        return self._max_delay

    @property
    def dynamics_seed(self):
        """
        The seed used to construct the network and set its properties. If no
        explicit dynamics seed is used then it will also be used to seed the
        dynamics
        """
        return self._dynamics_seeds[self.mpi_rank()]

    @property
    def properties_seed(self):
        """
        The seed used to by random dynamic processes (typically in state
        assignments).
        """
        return self._properties_seeds[self.mpi_rank()]

    @property
    def all_properties_seeds(self):
        return self._properties_seeds

    @property
    def properties_rng(self):
        if self._properties_rng is None:
            raise Pype9UsageError(
                "Can only access rng inside simulation context")
        return self._properties_rng

    @property
    def base_seed(self):
        """
        Base seed from which all (except for structure seed if it is provided)
        process-specific seeds are generated
        """
        return self._base_seed

    @property
    def base_properties_seed(self):
        return self._base_properties_seed

    @property
    def all_dynamics_seeds(self):
        return self._dynamics_seeds

    @property
    def global_seed(self):
        """Global seed passed to NEST grng"""
        return self._global_seed

    def _set_seeds(self):
        """
        Generate seeds for each process/thread
        """
        seed = self.gen_seed() if self._base_seed is None else self._base_seed
        seed_gen_rng = numpy.random.RandomState(seed)
        if self._base_properties_seed is None:
            logger.info("Using {} as seed for both properties and dynamics of "
                        "{} simulation".format(seed, self.name))
            prop_seed_gen_rng = seed_gen_rng
        else:
            logger.info("Using {} as seed for properties and {} as seed for "
                        "dynamics of {} simulation"
                        .format(self._base_properties_seed, seed, self.name))
            prop_seed_gen_rng = numpy.random.RandomState(
                self._base_properties_seed)
        # Properties seeds are drawn before dynamics_seeds
        self._properties_seeds = numpy.asarray(
            prop_seed_gen_rng.uniform(low=0, high=self.max_seed,
                                        size=self.num_threads()), dtype=int)
        self._dynamics_seeds = numpy.asarray(
            seed_gen_rng.uniform(low=0, high=self.max_seed,
                                 size=self.num_threads()), dtype=int)
        self._global_seed = int(seed_gen_rng.uniform(low=0, high=self.max_seed,
                                                     size=1,))
        self._properties_rng = NumpyRNG(self.properties_seed)

    @property
    def derived_properties_seed(self):
        return int(self.properties_rng.uniform(low=0, high=self.max_seed,
                                               size=1))

    def run(self, t_stop, **kwargs):
        """
        Run the simulation until time ``t_stop``.

        Parameters
        ----------
        t_stop : nineml.Quantity (time)
            The time to run the simulation until
        """
        self._check_units('t_stop', t_stop, un.time)
        if not self._running:
            self._initialize()
            self._running = True
        self._run(t_stop, **kwargs)
        self._t = t_stop

    @abstractmethod
    def _run(self, t_stop, **kwargs):  # @UnusedVariable
        """
        Calls the simulator-specific functions to advance the simulation
        kernel until time t_stop

        Parameters
        ----------
        t_stop : nineml.Quantity (time)
            The time to run the simulation until
        """

    @abstractmethod
    def _prepare(self):
        "Reset the simulation and prepare it for creating new cells/networks"

    def _initialize(self):
        """
        Just in time initialisations that are performed before the simulation
        starts running.
        """
        for cell in self._registered_cells:
            cell.initialize()
        # Array initialisation is handled by PyNN

    @abstractmethod
    def mpi_rank(self):
        "The rank of the MPI node the code is running on"

    @abstractmethod
    def num_processes(self):
        "The number of MPI processes"

    @abstractmethod
    def num_threads(self):
        "The total number of threads across all MPI nodes"

    @classmethod
    def gen_seed(cls):
        return long(time.time())

    def register_cell(self, cell):
        self._registered_cells.append(cell)

    def register_array(self, array):
        self._registered_arrays.append(array)

    @classmethod
    def active(cls):
        if cls._active is not None:
            active = cls._active
        else:
            raise Pype9NoActiveSimulationError(
                "No {} simulations are currently active (cells and networks "
                "need to be initialized within an active simulation context)"
                .format(cls.name))
        return active

    def _check_units(self, varname, val, dimension, allow_none=False):
        if not (val is None and allow_none):
            try:
                assert val.units.dimension == dimension
            except (AssertionError, AttributeError):
                raise Pype9UsageError(
                    "Provided value to {} ({}) is not a valid '{}' "
                    "quantity".format(varname, val, dimension.name))
