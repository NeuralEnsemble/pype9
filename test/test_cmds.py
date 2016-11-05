import tempfile
import shutil
import neo.io
from pype9.cmd.simulate import run
import quantities as pq
import nest
import ninemlcatalog
from pype9.utils.testing import ReferenceBrunel2000
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestSimulateAndPlot(TestCase):

    ref_path = ''

    # Izhikevich simulation params
    t_stop = 100.0
    dt = 0.001
    U = (-14.0, 'mv/ms')
    V = (-65.0, 'mV')
    Isyn = ((20.0, 'pA'), (50.0, 'ms'), (0.0, 'pA'))
    nest_name = 'izhikevich'
    nineml_model_path = '//neuron/Izhikevich#SampleIzhikevich'

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_single_cell(self):
        out_path = '{out_dir}/v.neo.pkl'.format(self.tmpdir)
        for simulator in ('nest', 'neuron'):
            run("{nineml_model} {sim} {t_stop} {dt}"
                "--record V {out_path} "
                "--init_value U {U} "
                "--init_value V {V} "
                "--play Isyn //input/StepCurrent#StepCurrent current_output "
                "--play_prop Isyn amplitude {isyn_amp} "
                "--play_prop Isyn onset {isyn_onset} "
                "--play_init_value Isyn current_output {isyn_init}"
                .format(nineml_model=self.nineml_model_path, sim=simulator,
                        out_path=out_path, t_stop=self.t_stop, dt=self.dt,
                        U=' '.join(self.U), V=' '.join(self.V),
                        isyn_amp=' '.join(self.Isyn[0]),
                        isyn_onset=' '.join(self.Isyn[1]),
                        isyn_init=' '.join(self.Isyn[2])))
            v = neo.io.PickleIO(out_path).read().segments[0].analogsignals[0]
            ref_v = neo.io.PickleIO(
                self.ref_path).read().segments[0].analogsignals[0]
            self.assertEqual(v, ref_v)

    def _ref_nest_izhi(self):
        nest.SetKernelStatus({'resolution': self.dt})
        nineml_model = ninemlcatalog.load(self.nineml_model_path)
        params = {
            'a': float(nineml_model['a']),
            'b': float(nineml_model['b']),
            'c': float(nineml_model['c']),
            'd': float(nineml_model['d']),
            'I_e': 0.0, 'V_m': self.V[0], 'U_m': self.U[0],
            'V_th': float(nineml_model['theta'])}
        cell = nest.Create(self.nest_name, 1, params)
        step_input = nest.Create(
            'step_current_generator', 1,
            {'amplitude_values': [self.Isyn[2][0], self.Isyn[0][0]],
             'amplitude_times': [0.0, self.Isyn[1][0]],
             'start': 0.0,
             'stop': self.t_stop})
        nest.Connect(step_input, cell,
                     syn_spec={'receptor_type': 0,
                               'delay': self.dt})
        multimeter = nest.Create(
            'multimeter', 1, {"interval": self.dt})
        nest.SetStatus(multimeter, {'record_from': ['V_m']})
        nest.Connect(multimeter, cell)
        nest.Simulate(self.t_stop)
        return neo.AnalogSignal(
            nest.GetStatus(multimeter, 'events')[0]['V_m'],
            sampling_period=self.dt * pq.ms, units='mV')

    def _ref_nest_brunel(self):
        ReferenceBrunel2000()


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    tester = TestSimulateAndPlot()
    v = tester._ref_nest_izhi()
    plt.plot(v.times, v)
    plt.show()

#     def _ref_nest_brunel(self):
#         if self.input_train is not None:
#             port_name, signal, connection_properties = self.input_train
#             try:
#                 _, scale = self.nest_translations[port_name]
#             except KeyError:
#                 scale = 1.0
#             # FIXME: Should scale units
#             weight = connection_properties[0].value * scale
#             spike_times = (pq.Quantity(signal, 'ms') +
#                            (pq.ms - self.device_delay * pq.ms))
#             if any(spike_times < 0.0):
#                 raise Pype9RuntimeError(
#                     "Some spike are less than minimum delay and so can't be "
#                     "played into cell ({})".format(
#                         ', '.join(str(t) for t in
#                                   spike_times[spike_times < self.device_delay])))
#             generator = nest.Create(
#                 'spike_generator', 1, {'spike_times': spike_times})
#             nest.Connect(generator, self.nest_cell,
#                          syn_spec={'receptor_type':
#                                    (receptor_types[port_name]
#                                     if receptor_types else 0),
#                                    'delay': float(self.device_delay),
#                                    'weight': float(weight)})
#         self.nest_multimeter = nest.Create(
#             'multimeter', 1, {"interval": self.to_float(self.dt, 'ms')})
#         nest.SetStatus(
#             self.nest_multimeter,
#             {'record_from': [self.nest_state_variable]})
#         nest.Connect(self.nest_multimeter, self.nest_cell)
#         trans_states = {}
#         for name, qty in self.initial_states.iteritems():
#             try:
#                 varname, scale = self.nest_translations[name]
#                 qty = qty * scale
#             except (ValueError, KeyError):
#                 varname = self.nest_translations.get(name, name)
#             value = UnitHandlerNEST.scale_value(qty)
#             if varname is not None:
#                 trans_states[varname] = value
#         nest.SetStatus(self.nest_cell, trans_states)