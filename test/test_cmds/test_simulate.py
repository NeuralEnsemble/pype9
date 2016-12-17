import os.path
import tempfile
import shutil
import neo.io
import nest
import numpy as np
from nineml.units import Quantity
from pype9.cmd import simulate
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
import pyNN.neuron
import pyNN.nest
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
        simulate.run(argv.split())
        isyn = neo.io.PickleIO(in_path).read()[0].analogsignals[0]
        # Check sanity of input signal
        self.assertEqual(isyn.max(), self.isyn_amp[0],
                         "Max of isyn input signal {} did not match specified "
                         "amplitude, {}".format(isyn.max(), self.isyn_amp[0]))
        self.assertEqual(isyn.min(), self.isyn_init[0],
                         "Min of isyn input signal {} did not match specified "
                         "initial value, {}"
                         .format(isyn.min(), self.isyn_init[0]))
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


class TestSimulateNetwork(TestCase):

    brunel_path = 'network/Brunel2000/AI'
    reduced_brunel_fname = 'reduced_brunel.xml'
    recorded_pops = ('Exc', 'Inh')
    reduced_brunel_order = 10
    t_stop = 100.0
    dt = 0.001

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Create reduced version of Brunel network
        model = ninemlcatalog.load(self.brunel_path).as_network(
            'Brunel_AI_reduced')
        scale = self.reduced_brunel_order / model.population('Inh').size
        # rescale populations
        reduced_model = model.clone()
        for pop in reduced_model.populations:
            pop.size = int(np.ceil(pop.size * scale))
        for proj in (reduced_model.projection('Excitation'),
                     reduced_model.projection('Inhibition')):
            props = proj.connectivity.rule_properties
            number = props.property('number')
            props.set(nineml.Property(
                number.name,
                int(np.ceil(float(number.value) * scale)) * un.unitless))
        self.reduced_brunel_path = os.path.join(self.tmpdir,
                                                self.reduced_brunel_fname)
        reduced_model.write(self.reduced_brunel_path)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_network(self):
        nest.ResetKernel()
        for simulator in ('nest', 'neuron'):
            out_path = '{}/{}.neo.pkl'.format(self.tmpdir, simulator)
            argv = (
                "{nineml_model} {sim} {t_stop} {dt} "
                "--record Exc.spikes {out_path} exc "
                "--record Inh.spikes {out_path} inh "
                "--build_mode force"
                .format(nineml_model=self.reduced_brunel_path, sim=simulator,
                        out_path=out_path, t_stop=self.t_stop, dt=self.dt))
            simulate.run(argv.split())
            recs = {}
            for spiketrain in neo.io.PickleIO(out_path).read()[0].spiketrains:
                recs[spiketrain.name] = spiketrain
            ref_recs = self._ref_network(simulator)
            for pop_name in self.recorded_pops:
                self.assertTrue(
                    all(recs[pop_name] == ref_recs[pop_name]),
                    "'simulate' command produced different results to"
                    " to api reference for izhikevich model using "
                    "'{}' simulator".format(simulator))
                # TODO: Need a better test
                self.assertGreater(
                    len(recs[pop_name]), 0,
                    "No spikes generated for '{}' population using {}."
                    .format(pop_name, simulator))

    def _ref_network(self, simulator, external_input=None, **kwargs):
        nest.ResetKernel()
        if simulator == 'nest':
            NetworkClass = NetworkNEST
            pyNN_simulator = pyNN.nest.simulator.state
        elif simulator == 'neuron':
            NetworkClass = NetworkNEURON
            pyNN_simulator = pyNN.neuron.simulator.state
        else:
            assert False
        model = nineml.read(self.reduced_brunel_path).as_network(
            'ReducedBrunel')
        network = NetworkClass(model, **kwargs)
        if external_input is not None:
            network.component_array('Ext').play('spike_input__cell',
                                                external_input)
        for pop_name in self.recorded_pops:
            network.component_array(pop_name).record('spikes')
        pyNN_simulator.run(self.t_stop)
        recordings = {}
        for pop_name in self.recorded_pops:
            recordings[pop_name] = network.component_array(pop_name).recording(
                'spikes')
        return recordings
