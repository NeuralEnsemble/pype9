"""

  This package contains the XML handlers to read the NineML files and related
  functions/classes, the NineML base meta-class (a meta-class is a factory that
  generates classes) to generate a class for each NineML cell description (eg.
  a 'Purkinje' class for an NineML containing a declaration of a Purkinje
  cell), and the base class for each of the generated cell classes.

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from pype9.exceptions import Pype9RuntimeError, Pype9AttributeError
from itertools import chain
import time
import os.path
import quantities as pq
import nineml
from nineml.abstraction import Dynamics, Parameter
from nineml.user import Property, Quantity, Definition
from nineml.exceptions import name_error, NineMLNameError
from nineml.abstraction import BaseALObject
from nineml.user import BaseULObject


class CellMetaClass(type):

    """
    Metaclass for building NineMLCellType subclasses Called by
    nineml_celltype_from_model
    """

    def __new__(cls, component_class, default_properties=None,
                initial_states=None, name=None, saved_name=None, **kwargs):
        """
        `component_class`    -- A nineml.abstraction.Dynamics object
        `default_properties` -- default properties, if None, then all props = 0
        `initial_states`     -- initial states, if None, then all states = 0
        `name`               -- the name for the class
        `saved_name`         -- the name of the Dynamics object in the document
                                if diferent from the `name`
        """
        if not isinstance(component_class, Dynamics):
            raise Pype9RuntimeError(
                "Component class ({}) needs to be nineml Dynamics object")
        if (default_properties is not None and
                default_properties.component_class != component_class):
            raise Pype9RuntimeError(
                "Component class of default properties object ({}) does not "
                "match provided class ({})".format(
                    default_properties.component_class, component_class))
        # Extract out build directives
        build_mode = kwargs.pop('build_mode', 'lazy')
        verbose = kwargs.pop('verbose', False)
        if name is None:
            if saved_name is not None:
                name = saved_name
            else:
                name = component_class.name
        url = component_class.url
        try:
            Cell, build_options = cls._built_types[(name, url)]
            if build_options != kwargs:
                raise Pype9RuntimeError(
                    "Build options '{}' do not match previously built '{}' "
                    "cell class with same name ('{}'). Please specify a "
                    "different name (using a loaded nineml.Component instead "
                    "of a URL)."
                    .format(kwargs, name, build_options))
        except KeyError:
            # Initialise code generator
            code_gen = cls.CodeGenerator()
            (build_component_class, build_properties,
             build_initial_states) = code_gen.transform_for_build(
                component_class, default_properties, initial_states, **kwargs)
            # Set build dir default from original prototype url if not
            # explicitly provided
            build_dir = kwargs.pop('build_dir', None)
            if build_dir is None:
                if url is None:
                    raise Pype9RuntimeError(
                        "'build_dir' must be supplied when using component "
                        "classes created programmatically ('{}')".format(name))
                build_dir = code_gen.get_build_dir(url, name)
            if url is not None:
                mod_time = time.ctime(os.path.getmtime(url))
            else:
                mod_time = time.ctime()
            instl_dir = code_gen.generate(
                component_class=build_component_class,
                default_properties=build_properties,
                initial_state=build_initial_states,
                build_mode=build_mode, verbose=verbose, name=name,
                build_dir=build_dir, mod_time=mod_time, **kwargs)
            # Load newly build model
            cls.load_libraries(name, instl_dir)
            # Create class member dict of new class
            dct = {'name': name,
                   'component_class': component_class,
                   'default_properties': default_properties,
                   'initial_states': initial_states,
                   'install_dir': instl_dir,
                   'build_component_class': build_component_class,
                   'build_default_properties': build_properties,
                   'build_initial_states': build_initial_states,
                   'build_options': kwargs}
            # Create new class using Type.__new__ method
            Cell = super(CellMetaClass, cls).__new__(
                cls, name, (cls.BaseCellClass,), dct)
            # Save Cell class to allow it to save it being built again
            cls._built_types[(name, url)] = Cell, kwargs
        return Cell

    def __init__(cls, component_class, default_properties=None,
                 initial_states=None, name=None, saved_name=None, **kwargs):
        """
        This initialiser is empty, but since I have changed the signature of
        the __new__ method in the deriving metaclasses it complains otherwise
        (not sure if there is a more elegant way to do this).
        """
        pass

    def load_libraries(self, name, install_dir, **kwargs):
        """
        To be overridden by derived classes to allow the model to be loaded
        from compiled external libraries
        """
        pass


class Cell(object):

    def __init__(self, *properties, **kwprops):
        # Combine keyword and non-keyword properties into a single list
        if len(properties) == 1 and isinstance(properties[0],
                                               nineml.DynamicsProperties):
            self._nineml = properties[0]
        else:
            if len(properties) == 1 and isinstance(properties[0], dict):
                kwprops.update(properties[0])
                properties = []
            else:
                properties = list(properties)
            for name, pq_qty in kwprops.iteritems():
                qty = self._unit_handler.from_pq_quantity(pq_qty)
                properties.append(Property(name, qty.value, qty.units))
            # Init the 9ML component of the cell
            if self.default_properties is not None:
                prototype = self.default_properties
            else:
                prototype = self.component_class
            self._nineml = nineml.user.DynamicsProperties(
                prototype.name, prototype, properties)
        # Set up references from parameter names to internal variables and set
        # parameters
        for prop in self.properties:
            self.set(prop)
        # Flag to determine whether the cell has been initialised or not
        # (it makes a difference to how the state of the cell is updated,
        # either saved until the 'initialze' method is called or directly
        # set to the state)
        self._initialized = False
        self._initial_state = None

    @property
    def component_class(self):
        return self._nineml.component_class

    def _flag_created(self, flag):
        """
        Dis/Enable the override of setattr so that only properties of the 9ML
        component can be set
        """
        super(Cell, self).__setattr__('_created', flag)

    def __contains__(self, varname):
        return varname in chain(self.component_class.parameter_names,
                                self.component_class.state_variable_names)

    def __getattr__(self, varname):
        """
        Gets the value of parameters and state variables
        """
        if self._created:
            if varname not in self:
                raise Pype9AttributeError(
                    "'{}' is not a parameter or state variable of the '{}'"
                    " component class ('{}')"
                    .format(varname, self.component_class.name,
                            "', '".join(chain(
                                self.component_class.parameter_names,
                                self.component_class.state_variable_names))))
            val = self._get(varname)
            qty = self._unit_handler.assign_units(
                val, self.component_class[varname].dimension)
            return qty

    def __setattr__(self, varname, val):
        """
        Sets the value of parameters and state variables

        `varname` [str]: name of the of the parameter or state variable
        `val` [float|pq.Quantity|nineml.Quantity]: the value to set
        """
        if self._created:  # Once the __init__ method has set all the members
            if varname not in self:
                raise Pype9AttributeError(
                    "'{}' is not a parameter or state variable of the '{}'"
                    " component class ('{}')"
                    .format(varname, self.component_class.name,
                            "', '".join(chain(
                                self.component_class.parameter_names,
                                self.component_class.state_variable_names))))
            # If float, assume it is in the "natural" units of the simulator,
            # i.e. the units that quantities of the variable's dimension will
            # be translated into (e.g. voltage -> mV for NEURON)
            if isinstance(val, float):
                prop = Property(varname, Quantity(
                    val, self._unit_handler.dimension_to_units(
                        self.component_class.dimension_of(varname))))
            # If quantity, scale quantity to value in the "natural" units for
            # the simulator
            else:
                if isinstance(val, pq.Quantity):
                    qty = self._unit_handler.from_pq_quantity(val)
                else:
                    qty = val
                if varname in self.component_class.parameter_names:
                    prop = self._nineml.set(
                        Property(varname, qty.value, qty.units))
                val = self._unit_handler.scale_value(qty)
            # If varname is a parameter (not a state variable) set in
            # associated 9ML representation
            if varname in self.component_class.parameter_names:
                self._nineml.set(prop)
            self._set(varname, float(val))
        else:
            super(Cell, self).__setattr__(varname, val)

    def set(self, prop):
        """
        Sets the properties of the cell given a 9ML property
        """
        self._nineml.set(prop)
        self._set(prop.name, float(self._unit_handler.scale_value(prop)))

    def get(self, varname):
        """
        Gets the 9ML property associated with the varname
        """
        return self._nineml.prop(varname)

    def __dir__(self):
        """
        Append the property names to the list of attributes of a cell object
        """
        return list(set(chain(
            dir(super(self.__class__, self)), self.property_names,
            self.state_variable_names)))

    @property
    def properties(self):
        """
        The set of component_class properties (parameter values).
        """
        return self._nineml.properties

    @property
    def property_names(self):
        return self._nineml.property_names

    @property
    def state_variable_names(self):
        return self._nineml.component_class.state_variable_names

    def __repr__(self):
        return '{}(component_class="{}")'.format(
            self.__class__.__name__, self._nineml.component_class.name)

    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return self._nineml.to_xml(document, **kwargs)

    @property
    def used_units(self):
        return self._nineml.used_units

    def update_state(self, state):
        if self._initialized:
            self._set_state(state)
        else:
            super(Cell, self).__setattr__('_initial_state', state)

    def _set_state(self, state):
        for k, q in state.iteritems():
            setattr(self, k, q)  # FIXME: Need to convert units

    def initialize(self):
        if self._initial_state is None:
            raise Pype9RuntimeError("Initial state not set for '{}' cell"
                                    .format(self.name))
        self._set_state(self._initial_state)
        super(Cell, self).__setattr__('_initialized', True)

    def write(self, file):  # @ReservedAssignment
        self._nineml.write(file)

    def run(self, simulation_time, reset=True, timestep='cvode', rtol=None,
            atol=None):
        if self not in (c() for c in self._controller.registered_cells):
            raise Pype9RuntimeError(
                "PyPe9 Cell '{}' is not being recorded".format(self.name))
        self._controller.run(simulation_time=simulation_time, reset=reset,
                                  timestep=timestep, rtol=rtol, atol=atol)

    def reset_recordings(self):
        raise NotImplementedError("Should be implemented by derived class")

    def clear_recorders(self):
        """
        Clears all recorders and recordings
        """
        super(Cell, self).__setattr__('_recorders', {})
        super(Cell, self).__setattr__('_recordings', {})
        self._controller.deregister_cell(self)

    def _initialise_local_recording(self):
        if not hasattr(self, '_recorders'):
            self.clear_recorders()
            self._controller.register_cell(self)

    def record(self, port_name):
        raise NotImplementedError("Should be implemented by derived class")

    def recording(self, port_name):
        raise NotImplementedError("Should be implemented by derived class")

    # This has to go last to avoid clobbering the property decorators
    def property(self, name):
        return self._nineml.property(name)

    def _check_connection_properties(self, port_name, properties):
        props_dict = dict((p.name, p) for p in properties)
        params_dict = dict(
            (p.name, p) for p in
            self._nineml.connection_parameters(port_name).parameters)
        if set(props_dict.iterkeys()) != set(params_dict.iterkeys()):
            raise Pype9RuntimeError(
                "Mismatch between provided property and parameter names:"
                "\nParameters: '{}'\nProperties: '{}'"
                .format("', '".join(params_dict.iterkeys()),
                        "', '".join(props_dict.iterkeys())))
        for prop in properties:
            if params_dict[prop.name].dimension != prop.units.dimension:
                raise Pype9RuntimeError(
                    "Dimension of property '{}' ({}) does not match that of "
                    "the corresponding parameter ({})"
                    .format(prop.name, prop.units.dimension,
                            params_dict[prop.name].dimension))


class DynamicsWithSynapses(BaseALObject):

    nineml_type = 'Dynamics'
    defining_attributes = ('_dynmaics', '_synapses', '_connection_parameters')

    def __init__(self, dynamics, synapses=[], connection_parameters=[]):
        self._dynamics = dynamics
        self._synapses = dict((s.name, s) for s in synapses)
        self._connection_parameters = dict((pw.port, pw)
                                           for pw in connection_parameters)
        for conn_param in self._all_connection_parameters():
            try:
                dyn_param = self._dynamics.parameter(conn_param.name)
                if conn_param.dimension != dyn_param.dimension:
                    raise Pype9RuntimeError(
                        "Inconsistent dimensions between connection parameter"
                        " '{}' ({}) and parameter of the same name ({})"
                        .format(conn_param.name, conn_param.dimension,
                                dyn_param.dimension))
            except NineMLNameError:
                raise Pype9RuntimeError(
                    "Connection parameter '{}' does not refer to a parameter "
                    "in the base MultiDynamics class ('{}')"
                    .format(conn_param, "', '".join(
                        sp.name for sp in self._dynamics.parameters)))
        # Copy what would be class members in the dynamics class so it will
        # appear like an object of that class
        self.defining_attributes = (dynamics.defining_attributes +
                                    ('_synapses', '_connection_parameters'))
        self.class_to_member = dict(
            dynamics.class_to_member.items() +
            [('Synapse', 'synapse'),
             ('ConnectionParameter', 'connection_parameter')])

    def __repr__(self):
        return ("DynamicsWithSynapses(dynamics={}, synapses=[{}], "
                "connection_parameters=[{}])"
                .format(self._dynamics,
                        ', '.format(repr(s) for s in self.synapses),
                        ', '.format(repr(cp)
                                    for cp in self.connection_parameters)))

    def __getattr__(self, name):
        """
        If an attribute isn't pass it on to the dynamics class so the class can
        be ducked-typed with the Dynamics class
        """
        return getattr(self._dynamics, name)

    def _all_connection_parameters(self):
        return set(chain(*(
            cp.parameters for cp in self.connection_parameters)))

    def _all_connection_parameter_names(self):
        return (p.name for p in self._all_connection_parameters())

    @property
    def parameters(self):
        return (p for p in self._dynamics.parameters
                if p.name not in self._all_connection_parameter_names())

    @name_error
    def parameter(self, name):
        if name in self._all_connection_parameter_names():
            raise KeyError(name)
        else:
            return self._dynamics.parameter(name)

    @name_error
    def synapse(self, name):
        return self._synapses[name]

    @name_error
    def connection_paramter(self, name):
        return self._connection_parameters[name]

    @property
    def synapses(self):
        return self._synapses.itervalues()

    @property
    def connection_parameters(self):
        return self._connection_parameters.itervalues()

    @property
    def num_synapses(self):
        return len(self._synapses)

    @property
    def num_connection_parameters(self):
        return len(self._connection_parameters)

    @property
    def synapse_names(self):
        return self._synapses.iterkeys()

    @property
    def connection_paramter_names(self):
        return self._connection_parameters.iterkeys()


class DynamicsWithSynapsesProperties(BaseULObject):

    nineml_type = 'DynamicsProperties'
    defining_attributes = ('_dynamics_properties', '_synapses',
                           '_connection_properties')

    def __init__(self, dynamics_properties, synapse_properties=[],
                 connection_properties=[]):
        self._dynamics_properties = dynamics_properties
        self._synapses = dict((s.name, s) for s in synapse_properties)
        self._connection_properties = dict((cp.port, cp)
                                           for cp in connection_properties)
        # Extract the AL objects for the definition
        synapses = (Synapse(s.name, s.dynamics_properties.component_class,
                            s.port_connections)
                    for s in synapse_properties)
        connection_parameters = (
            ConnectionParameter(
                cp.port,
                [Parameter(p.name, p.units.dimension) for p in cp.properties])
            for cp in connection_properties)
        self._definition = Definition(
            DynamicsWithSynapses(dynamics_properties.component_class,
                                 synapses, connection_parameters))
        # Copy what would be class members in the dynamics class so it will
        # appear like an object of that class
        self.defining_attributes = (dynamics_properties.defining_attributes +
                                    ('_synapses', '_connection_properties'))
        self.class_to_member = dict(
            dynamics_properties.class_to_member.items() +
            [('Synapse', 'synapse'),
             ('ConnectionProperty', 'connection_property')])

    def __repr__(self):
        return ("DynamicsWithSynapsesProperties(dynamics_properties={}, "
                "synapses=[{}], connection_properties=[{}])"
                .format(self._dynamics_properties,
                        ', '.format(repr(s) for s in self.synapses),
                        ', '.format(repr(cp)
                                    for cp in self.connection_properties)))

    def __getattr__(self, name):
        """
        If an attribute isn't pass it on to the dynamics class so the class can
        be ducked-typed with the Dynamics class
        """
        return getattr(self._dynamics_properties, name)

    @property
    def definition(self):
        return self._definition

    def synapse(self, name):
        return self._synapses[name]

    def connection_property(self, name):
        return self._connection_properties[name]

    @property
    def synapses(self):
        return self._synapses.itervalues()

    @property
    def connection_properties(self):
        return self._connection_properties.itervalues()

    @property
    def num_synapses(self):
        return len(self._synapses)

    @property
    def num_connection_properties(self):
        return len(self._connection_properties)

    @property
    def synapse_names(self):
        return self._synapses.iterkeys()

    @property
    def connection_property_names(self):
        return self._connection_properties.iterkeys()


class ConnectionParameter(BaseALObject):

    nineml_type = 'ConnectionParameter'
    defining_attributes = ('port', 'parameters')

    def __init__(self, port, parameters):
        self._port = port
        self._parameters = parameters

    def __repr__(self):
        return ("ConnectionParameter(port={}, parameters=[{}])"
                .format(self.port,
                        ', '.join(repr(p) for p in self.parameters)))

    @property
    def port(self):
        return self._port

    @property
    def parameters(self):
        return self._parameters


class ConnectionProperty(BaseULObject):

    nineml_type = 'ConnectionProperty'
    defining_attributes = ('port', 'properties')

    def __init__(self, port, properties):
        self._port = port
        self._properties = properties

    def __repr__(self):
        return ("ConnectionProperty(port={}, properties=[{}])"
                .format(self.port,
                        ', '.join(repr(p) for p in self.properties)))

    @property
    def port(self):
        return self._port

    @property
    def properties(self):
        return self._properties


class Synapse(BaseALObject):

    nineml_type = 'Synapse'
    defining_attributes = ('name', 'dynamics', 'port_connections')

    def __init__(self, name, dynamics, port_connections):
        self._name = name
        self._dynamics = dynamics
        self._port_connections = port_connections

    def __repr__(self):
        return ("Synapse(name='{}', dynamics={}, port_connections=[{}])"
                .format(self.name, self.dynamics,
                        ', '.join(repr(p) for p in self.port_connections)))

    @property
    def name(self):
        return self._name

    @property
    def dynamics(self):
        return self._dynamics

    @property
    def port_connections(self):
        return self._port_connections


class SynapseProperties(BaseULObject):

    nineml_type = 'SynapseProperties'
    defining_attributes = ('name', 'dynamics_properties', 'port_connections')

    def __init__(self, name, dynamics_properties, port_connections):
        self._name = name
        self._dynamics_properties = dynamics_properties
        self._port_connections = port_connections

    def __repr__(self):
        return ("Synapse(name='{}', dynamics_properties={}, "
                "port_connections=[{}])"
                .format(self.name, self.dynamics_properties,
                        ', '.join(repr(p) for p in self.port_connections)))

    @property
    def name(self):
        return self._name

    @property
    def dynamics_properties(self):
        return self._dynamics_properties

    @property
    def port_connections(self):
        return self._port_connections
