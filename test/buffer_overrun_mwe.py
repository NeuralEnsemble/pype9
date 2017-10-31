from __future__ import division
from __future__ import print_function
import ninemlcatalog
import numpy
from itertools import chain
from nineml import units as un, Property
from pype9.simulate.neuron import (
    Network, Simulation, CellMetaClass)
import nineml
from builtins import zip
from past.utils import old_div
try:
    from mpi4py import MPI  # @UnusedImport @IgnorePep8 This is imported before NEURON to avoid a bug in NEURON
except ImportError:
    pass
import os.path
import collections
from itertools import chain
import operator
import quantities as pq
import neo
from pype9.simulate.neuron.cells.code_gen import CodeGenerator, REGIME_VARNAME
from neuron import h, load_mechanisms
from nineml import units as un
from nineml.abstraction import EventPort
from nineml.exceptions import NineMLNameError
from math import pi
from pype9.simulate.common.cells import base
from pype9.simulate.neuron.units import UnitHandler
from pype9.simulate.neuron.simulation import Simulation
from pype9.annotations import (
    PYPE9_NS, BUILD_TRANS, MEMBRANE_CAPACITANCE, EXTERNAL_CURRENTS,
    MEMBRANE_VOLTAGE, MECH_TYPE, ARTIFICIAL_CELL_MECH)
from pype9.exceptions import (
    Pype9RuntimeError, Pype9UsageError, Pype9Unsupported9MLException)
import logging

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

with Simulation(dt=0.01 * un.ms, seed=1) as sim:
    rng = Simulation.active().properties_rng

    dynamics_properties = nineml_model.dynamics_properties
    dynamics = dynamics_properties.component_class
    print(43)
    model = CellMetaClass(
        component_class=dynamics,
        default_properties=dynamics_properties,
        initial_state=list(dynamics_properties.initial_values),
        name=nineml_model.name,
        build_mode='purge', standalone=False)
    print(50)
#     model(dynamics_properties, _in_array=True)
    component_class = dynamics
    # Construct all the NEURON structures
    _sec = h.Section()  # @UndefinedVariable
    # Insert dynamics mechanism (the built component class)
    HocClass = getattr(h, nineml_model.name)
    _hoc = HocClass(0.5, sec=_sec)
    # A recordable of 'spikes' is needed for PyNN compatibility
    recordable = {'spikes': None}
    # Add a recordable entry for each event send ports
    # TODO: These ports aren't able to be recorded from at present because
    #       different event ports are not distinguishable in Neuron (well
    #       not easily anyway). Users should use 'spikes' instead for now
#     for port in chain(component_class.event_send_ports):
#         recordable[port.name] = None
#     for port in chain(component_class.analog_send_ports,
#                       component_class.state_variables):
#         if port.name != component_class.annotations.get(
#                 (BUILD_TRANS, PYPE9_NS), MEMBRANE_VOLTAGE, default=None):
#             recordable[port.name] = getattr(
#                 _hoc, '_ref_' + port.name)
    # Get the membrane capacitance property if not an artificial cell
    if model.build_component_class.annotations.get(
            (BUILD_TRANS, PYPE9_NS), MECH_TYPE) == ARTIFICIAL_CELL_MECH:
        cm_param_name = None
    else:
        # In order to scale the distributed current to the same units as
        # point process current, i.e. mA/cm^2 -> nA the surface area needs
        # to be 100um. mA/cm^2 = -3-(-2^2) = 10^1, 100um^2 = 2 + -6^2 =
        # 10^(-10), nA = 10^(-9). 1 - 10 = - 9. (see PyNN Izhikevich neuron
        # implementation)
        _sec.L = 10.0
        _sec.diam = 10.0 / pi
        cm_param_name = model.build_component_class.annotations.get(
            (BUILD_TRANS, PYPE9_NS), MEMBRANE_CAPACITANCE)
        if cm_param_name not in component_class.parameter_names:
            # Set capacitance to capacitance of section to default value
            # for input currents
            # Set capacitance in NMODL
            setattr(_hoc, cm_param_name,
                    float(DEFAULT_CM.in_units(un.nF)))
            # Set capacitance in HOC section
            surface_area = (_sec.L * un.um) * (_sec.diam * pi * un.um)
            specific_cm = DEFAULT_CM / surface_area
            _sec.cm = float(specific_cm.in_units(un.uF / un.cm ** 2))
#         recordable[component_class.annotations.get(
#             (BUILD_TRANS, PYPE9_NS),
#             MEMBRANE_VOLTAGE)] = _sec(0.5)._ref_v
    # Set up members required for PyNN
    spike_times = h.Vector(0)
    traces = {}
    gsyn_trace = {}
    recording_time = 0
    rec = h.NetCon(_hoc, None, sec=_sec)
    def _set(varname, val):  # @IgnorePep8
        try:
            setattr(_hoc, varname, val)
            # If capacitance, also set the section capacitance
            if varname == cm_param_name:
                # This assumes that the value of the capacitance is in nF
                # which it should be from the super setattr method
                _sec.cm = float((
                    val * un.nF / surface_area).in_units(old_div(un.uF,
                                                                 un.cm ** 2)))
        except LookupError:
            varname = _escaped_name(varname)
            try:
                setattr(_sec, varname, val)
            except AttributeError:
                # Check to see if parameter has been removed in build
                # transform and if not raise the error
                if varname not in dynamics.parameter_names:
                    raise AttributeError(
                        "Could not set '{}' to hoc object or NEURON section"
                        .format(varname))
    _inputs = {}
    _input_auxs = []
    # Need to use the build_component_class to get the same index as was
    # used to construct the indices
    # FIXME: These indices will need to be saved somewhere in the
    #        annotations of the build class so they can be reloaded
    if model.build_component_class.num_event_receive_ports:
        ports_n_indices = [
            (model.build_component_class.index_of(p), p.name)
            for p in model.build_component_class.event_receive_ports]
        # Get event receive ports sorted by the indices
        sorted_ports = list(zip(
            *sorted(ports_n_indices, key=operator.itemgetter(0))))[1]
    else:
        sorted_ports = []
    type = collections.namedtuple('Type', 'receptor_types')(
        sorted_ports)
    # Call base init (needs to be after 9ML init)
#     super(Cell, self).__init__(*args, **kwargs)
    # Flag to determine whether the cell has been initialized or not
    # (it makes a difference to how the state of the cell is updated,
    # either saved until the 'initialze' method is called or directly
    # set to the state)
    sim = Simulation.active()
    t_start = sim.t_start
    _t_stop = None
    print(52)
print("Done testing")
