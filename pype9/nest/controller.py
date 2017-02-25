import time
import tempfile
import numpy
import nest
from pype9.base.controller import BaseController
from pyNN.nest.simulator import _State as PyNNState


class _Controller(BaseController, PyNNState):
    """Represent the simulator state."""

    instance_counter = 0

    def __init__(self):
        """Initialize the simulator."""
        super(_Controller, self).__init__()
        self.tempdirs = []
        self.clear()
        self._device_delay = None

    def set_delays(self, min_delay, max_delay, device_delay):
        self._device_delay = float(device_delay)
#         if min_delay != 'auto':
#             min_delay = float(min_delay)
#             max_delay = float(max_delay)
#             for synapse_model in nest.Models(mtype='synapses'):
#                 nest.SetDefaults(synapse_model, {'delay': min_delay,
#                                                  'min_delay': min_delay,
#                                                  'max_delay': max_delay})

    @property
    def device_delay(self):
        if self._device_delay is None:
            return self.min_delay
        else:
            return self._device_delay

    def run(self, simtime, reset=True, reset_nest_time=False):
        """Advance the simulation for a certain time."""
        if reset:
            self.reset(reset_nest_time=reset_nest_time)
        for device in self.recording_devices:
            if not device._connected:
                device.connect_to_cells()
                device._local_files_merged = False
        if not self.running and simtime > 0:
            simtime += self.dt
            self.running = True
        nest.Simulate(simtime)

    def run_until(self, tstop):
        self.run(tstop - self.t)

    def reset(self, reset_nest_time=True):
        if reset_nest_time:
            nest.SetKernelStatus({'time': 0.0})
        self.t_start = 0.0
        for p in self.populations:
            for variable, initial_value in p.initial_values.items():
                p._set_initial_value_array(variable, initial_value)
        self.running = False
        self.segment_counter += 1
        self.reset_cells()

    def clear(self, **kwargs):
        # Set initial values
        self.populations = []
        self.recording_devices = []
        self.recorders = set()
        # clear the sli stack, if this is not done --> memory leak cause the
        # stack increases
        nest.sr('clear')
        # set tempdir
        tempdir = tempfile.mkdtemp()
        self.tempdirs.append(tempdir)  # append tempdir to tempdirs list
        nest.SetKernelStatus({'data_path': tempdir})
        self.segment_counter = 0
        # Get values before they are reset
        dt = kwargs.get('dt', self.dt)
        num_processes = self.num_processes
        threads = self.threads
        # Reset network and kernel
        nest.ResetKernel()
        nest.SetKernelStatus({'overwrite_files': True, 'resolution': dt})
        if 'dt' in kwargs:
            self.dt = kwargs['dt']
        # set kernel RNG seeds
        self.num_threads = kwargs.get('threads', 1)
        if 'grng_seed' in kwargs:
            self.grng_seed = kwargs['grng_seed']
        if 'rng_seeds' in kwargs:
            self.rng_seeds = kwargs['rng_seeds']
        else:
            rng = numpy.random.RandomState(kwargs.get('rng_seed',
                                                      int(time.time())))
            n = num_processes * threads
            self.rng_seeds = list(
                numpy.asarray(rng.uniform(low=0, high=100000, size=n),
                              dtype=int))
        self.reset(reset_nest_time=False)

controller = _Controller()
