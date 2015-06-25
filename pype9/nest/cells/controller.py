import nest
import tempfile
import numpy
from ..controller import SimulationController


def nest_property(name, dtype):
    """Return a property that accesses a NEST kernel parameter"""

    def _get(self):
        return nest.GetKernelStatus(name)

    def _set(self, val):
            nest.SetKernelStatus({name: dtype(val)})

    return property(fget=_get, fset=_set)


class _SimulationController(SimulationController):
    """Represent the simulator state."""

    instance_counter = 0

    def __init__(self):
        """Initialize the simulator."""
        super(_SimulationController, self).__init__()
        self.t_start = 0
        self.write_on_end = []
        self.recorders = set([])
        self.initialized = False
        self.optimize = False
        self.spike_precision = "off_grid"
        self.verbosity = "warning"
        self._cache_num_processes = nest.GetKernelStatus()['num_processes']
        # allow NEST to erase previously written files
        # (defaut with all the other simulators)
        nest.SetKernelStatus({'overwrite_files': True})
        self.tempdirs = []
        self.recording_devices = []
        self.populations = []
        self.segment_counter = 0

    @property
    def t(self):
        return max(nest.GetKernelStatus('time') - self.dt, 0.0)

    dt = nest_property('resolution', float)

    threads = nest_property('local_num_threads', int)

    grng_seed = nest_property('grng_seed', int)

    rng_seeds = nest_property('rng_seeds', list)

    @property
    def min_delay(self):
        # this rather complex implementation is needed to handle
        # min_delay='auto'
        kernel_delay = nest.GetKernelStatus('min_delay')
        syn_delay = nest.GetDefaults('static_synapse')['min_delay']
        if syn_delay == numpy.inf or syn_delay > 1e300:
            return kernel_delay
        else:
            return max(kernel_delay, syn_delay)

    def set_delays(self, min_delay, max_delay):
        if min_delay != 'auto':
            min_delay = float(min_delay)
            max_delay = float(max_delay)
            for synapse_model in nest.Models(mtype='synapses'):
                nest.SetDefaults(synapse_model, {'delay': min_delay,
                                                 'min_delay': min_delay,
                                                 'max_delay': max_delay})

    @property
    def max_delay(self):
        return nest.GetDefaults('static_synapse')['max_delay']

    @property
    def num_processes(self):
        return self._cache_num_processes

    @property
    def mpi_rank(self):
        return nest.Rank()

    def _get_spike_precision(self):
        ogs = nest.GetKernelStatus('off_grid_spiking')
        return ogs and "off_grid" or "on_grid"

    def _set_spike_precision(self, precision):
        if precision == 'off_grid':
            nest.SetKernelStatus({'off_grid_spiking': True})
            self.default_recording_precision = 15
        elif precision == 'on_grid':
            nest.SetKernelStatus({'off_grid_spiking': False})
            self.default_recording_precision = 3
        else:
            raise ValueError("spike_precision must be 'on_grid' or 'off_grid'")

    spike_precision = property(fget=_get_spike_precision,
                               fset=_set_spike_precision)

    def _set_verbosity(self, verbosity):
        nest.sli_run("M_%s setverbosity" % verbosity.upper())
    verbosity = property(fset=_set_verbosity)

    def run(self, simtime, reset=True):
        """Advance the simulation for a certain time."""
        if reset:
            self.reset()
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

    def reset(self):
        nest.ResetNetwork()
        nest.SetKernelStatus({'time': 0.0})
        for p in self.populations:
            for variable, initial_value in p.initial_values.items():
                p._set_initial_value_array(variable, initial_value)
        self.running = False
        self.t_start = 0.0
        self.segment_counter += 1
        self.reset_cells()

    def clear(self):
        self.populations = []
        self.recording_devices = []
        self.recorders = set()
        # clear the sli stack, if this is not done --> memory leak cause the
        # stack increases
        nest.sr('clear')
        # reset the simulation kernel
        nest.ResetKernel()
        # set tempdir
        tempdir = tempfile.mkdtemp()
        self.tempdirs.append(tempdir)  # append tempdir to tempdirs list
        nest.SetKernelStatus({'data_path': tempdir})
        self.segment_counter = -1
        self.reset()

simulation_controller = _SimulationController()
