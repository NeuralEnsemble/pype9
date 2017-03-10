from abc import ABCMeta, abstractmethod
import os
from nineml import units as un
import numpy
from binascii import hexlify
from pype9.exceptions import Pype9UsageError, Pype9NoActiveSimulationError
import logging
from pyNN.random import NumpyRNG

logger = logging.getLogger('PyPe9')


class BaseSimulation(object):
    """
    Base class of all simulation classes that prepare and run the simulator
    kernel.

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
    structure_seed : int | None
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
    kill_on_exit : bool
        Flags whether to destroy all simulator-specific objects upon exiting
        the simulation context (leaving only recorded data). Should typically
        only required to be set to False when debugging code.
    options : dict(str, object)
        Options passed to the simulator-specific methods
    """

    __metaclass__ = ABCMeta

    def __init__(self, dt, t_start=0.0 * un.s, seed=None, structure_seed=None,
                 min_delay=None, max_delay=None, kill_on_exit=True, **options):
        self._check_units('dt', dt, un.time)
        self._check_units('t_start', dt, un.time)
        self._check_units('min_delay', dt, un.time, allow_none=True)
        self._check_units('max_delay', dt, un.time, allow_none=True)
        self._dt = dt
        self._t_start = t_start
        self._t = t_start
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._kill_on_exit = kill_on_exit
        self._options = options
        self._registered_cells = None
        self._registered_arrays = None
        if seed is None:
            seed = self.gen_seed()
        seed_gen_rng = numpy.random.RandomState(seed)
        self._seeds = numpy.asarray(
            seed_gen_rng.uniform(low=0, high=2 ** 32 - 1,
                                 size=self.num_threads() + 1), dtype=int)
        if structure_seed is None:
            logger.info("Using {} as seed for both structure and dynamics of "
                        "{} simulation".format(seed, self.name))
            struct_seed_gen_rng = seed_gen_rng
        else:
            logger.info("Using {} as seed for structure and {} as seed for "
                        "dynamics of {} simulation"
                        .format(structure_seed, seed, self.name))
            struct_seed_gen_rng = numpy.random.RandomState(structure_seed)
        self._structure_seeds = numpy.asarray(
            struct_seed_gen_rng.uniform(
                low=0, high=2 ** 32 - 1, size=self.num_threads()), dtype=int)

    def __enter__(self):
        if self.__class__._active is not None:
            raise Pype9UsageError(
                "Cannot enter context of multiple {} simulations at the same "
                "time".format(self.__class__.name))
        self._structure_rng = NumpyRNG(self.structure_seed)
        self._running = False
        self._prepare()
        self._registered_cells = []
        self._registered_arrays = []
        self.__class__._active = self
        return self

    def __exit__(self, type_, value, traceback):  # @UnusedVariable
        t_stop = self.t
        self.__class__._active = None
        if self._kill_on_exit:
            for cell in self._registered_cells:
                cell._kill(t_stop)
            for array in self._registered_arrays:
                array._kill(t_stop)
            self._exit()
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
    def seed(self):
        """
        The seed used to construct the network and set its properties. If no
        explicit dynamics seed is used then it will also be used to seed the
        dynamics
        """
        return self._seeds[self.mpi_rank()]

    @property
    def all_seeds(self):
        return self._seeds[:-1]

    @property
    def global_seed(self):
        """Global seed passed to NEST grng"""
        return self._seeds[-1]

    @property
    def structure_seed(self):
        """
        The seed used to by random dynamic processes (typically in state
        assignments).
        """
        return self._structure_seeds[self.mpi_rank()]

    @property
    def all_structure_seeds(self):
        return self._structure_seeds

    @property
    def structure_rng(self):
        if self._structure_rng is None:
            raise Pype9UsageError(
                "Can only access rng inside simulation context")
        return self._structure_rng

    @property
    def derived_structure_seed(self):
        return int(self.structure_rng.uniform(low=0, high=1e12, size=1))

    def run(self, t_stop, **kwargs):
        """
        Run the simulation until time 't'.

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

    @abstractmethod
    def _initialize(self):
        """
        Just in time initialisations that are performed before the simulation
        starts running.
        """

    @abstractmethod
    def _exit(self):
        """
        Code used to clean up the simulator state after a simulation exits
        """

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
        return int(hexlify(os.urandom(4)), 16)

    @classmethod
    def register_cell(cls, cell):
        cls.active()._registered_cells.append(cell)

    @classmethod
    def register_array(cls, array):
        cls.active()._registered_arrays.append(array)

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
