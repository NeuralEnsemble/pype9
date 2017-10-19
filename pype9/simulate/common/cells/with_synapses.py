from builtins import object
from itertools import chain
from abc import ABCMeta
from nineml.abstraction import BaseALObject, Dynamics, Parameter
from nineml.user import (
    BaseULObject, DynamicsProperties, MultiDynamics, MultiDynamicsProperties,
    Definition, AnalogPortConnection, EventPortConnection, Property)
from nineml.base import ContainerObject, DocumentLevelObject
from nineml.exceptions import name_error, NineMLNameError
from pype9.exceptions import Pype9RuntimeError
import nineml
from nineml.utils import validate_identifier
from future.utils import with_metaclass


class ConnectionParameterSet(BaseALObject, ContainerObject):

    nineml_type = 'ConnectionParameterSet'
    nineml_attr = ('port',)
    nineml_children = (Parameter,)

    def __init__(self, port, parameters):
        super(ConnectionParameterSet, self).__init__()
        ContainerObject.__init__(self)
        self._port = validate_identifier(port)
        for param in parameters:
            self.add(param.clone(as_class=Parameter))

    def __repr__(self):
        return ("ConnectionParameterSet(port={}, parameters=[{}])"
                .format(self.port,
                        ', '.join(repr(p) for p in self.parameters)))

    @property
    def port(self):
        return self._port

    @property
    def key(self):
        return self.port

    @name_error
    def parameter(self, name):
        return self._parameters[name]

    @property
    def parameters(self):
        return iter(self._parameters.values())

    @property
    def parameter_names(self):
        return iter(self._parameters.keys())

    def clone(self, memo=None, **kwargs):
        return self.__class__(
            self.port,
            [p.clone(memo=memo, **kwargs) for p in self.parameters])

    def serialize_node(self, node, **options):
        node.children(self.parameters, **options)
        node.attr('port', self.port)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable @IgnorePep8
        return cls(node.attr('port'),
                   node.children(Parameter, **options))


class ConnectionPropertySet(BaseULObject, ContainerObject):

    nineml_type = 'ConnectionPropertySet'
    nineml_attr = ('port',)
    nineml_children = (Property,)

    def __init__(self, port, properties):
        super(ConnectionPropertySet, self).__init__()
        ContainerObject.__init__(self)
        self._port = validate_identifier(port)
        for prop in properties:
            self.add(prop.clone(as_class=Property))

    def __repr__(self):
        return ("ConnectionPropertySet(port={}, properties=[{}])"
                .format(self.port,
                        ', '.join(repr(p) for p in self.properties)))

    @property
    def port(self):
        return self._port

    @property
    def key(self):
        return self.port

    @property
    def properties(self):
        return iter(self._properties.values())

    @property
    def property_names(self):
        return iter(self._properties.keys())

    def clone(self, memo=None, **kwargs):
        return self.__class__(
            self.port,
            [p.clone(memo=memo, **kwargs) for p in self.properties])

    def serialize_node(self, node, **options):
        node.children(self.properties, **options)
        node.attr('port', self.port)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable @IgnorePep8
        return cls(node.attr('port'),
                   node.children(Property, **options))

    # This needs to be last not to overwite the property decorator
    @name_error
    def property(self, name):
        return self._properties[name]


class Synapse(BaseALObject, ContainerObject):

    nineml_type = 'Synapse'
    nineml_attr = ('name',)
    nineml_child = {'dynamics': None}
    nineml_children = (AnalogPortConnection, EventPortConnection)

    def __init__(self, name, dynamics, port_connections=None,
                 analog_port_connections=None, event_port_connections=None):
        super(Synapse, self).__init__()
        ContainerObject.__init__(self)
        self._name = validate_identifier(name)
        self._dynamics = dynamics.clone()
        if port_connections is None:
            port_connections = []
        if analog_port_connections is None:
            analog_port_connections = []
        if event_port_connections is None:
            event_port_connections = []
        for port_conn in chain(port_connections, analog_port_connections,
                               event_port_connections):
            self.add(port_conn.clone())

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

    def port_connection(self, name):
        try:
            return self.analog_port_connection(name)
        except NineMLNameError:
            return self.event_port_connection(name)

    @property
    def port_connections(self):
        return chain(self.analog_port_connections, self.event_port_connections)

    @property
    def num_port_connections(self):
        return (self.num_analog_port_connections +
                self.num_event_port_connections)

    @property
    def port_connection_names(self):
        return chain(self.analog_port_connection_names,
                     self.event_port_connection_names)

    @name_error
    def analog_port_connection(self, name):
        return self._analog_port_connections[name]

    @property
    def analog_port_connections(self):
        return iter(self._analog_port_connections.values())

    @property
    def num_analog_port_connections(self):
        return len(self._analog_port_connections)

    @property
    def analog_port_connection_names(self):
        return iter(self._analog_port_connections.keys())

    @name_error
    def event_port_connection(self, name):
        return self._event_port_connections[name]

    @property
    def event_port_connections(self):
        return iter(self._event_port_connections.values())

    @property
    def num_event_port_connections(self):
        return len(self._event_port_connections)

    @property
    def event_port_connection_names(self):
        return iter(self._event_port_connections.keys())

    def clone(self, memo=None, **kwargs):
        return self.__class__(
            self.name,
            self.dynamics.clone(memo=memo, **kwargs),
            [pc.clone(memo=memo, **kwargs) for pc in self.port_connections])

    def serialize_node(self, node, **options):
        node.attr('name', self.name, **options)
        node.child(self.dynamics, **options)
        node.children(self.event_port_connections, **options)
        node.children(self.analog_port_connections, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        # The only supported op at this stage
        dynamics = node.child((Dynamics, MultiDynamics), **options)
        port_connections = node.children(
            (EventPortConnection, AnalogPortConnection), **options)
        return cls(node.attr('name', **options), dynamics, port_connections)


class SynapseProperties(BaseULObject, ContainerObject):

    nineml_type = 'SynapseProperties'
    nineml_attr = ('name',)
    nineml_child = {'dynamics_properties': DynamicsProperties}
    nineml_children = (AnalogPortConnection, EventPortConnection)

    def __init__(self, name, dynamics_properties, port_connections=None,
                 analog_port_connections=None, event_port_connections=None):
        super(SynapseProperties, self).__init__()
        ContainerObject.__init__(self)
        self._name = validate_identifier(name)
        self._dynamics_properties = dynamics_properties.clone()
        if port_connections is None:
            port_connections = []
        if analog_port_connections is None:
            analog_port_connections = []
        if event_port_connections is None:
            event_port_connections = []
        for port_conn in chain(port_connections, analog_port_connections,
                               event_port_connections):
            self.add(port_conn.clone())

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
        return chain(self.analog_port_connections, self.event_port_connections)

    @property
    def analog_port_connections(self):
        return list(self._analog_port_connections.values())

    @property
    def event_port_connections(self):
        return list(self._event_port_connections.values())

    @name_error
    def analog_port_connection(self, key):
        return self._analog_port_connections[key]

    @name_error
    def event_port_connection(self, key):
        return self._event_port_connections[key]

    @property
    def analog_port_connection_keys(self):
        return list(self._analog_port_connections.keys())

    @property
    def event_port_connection_keys(self):
        return list(self._event_port_connections.keys())

    @property
    def num_analog_port_connections(self):
        return len(self._analog_port_connections)

    @property
    def num_event_port_connections(self):
        return len(self._event_port_connections)

    def serialize_node(self, node, **options):
        node.attr('name', self.name)
        node.child(self.dynamics_properties, **options)
        node.children(self.event_port_connections, **options)
        node.children(self.analog_port_connections, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        # The only supported op at this stage
        dynamics_properties = node.child(
            (DynamicsProperties, MultiDynamicsProperties), **options)
        port_connections = node.children(
            (EventPortConnection, AnalogPortConnection), **options)
        return cls(node.attr('name', **options), dynamics_properties,
                   port_connections)


class WithSynapses(with_metaclass(ABCMeta, object)):
    """
    Mixin class to be mixed with Dynamics and MultiDynamics classes in order
    to handle synapses (and their potential flattening to weights)
    """

    nineml_attr = ('name',)
    nineml_child = {'dynamics': None}
    nineml_children = (Synapse, ConnectionParameterSet)

    def __init__(self, name, dynamics, synapses, connection_parameter_sets):
        assert isinstance(dynamics, (Dynamics, MultiDynamics))
        # Initialise Dynamics/MultiDynamics base classes
        self._name = validate_identifier(name)
        self._dynamics = dynamics
        self.add(*synapses)
        self.add(*connection_parameter_sets)
        for conn_param in self.all_connection_parameters():
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
        self._dimension_resolver = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = validate_identifier(name)

    def __repr__(self):
        return ("{}WithSynapses(dynamics={}, synapses=[{}], "
                "connection_parameter_sets=[{}])"
                .format(self._dynamics.__class__.__name__, self._dynamics,
                        ', '.format(repr(s) for s in self.synapses),
                        ', '.format(repr(cp)
                                    for cp in self.connection_parameter_sets)))

    def all_connection_parameters(self):
        return set(chain(*(
            cp.parameters for cp in self.connection_parameter_sets)))

    def all_connection_parameter_names(self):
        return (p.name for p in self.all_connection_parameters())

    @property
    def dynamics(self):
        return self._dynamics

    @property
    def parameters(self):
        return (p for p in self._dynamics.parameters
                if p.name not in self.all_connection_parameter_names())

    @property
    def attributes_with_dimension(self):
        return chain(self._dynamics.attributes_with_dimension,
                     self.all_connection_parameters())

    @property
    def parameter_names(self):
        return (p.name for p in self.parameters)

    @name_error
    def parameter(self, name):
        if name in self.all_connection_parameter_names():
            raise KeyError(name)
        else:
            return self._dynamics.parameter(name)

    @property
    def num_parameters(self):
        return len(list(self.parameters))

    @name_error
    def synapse(self, name):
        return self._synapses[name]

    @name_error
    def connection_parameter_set(self, name):
        return self._connection_parameter_sets[name]

    @property
    def synapses(self):
        return iter(self._synapses.values())

    @property
    def connection_parameter_sets(self):
        return iter(self._connection_parameter_sets.values())

    @property
    def num_synapses(self):
        return len(self._synapses)

    @property
    def num_connection_parameter_sets(self):
        return len(self._connection_parameter_sets)

    @property
    def synapse_names(self):
        return iter(self._synapses.keys())

    @property
    def connection_parameter_set_keys(self):
        return iter(self._connection_parameter_sets.keys())

    @classmethod
    def wrap(cls, dynamics, synapses=None, connection_parameter_sets=None):
        if synapses is None:
            synapses = []
        if connection_parameter_sets is None:
            connection_parameter_sets = []
        if isinstance(dynamics, MultiDynamics):
            wrapped_cls = MultiDynamicsWithSynapses
        elif isinstance(dynamics, Dynamics):
            wrapped_cls = DynamicsWithSynapses
        else:
            raise Pype9RuntimeError(
                "Cannot wrap '{}' class with WithSynapses, only Dynamics and "
                "MultiDynamics".format(type(dynamics)))
        name = dynamics.name
        dynamics = dynamics.clone()
        dynamics.name = name + '__sans_synapses'
        return wrapped_cls(name, dynamics, synapses, connection_parameter_sets)

    def clone(self, memo=None, **kwargs):
        return self.__class__(
            self.name,
            self.dynamics.clone(memo=memo, **kwargs),
            (s.clone(memo=memo, **kwargs) for s in self.synapses),
            (cps.clone(memo=memo, **kwargs)
             for cps in self.connection_parameter_sets))

    def serialize_node(self, node, **options):
        node.attr('name', self.name, **options)
        node.child(self.dynamics, within='Cell', **options)
        node.children(self.synapses, **options)
        node.children(self.connection_parameter_sets, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        # The only supported op at this stage
        dynamics = node.child((Dynamics, MultiDynamics), allow_ref=True,
                              within='Cell', **options)
        synapses = node.children(Synapse, **options)
        parameter_sets = node.children(ConnectionParameterSet, **options)
        name = node.attr('name', **options)
        return cls(name, dynamics, synapses, parameter_sets)

    def write(self, fname, **kwargs):
        """
        Writes the top-level NineML object to file in XML.
        """
        nineml.write(fname, self, **kwargs)


class DynamicsWithSynapses(WithSynapses, Dynamics):

    nineml_type = 'DynamicsWithSynapses'
    wrapped_class = Dynamics

    def __init__(self, name, dynamics, synapses=[],
                 connection_parameter_sets=[]):
        BaseALObject.__init__(self)
        DocumentLevelObject.__init__(self)
        ContainerObject.__init__(self)
        WithSynapses.__init__(self, name, dynamics, synapses,
                              connection_parameter_sets)
        # Create references to all dynamics member variables so that inherited
        # Dynamics properties and methods can find them.
        self._annotations = dynamics._annotations
        self._parameters = dynamics._parameters
        self._aliases = dynamics._aliases
        self._constants = dynamics._constants
        self._state_variables = dynamics._state_variables
        self._regimes = dynamics._regimes
        self._state_variables = dynamics._state_variables
        self._analog_send_ports = dynamics._analog_send_ports
        self._analog_receive_ports = dynamics._analog_receive_ports
        self._analog_reduce_ports = dynamics._analog_reduce_ports
        self._event_receive_ports = dynamics._event_receive_ports
        self._event_send_ports = dynamics._event_send_ports


class MultiDynamicsWithSynapses(WithSynapses, MultiDynamics):

    nineml_type = 'MultiDynamicsWithSynapses'
    wrapped_class = MultiDynamics

    def __init__(self, name, dynamics, synapses=[],
                 connection_parameter_sets=[]):
        BaseALObject.__init__(self)
        DocumentLevelObject.__init__(self)
        ContainerObject.__init__(self)
        WithSynapses.__init__(self, name, dynamics, synapses,
                              connection_parameter_sets)
        # Create references to all dynamics member variables so that inherited
        # Dynamics properties and methods can find them.
        self._annotations = dynamics._annotations
        self._sub_components = dynamics._sub_components
        self._analog_send_port_exposures = dynamics._analog_send_port_exposures
        self._analog_receive_port_exposures = (
            dynamics._analog_receive_port_exposures)
        self._analog_reduce_port_exposures = (
            dynamics._analog_reduce_port_exposures)
        self._event_send_port_exposures = dynamics._event_send_port_exposures
        self._event_receive_port_exposures = (
            dynamics._event_receive_port_exposures)
        self._analog_port_connections = dynamics._analog_port_connections
        self._event_port_connections = dynamics._event_port_connections


class WithSynapsesProperties(with_metaclass(ABCMeta, object)):
    """
    Mixin class to be mixed with DynamicsProperties and MultiDynamicsProperties
    classes in order to handle synapses (and their potential flattening to
    weights)
    """
    nineml_child = {'dynamics_properties': None}
    nineml_children = (SynapseProperties, ConnectionPropertySet)

    def __init__(self, name, dynamics_properties, synapse_propertiess=[],
                 connection_property_sets=[]):
        self._name = validate_identifier(name)
        self._dynamics_properties = dynamics_properties
        self.add(*synapse_propertiess)
        self.add(*connection_property_sets)
        # Extract the AL objects for the definition
        synapses = (Synapse(s.name, s.dynamics_properties.component_class,
                            s.port_connections)
                    for s in synapse_propertiess)
        connection_parameter_sets = (
            ConnectionParameterSet(
                cp.port,
                [Parameter(p.name, p.units.dimension) for p in cp.properties])
            for cp in connection_property_sets)
        self._definition = Definition(
            WithSynapses.wrap(dynamics_properties.component_class,
                              synapses, connection_parameter_sets))

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = validate_identifier(name)

    def __repr__(self):
        return ("{}WithSynapsesProperties(dynamics_properties={}, "
                "synapse_properties=[{}], connection_property_sets=[{}])"
                .format(self._dynamics_properties.__class__.__name__,
                        self._dynamics_properties,
                        ', '.format(repr(s) for s in self.synapse_propertiess),
                        ', '.format(repr(cp)
                                    for cp in self.connection_property_sets)))

    @property
    def definition(self):
        return self._definition

    @property
    def component_class(self):
        return self.definition.component_class

    @property
    def dynamics_properties(self):
        return self._dynamics_properties

    @property
    def properties(self):
        return (p for p in self._dynamics_properties.properties
                if p.name not in self._all_connection_property_names())

    @property
    def property_names(self):
        return (p.name for p in self.properties)

    @property
    def num_properties(self):
        return len(list(self.properties))

    @name_error
    def synapse_properties(self, name):
        return self._synapse_propertiess[name]

    def connection_property_set(self, name):
        return self._connection_property_sets[name]

    @property
    def synapse_propertiess(self):
        return iter(self._synapse_propertiess.values())

    @property
    def connection_property_sets(self):
        return iter(self._connection_property_sets.values())

    @property
    def num_synapse_propertiess(self):
        return len(self._synapse_propertiess)

    @property
    def num_connection_property_sets(self):
        return len(self._connection_property_sets)

    @property
    def synapse_propertiess_names(self):
        return iter(self._synapse_propertiess.keys())

    @property
    def connection_property_set_names(self):
        return iter(self._connection_property_sets.keys())

    def _all_connection_properties(self):
        return set(chain(*(
            cp.properties for cp in self.connection_property_sets)))

    def _all_connection_property_names(self):
        return (p.name for p in self._all_connection_properties())

    # NB: Has to be defined last to avoid overriding the in-built decorator
    # named 'property' as used above
    @name_error
    def property(self, name):
        if name in self._all_connection_property_names():
            raise KeyError(name)
        else:
            return self._dynamics_properties.property(name)

    @classmethod
    def wrap(cls, dynamics_properties, synapses_properties=[],
             connection_property_sets=[]):
        if isinstance(dynamics_properties, MultiDynamicsProperties):
            wrapped_cls = MultiDynamicsWithSynapsesProperties
        elif isinstance(dynamics_properties, DynamicsProperties):
            wrapped_cls = DynamicsWithSynapsesProperties
        else:
            raise Pype9RuntimeError(
                "Cannot wrap '{}' class with WithSynapses, only Dynamics and "
                "MultiDynamics".format(type(dynamics_properties)))
        return wrapped_cls(
            dynamics_properties.name, dynamics_properties, synapses_properties,
            connection_property_sets)

    def clone(self, memo=None, **kwargs):
        return self.__class__(
            self.name,
            self.dynamics_properties.clone(memo=memo, **kwargs),
            (s.clone(memo=memo, **kwargs) for s in self.synapses),
            (cps.clone(memo=memo, **kwargs)
             for cps in self.connection_property_sets))

    def serialize_node(self, node, **options):
        node.attr('name', self.name, **options)
        node.child(self.dynamics_properties, within='Cell', **options)
        node.children(self.synapses, **options)
        node.children(self.connection_property_sets, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        # The only supported op at this stage
        dynamics_properties = node.child(
            (DynamicsProperties, MultiDynamicsProperties), allow_ref=True,
            within='Cell', **options)
        synapse_properties = node.children(SynapseProperties, **options)
        property_sets = node.children(ConnectionParameterSet, **options)
        name = node.attr('name', **options)
        return cls(name, dynamics_properties, synapse_properties,
                   property_sets)


class DynamicsWithSynapsesProperties(WithSynapsesProperties,
                                     DynamicsProperties):

    def __init__(self, name, dynamics_properties, synapse_propertiess=[],
                 connection_property_sets=[]):
        # Initiate inherited base classes
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self)
        ContainerObject.__init__(self)
        WithSynapsesProperties.__init__(self, name, dynamics_properties,
                                        synapse_propertiess,
                                        connection_property_sets)
        # Create references to all dynamics member variables so that inherited
        # DynamicsProperties properties and methods can find them.
        self._annotations = dynamics_properties._annotations
        self._properties = dynamics_properties._properties
        self._initial_values = dynamics_properties._initial_values
        self._initial_regime = dynamics_properties._initial_regime


class MultiDynamicsWithSynapsesProperties(WithSynapsesProperties,
                                          MultiDynamicsProperties):

    def __init__(self, name, dynamics_properties, synapse_propertiess=[],
                 connection_property_sets=[]):
        # Initiate inherited base classes
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self)
        ContainerObject.__init__(self)
        WithSynapsesProperties.__init__(self, name, dynamics_properties,
                                        synapse_propertiess,
                                        connection_property_sets)
        # Create references to all dynamics member variables so that inherited
        # MultiDynamicsProperties properties and methods can find them.
        self._annotations = dynamics_properties._annotations
        self._sub_components = dynamics_properties._sub_components


class_map = {'Synapse': Synapse,
             'SynapseProperties': SynapseProperties,
             'DynamicsWithSynapses': DynamicsWithSynapses,
             'DynamicsWithSynapsesProperties': DynamicsWithSynapsesProperties,
             'ConnectionParameterSet': ConnectionParameterSet,
             'ConnectionPropertySet': ConnectionPropertySet,
             'MultiDynamicsWithSynapses': MultiDynamicsWithSynapses,
             'MultiDynamicsWithSynapsesProperties':
             MultiDynamicsWithSynapsesProperties}


def read(url, class_map=class_map, **kwargs):
    return nineml.read(url, class_map=class_map, **kwargs)
