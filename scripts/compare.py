"""
Command that compares a 9ML model with an existing version in NEURON and/or
NEST
"""
import argparse
import pyNN.neuron  # @UnusedImport - imports PyNN mechanisms
import neuron
import nest
from neuron import h
try:
    import pylab as plt
except ImportError:
    plt = None
from pype9.neuron.cells import (
    CellMetaClass as CellMetaClassNEURON,
    simulation_controller as simulatorNEURON)
from pype9.nest.cells import (
    CellMetaClass as CellMetaClassNEST,
    simulation_controller as simulatorNEST)
import numpy
import quantities as pq
import neo
import nineml
from pype9.exceptions import Pype9RuntimeError


class Comparer(object):
    """
    The Comparer class is used to compare the dynamics of a 9ML model simulated
    in either NEURON or NEST with a native model in either of those simulators
    (or both)
    """

    min_delay = 0.2
    max_delay = 10.0

    def __init__(self, nineml_model, parameters, state_variable, simulators,
                 dt, initial_states, neuron_model=None, nest_model=None,
                 input_signal=None, input_train=None,
                 neuron_translations={}, nest_translations={}):
        """
        nineml_model   -- 9ML model to compare
        nineml_sims    -- tuple of simulator names to simulate the 9ML model in
        duration       -- simulation duration
        dt             -- simulation time step
        initial_states -- a dictionary of the initial states
        neuron_model   -- a tuple containing the name of neuron model and a
                          dictionary of parameter and state name mappings
        nest_model     -- a tuple containing the name of nest model and a
                          dictionary of parameter and state name mappings
        input_signal  -- tuple containing the analog signal (in Neo format)
                          and the port to play it into
        input_train    -- tuple containing the event train (in Neo format)
                          and the port to play it into
        """
        self.simulate_neuron = ('neuron' in simulators or
                                neuron_model is not None)
        self.simulate_nest = 'nest' in simulators or nest_model is not None
        self.dt = self.to_float(dt, 'ms')
        self.state_variable = state_variable
        self.nineml_model = nineml_model
        self.parameters = parameters
        self.neuron_model = neuron_model
        self.nest_model = nest_model
        self.simulators = simulators
        self.neuron_translations = neuron_translations
        self.nest_translations = nest_translations
        self.initial_states = initial_states
        self.input_signal = input_signal
        self.input_train = input_train
        self.nml_cells = {}
        if self.state_variable in self.nest_translations:
            self.nest_state_variable = self.nest_translations[
                self.state_variable][0]
        else:
            self.nest_state_variable = self.state_variable
        if self.state_variable in self.neuron_translations:
            self.neuron_state_variable = self.neuron_translations[
                self.state_variable][0]
        else:
            self.neuron_state_variable = self.state_variable

    def simulate(self, duration):
        """
        Run and the simulation
        """
        if self.simulate_neuron:
            h.dt = self.dt
        if self.simulate_nest:
            nest.SetKernelStatus({'resolution': self.dt})
        for simulator in self.simulators:
            self._create_9ML(nineml_model, simulator)
        if self.neuron_model is not None:
            self._create_NEURON(self.neuron_model)
        if self.nest_model is not None:
            self._create_NEST(self.nest_model)
        if self.simulate_neuron:
            simulatorNEURON.run(duration)
        if self.simulate_nest:
            simulatorNEST.run(duration)

    def plot(self):
        legend = []
        for simulator in self.simulators:
            self._plot_9ML(simulator)
            legend.append('{} (9ML-{})'.format(self.nineml_model.name,
                                               simulator.upper()))
        if self.neuron_model:
            self._plot_NEURON()
            legend.append(self.neuron_model + ' (NEURON)')
        if self.nest_model:
            self._plot_NEST()
            legend.append(self.nest_model + ' (NEST)')
        plt.legend(legend)
        plt.show()

    def _create_9ML(self, model, simulator):
        # -----------------------------------------------------------------
        # Set up 9MLML cell
        # -----------------------------------------------------------------
        if simulator.lower() == 'neuron':
            CellMetaClass = CellMetaClassNEURON
        elif simulator.lower() == 'nest':
            CellMetaClass = CellMetaClassNEST
        else:
            assert False
        self.nml_cells[simulator] = CellMetaClass(model, build_mode='force')()
        if self.input_signal is not None:
            self.nml_cells[simulator].play(*self.input_signal)
        if self.input_train is not None:
            self.nml_cells[simulator].play(*self.input_train)
        self.nml_cells[simulator].record(self.state_variable)
        self.nml_cells[simulator].update_state(self.initial_states)

    def _create_NEURON(self, neuron_name):
        # -----------------------------------------------------------------
        # Set up NEURON section
        # -----------------------------------------------------------------
        self.nrn_cell_sec = h.Section()
        try:
            self.nrn_cell = eval(
                'h.{}(0.5, sec=self.nrn_cell_sec)'.format(neuron_name))
            self.nrn_cell_sec.L = 10
            self.nrn_cell_sec.diam = 10 / numpy.pi
            self.nrn_cell_sec.cm = 1.0
        except TypeError:
            self.nrn_cell_sec.insert(neuron_name)
            self.nrn_cell = self.nrn_cell_sec(0.5)
            self.nrn_cell_sec.L = 100
            self.nrn_cell_sec.diam = 1000 / numpy.pi
            self.nrn_cell_sec.cm = 0.2
        # Check to see if any translated parameter names start with 'pas.' in
        # which case a passive mechanism needs to be inserted
        if any(self.neuron_translations.get(k, (k, 1))[0].startswith('pas.')
               for k in parameters.iterkeys()):
            self.nrn_cell_sec.insert('pas')
        for name, value in self.parameters.iteritems():
            try:
                varname, scale = self.neuron_translations[name]
                value = value * scale
            except (ValueError, KeyError):
                varname = self.neuron_translations.get(name, name)
                value = value
            if varname == 'pas.g':
                self.nrn_cell_sec(0.5).pas.g = value
            elif varname == 'pas.e':
                self.nrn_cell_sec(0.5).pas.e = value
            elif varname == 'cm':
                self.nrn_cell_sec.cm = value
            else:
                setattr(self.nrn_cell, name, value)
        for name, value in self.initial_states.iteritems():
            try:
                varname, scale = self.neuron_translations[name]
                value = value * scale
            except (ValueError, KeyError):
                varname = self.neuron_translations.get(name, name)
                value = value
            try:
                setattr(self.nrn_cell, name, value)
            except LookupError:
                setattr(self.nrn_cell_sec, name, value)
        # Specify current injection
        if self.input_signal is not None:
            _, signal = self.input_signal
            self._nrn_iclamp = h.IClamp(0.5, sec=self.nrn_cell_sec)
            self._nrn_iclamp.delay = 0.0
            self._nrn_iclamp.dur = 1e12
            self._nrn_iclamp.amp = 0.0
            self._nrn_iclamp_amps = h.Vector(pq.Quantity(signal, 'nA'))
            self._nrn_iclamp_times = h.Vector(pq.Quantity(signal.times, 'ms'))
            self._nrn_iclamp_amps.play(self._nrn_iclamp._ref_amp,
                                       self._nrn_iclamp_times)
        if self.input_train is not None:
            _, train = self.input_train
            self._vstim = h.VecStim()
            self._vstim_times = h.Vector(pq.Quantity(train, 'ms'))
            self._vstim.play(self._vstim_times)
            self._vstim_con = h.NetCon(self._vstim, self._hoc, sec=self._sec)
        # Record Time from NEURON (neuron.h._ref_t)
        self._nrn_rec = self.NEURONRecorder(self.nrn_cell_sec, self.nrn_cell)
        self._nrn_rec.record(self.neuron_state_variable)

    def _create_NEST(self, nest_name):
        trans_params = {}
        for name, value in parameters.iteritems():
            try:
                varname, scale = self.nest_translations[name]
                value = value * scale
            except (ValueError, KeyError):
                varname = self.nest_translations.get(name, name)
                value = value
            trans_params[varname] = value
        self.nest_cell = nest.Create(nest_name, 1, trans_params)
        try:
            receptor_types = nest.GetDefaults(nest_name)['receptor_types']
        except KeyError:
            receptor_types = None
        if self.input_signal is not None:
            port_name, signal = self.input_signal
            generator = nest.Create(
                'step_current_generator', 1,
                {'amplitude_values': pq.Quantity(signal, 'pA'),
                 'amplitude_times': (pq.Quantity(signal.times, 'ms') -
                                     self.min_delay * pq.ms),
                 'start': float(pq.Quantity(signal.t_start, 'ms')),
                 'stop': float(pq.Quantity(signal.t_stop, 'ms'))})
            nest.Connect(generator, self.nest_cell,
                         syn_spec={'receptor_type':
                                   (receptor_types[port_name]
                                    if receptor_types else 0),
                                   'delay': self.min_delay})
        if self.input_train is not None:
            port_name, signal = self.input_train
            spike_times = (pq.Quantity(signal, 'ms') - self.min_delay * pq.ms)
            if any(spike_times < 0.0):
                raise Pype9RuntimeError(
                    "Some spike are less than minimum delay and so can't be "
                    "played into cell ({})".format(
                        ', '.join(spike_times < self.min_delay)))
            generator = nest.Create(
                'spike_generator', 1, {'spike_times': spike_times})
            nest.Connect(generator, self.nest_cell,
                         syn_spec={'receptor_type':
                                   (receptor_types[port_name]
                                    if receptor_types else 0),
                                   'delay': self.min_delay})
        self.nest_multimeter = nest.Create(
            'multimeter', 1, {"interval": self.to_float(self.dt, 'ms')})
        nest.SetStatus(
            self.nest_multimeter,
            {'record_from': [self.nest_state_variable]})
        nest.Connect(self.nest_multimeter, self.nest_cell)
        trans_states = {}
        for name, value in self.initial_states.iteritems():
            try:
                varname, scale = self.nest_translations[name]
                value = value * scale
            except (ValueError, KeyError):
                varname = self.nest_translations.get(name, name)
                value = value
            trans_states[varname] = value
        nest.SetStatus(self.nest_cell, trans_states)

    def _plot_NEURON(self):  # @UnusedVariable
        pnn_t, pnn_v = self._get_NEURON_signal()
        plt.plot(pnn_t[:-1], pnn_v[1:])

    def _plot_NEST(self):
        nest_v = self._get_NEST_signal()
        plt.plot(pq.Quantity(nest_v.times, 'ms'), pq.Quantity(nest_v, 'mV'))

    def _plot_9ML(self, sim_name):  # @UnusedVariable
        nml_v = self.nml_cells[sim_name].recording(self.state_variable)
        plt.plot(nml_v.times, nml_v)

    def _diff_NEURON(self):  # @UnusedVariable
        _, pnn_v = self._get_NEURON_signal()
        nml_v = self.nml_cells['NEURON'].recording('v')
        return float(pq.Quantity((nml_v - pnn_v[1:] * pq.mV).sum(), 'V'))

    def _diff_NEST(self):
        nest_v = self._get_NEST_signal()
        nml_v = self.nml_cells['NEST'].recording(self.nest_state_variable)
        return float(pq.Quantity((nml_v - nest_v * pq.mV).sum(), 'V'))

    def _get_NEURON_signal(self):
        return self._nrn_rec.recording(self.neuron_state_variable)

    def _get_NEST_signal(self):
        return neo.AnalogSignal(
            nest.GetStatus(
                self.nest_multimeter, 'events')[0][self.nest_state_variable],
            sampling_period=simulatorNEST.dt * pq.ms, units='mV')  # @UndefinedVariable @IgnorePep8

    @classmethod
    def to_float(cls, qty, units):
        return float(pq.Quantity(qty, units))

    class NEURONRecorder(object):

        def __init__(self, sec, mech):
            self.sec = sec
            self.mech = mech
            self.rec_t = h.Vector()
            self.rec_t.record(neuron.h._ref_t)
            self.recs = {}

        def record(self, varname):
            rec = h.Vector()
            self.recs[varname] = rec
            if varname == 'v':
                rec.record(self.sec(0.5)._ref_v)
            elif varname == 'Cm':
                rec.record(self.sec(0.5)._ref_cm)
            else:
                rec.record(getattr(self.mech, '_ref_' + varname))

        def recording(self, varname):
            return numpy.array(self.rec_t), numpy.array(self.recs[varname])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('nineml_file', type=str,
                        help="The 9ML model to compare")
    parser.add_argument('--simulator', type=str, action='append',
                        help="The simulators to run the 9ML model in",
                        default=[])
    parser.add_argument('--model_name', type=str, default=None,
                        help="The name of the model to select within the file")
    parser.add_argument('--nest', type=str, default=None,
                        help="The name of the nest model to compare against")
    parser.add_argument('--neuron', type=str, default=None,
                        help="The name of the NEURON model to compare against")
    parser.add_argument('--dt', type=float, default=0.01,
                        help="The simulation timestep (ms)")
    parser.add_argument('--state_variable', type=str, default='v',
                        help="The variable to compare")
    parser.add_argument('--plot', action='store_true',
                        help="Plot the simulations")
    parser.add_argument('--parameter', '-p', nargs=2, action='append',
                        help="A parameter name/value pair",
                        metavar=('NAME', 'VALUE'), default=[])
    parser.add_argument('--initial_state', '-i', nargs=2, action='append',
                        help="An initial state name/value pair",
                        metavar=('NAME', 'VALUE'), default=[])
    parser.add_argument('--duration', type=float, default=100.0,
                        help="Duration of the simulation (ms)")
    parser.add_argument('--nest_trans', '-s', nargs=3, action='append',
                        help=("A translation for a parameter or state to the "
                              "name/scale used in the nest model"),
                        metavar=('OLD', 'NEW', 'SCALE'), default=[])
    parser.add_argument('--neuron_trans', '-u', nargs=3, action='append',
                        help=("A translation for a parameter or state to the "
                              "name/scale used in the neuron model"),
                        metavar=('OLD', 'NEW', 'SCALE'), default=[])
    parser.add_argument('--input_signal', type=str, nargs=2, default=None,
                        help=("Port name and path to the analog signal to "
                              "inject"), metavar=('PORT', 'NEO_FILE'))
    parser.add_argument('--input_train', type=str, nargs=2, default=None,
                        help=("Port name and path to the event train to "
                              "inject"), metavar=('PORT', 'NEO_FILE'))
    parser.add_argument('--input_step', type=str, nargs=3, default=None,
                        help=("Instead of a input signal, specify a simple "
                              "step function (port_name, start, amplitude)"),
                        metavar=('PORT', 'START_TIME', 'AMPLITUDE'))
    parser.add_argument('--input_freq', type=str, nargs=2, default=None,
                        help=("Instead of a input train, specify a simple "
                              "input event frequency (port_name, frequency)"),
                        metavar=('PORT', 'FREQUENCY'))
    args = parser.parse_args()
    if len(args.simulator) == 0 and args.neuron is None and args.nest is None:
        raise Pype9RuntimeError("No simulations specified")
    nineml_doc = nineml.read(args.nineml_file)
    if args.model_name:
        nineml_model = nineml_doc[args.model_name]
    else:
        components = list(nineml_doc.components)
        if len(components) == 1:
            nineml_model = components[0]
        elif len(components) == 0:
            component_classes = list(nineml_doc.component_classes)
            if len(component_classes) == 1:
                nineml_model = component_classes[0]
            else:
                raise Pype9RuntimeError(
                    "Multiple component classes found in '{}' file, need to "
                    "specify the --model_name parameter")
        else:
            raise Pype9RuntimeError(
                "Multiple components found in '{}' file, need to "
                "specify the --model_name parameter")
    parameters = dict((k, float(v)) for k, v in args.parameter)
    initial_states = dict((k, float(v)) for k, v in args.initial_state)
    nest_translations = dict((o, (n, float(s))) for o, n, s in args.nest_trans)
    neuron_translations = dict((o, (n, float(s)))
                               for o, n, s in args.neuron_trans)
    if args.input_signal is not None:
        if args.input_step is not None:
            raise Pype9RuntimeError(
                "Cannot use '--input_signal' and '--input_step' "
                "simultaneously")
        port_name, fpath = args.input_signal
        signal = neo.PickleIO(fpath).read()
        input_signal = (port_name, signal)
    elif args.input_step is not None:
        port_name, start_time, amplitude = args.input_step
        start_time = float(start_time)
        amplitude = float(amplitude)
        num_preceding = int(numpy.floor(start_time / args.dt))
        num_remaining = int(numpy.ceil((args.duration - start_time) / args.dt))
        signal = neo.AnalogSignal(
            numpy.concatenate((numpy.zeros(num_preceding),
                               numpy.ones(num_remaining) * amplitude)),
            sampling_period=args.dt * pq.ms, units='nA', time_units='ms')
        input_signal = (port_name, signal)
    else:
        input_signal = None
    if args.input_train is not None:
        if args.input_freq is not None:
            raise Pype9RuntimeError(
                "Cannot use '--input_train' and '--input_freq' "
                "simultaneously")
        port_name, fpath = args.input_train
        train = neo.PickleIO(fpath).read()
        input_train = (port_name, train)
    elif args.input_freq is not None:
        port_name, freq = args.input_freq
        train = neo.SpikeTrain(
            numpy.arange(0.0, args.duration, 1 / float(freq)),
            units='ms', t_stop=args.duration * pq.ms)
    else:
        input_train = None
    comparer = Comparer(nineml_model, parameters=parameters,
                        state_variable=args.state_variable,
                        simulators=args.simulator, dt=args.dt,
                        initial_states=initial_states,
                        neuron_model=args.neuron, nest_model=args.nest,
                        input_signal=input_signal, input_train=input_train,
                        nest_translations=nest_translations,
                        neuron_translations=neuron_translations)
    comparer.simulate(args.duration)
    if args.plot:
        comparer.plot()

#         models = [('Izhikevich2003', 'Izhikevich', 'izhikevich'),
#               ('AdExpIaF', 'AdExpIF', 'aeif_cond_alpha'),
#               ('HodgkinHuxley', 'hh_traub', 'hh_cond_exp_traub'),
#               ('LeakyIntegrateAndFire', 'ResetRefrac', 'iaf_psc_alpha')]
# 
#     initial_states = {'Izhikevich2003': {'u': -14 * pq.mV / pq.ms,
#                                          'v': -65.0 * pq.mV},
#                       'AdExpIaF': {'w': 0.0 * pq.nA,
#                                    'v': -65 * pq.mV},
#                       'HodgkinHuxley': {'v': -65 * pq.mV,
#                                         'm': 0, 'h': 1, 'n': 0},
#                       'LeakyIntegrateAndFire': {'v': -65 * pq.mV,
#                                                 'end_refractory': 0.0}}
# 
#     neuron_pas = {'Izhikevich2003': None,
#                   'AdExpIaF': None,
#                   'HodgkinHuxley': None,
#                   'LeakyIntegrateAndFire': {'g': 0.00025, 'e': -70}}
#     neuron_params = {'Izhikevich2003': None,
#                      'AdExpIaF': None,
#                      'HodgkinHuxley': None,
#                      'LeakyIntegrateAndFire': {
#                          'vthresh': -55,
#                          'vreset': -70,
#                          'trefrac': 2}}
# 
#     nest_states = {'Izhikevich2003': {'u': 'U_m', 'v': 'V_m'},
#                    'AdExpIaF': {'w': 'w', 'v': 'V_m'},
#                    'HodgkinHuxley': {'v': 'V_m', 'm': 'Act_m', 'h': 'Act_h',
#                                      'n': 'Inact_n'},
#                    'LeakyIntegrateAndFire': {'v': 'V_m',
#                                              'end_refractory': None}}
#     nest_params = {'Izhikevich2003': {'a': 0.02, 'c': -65.0, 'b': 0.2,
#                                       'd': 2.0},
#                    'AdExpIaF': {},
#                    'HodgkinHuxley': {},
#                    'LeakyIntegrateAndFire': {"C_m": 250.0,
#                                              "tau_m": 20.0,
#                                              "tau_syn_ex": 0.5,
#                                              "tau_syn_in": 0.5,
#                                              "t_ref": 2.0,
#                                              "E_L": 0.0,
#                                              "V_reset": 0.0,
#                                              "V_m": 0.0,
#                                              "V_th": 20.0}}
#     paradigms = {'Izhikevich2003': {'duration': 100 * pq.ms,
#                                     'stim_amp': 0.02 * pq.nA,
#                                     'stim_start': 20 * pq.ms,
#                                     'dt': 0.02 * pq.ms},
#                  'AdExpIaF': {'duration': 50 * pq.ms,
#                               'stim_amp': 1 * pq.nA,
#                               'stim_start': 25 * pq.ms,
#                               'dt': 0.002 * pq.ms},
#                  'HodgkinHuxley': {'duration': 100 * pq.ms,
#                                    'stim_amp': 0.5 * pq.nA,
#                                    'stim_start': 50 * pq.ms,
#                                    'dt': 0.002 * pq.ms},
#                  'LeakyIntegrateAndFire': {'duration': 50 * pq.ms,
#                                            'stim_amp': 1 * pq.nA,
#                                            'stim_start': 25 * pq.ms,
#                                            'dt': 0.002 * pq.ms}}
