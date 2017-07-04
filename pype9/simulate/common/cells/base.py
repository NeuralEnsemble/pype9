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
import numpy as np
import quantities as pq
import neo
import nineml
from nineml.abstraction import Dynamics, Regime
from nineml.user import Property, Initial
from nineml.exceptions import NineMLNameError
from pype9.annotations import PYPE9_NS
from pype9.exceptions import (
    Pype9RuntimeError, Pype9AttributeError, Pype9DimensionError,
    Pype9UsageError)
import logging
from .with_synapses import WithSynapses


logger = logging.Logger("Pype9")


class CellMetaClass(type):
    """
    Metaclass for creating simulator-specific cell classes from 9ML Dynamics
    classes. Instantiating a CellMetaClass with a ``nineml.Dynamics`` instance
    will generate, compile and load the required simulator-specific code and
    create a class that can be used to instantiate dynamics objects.

    Parameters
    ----------
    component_class : nineml.Dynamics
        The 9ML component class to create the Cell class for
    name : str
        The name of the cell class, which is used for the generated simulator
        code. If None, the name of the component_class is used. Note, names
        must be unique among classes loaded within the same simulation script.
    saved_name : str
        The name of the Dynamics object in the document if different from
        the `name` argument
    build_dir : str (directory path)
        The directory in which to build the simulator-native code
    build_mode : str
        The strategy used to build and compile the model. Can be one of
        ::class::BaseCodeGenerator.BUILD_MODE_OPTIONS
    """

    def __new__(cls, component_class, name=None, saved_name=None,
                build_dir=None, build_mode='lazy', **kwargs):
        # Grab the url before the component class is cloned
        url = component_class.url
        # Clone component class so annotations can be added to it and not bleed
        # into the calling code.
        component_class = component_class.clone()
        # If the component class is not already wrapped in a WithSynapses
        # object, wrap it in one before passing to the code template generator
        if not isinstance(component_class, WithSynapses):
            if name == component_class.name:
                raise Pype9UsageError(
                    "Cannot explicitly use same name ('{}') for build class as"
                    " component class without synapses".format(name))
            component_class = WithSynapses.wrap(component_class)
        # Extract out build directives
        if name is None:
            if saved_name is not None:
                name = saved_name
            else:
                name = component_class.name
        # Get transformed build class
        code_gen = cls.CodeGenerator()
        build_component_class = code_gen.transform_for_build(
            name=name, component_class=component_class, **kwargs)
        create_class = False
        try:
            Cell = cls._built_types[name]
            if not Cell.build_component_class.equals(
                    build_component_class, annotations_ns=[PYPE9_NS]):
                create_class = True
        except KeyError:
            create_class = True
        if create_class:
            # Generate and compile cell class
            instl_dir = code_gen.generate(
                component_class=build_component_class,
                build_mode=build_mode, name=name,
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

    def __init__(self, component_class, name=None, saved_name=None,
                 build_dir=None, build_mode='lazy', **kwargs):
        # This initializer is empty, but since I have changed the signature of
        # the __new__ method in the deriving metaclasses it complains otherwise
        # (not sure if there is a more elegant way to do this).
        pass

    def load_libraries(self, name, install_dir, **kwargs):
        """
        To be overridden by derived classes to allow the model to be loaded
        from compiled external libraries
        """
        pass


class Cell(object):
    """
    Base class for all cell classes created from the CellMetaClass. It defines
    all methods that can be called on cell model objects.

    Parameters
    ----------
    args : list(DynamicsProperties)
        A singlton
    kwargs : dict(str, nineml.Quantity)
        Parameters and initial state variables to initiate the cell with.
    regime_ : str
        Name of regime the cell will be initiated in
    """

    def __init__(self, *args, **kwargs):
        self._in_array = kwargs.pop('_in_array', False)
        # Flag to determine whether the cell has been initialized or not
        # (it makes a difference to how the state of the cell is updated,
        # either saved until the 'initialze' method is called or directly
        # set to the state)
        sim = self.Simulation.active()
        self._t_start = sim.t_start
        self._t_stop = None
        if self.in_array:
            for k, v in kwargs.iteritems():
                self._set(k, v)  # Values should be in the right units.
            self._regime_index = None
        else:
            # Set initial regime of the cell
            regime = kwargs.pop('regime_', None)
            if regime is None:
                if self.component_class.num_regimes == 1:
                    regime = next(self.component_class.regime_names)
                else:
                    raise Pype9UsageError(
                        "Need to specify initial regime using initial_regime "
                        "kwarg for component class with multiple regimes "
                        "('{}')".format(self.component_class.regime_names))
            self.set_regime(regime)
            # Set the properties and initial values of the cell
            if args:
                if len(args) > 1 or not isinstance(args[0],
                                                   nineml.DynamicsProperties):
                    raise Pype9UsageError(
                        "'{}' cell __init__ method only takes one non-keyword "
                        " argument (DynamicsProperties), provided {}"
                        .format(self.name, ', '.join(str(a) for a in args)))
                prototype = args[0]
            else:
                prototype = self.component_class
            properties = []
            initial_values = []
            for name, qty in kwargs.iteritems():
                if isinstance(qty, pq.Quantity):
                    qty = self.UnitHandler.from_pq_quantity(qty)
                if name in self.component_class.state_variable_names:
                    initial_values.append(nineml.Initial(name, qty))
                else:
                    properties.append(nineml.Property(name, qty))
            self._nineml = nineml.DynamicsProperties(
                name=self.name + '_properties',
                definition=prototype,
                properties=properties, initial_values=initial_values,
                check_initial_values=True)
            # Set up references from parameter names to internal variables and
            # set parameters
            for p in chain(self.properties, self.initial_values):
                qty = p.quantity
                if qty.value.nineml_type != 'SingleValue':
                    raise Pype9UsageError(
                        "Only SingleValue quantities can be used to initiate "
                        "individual cell classes ({})".format(p))
                self._set(p.name, float(self.UnitHandler.scale_value(qty)))
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
        if self._created:
            # Once the __init__ method has set all the members
            if varname not in self:
                raise Pype9AttributeError(
                    "'{}' is not a parameter or state variable of the '{}'"
                    " component class ('{}')"
                    .format(varname, self.component_class.name,
                            "', '".join(chain(
                                self.component_class.parameter_names,
                                self.component_class.state_variable_names))))
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
            if not self.in_array:
                # Set the quantity in the nineml class
                if varname in self.component_class.state_variable_names:
                    self._nineml.set(Initial(varname, qty))
                else:
                    self._nineml.set(Property(varname, qty))
            # Set the value in the simulator
            self._set(varname, float(self.UnitHandler.scale_value(qty)))
        else:
            super(Cell, self).__setattr__(varname, val)

    def set_regime(self, regime):
        if regime not in self.component_class.regime_names:
            raise Pype9UsageError(
                "'{}' is not a name of a regime in '{} cells "
                "(regimes are '{}')".format(
                    regime, self.name,
                    "', '".join(self.component_class.regime_names)))
        try:
            # If regime is an integer (as it will be when passed from PyNN)
            self._regime_index = int(regime)
        except ValueError:
            # If the regime is the regime name
            self._regime_index = self.regime_index(regime)
        self._set_regime()

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
    def initial_values(self):
        return self._nineml.initial_values

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

    def serialize(self, document, **kwargs):  # @UnusedVariable
        return self._nineml.serialize(document, **kwargs)

    @property
    def used_units(self):
        return self._nineml.used_units

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
        for iv in self._nineml.initial_values:
            setattr(self, iv.name, iv.quantity)
        self._set_regime()

    def write(self, file, **kwargs):  # @ReservedAssignment
        if self.in_array:
            raise Pype9UsageError(
                "Can only write cell properties when they are not in an "
                "array")
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
        """
        Specify the recording of a send port or state-variable before the
        simulation.
        """
        raise NotImplementedError("Should be implemented by derived class")

    def record_regime(self):
        """
        Returns the current regime at each timestep. Periods spent in each
        regimes can be retrieved with the ``regime_epochs`` method.
        """
        raise NotImplementedError("Should be implemented by derived class")

    def recording(self, port_name):
        """
        Return recorded data as a dictionary containing one numpy array for
        each neuron, ids as keys.

        Parameters
        ----------
        port_name : str
            Name of the port to retrieve the recording for
        """
        raise NotImplementedError("Should be implemented by derived class")

    def _regime_recording(self):
        raise NotImplementedError("Should be implemented by derived class")

    def regime_epochs(self):
        """
        Retrieves the periods spent in each regime during the simulation
        in a neo.core.EpochArray
        """
        try:
            rec = self._regime_recording()
        except KeyError:
            raise Pype9UsageError(
                "Regime transitions not recorded, call 'record_regime' before"
                " simulation")
        cc = self.build_component_class
        index_map = dict((cc.index_of(r), r.name) for r in cc.regimes)
        trans_inds = np.nonzero(
            np.asarray(rec[1:]) != np.asarray(rec[:-1]))[0] + 1
        # Insert initial regime
        trans_inds = np.insert(trans_inds, 0, 0)
        labels = [index_map[int(r)] for r in rec[trans_inds]]
        times = rec.times[trans_inds]
        epochs = np.append(times, rec.t_stop) * times.units
        durations = epochs[1:] - epochs[:-1]
        return neo.EpochArray(
            times=times, durations=durations, labels=labels,
            name='{}_regimes'.format(self.name))

    def play(self, port_name, signal, properties=[]):
        """
        Plays an analog signal or train of events into a port of the
        cell

        Parameters
        ----------
        port_name : str
            The name of the port to play the signal into
        signal : neo.AnalogSignal | neo.SpikeTrain
            The signal to play into the cell
        properties : dict(str, nineml.Quantity)
            Connection properties when playing into a event receive port
            with static connection properties
        """
        raise NotImplementedError("Should be implemented by derived class")

    def connect(self, sender, send_port_name, receive_port_name, delay,
                properties=[]):
        """
        Connects an event send port from other into an event receive port in
        the cell

        Parameters
        ----------
        sender : pype9.simulator.base.cells.Cell
            The sending cell to connect the from
        send_port_name : str
            Name of the port in the sending cell to connect to
        receive_port_name : str
            Name of the receive port in the current cell to connect from
        delay : nineml.Quantity (time)
            The delay of the connection
        properties : list(nineml.Property)
            The connection properties of the event port
        """
        raise NotImplementedError("Should be implemented by derived class")

    # This has to go last to avoid clobbering the property decorators
    def property(self, name):
        return self._nineml.property(name)

    def _check_connection_properties(self, port_name, properties):
        props_dict = dict((p.name, p) for p in properties)
        try:
            param_set = self._nineml.component_class.connection_parameter_set(
                port_name)
        except NineMLNameError:
            return  # No parameter set, so no need to check
        params_dict = dict((p.name, p) for p in param_set.parameters)
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
