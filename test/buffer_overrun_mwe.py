from __future__ import division
from __future__ import print_function
import ninemlcatalog
import numpy
from nineml import units as un, Property
from pype9.simulate.neuron import (
    Network, Simulation, CellMetaClass)
try:
    from mpi4py import MPI  # @UnusedImport @IgnorePep8 This is imported before NEURON to avoid a bug in NEURON
except ImportError:
    pass
from neuron import h
DEFAULT_CM = 1.0 * un.nF  # Chosen to match point processes (...I think).

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

(flat_comp_arrays, flat_conn_groups,
 flat_selections) = Network._flatten_to_arrays_and_conns(model)
nineml_model = flat_comp_arrays['Exc']

# model_path = '/Users/tclose/pype9/test/exc.yml'
# 
# nineml_model.write(model_path)
# nineml_model = nineml.read(model_path)['Exc']

mech_name = 'buff_overrun_exc'
build_dir = '/Users/tclose/__pype9__/mwe_buffer_overrun'

with Simulation(dt=0.01 * un.ms, seed=1) as sim:
#     dynamics_properties = nineml_model.dynamics_properties
#     dynamics = dynamics_properties.component_class
#     model = CellMetaClass(
#         component_class=dynamics,
#         default_properties=dynamics_properties,
#         initial_state=list(dynamics_properties.initial_values),
#         name=mech_name,
#         build_mode='purge', standalone=False,
#         build_dir=build_dir)
    CellMetaClass.load_libraries(None, build_dir)
    # Construct all the NEURON structures
    _sec = h.Section()  # @UndefinedVariable
    # Insert dynamics mechanism (the built component class)
    HocClass = getattr(h, mech_name)
    _hoc = HocClass(0.5, sec=_sec)
    # Set capacitance in NMODL
    print(float(DEFAULT_CM.in_units(un.nF)))
    setattr(_hoc, 'cm___pype9', 1.0)
#             float(DEFAULT_CM.in_units(un.nF)))
    rec = h.NetCon(_hoc, None, sec=_sec)
print("Done testing")
