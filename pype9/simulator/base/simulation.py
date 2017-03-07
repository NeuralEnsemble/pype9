from abc import ABCMeta, abstractmethod
import os
import nineml
from nineml import units as un
import numpy
from binascii import hexlify
from pype9.exceptions import Pype9UsageError, Pype9NoActiveSimulationError


class BaseSimulation(object):

    __metaclass__ = ABCMeta
    MASTER = 0
    DEFAULT_MAX_DELAY = 10.0 * un.ms

    def __init__(self, dt, t_start=0.0 * un.s, seed=None,
                 dynamics_seed=None, min_delay=None, max_delay=None,
                 last_simulation=False, **options):
        """
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
        dynamics_seed : int | None
            The seed used for the RNG in the dynamic process, e.g. Poisson
            distributions.
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
        last_simulation : bool
            Flags whether the simulation is the last simulation, in which
            case the simulator should be closed gracefully
        """
        try:
            assert t_start.dimension == un.time
        except:
            raise Pype9UsageError(
                "Provided value to t_stop ({}) is not a valid time quantity"
                .format(t_start))
        self._dt = dt
        self._t_start = t_start
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._last_simulation = last_simulation
        self._options = options
        self._registered_cells = []
        self._registered_arrays = []
        seed_gen_rng = numpy.random.RandomState(
            seed if seed is not None else self.gen_seed())
        self._seeds = numpy.asarray(
            seed_gen_rng.uniform(low=0, high=1e12, size=self.num_threads()),
            dtype=int)
        dyn_seed_gen_rng = (numpy.random.RandomState(dynamics_seed)
                            if dynamics_seed is not None else seed_gen_rng)
        self._dynamics_seeds = numpy.asarray(
            dyn_seed_gen_rng.uniform(
                low=0, high=1e12, size=self.num_threads()), dtype=int)

    def __enter__(self):
        if self.simulator_closed:
            raise Pype9UsageError(
                "Simulator has already been closed. Please set "
                "'last_simulation' to False if you want to run multiple "
                "simulations")
        if self.active_simulation is not None:
            raise Pype9UsageError(
                "Cannot instantiate more than one instance of Simulation")
        self.active_simulation = self
        self._running = False
        self._reset()

    def __exit__(self):
        self.run_until(self.t_stop)
        self.active_simulation = None
        for cell in self._registered_cells:
            cell._kill()
        for array in self._registered_arrays:
            array._kill()

    @property
    def t_stop(self):
        return self._t_stop

    @property
    def dt(self):
        return self._dt

    @property
    def seed(self):
        """
        The seed used to construct the network and set its properties. If no
        explicit dynamics seed is used then it will also be used to seed the
        dynamics
        """
        return self._seeds[self.mpi_rank()]

    @property
    def dynamics_seed(self):
        """
        The seed used to by random dynamic processes (typically in state
        assignments).
        """
        return self._dyn_seed[self.mpi_rank()]

    @abstractmethod
    def run_until(self, t):  # @UnusedVariable
        """
        Run the simulation until time 't'. Typically won't be called explicitly
        as the __exit__ function will run the simulation until t_stop. However,
        it may be required if a state needs to be updated mid-way through the
        simulation.

        Parameters
        ----------
        t : nineml.Quantity (time)
            The time to run the simulation until
        """
        if not self._running:
            self._pre_run()
            self._running = True

    @abstractmethod
    def _reset(self):
        "Reset the simulation and prepare it for creating new cells/networks"

    @abstractmethod
    def _initialise(self):
        """
        Just in time initialisations that are performed before the simulation
        starts running.
        """

    @abstractmethod
    def _set_seeds(self):
        "Sets the seeds used to initiate the RNGs used in the simulation"

    def set_delays(self, network_or_cell):
        """
        Sets the min and max delays from the 9ML model to be simulated if they
        were not explicitly provided in the __init__ method.

        Parameters
        ----------
        network_or_cell : nineml.Network | nineml.Dynamics
            The network or cell to be simulated.
        """
        if isinstance(network_or_cell, nineml.Network):
            min_delay, max_delay = network_or_cell.delay_limits()
        else:
            assert isinstance(network_or_cell, nineml.Dynamics)
            min_delay = self.dt
            max_delay = self.DEFAULT_MAX_DELAY
        if self._min_delay is None:
            self._min_delay = min_delay
        if self._max_delay is None:
            self._max_delay = max_delay

    @abstractmethod
    def close_simulator(self):
        "Gracefully close the simulator (important in parallel contexts)"
        self.simulated_closed = True

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
        cls.active_simulation._registered_cells.append(cell)

    @classmethod
    def register_array(cls, array):
        cls.active_simulation._registered_arrays.append(array)

    @classmethod
    def active(cls):
        if cls._active is not None:
            active = cls._active
        else:
            raise Pype9NoActiveSimulationError(
                "No {} simulations are currently active (cells and networks "
                "need to be initialised within an active simulation context)"
                .format(cls.__name__))
        return active
