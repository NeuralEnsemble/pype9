import os.path
import tempfile
import shutil
import neo.io
import numpy as np
from pype9.cmd import simulate
from pype9.cmd._utils import parse_units
import ninemlcatalog
from pype9.simulator.neuron import (
    Simulation as NeuronSimulation,
    CellMetaClass as NeuronCellMetaClass,
    Network as NetworkNEURON)
from pype9.simulator.nest import (
    Simulation as NESTSimulation,
    CellMetaClass as NESTCellMetaClass,
    Network as NetworkNEST)
import nineml
import nineml.units as un
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestSimulateCell(TestCase):

    ref_path = ''

    # Izhikevich simulation params
    t_stop = 100.0
    dt = 0.001
    U = (-14.0, 'mV/ms')
    V = (-65.0, 'mV')
    izhi_path = '//neuron/Izhikevich#IzhikevichFastSpikingDefault'
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
                "--record current_output {out_path} "
                "--prop amplitude {amp} "
                "--prop onset {onset} "
                "--init_value current_output {init} "
                "--build_mode force"  # FIXME: This should be converted to lazy
                .format(input_model=self.isyn_path, out_path=in_path,
                        t_stop=self.t_stop, dt=self.dt,
                        amp='{} {}'.format(*self.isyn_amp),
                        onset='{} {}'.format(*self.isyn_onset),
                        init='{} {}'.format(*self.isyn_init)))
        # Run input signal simulation
        simulate.run(argv.split())
        isyn = neo.io.PickleIO(in_path).read()[0].analogsignals[0]
        # Check sanity of input signal
        self.assertEqual(isyn.max(), self.isyn_amp[0],
                         "Max of isyn input signal {} ({}) did not match "
                         "specified amplitude, {}".format(
                             isyn.max(), in_path, self.isyn_amp[0]))
        self.assertEqual(isyn.min(), self.isyn_init[0],
                         "Min of isyn input signal {} ({}) did not match "
                         "specified initial value, {}"
                         .format(isyn.min(), in_path, self.isyn_init[0]))
        for simulator in ('nest', 'neuron'):
            argv = (
                "{nineml_model} {sim} {t_stop} {dt} "
                "--record V {out_path} "
                "--init_value U {U} "
                "--init_value V {V} "
                "--init_regime subVb"
                "--play Isyn {in_path} "
                "--build_mode force"
                .format(nineml_model=self.izhi_path, sim=simulator,
                        out_path=out_path, in_path=in_path, t_stop=self.t_stop,
                        dt=self.dt, U='{} {}'.format(*self.U),
                        V='{} {}'.format(*self.V),
                        isyn_amp='{} {}'.format(*self.isyn_amp),
                        isyn_onset='{} {}'.format(*self.isyn_onset),
                        isyn_init='{} {}'.format(*self.isyn_init)))
            simulate.run(argv.split())
            data_seg = neo.io.PickleIO(out_path).read()[0]
            v = data_seg.analogsignals[0]
            regimes = data_seg.epocharrays[0]
            ref_v, ref_regimes = self._ref_single_cell(simulator, isyn)
            self.assertTrue(all(v == ref_v),
                             "'simulate' command produced different results to"
                             " to api reference for izhikevich model using "
                             "'{}' simulator".format(simulator))
            # FIXME: Need a better test
            self.assertGreater(
                v.max(), -60.0,
                "No spikes generated for '{}' (max val: {}) version of Izhi "
                "model. Probably error in 'play' method if all dynamics tests "
                "pass ".format(simulator, v.max()))
            self.assertTrue(all(regimes.times == ref_regimes.times))
            self.assertTrue(all(regimes.durations == ref_regimes.durations))
            self.assertTrue(all(regimes.labels == ref_regimes.labels))
            self.assertEqual(regimes.labels[0], 'subVb')
            self.assertTrue('subthreshold' in regimes.labels)

    def _ref_single_cell(self, simulator, isyn):
        if simulator == 'neuron':
            metaclass = NeuronCellMetaClass
            Simulation = NeuronSimulation
        else:
            metaclass = NESTCellMetaClass
            Simulation = NESTSimulation
        nineml_model = ninemlcatalog.load(self.izhi_path)
        Cell = metaclass(nineml_model.component_class, name='izhikevichAPI')
        with Simulation(dt=self.dt * un.ms) as sim:
            cell = Cell(nineml_model, U=self.U[0] * parse_units(self.U[1]),
                        V=self.V[0] * parse_units(self.V[1]))
            cell.record('V')
            cell.play('Isyn', isyn)
            sim.run(self.t_stop * un.ms)
        return cell.recording('V'), cell.regime_epochs()


class TestSimulateNetwork(TestCase):

    brunel_path = 'network/Brunel2000/AI'
    brunel_name = 'Brunel_AI_reduced'
    reduced_brunel_fname = 'reduced_brunel.xml'
    recorded_pops = ('Exc', 'Inh')
    reduced_brunel_order = 10
    t_stop = 100.0
    dt = 0.001
    seed = 12345

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Create reduced version of Brunel network
        model = ninemlcatalog.load(self.brunel_path).as_network(
            self.brunel_name)
        scale = float(self.reduced_brunel_order) / model.population('Inh').size
        # rescale populations
        reduced_model = model.clone()
        for pop in reduced_model.populations:
            pop.size = int(np.ceil(pop.size * scale))
        for proj in reduced_model.projections:
            connectivity = proj.connectivity
            connectivity._src_size = proj.pre.size
            connectivity._dest_size = proj.post.size
            if proj.name in ('Excitation', 'Inhibition'):
                props = connectivity.rule_properties
                number = props.property('number')
                props.set(nineml.Property(
                    number.name,
                    int(np.ceil(float(number.value) * scale)) * un.unitless))
        self.reduced_brunel_path = os.path.join(self.tmpdir,
                                                self.reduced_brunel_fname)
        reduced_model.write(self.reduced_brunel_path)  # , version=2)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_network(self):
        for simulator in ('nest', ):  # , 'neuron'):
            argv = (
                "{model_url}#{model_name} {sim} {t_stop} {dt} "
                "--record Exc.spike_output {tmpdir}/Exc-{sim}.neo.pkl "
                "--record Inh.spike_output {tmpdir}/Inh-{sim}.neo.pkl "
                "--build_mode force "
                "--seed {seed}"
                .format(model_url=self.reduced_brunel_path,
                        model_name=self.brunel_name, sim=simulator,
                        tmpdir=self.tmpdir, t_stop=self.t_stop, dt=self.dt,
                        seed=self.seed))
            simulate.run(argv.split())
            ref_recs = self._ref_network(simulator)
            for pop_name in self.recorded_pops:
                rec_path = '{}/{}-{}.neo.pkl'.format(self.tmpdir, pop_name,
                                                     simulator)
                rec = neo.io.PickleIO(rec_path).read()[0].spiketrains
                ref = ref_recs[pop_name].spiketrains
                self.assertTrue(
                    all(all(c == f) for c, f in zip(rec, ref)),
                    "'simulate' command produced different results to"
                    " to api reference for izhikevich model using "
                    "'{}' simulator".format(simulator))
                # TODO: Need a better test
                self.assertGreater(
                    len(rec), 0,
                    "No spikes generated for '{}' population using {}."
                    .format(pop_name, simulator))

    def _ref_network(self, simulator, external_input=None, **kwargs):
        if simulator == 'nest':
            NetworkClass = NetworkNEST
            Simulation = NESTSimulation
        elif simulator == 'neuron':
            NetworkClass = NetworkNEURON
            Simulation = NeuronSimulation
        else:
            assert False
        model = nineml.read(self.reduced_brunel_path).as_network(
            'ReducedBrunel')
        with Simulation(dt=self.dt * un.ms, seed=self.seed,
                        **model.delay_limits()) as sim:
            network = NetworkClass(model, **kwargs)
            if external_input is not None:
                network.component_array('Ext').play('spike_input__cell',
                                                    external_input)
            for pop_name in self.recorded_pops:
                network.component_array(pop_name).record('spike_output')
            sim.run(self.t_stop * un.ms)
        recordings = {}
        for pop_name in self.recorded_pops:
            recordings[pop_name] = network.component_array(pop_name).recording(
                'spike_output')
        return recordings
