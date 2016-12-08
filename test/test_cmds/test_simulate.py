import os.path
import tempfile
import shutil
import neo.io
import nest
from nineml.units import Quantity
from pype9.cmd import simulate, convert
from pype9.cmd._utils import parse_units
import ninemlcatalog
from pype9.neuron import (
    CellMetaClass as CellMetaClassNEURON,
    simulation_controller as simulatorNEURON,
    Network as NetworkNEURON)
from pype9.nest import (
    CellMetaClass as CellMetaClassNEST,
    simulation_controller as simulatorNEST,
    Network as NetworkNEST)
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestSimulate(TestCase):

    ref_path = ''

    # Izhikevich simulation params
    t_stop = 100.0
    dt = 0.001
    U = (-14.0, 'mV/ms')
    V = (-65.0, 'mV')
    izhi_path = '//neuron/Izhikevich#SampleIzhikevich'
    isyn_path = os.path.join(os.path.relpath(ninemlcatalog.root), 'input',
                             'StepCurrent.xml#StepCurrent')
    isyn_amp = (20.0, 'pA')
    isyn_onset = (50.0, 'ms')
    isyn_init = (0.0, 'pA')

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_single_cell(self):
        in_path = '{}/isyn.pkl'.format(self.tmpdir)
        out_path = '{}/v.pkl'.format(self.tmpdir)
        # First simulate input signal to have something to play into izhikevich
        # cell
        argv = ("{input_model} nest {t_stop} {dt} "
                "--record current_output {out_path} isyn "
                "--prop amplitude {amp} "
                "--prop onset {onset} "
                "--init_value current_output {init} "
                "--build_mode lazy"
                .format(input_model=self.isyn_path, out_path=in_path,
                        t_stop=self.t_stop, dt=self.dt,
                        U='{} {}'.format(*self.U), V='{} {}'.format(*self.V),
                        amp='{} {}'.format(*self.isyn_amp),
                        onset='{} {}'.format(*self.isyn_onset),
                        init='{} {}'.format(*self.isyn_init)))
        # Run input signal simulation
        print "running input simulation"
        simulate.run(argv.split())
        print "finished running input simulation"
        isyn = neo.io.PickleIO(in_path).read()[0].analogsignals[0]
        # Check sanity of input signal
        self.assertEqual(isyn.max(), self.isyn_amp[0],
                         "Max of isyn input signal {} did not match specified "
                         "amplitude, {}".format(isyn.max(), self.isyn_amp[0]))
        self.assertEqual(isyn.min(), self.isyn_init[0],
                         "Min of isyn input signal {} did not match specified "
                         "initial value, {}"
                         .format(isyn.max(), self.isyn_init[0]))
        nest.ResetKernel()
        for simulator in ('nest', 'neuron'):
            argv = (
                "{nineml_model} {sim} {t_stop} {dt} "
                "--record V {out_path} v "
                "--init_value U {U} "
                "--init_value V {V} "
                "--play Isyn {in_path} isyn "
                "--build_mode force"
                .format(nineml_model=self.izhi_path, sim=simulator,
                        out_path=out_path, in_path=in_path, t_stop=self.t_stop,
                        dt=self.dt, U='{} {}'.format(*self.U),
                        V='{} {}'.format(*self.V),
                        isyn_amp='{} {}'.format(*self.isyn_amp),
                        isyn_onset='{} {}'.format(*self.isyn_onset),
                        isyn_init='{} {}'.format(*self.isyn_init)))
            simulate.run(argv.split())
            v = neo.io.PickleIO(out_path).read()[0].analogsignals[0]
            ref_v = self._ref_single_cell(simulator, isyn)
            self.assertTrue(all(v == ref_v),
                             "'simulate' command produced different results to"
                             " to api reference for izhikevich model using "
                             "'{}' simulator".format(simulator))
            # TODO: Need a better test
            self.assertGreater(
                v.max(), -60.0,
                "No spikes generated for '{}' (max val: {}) version of Izhi "
                "model. Probably error in 'play' method if all dynamics tests "
                "pass ".format(simulator, v.max()))
# 
#     def test_network(self):
#         record_duration = simtime - record_start
#         # Construct 9ML network
#         self._setup('nest')
#         # Set up spike recorders for reference network
#         pops = {'nineml': nml, 'reference': ref}
#         spikes = {}
#         multi = {}
#         for model_ver in ('nineml', 'reference'):
#             spikes[model_ver] = {}
#             multi[model_ver] = {}
#             for pop_name in record_pops:
#                 pop = numpy.asarray(pops[model_ver][pop_name], dtype=int)
#                 record_inds = numpy.asarray(numpy.unique(numpy.floor(
#                     numpy.arange(start=0, stop=len(pop),
#                                  step=len(pop) / record_size))), dtype=int)
#                 spikes[model_ver][pop_name] = nest.Create("spike_detector")
#                 nest.SetStatus(spikes[model_ver][pop_name],
#                                [{"label": "brunel-py-" + pop_name,
#                                  "withtime": True, "withgid": True}])
#                 nest.Connect(list(pop[record_inds]),
#                              spikes[model_ver][pop_name],
#                              syn_spec="excitatory")
#                 if record_states:
#                     # Set up voltage traces recorders for reference network
#                     if self.record_params[pop_name][model_ver]:
#                         multi[model_ver][pop_name] = nest.Create(
#                             'multimeter',
#                             params={'record_from':
#                                     self.record_params[pop_name][model_ver]})
#                         nest.Connect(multi[model_ver][pop_name],
#                                      list(pop[record_inds]))
#         # Simulate the network
#         nest.Simulate(simtime)
#         rates = {'reference': {}, 'nineml': {}}
#         psth = {'reference': {}, 'nineml': {}}
#         for model_ver in ('reference', 'nineml'):
#             for pop_name in record_pops:
#                 events = nest.GetStatus(spikes[model_ver][pop_name],
#                                         "events")[0]
#                 spike_times = numpy.asarray(events['times'])
#                 senders = numpy.asarray(events['senders'])
#                 inds = numpy.asarray(spike_times > record_start, dtype=bool)
#                 spike_times = spike_times[inds]
#                 senders = senders[inds]
#                 rates[model_ver][pop_name] = (
#                     1000.0 * len(spike_times) / record_duration)
#                 psth[model_ver][pop_name] = (
#                     numpy.histogram(
#                         spike_times,
#                         bins=int(numpy.floor(record_duration /
#                                              bin_width)))[0] /
#                     bin_width)
#                 if plot:
#                     plt.figure()
#                     plt.scatter(spike_times, senders)
#                     plt.xlabel('Time (ms)')
#                     plt.ylabel('Cell Indices')
#                     plt.title("{} - {} Spikes".format(model_ver, pop_name))
#                     plt.figure()
#                     plt.hist(spike_times,
#                              bins=int(
#                                  numpy.floor(record_duration / bin_width)))
#                     plt.xlabel('Time (ms)')
#                     plt.ylabel('Rate')
#                     plt.title("{} - {} PSTH".format(model_ver, pop_name))
#                     if record_states:
#                         for param in self.record_params[pop_name][model_ver]:
#                             events, interval = nest.GetStatus(
#                                 multi[model_ver][pop_name], ["events",
#                                                              'interval'])[0]
#                             sorted_vs = sorted(zip(events['senders'],
#                                                    events['times'],
#                                                    events[param]),
#                                                key=itemgetter(0))
#                             plt.figure()
#                             legend = []
#                             for sender, group in groupby(sorted_vs,
#                                                          key=itemgetter(0)):
#                                 _, t, v = zip(*group)
#                                 t = numpy.asarray(t)
#                                 v = numpy.asarray(v)
#                                 inds = t > record_start
#                                 plt.plot(t[inds] * interval, v[inds])
#                                 legend.append(sender)
#                             plt.xlabel('Time (ms)')
#                             plt.ylabel(param)
#                             plt.title("{} - {} {}".format(model_ver, pop_name,
#                                                           param))
#                             plt.legend(legend)
#         for pop_name in record_pops:
#             if rates['reference'][pop_name]:
#                 percent_rate_error = abs(
#                     rates['nineml'][pop_name] /
#                     rates['reference'][pop_name] - 1.0) * 100
#             elif not rates['nineml'][pop_name]:
#                 percent_rate_error = 0.0
#             else:
#                 percent_rate_error = float('inf')
#             self.assertLess(
#                 percent_rate_error,
#                 self.rate_percent_error[pop_name], msg=(
#                     "Rate of '{}' ({}) doesn't match reference ({}) within {}%"
#                     " ({}%)".format(pop_name, rates['nineml'][pop_name],
#                                     rates['reference'][pop_name],
#                                     self.rate_percent_error[pop_name],
#                                     percent_rate_error)))
#             if numpy.std(psth['reference'][pop_name]):
#                 percent_psth_stdev_error = abs(
#                     numpy.std(psth['nineml'][pop_name]) /
#                     numpy.std(psth['reference'][pop_name]) - 1.0) * 100
#             elif not numpy.std(psth['nineml'][pop_name]):
#                 percent_psth_stdev_error = 0.0
#             else:
#                 percent_psth_stdev_error = float('inf')
#             self.assertLess(
#                 percent_psth_stdev_error,
#                 self.psth_percent_error[pop_name],
#                 msg=(
#                     "Std. Dev. of PSTH for '{}' ({}) doesn't match "
#                     "reference ({}) within {}% ({}%)".format(
#                         pop_name,
#                         numpy.std(psth['nineml'][pop_name]) / bin_width,
#                         numpy.std(psth['reference'][pop_name]) / bin_width,
#                         self.psth_percent_error[pop_name],
#                         percent_psth_stdev_error)))
#         if plot:
#             plt.show()

    def _ref_single_cell(self, simulator, isyn):
        if simulator == 'neuron':
            metaclass = CellMetaClassNEURON
            simulation_controller = simulatorNEURON
        else:
            nest.ResetKernel()
            metaclass = CellMetaClassNEST
            simulation_controller = simulatorNEST
        nineml_model = ninemlcatalog.load(self.izhi_path)
        cell = metaclass(nineml_model.component_class,
                         name='izhikevichAPI')(nineml_model)
        cell.set_state({'U': Quantity(self.U[0], parse_units(self.U[1])),
                           'V': Quantity(self.V[0], parse_units(self.V[1]))})
        cell.record('V')
        cell.play('Isyn', isyn)
        simulation_controller.run(self.t_stop)
        return cell.recording('V')

    def _ref_network(self, simulator):
        pass
