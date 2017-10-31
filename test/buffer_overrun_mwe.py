from __future__ import division
from __future__ import print_function
import ninemlcatalog
import numpy
from nineml import units as un, Property
from pype9.simulate.neuron import (
    Network, Simulation, UnitHandler, PyNNCellWrapperMetaClass)
from pyNN.neuron import simulator
from pype9.simulate.common.network.values import get_pyNN_value

model = ninemlcatalog.load('network/Brunel2000/AI').as_network('Brunel_AI')
# Don't clone so that the url is not reset
model = model.clone()
scale = 1 / model.population('Inh').size
# rescale populations
for pop in model.populations:
    pop.size = int(numpy.ceil(pop.size * scale))
for proj in (model.projection('Excitation'),
             model.projection('Inhibition')):
    props = proj.connectivity.rule_properties
    number = props.property('number')
    props.set(Property(
        number.name,
        int(numpy.ceil(float(number.value) * scale)) * un.unitless))

model.population('Ext').cell['rate'] = 300 / un.s
print(27)
with Simulation(dt=0.01 * un.ms, seed=1) as sim:
    rng = Simulation.active().properties_rng
    (flat_comp_arrays, flat_conn_groups,
     flat_selections) = Network._flatten_to_arrays_and_conns(model)
    nineml_model = flat_comp_arrays['Exc']
    dynamics_properties = nineml_model.dynamics_properties
    dynamics = dynamics_properties.component_class
    print(35)
    celltype = PyNNCellWrapperMetaClass(
        name=nineml_model.name, component_class=dynamics,
        default_properties=dynamics_properties,
        initial_state=list(dynamics_properties.initial_values),
        initial_regime=dynamics_properties.initial_regime,
        build_mode='purge')
    print(41)
    rng = Simulation.active().properties_rng
    cellparams = dict(
        (p.name, get_pyNN_value(p, UnitHandler, rng))
        for p in dynamics_properties.properties)
    initial_values = dict(
        (i.name, get_pyNN_value(i, UnitHandler, rng))
        for i in dynamics_properties.initial_values)
    initial_values['_regime'] = celltype.model.regime_index(
        dynamics_properties.initial_regime)
    print(51)
    size = nineml_model.size
    first_id = simulator.state.gid_counter
    last_id = simulator.state.gid_counter + size - 1
    all_cells = numpy.array([id for id in range(first_id, last_id + 1)],  # @ReservedAssignment @IgnorePep8
                            simulator.ID)
    parameter_space = celltype.parameter_space
    parameter_space.shape = (size,)
    parameter_space.evaluate(mask=None)
    print(60)
    for i, (id, is_local, params) in enumerate(zip(all_cells, parameter_space)):  # @ReservedAssignment @IgnorePep8
        all_cells[i] = simulator.ID(id)
        if is_local:
            if hasattr(celltype, "extra_parameters"):
                params.update(celltype.extra_parameters)
            all_cells[i]._build_cell(celltype.model, params)
    sim.run(20 * un.ms)
print("Done testing")
