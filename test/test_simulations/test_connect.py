#!/usr/bin/env python
import sys
import logging
import nineml.units as un
from nineml.abstraction import (
    Dynamics, StateVariable, EventSendPort,
    EventReceivePort, OutputEvent, Regime, OnEvent, Parameter,
    OnCondition, StateAssignment)
# from nineml.abstraction import Alias, AnalogSendPort, AnalogReceivePort
from pype9.simulate.neuron import (
    CellMetaClass as NeuronCellMetaClass,
    Simulation as NeuronSimulation)
argv = sys.argv[1:]  # Save argv before it is clobbered by the NEST init.
from pype9.simulate.nest import ( # @IgnorePep8
    CellMetaClass as NESTCellMetaClass,
    Simulation as NESTSimulation)
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


logger = logging.getLogger('PyPe9')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class TestConnect(TestCase):

    delay = 1 * un.ms

    def test_event_connect(self):  # @UnusedVariable

        rate9ML = Dynamics(
            name="ConstantRate",
            parameters=[Parameter('rate', dimension=un.per_time)],
            state_variables=[StateVariable('t_next', dimension=un.time)],
            event_ports=[EventSendPort('spike_out')],
            regimes=[Regime(
                name='default',
                transitions=[OnCondition(
                    't > t_next',
                    state_assignments=[
                        StateAssignment('t_next', 't + 1.0/rate')],
                    output_events=[OutputEvent('spike_out')])])])

        parrot9ML = Dynamics(
            name="Parrot",
            regimes=[
                Regime(name="default",
                       transitions=[
                           OnEvent("spike_in",
                                   output_events=[
                                       OutputEvent('spike_out')])])],
            event_ports=[EventReceivePort(name='spike_in'),
                         EventSendPort(name='spike_out')])

        for CellMetaClass, Simulation in ((NESTCellMetaClass, NESTSimulation),
                                          (NeuronCellMetaClass,
                                           NeuronSimulation)):
            Rate = CellMetaClass(rate9ML)
            Parrot = CellMetaClass(parrot9ML)
            with Simulation(dt=0.1 * un.ms) as sim:
                rate = Rate(rate=100 * un.Hz, t_next=10 * un.ms)
                parrot = Parrot()
                parrot.connect(rate, 'spike_out', 'spike_in', delay=self.delay)
                rate.record('spike_out')
                parrot.record('spike_out')
                sim.run(100 * un.ms)
            rate_spikes = rate.recording('spike_out')
            parrot_spikes = parrot.recording('spike_out')
            delay = parrot.UnitHandler.to_pq_quantity(self.delay)
            self.assertTrue(all(rate_spikes == (parrot_spikes - delay)),
                            "{} doesn't equal {}".format(rate_spikes,
                                                         parrot_spikes))

#     def test_analog_connect(self):
#
#         step9ML = Dynamics(
#             name="StepCurrent",
#             parameters=[Parameter(dimension=un.current, name="amplitude"),
#                         Parameter(dimension=un.time, name="onset")],
#             analog_ports=[AnalogSendPort(name='i_out',
#                                          dimension=un.current)],
#             state_variables=[StateVariable('i_out', dimension=un.current)],
#             regimes=[Regime(
#                 name='default',
#                 transitions=[
#                     OnCondition(
#                         't > onset',
#                         state_assignments=[
#                             StateAssignment('i_out', 'amplitude')],
#                         target_regime_name='default')])])
#
#         relay9ML = Dynamics(
#             name="Relay",
#             aliases=[Alias('i_out', 'i_in')],
#             analog_ports=[AnalogReceivePort(name='i_in'),
#                           AnalogSendPort(name='i_out')],
#             regimes=[Regime(name='default')])
#
#         for CellMetaClass, Simulation in (
#             (NESTCellMetaClass, NESTSimulation),
#                 (NeuronCellMetaClass, NeuronSimulation)):
#             Step = CellMetaClass(step9ML)
#             Relay = CellMetaClass(relay9ML)
#             with Simulation(dt=0.1 * un.ms) as sim:
#                 step = Step(amplitude=50 * un.nA, onset=50 * un.ms,
#                             i_out=0 * un.A)
#                 relay = Relay()
#                 relay.connect(step, 'i_out', 'i_in', delay=self.delay)
#                 step.record('i_out')
#                 relay.record('i_out')
#                 sim.run(100 * un.ms)
#             step_i = step.recording('spike_out')
#             relay_i = relay.recording('spike_out')
#             delay = relay.UnitHandler.to_pq_quantity(self.delay)
#             self.assertTrue(all(step_i == (relay_i - delay)),
#                             "{} doesn't equal {}".format(step_i, relay_i))
