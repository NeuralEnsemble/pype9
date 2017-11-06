"""
Constructs a leaky integrate and fire model with an alpha synapse and connects
it to an input source that fires spikes at a constant rate
"""
from __future__ import division
from past.utils import old_div
import os
import nest
from argparse import ArgumentParser
from nineml import units as un, MultiDynamics
from pype9.simulate.common.cells import WithSynapses, ConnectionParameterSet
import ninemlcatalog
import numpy
from matplotlib import pyplot as plt

parser = ArgumentParser(__doc__)
parser.add_argument('--timestep', type=float, default=0.01,
                    help=("Timestep of the simulation"))
parser.add_argument('--weight', type=float, default=3.0,
                    help=("Weight of the synapse (nA)"))
parser.add_argument('--rate', type=float, default=40.0,
                    help=("Rate of the input spike train (Hz)"))
parser.add_argument('--tau', type=float, default=20,
                    help=("Tau parameter of the LIAF model (ms)"))
parser.add_argument('--simtime', type=float, default=200.0,
                    help=("Simulation time (ms)"))
parser.add_argument('--build_mode', type=str, default='lazy',
                    help=("The build mode to apply when creating the cell "
                          "class"))
args = parser.parse_args()

# Import of nest needs to be after arguments have been passed as it kills them
# before the SLI interpreter tries to read them.
from pype9.simulate.nest import CellMetaClass, simulation, UnitHandler  # @IgnorePep8


build_dir = os.path.join(os.getcwd(), '9build', 'liaf_with_alpha')
# Whether weight should be a parameter of the cell or passed as a weight
# parameter
connection_weight = False
# Get and combine 9ML models
input_model = ninemlcatalog.load(
    'input/ConstantRate', 'ConstantRate')
liaf_model = ninemlcatalog.load(
    'neuron/LeakyIntegrateAndFire', 'LeakyIntegrateAndFire')
alpha_model = ninemlcatalog.load(
    'postsynapticresponse/Alpha', 'Alpha')
weight_model = ninemlcatalog.load(
    'plasticity/Static', 'Static')
multi_model = MultiDynamics(
    name="test_alpha_syn",
    sub_components={'cell': liaf_model, 'psr': alpha_model,
                    'pls': weight_model},
    port_connections=[('psr', 'i_synaptic', 'cell', 'i_synaptic'),
                      ('pls', 'fixed_weight', 'psr', 'q')],
    port_exposures=[('psr', 'spike'), ('cell', 'spike_output')])
conn_params = []
if connection_weight:
    # FIXME: Need to check that the spike port corresponds to a proper port
    conn_params.append(ConnectionParameterSet(
        'spike__psr', [multi_model.parameter('weight__pls')]))

# Reinterpret the multi-component model as one containing synapses that can
# be set by connection weights
w_syn_model = WithSynapses.wrap(multi_model,
                                connection_parameter_sets=conn_params)
# Generate Pype9 classes
Input = CellMetaClass(input_model, build_mode=args.build_mode)
Cell = CellMetaClass(w_syn_model, build_dir=build_dir,
                     build_mode=args.build_mode)
# Create instances
rate = args.rate * un.Hz
weight = args.weight * un.nA
input = Input(rate=rate)  # @ReservedAssignment
cell_params = {
    'tau__cell': args.tau * un.ms, 'e_leak__cell': 0.0 * un.mV,
    'refractory_period__cell': 2.0 * un.ms,
    'Cm__cell': 250.0 * un.pF, 'v_threshold__cell': 20.0 * un.mV,
    'v_reset__cell': 0.0 * un.mV, 'tau__psr': 0.5 * un.ms}
if not connection_weight:
    cell_params['weight__pls'] = weight
with simulation(args.timestep * un.ms) as sim:
    cell = Cell(cell_params)
    # Connect cells (using underlying NEST connector)
    syn_spec = {'receptor_type': 1}
    if connection_weight:
        syn_spec['weight'] = UnitHandler.scale_value(weight)
    nest.Connect(input._cell, cell._cell, syn_spec=syn_spec)
    # Set initial conditions
    input.update_state({'t_next': old_div((1 * un.unitless), rate)})
    cell.update_state({
        'b__psr': 0.0 * un.nA,
        'a__psr': 0.0 * un.nA,
        'end_refractory__cell': 0.0 * un.ms,
        'v__cell': 0.0 * un.mV})
    # Set up recorders
    cell.record('spike_output__cell')
    cell.record('v__cell')
    # Run simulation
    sim.run(args.simtime * un.ms)
# Get recordings
spikes = cell.recording('spike_output__cell')
v = cell.recording('v__cell')
max_v = float(numpy.max(v))
# Plot recordings
plt.plot(v.times, v)
plt.title("LIAF with Alpha Syn - Membrane Potential")
plt.ylabel("Membrane Voltage (mV)")
plt.xlabel("Time (ms)")
plt.figure()
plt.scatter(spikes, numpy.ones(len(spikes)))
plt.title('LIAF with Alpha Syn - Output spikes')
plt.xlabel("Time (ms)")
plt.ylabel("Cell Index")
plt.show()
