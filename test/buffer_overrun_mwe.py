from __future__ import division
from __future__ import print_function
import ninemlcatalog
import numpy
from itertools import chain
from nineml import units as un, Property
from pype9.simulate.neuron import (
    Network, Simulation, UnitHandler, PyNNCellWrapperMetaClass,
    CellMetaClass)
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
with Simulation(dt=0.01 * un.ms, seed=1) as sim:
    rng = Simulation.active().properties_rng
    (flat_comp_arrays, flat_conn_groups,
     flat_selections) = Network._flatten_to_arrays_and_conns(model)
    nineml_model = flat_comp_arrays['Exc']
    dynamics_properties = nineml_model.dynamics_properties
    dynamics = dynamics_properties.component_class
    print(35)
#     celltype = PyNNCellWrapperMetaClass(
#         name=nineml_model.name, component_class=dynamics,
#         default_properties=dynamics_properties,
#         initial_state=list(dynamics_properties.initial_values),
#         initial_regime=dynamics_properties.initial_regime,
#         build_mode='purge')
    model = CellMetaClass(
        component_class=dynamics,
        default_properties=dynamics_properties,
        initial_state=list(dynamics_properties.initial_values),
        name=nineml_model.name,
        build_mode='purge', standalone=False)
    dct = {'model': model,
           'default_properties': dynamics_properties,
           'initial_state': list(dynamics_properties.initial_values),
           'initial_regime': dynamics_properties.initial_regime,
           'extra_parameters': {'_in_array': True}}
#     celltype = super(PyNNCellWrapperMetaClass, cls).__new__(
#         cls, name, (PyNNCellWrapper,), dct)
    component_class = dct['model'].component_class
    default_properties = dct['default_properties']  # @UnusedVariable
    initial_state = dct['initial_state']  # @UnusedVariable
    initial_regime_index = dct['model'].regime_index(dct['initial_regime'])
    dct['parameter_names'] = tuple(component_class.parameter_names)
    dct['recordable'] = list(chain(('spikes',),
                                    component_class.send_port_names,
                                    component_class.state_variable_names))
    dct['receptor_types'] = tuple(component_class.event_receive_port_names)
    # List units for each state variable
    dct['units'] = dict(
        (sv.name, UnitHandler.to_pq_quantity(
            1 * UnitHandler.dimension_to_units(sv.dimension)))
        for sv in component_class.state_variables)
    dct["default_parameters"] = dict(
        (p.name, (
            UnitHandler.scale_value(p.quantity)
            if p.value.nineml_type == 'SingleValue' else float('nan')))
        for p in default_properties)
    dct["default_initial_values"] = dict(
        (i.name, (
            UnitHandler.scale_value(i.quantity)
            if i.value.nineml_type == 'SingleValue' else float('nan')))
        for i in initial_state)
    dct['default_initial_values']['_regime'] = initial_regime_index
    dct["weight_variables"] = (
        component_class.all_connection_parameter_names())
    # FIXME: Need to determine whether cell is "injectable" and/or
    #        conductance-based
    dct["injectable"] = True
    dct["conductance_based"] = True
    recordable_keys = list(model(dynamics_properties,
                                 _in_array=True).recordable.keys())
    print(42)
print("Done testing")
