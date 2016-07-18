import sys
from argparse import ArgumentParser
import ninemlcatalog
argv = sys.argv[1:]


def construct_reference(self, nest_name):
    trans_params = {}
    for prop in self.properties.properties:
        name = prop.name
        value = prop.value
        try:
            varname, scale = self.nest_translations[name]
            value = value * scale
        except (ValueError, KeyError):
            varname = self.nest_translations.get(name, name)
        value = UnitHandlerNEST.scale_value(Quantity(value, prop.units))
        if varname is not None:
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
                                 self.device_delay * pq.ms),
             'start': float(pq.Quantity(signal.t_start, 'ms')),
             'stop': float(pq.Quantity(signal.t_stop, 'ms'))})
        nest.Connect(generator, self.nest_cell,
                     syn_spec={'receptor_type':
                               (receptor_types[port_name]
                                if receptor_types else 0),
                               'delay': self.device_delay})
    if self.input_train is not None:
        port_name, signal, connection_properties = self.input_train
        try:
            _, scale = self.nest_translations[port_name]
        except KeyError:
            scale = 1.0
        # FIXME: Should scale units
        weight = connection_properties[0].value * scale
        spike_times = (pq.Quantity(signal, 'ms') +
                       (pq.ms - self.device_delay * pq.ms))
        if any(spike_times < 0.0):
            raise Pype9RuntimeError(
                "Some spike are less than minimum delay and so can't be "
                "played into cell ({})".format(
                    ', '.join(str(t) for t in
                              spike_times[spike_times < self.device_delay])))
        generator = nest.Create(
            'spike_generator', 1, {'spike_times': spike_times})
        nest.Connect(generator, self.nest_cell,
                     syn_spec={'receptor_type':
                               (receptor_types[port_name]
                                if receptor_types else 0),
                               'delay': float(self.device_delay),
                               'weight': float(weight)})
    self.nest_multimeter = nest.Create(
        'multimeter', 1, {"interval": self.to_float(self.dt, 'ms')})
    nest.SetStatus(
        self.nest_multimeter,
        {'record_from': [self.nest_state_variable]})
    nest.Connect(self.nest_multimeter, self.nest_cell)
    trans_states = {}
    for name, qty in self.initial_states.iteritems():
        try:
            varname, scale = self.nest_translations[name]
            qty = qty * scale
        except (ValueError, KeyError):
            varname = self.nest_translations.get(name, name)
        value = UnitHandlerNEST.scale_value(qty)
        if varname is not None:
            trans_states[varname] = value
    nest.SetStatus(self.nest_cell, trans_states)

parser = ArgumentParser()
parser.add_argument('--fast_spiking', action='store_true', default=False,
                    help=("Whether to use the \"fast-spiking\" version of the "
                          "Izhikevich neuron or not"))
args = parser.parse_args(argv)

if args.fast_spiking:
    nineml_model = ninemlcatalog.load('neuron/Izhikevich',
                                      'IzhikevichFastSpiking')
else:
    nineml_model = ninemlcatalog.load('neuron/Izhikevich', 'Izhikevich'),



    def _create_9ML(self, model, properties, simulator):
        # -----------------------------------------------------------------
        # Set up 9MLML cell
        # -----------------------------------------------------------------
        if simulator.lower() == 'neuron':
            CellMetaClass = CellMetaClassNEURON
        elif simulator.lower() == 'nest':
            CellMetaClass = CellMetaClassNEST
        else:
            assert False
        self.nml_cells[simulator] = CellMetaClass(
            model, name=self.build_name, default_properties=properties,
            initial_regime=self.initial_regime,
            **self.build_args[simulator])()
        if self.input_signal is not None:
            self.nml_cells[simulator].play(*self.input_signal)
        if self.input_train is not None:
            self.nml_cells[simulator].play(*self.input_train)
        self.nml_cells[simulator].record(self.state_variable)
        for state_var in self.auxiliary_states:
            self.nml_cells[simulator].record(state_var)
        self.nml_cells[simulator].update_state(self.initial_states)

if self.simulate_nest:
    nest.ResetKernel()
    simulatorNEST.clear(rng_seed=nest_rng_seed, dt=self.dt)
    simulation_controller.set_delays(self.min_delay, self.max_delay,
                                     self.device_delay)
if self.simulate_neuron:
    simulatorNEURON.clear(rng_seed=neuron_rng_seed)
    neuron.h.dt = self.dt
for simulator in self.simulators:
    self._create_9ML(self.nineml_model, self.properties, simulator)
if self.nest_ref is not None:
    self._create_NEST(self.nest_ref)
if self.neuron_ref is not None:
    self._create_NEURON(self.neuron_ref)
if self.simulate_nest:
    simulatorNEST.run(duration)
if self.simulate_neuron:
    simulatorNEURON.run(duration)

comparer = Comparer(
    nineml_model=ninemlcatalog.load(
        'neuron/Izhikevich', 'Izhikevich'),
    state_variable='V', dt=dt, simulators=simulators,
    properties=ninemlcatalog.load(
        'neuron/Izhikevich', 'SampleIzhikevich'),
    initial_states={'U': -14.0 * pq.mV / pq.ms, 'V': -65.0 * pq.mV},
    neuron_ref='Izhikevich', nest_ref='izhikevich',
    input_signal=input_step('Isyn', 0.02, 50, 100, dt),
    nest_translations={'V': ('V_m', 1), 'U': ('U_m', 1),
                       'weight': (None, 1), 'C_m': (None, 1),
                       'theta': ('V_th', 1),
                       'alpha': (None, 1), 'beta': (None, 1),
                       'zeta': (None, 1)},
    neuron_translations={'C_m': (None, 1), 'weight': (None, 1),
                         'V': ('v', 1), 'U': ('u', 1),
                         'alpha': (None, 1), 'beta': (None, 1),
                         'zeta': (None, 1), 'theta': ('vthresh', 1)},
    neuron_build_args={'build_mode': build_mode},
    nest_build_args={'build_mode': build_mode},
    build_name='Izhikevich9ML')
comparer.simulate(duration, nest_rng_seed=NEST_RNG_SEED,
                  neuron_rng_seed=NEURON_RNG_SEED)
comparisons = comparer.compare()


        # Force compilation of code generation
# Perform comparison in subprocess
comparer = Comparer(
    nineml_model=ninemlcatalog.load(
        'neuron/Izhikevich', 'IzhikevichFastSpiking'),
    state_variable='V', dt=dt, simulators=simulators,
    properties=ninemlcatalog.load(
        'neuron/Izhikevich', 'SampleIzhikevichFastSpiking'),
    initial_states={'U': -1.625 * pq.pA, 'V': -65.0 * pq.mV},
    input_signal=input_step('iSyn', 100 * pq.pA, 25.0, 100, dt),
    initial_regime='subVb',
    neuron_build_args={'build_mode': build_mode,
                       'external_currents': ['iSyn']},
    nest_build_args={'build_mode': build_mode}) #, auxiliary_states=['U']) # @IgnorePep8
comparer.simulate(duration, nest_rng_seed=NEST_RNG_SEED,
                  neuron_rng_seed=NEURON_RNG_SEED)