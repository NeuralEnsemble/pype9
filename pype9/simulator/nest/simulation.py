from pype9.simulator.base.simulation import BaseSimulation


class Simulation(BaseSimulation):
    """Represent the simulator state."""

    _active = None

    def __init__(self, *args, **kwargs):
        super(Simulation, self).__init__(*args, **kwargs)
        self._device_delay = None

    @property
    def device_delay(self):
        if self._device_delay is None:
            return self.min_delay
        else:
            return self._device_delay

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
        if not self._running:
            self._pre_run()
            self._running = True

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

#     def run(self, simtime, reset=True, reset_nest_time=False):
#         """Advance the simulation for a certain time."""
#         if reset:
#             self.reset(reset_nest_time=reset_nest_time)
#         for device in self.recording_devices:
#             if not device._connected:
#                 device.connect_to_cells()
#                 device._local_files_merged = False
#         if not self.running and simtime > 0:
#             simtime += self.dt
#             self.running = True
#         nest.Simulate(simtime)
#
#     def run_until(self, tstop):
#         self.run(tstop - self.t)
#
#     def reset(self, reset_nest_time=True):
#         if reset_nest_time:
#             nest.SetKernelStatus({'time': 0.0})
#         self.t_start = 0.0
#         for p in self.populations:
#             for variable, initial_value in p.initial_values.items():
#                 p._set_initial_value_array(variable, initial_value)
#         self.running = False
#         self.segment_counter += 1
#         self.reset_cells()
#
#     def clear(self, **kwargs):
#         # Set initial values
#         self.populations = []
#         self.recording_devices = []
#         self.recorders = set()
#         # clear the sli stack, if this is not done --> memory leak cause the
#         # stack increases
#         nest.sr('clear')
#         # set tempdir
#         tempdir = tempfile.mkdtemp()
#         self.tempdirs.append(tempdir)  # append tempdir to tempdirs list
#         nest.SetKernelStatus({'data_path': tempdir})
#         self.segment_counter = 0
#         # Get values before they are reset
#         dt = kwargs.get('dt', self.dt)
#         num_processes = self.num_processes
#         threads = self.threads
#         # Reset network and kernel
#         nest.ResetKernel()
#         nest.SetKernelStatus({'overwrite_files': True, 'resolution': dt})
#         if 'dt' in kwargs:
#             self.dt = kwargs['dt']
#         # set kernel RNG seeds
#         self.num_threads = kwargs.get('threads', 1)
#         if 'grng_seed' in kwargs:
#             self.grng_seed = kwargs['grng_seed']
#         if 'rng_seeds' in kwargs:
#             self.rng_seeds = kwargs['rng_seeds']
#         else:
#
#         self.reset(reset_nest_time=False)


def simulation(*args, **kwargs):
    return Simulation(*args, **kwargs)
