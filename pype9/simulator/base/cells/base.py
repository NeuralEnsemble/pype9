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
from itertools import chain
from copy import deepcopy
import quantities as pq
import nineml
from nineml.abstraction import Dynamics, Regime
from nineml.user import MultiDynamicsProperties, Property
from nineml.units import Quantity
from pype9.annotations import PYPE9_NS
from pype9.exceptions import (
    Pype9RuntimeError, Pype9AttributeError, Pype9DimensionError,
    Pype9UsageError)
import logging
from .with_synapses import WithSynapses, WithSynapsesProperties

logger = logging.Logger("Pype9")


class CellMetaClass(type):

    """
    Metaclass for building NineMLCellType subclasses Called by
    nineml_celltype_from_model
    """

    def __new__(cls, component_class, name=None, saved_name=None,
                build_dir=None, build_mode='lazy', verbose=False,
                **kwargs):
        """
        Parameters
        ----------
        component_class : Dynamics
            A nineml.abstraction.Dynamics object
        default_properties: DynamicsProperties
            default properties, if None, then all props = 0
        initial_states : dict[str, Quantity]
            initial states, if None, then all states = 0
        name : str
            The name for the class
        saved_name : str
            The name of the Dynamics object in the document if different from
            the `name`
        build_dir : str - directory path
            The directory in which to build the simulator-native code
        verbose : bool
            Whether to print out debugging information
        """
        # Grab the url before the component class is cloned
        url = component_class.url
        # Clone component class so annotations can be added to it and not bleed
        # into the calling code.
        component_class = component_class.clone()
        # If the component class is not already wrapped in a WithSynapses
        # object, wrap it in one before passing to the code template generator
        if not isinstance(component_class, WithSynapses):
            component_class = WithSynapses.wrap(component_class)
        # Extract out build directives
        if name is None:
            if saved_name is not None:
                name = saved_name
            else:
                name = component_class.name
        create_class = False
        try:
            # FIXME: This lookup should ideally be done on the component-class/
            #        build properties
            Cell = cls._built_types[name]
            if not Cell.component_class.equals(component_class,
                                               annotations_ns=[PYPE9_NS]):
                create_class = True
        except KeyError:
            create_class = True
        if create_class:
            # Initialise code generator
            code_gen = cls.CodeGenerator()
            build_component_class = code_gen.transform_for_build(
                name=name, component_class=component_class, **kwargs)
            # Generate and compile cell class
            instl_dir = code_gen.generate(
                component_class=build_component_class,
                build_mode=build_mode, verbose=verbose, name=name,
                build_dir=build_dir, url=url, **kwargs)
            # Load newly build model
            cls.load_libraries(name, instl_dir)
            # Create class member dict of new class
            dct = {'name': name,
                   'component_class': component_class,
                   'install_dir': instl_dir,
                   'build_component_class': build_component_class}
            # Create new class using Type.__new__ method
            Cell = super(CellMetaClass, cls).__new__(
                cls, name, (cls.BaseCellClass,), dct)
            # Save Cell class to allow it to save it being built again
            cls._built_types[name] = Cell
        return Cell

    def __init__(cls, component_class, default_properties=None,
                 initial_states=None, name=None, saved_name=None, **kwargs):
        """
        This initializer is empty, but since I have changed the signature of
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
        self._in_pynn = kwprops.pop('_in_pynn', False)
        # Combine keyword and non-keyword properties into a single list
        if len(properties) == 1 and isinstance(properties[0],
                                               nineml.DynamicsProperties):
            self._nineml = properties[0]
        else:
            # Check to see if properties is a dictionary of name/quantity pairs
            if len(properties) == 1 and isinstance(properties[0], dict):
                kwprops.update(properties[0])
                properties = []
            else:
                properties = list(properties)
            # Convert "Python-Quantities" quantities into 9ML quantities
            for name, pq_qty in kwprops.iteritems():
                qty = self.UnitHandler.from_pq_quantity(pq_qty)
                properties.append(Property(name, qty.value * qty.units))
            # If default properties not provided create a Dynamics Properties
            # from the provided properties
            if self.default_properties is None:
                # FIXME: Probably should just initialize the properties to NaN
                #        or something
                self._nineml = nineml.user.DynamicsProperties(
                    self.component_class.name + 'Properties',
                    self.component_class, properties)
            # If no properties provided use the default properties
            elif not properties:
                self._nineml = deepcopy(self.default_properties)
            # Otherwise use the default properties as a prototype and override
            # where specific properties are provided
            else:
                if isinstance(self.default_properties,
                              MultiDynamicsProperties):
                    logger.warning("Unable to set default properties for '{}' "
                                   "cell as it is MultiDynamicsProperties"
                                   .format(self.name))
                    self._nineml = deepcopy(self.default_properties)
                else:
                    self._nineml = type(self.default_properties)(
                        self.default_properties.name, self.default_properties,
                        properties)
        # Set up references from parameter names to internal variables and set
        # parameters
        for prop in self.properties:
            self.set(prop)
        # Flag to determine whether the cell has been initialized or not
        # (it makes a difference to how the state of the cell is updated,
        # either saved until the 'initialze' method is called or directly
        # set to the state)
        self._initialized = False
        self._initial_states = None
        self._initial_regime = None
        sim = self.Simulation.active()
        self._t_start = sim.t_start
        self._t_stop = None
        if not self._in_pynn:
            sim.register_cell(self)

    @property
    def component_class(self):
        return self._nineml.component_class

    @property
    def in_array(self):
        return self._in_array

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
            qty = self.UnitHandler.assign_units(
                val, self.component_class.element(
                    varname, class_map=Dynamics.class_to_member).dimension)
            return qty

    def __setattr__(self, varname, val):
        """
        Sets the value of parameters and state variables

        Parameters
        ----------
        varname : str
            Name of the of the parameter or state variable
        val : float | pq.Quantity | nineml.Quantity
            The value to set
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
                    val, self.UnitHandler.dimension_to_units(
                        self.component_class.dimension_of(varname))))
            # If quantity, scale quantity to value in the "natural" units for
            # the simulator
            else:
                if isinstance(val, pq.Quantity):
                    qty = self.UnitHandler.from_pq_quantity(val)
                else:
                    qty = val
                if qty.units.dimension != self.component_class.dimension_of(
                        varname):
                    raise Pype9DimensionError(
                        "Attempting so set '{}', which has dimension {} to "
                        "{}, which has dimension {}".format(
                            varname,
                            self.component_class.dimension_of(varname), qty,
                            qty.units.dimension))
                val = self.UnitHandler.scale_value(qty)
                prop = Property(varname, qty)
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
        # FIXME: Need to reenable the update of the nineml
        #        object. Currently it is difficult to set a property in the
        #        if it is a MultiDynamics object (but not impossible)
#         self._nineml.set(prop)
        self._set(prop.name, float(self.UnitHandler.scale_value(prop)))

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

    @properties.setter
    def properties(self, props):
        for prop in props.properties:
            self.set(prop)

    @property
    def property_names(self):
        return self._nineml.property_names

    @property
    def state_variable_names(self):
        return self.component_class.state_variable_names

    @property
    def event_receive_port_names(self):
        return self.component_class.event_receive_port_names

    def __repr__(self):
        return '{}(component_class="{}")'.format(
            self.__class__.__name__, self._nineml.component_class.name)

    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return self._nineml.to_xml(document, **kwargs)

    @property
    def used_units(self):
        return self._nineml.used_units

    def set_state(self, states, regime=None):
        if self._initialized:
            self._set_state((states, regime))
        else:
            if self._initial_states is None:
                super(Cell, self).__setattr__('_initial_states', {})
            self._initial_states.update(states)
            if regime is not None:
                super(Cell, self).__setattr__('_initial_regime', regime)

    def _set_state(self, states, regime):
        for k, q in states.iteritems():
            setattr(self, k, q)  # FIXME: Need to convert units
        if regime is not None:
            try:
                # If regime is an integer (as it will be when passed from PyNN)
                regime_index = int(regime)
            except ValueError:
                # If the regime is the regime name
                regime_index = self.regime_index(regime)
            self._set_regime(regime_index)

    @classmethod
    def regime_index(cls, name):
        """
        Returns the index of the regime corresponding to 'name' as used in the
        code generation (useful when creating arrays to set a population regime
        values)
        """
        return cls.build_component_class.index_of(
            cls.build_component_class.regime(name),
            class_map=Dynamics.class_to_member)

    @classmethod
    def from_regime_index(cls, index):
        """
        The reciprocal of regime_index, returns the regime name from its index
        """
        return cls.build_component_class.from_index(
            index, Regime.nineml_type, class_map=Dynamics.class_to_member).name

    def initialize(self):
        if self._initial_states is None:
            raise Pype9UsageError("Initial state not set for '{}' cell"
                                  .format(self.name))
        if self._initial_regime is None:
            if self.component_class.num_regimes == 1:
                initial_regime = next(self.component_class.regimes).name
            else:
                raise Pype9UsageError("Initial regime not set for '{}' cell"
                                      .format(self.name))
        else:
            initial_regime = self._initial_regime
        self._set_state(self._initial_states, initial_regime)
        super(Cell, self).__setattr__('_initialized', True)

    def write(self, file, **kwargs):  # @ReservedAssignment
        self._nineml.write(file, **kwargs)

    def reset_recordings(self):
        raise NotImplementedError("Should be implemented by derived class")

    def clear_recorders(self):
        """
        Clears all recorders and recordings
        """
        super(Cell, self).__setattr__('_recorders', {})
        super(Cell, self).__setattr__('_recordings', {})

    def _initialize_local_recording(self):
        if not hasattr(self, '_recorders'):
            self.clear_recorders()

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
            self._nineml.component_class.connection_parameter_set(
                port_name).parameters)
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

    def _kill(self, t_stop):
        """
        Caches recording data and sets all references to the actual
        simulator object to None ahead of a simulator reset. This allows cell
        data to be accessed after a simulation has completed, and potentially
        a new simulation to have been started.
        """
        # TODO: Cache has not been implemented yet
        super(Cell, self).__setattr__('_t_stop', t_stop)

    def is_dead(self):
        return self._t_stop is not None
