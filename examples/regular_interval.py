import os
import nest
from nineml import units as un, MultiDynamics
from pype9.base.cells import WithSynapses, ConnectionParameterSet
from pype9.nest import CellMetaClass, simulation_controller, UnitHandler
import ninemlcatalog
import numpy
from matplotlib import pyplot as plt
build_dir = os.path.join(os.getcwd(), '9build', 'regular_interval')
# Whether weight should be a parameter of the cell or passed as a weight
# parameter
connection_weight = False
# Get and combine 9ML models
input_model = ninemlcatalog.load(
    'input/RegularInterval', 'RegularInterval')
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
    port_exposures=[('psr', 'spike')])
conn_params = []
if connection_weight:
    # FIXME: Need to check that the spike port corresponds to a proper port
    conn_params.append(ConnectionParameterSet(
        'spike__psr', [multi_model.parameter('weight__pls')]))
w_syn_model = WithSynapses.wrap(multi_model,
                                connection_parameter_sets=conn_params)
# Generate Pype9 classes
Input = CellMetaClass(input_model)
Cell = CellMetaClass(w_syn_model, build_dir=build_dir, build_mode='force')
# Create instances
rate = 20.0 * un.Hz
weight = 56.2184675063 * un.pA  # 20.6801552437 * un.pA
input = Input(rate=rate)  # @ReservedAssignment
cell_params = {
    'tau__cell': 20.0 * un.ms, 'e_leak__cell': 0.0 * un.mV,
    'refractory_period__cell': 2.0 * un.ms,
    'Cm__cell': 250.0 * un.pF, 'v_threshold__cell': 20.0 * un.mV,
    'v_reset__cell': 0.0 * un.mV, 'tau__psr': 0.5 * un.ms}
if not connection_weight:
    cell_params['weight__pls'] = weight
cell = Cell(cell_params)
# Connect cells (using underlying NEST connector)
syn_spec = {'receptor_type': 1}
if connection_weight:
    syn_spec['weight'] = UnitHandler.scale_value(weight)
nest.Connect(input._cell, cell._cell, syn_spec=syn_spec)
# Set initial conditions
input.update_state({'t_next': (1 * un.unitless) / rate})
cell.update_state({
    'b__psr': 0.0 * un.nA,
    'a__psr': 0.0 * un.nA,
    'end_refractory__cell': 0.0 * un.ms,
    'v__cell': 0.0 * un.mV})
# Set up recorders
input.record('spike_output')
cell.record('v__cell')
# Run simulation
simulation_controller.run(100.0)
# Get recordings
spikes = input.recording('spike_output')
v = cell.recording('v__cell')
max_v = float(numpy.max(v))
print "required weight: {}".format((0.1 / max_v) * weight)
# Plot recordings
plt.plot(v.times, v)
plt.figure()
plt.scatter(spikes, numpy.ones(len(spikes)))
plt.show()
