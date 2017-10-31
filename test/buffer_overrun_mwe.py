from __future__ import division
from __future__ import print_function
import ninemlcatalog
import numpy
from nineml import units as un, Property
from pype9.simulate.neuron import (
    Network, Simulation, ComponentArray)

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
    # Get RNG for random distribution values and connectivity
    rng = Simulation.active().properties_rng
    (flat_comp_arrays, flat_conn_groups,
     flat_selections) = Network._flatten_to_arrays_and_conns(model)
    exc = ComponentArray(flat_comp_arrays['Exc'],
                         build_dir='/Users/tclose/__pype9__/Exc',
                         build_mode='purge')
    sim.run(20 * un.ms)
print("Done testing")
