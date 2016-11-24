from itertools import chain
from abc import ABCMeta
from nineml.abstraction import BaseALObject, Dynamics, Parameter
from nineml.abstraction.componentclass.visitors.xml import (
    ComponentClassXMLWriter, ComponentClassXMLLoader)
from nineml.user import (
    BaseULObject, DynamicsProperties, MultiDynamics, MultiDynamicsProperties,
    Definition, AnalogPortConnection, EventPortConnection)
from nineml.base import ContainerObject, DocumentLevelObject
from nineml.exceptions import name_error, NineMLNameError
from pype9.exceptions import Pype9RuntimeError
from nineml.xml import (
    from_child_xml, unprocessed_xml, get_xml_attr, E, extract_xmlns)
from nineml.annotations import annotate_xml, read_annotations


class WithSynapses(object):
    """
    Mixin class to be mixed with Dynamics and MultiDynamics classes in order
    to handle synapses (and their potential flattening to weights)
    """

    __metaclass__ = ABCMeta

    def __init__(self, name, dynamics, synapses, connection_parameter_sets):
        assert isinstance(dynamics, (Dynamics, MultiDynamics))
        # Initialise Dynamics/MultiDynamics base classes
        self._name = name
        self._dynamics = dynamics
        self._synapses = dict((s.name, s) for s in synapses)
        self._connection_parameter_sets = dict(
            (pw.port, pw) for pw in connection_parameter_sets)
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
        # Copy what would be class members in the dynamics class so it will
        # appear like an object of that class
        self.defining_attributes = (
            dynamics.defining_attributes +
            ('_synapses', '_connection_parameter_sets'))
        self.class_to_member = dict(
            dynamics.class_to_member.items() +
            [('Synapse', 'synapse'),
             ('ConnectionParameterSet', 'connection_parameter_set')])

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

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
        return self._synapses.itervalues()

    @property
    def connection_parameter_sets(self):
        return self._connection_parameter_sets.itervalues()

    @property
    def num_synapses(self):
        return len(self._synapses)

    @property
    def num_connection_parameter_sets(self):
        return len(self._connection_parameter_sets)

    @property
    def synapse_names(self):
        return self._synapses.iterkeys()

    @property
    def connection_parameter_set_names(self):
        return self._connection_parameter_sets.iterkeys()

    @classmethod
    def wrap(cls, dynamics, synapses=[], connection_parameter_sets=[]):
        if isinstance(dynamics, MultiDynamics):
            wrapped_cls = MultiDynamicsWithSynapses
        elif isinstance(dynamics, Dynamics):
            wrapped_cls = DynamicsWithSynapses
        else:
            raise Pype9RuntimeError(
                "Cannot wrap '{}' class with WithSynapses, only Dynamics and "
                "MultiDynamics".format(type(dynamics)))
        return wrapped_cls(dynamics.name, dynamics, synapses,
                           connection_parameter_sets)

    def clone(self, memo=None, **kwargs):
        return self.__class__(
            self.name,
            self.dynamics.clone(memo=memo, **kwargs),
            (s.clone(memo=memo, **kwargs) for s in self.synapses),
            (cps.clone(memo=memo, **kwargs)
             for cps in self.connection_parameter_sets))

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):
        return E(self.nineml_type,
                 E.Cell(self.dynamics.to_xml(document, E=E, **kwargs)),
                 *chain((s.to_xml(document, E, **kwargs)
                         for s in self.synapses),
                        (cps.to_xml(document, E, **kwargs)
                         for cps in self.connection_parameter_sets)),
                 name=self.name)

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        # The only supported op at this stage
        dynamics = from_child_xml(
            element, cls.wrapped_class, document, within='Cell',
            allow_reference=True, **kwargs)
        synapses = from_child_xml(
            element, Synapse, document, multiple=True, allow_none=True,
            **kwargs)
        parameter_sets = from_child_xml(
            element, ConnectionParameterSet, document, multiple=True,
            allow_none=True, **kwargs)
        name = get_xml_attr(element, 'name', document, **kwargs)
        return cls(name, dynamics, synapses, parameter_sets)

    def write(self, fname):
        """
        Writes the top-level NineML object to file in XML.
        """
        pype9.base.document.write(self, fname)


class DynamicsWithSynapses(WithSynapses, Dynamics):

    nineml_type = 'DynamicsWithSynapses'
    wrapped_class = Dynamics

    def __init__(self, name, dynamics, synapses=[],
                 connection_parameter_sets=[]):
        WithSynapses.__init__(self, name, dynamics, synapses,
                              connection_parameter_sets)
        BaseALObject.__init__(self)
        DocumentLevelObject.__init__(self, dynamics.document)
        ContainerObject.__init__(self)
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
        WithSynapses.__init__(name, self, dynamics, synapses,
                              connection_parameter_sets)
        BaseALObject.__init__(self)
        DocumentLevelObject.__init__(self, dynamics.document)
        ContainerObject.__init__(self)
        # Create references to all dynamics member variables so that inherited
        # Dynamics properties and methods can find them.
        self._annotations = dynamics._annotations
        self._sub_components = dynamics._sub_components
        self._analog_send_ports = dynamics._analog_send_ports
        self._analog_receive_ports = dynamics._analog_receive_ports
        self._analog_reduce_ports = dynamics._analog_reduce_ports
        self._event_send_ports = dynamics._event_send_ports
        self._event_receive_ports = dynamics._event_receive_ports
        self._analog_port_connections = dynamics._analog_port_connections
        self._event_port_connections = dynamics._event_port_connections


class WithSynapsesProperties(object):
    """
    Mixin class to be mixed with DynamicsProperties and MultiDynamicsProperties
    classes in order to handle synapses (and their potential flattening to
    weights)
    """

    __metaclass__ = ABCMeta

    def __init__(self, name, dynamics_properties, synapse_properties=[],
                 connection_property_sets=[]):
        self._name = name
        self._dynamics_properties = dynamics_properties
        self._synapses = dict((s.name, s) for s in synapse_properties)
        self._connection_property_sets = dict(
            (cp.port, cp) for cp in connection_property_sets)
        # Extract the AL objects for the definition
        synapses = (Synapse(s.name, s.dynamics_properties.component_class,
                            s.port_connections)
                    for s in synapse_properties)
        connection_parameter_sets = (
            ConnectionParameterSet(
                cp.port,
                [Parameter(p.name, p.units.dimension) for p in cp.properties])
            for cp in connection_property_sets)
        self._definition = Definition(
            WithSynapses.wrap(dynamics_properties.component_class,
                              synapses, connection_parameter_sets))
        # Copy what would be class members in the dynamics class so it will
        # appear like an object of that class
        self.defining_attributes = (dynamics_properties.defining_attributes +
                                    ('_synapses', '_connection_property_sets'))
        self.class_to_member = dict(
            dynamics_properties.class_to_member.items() +
            [('Synapse', 'synapse'),
             ('ConnectionPropertySet', 'connection_property_set')])

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def __repr__(self):
        return ("{}WithSynapsesProperties(dynamics_properties={}, "
                "synapses=[{}], connection_property_sets=[{}])"
                .format(self._dynamics_properties.__class__.__name__,
                        self._dynamics_properties,
                        ', '.format(repr(s) for s in self.synapses),
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
    def synapse(self, name):
        return self._synapses[name]

    def connection_property_set(self, name):
        return self._connection_property_sets[name]

    @property
    def synapses(self):
        return self._synapses.itervalues()

    @property
    def connection_property_sets(self):
        return self._connection_property_sets.itervalues()

    @property
    def num_synapses(self):
        return len(self._synapses)

    @property
    def num_connection_property_sets(self):
        return len(self._connection_property_sets)

    @property
    def synapse_names(self):
        return self._synapses.iterkeys()

    @property
    def connection_property_set_names(self):
        return self._connection_property_sets.iterkeys()

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


class DynamicsWithSynapsesProperties(WithSynapsesProperties,
                                     DynamicsProperties):

    def __init__(self, name, dynamics_properties, synapses_properties=[],
                 connection_property_sets=[]):
        WithSynapsesProperties.__init__(self, name, dynamics_properties,
                                        synapses_properties,
                                        connection_property_sets)
        # Initiate inherited base classes
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, dynamics_properties.document)
        ContainerObject.__init__(self)
        # Create references to all dynamics member variables so that inherited
        # DynamicsProperties properties and methods can find them.
        self._annotations = dynamics_properties._annotations
        self._properties = dynamics_properties._properties


class MultiDynamicsWithSynapsesProperties(WithSynapsesProperties,
                                          MultiDynamicsProperties):

    def __init__(self, name, dynamics_properties, synapses_properties=[],
                 connection_property_sets=[]):
        WithSynapsesProperties.__init__(self, name, dynamics_properties,
                                        synapses_properties,
                                        connection_property_sets)
        # Initiate inherited base classes
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, dynamics_properties.document)
        ContainerObject.__init__(self)
        # Create references to all dynamics member variables so that inherited
        # MultiDynamicsProperties properties and methods can find them.
        self._annotations = dynamics_properties._annotations
        self._sub_components = dynamics_properties._sub_components


class ConnectionParameterSet(BaseALObject):

    nineml_type = 'ConnectionParameterSet'
    defining_attributes = ('_port', '_parameters')

    def __init__(self, port, parameters):
        super(ConnectionParameterSet, self).__init__()
        self._port = port
        # Ensure that parameters are not _NamespaceParameters
        self._parameters = [Parameter(p.name, p.dimension) for p in parameters]

    def __repr__(self):
        return ("ConnectionParameterSet(port={}, parameters=[{}])"
                .format(self.port,
                        ', '.join(repr(p) for p in self.parameters)))

    @property
    def port(self):
        return self._port

    @property
    def parameters(self):
        return self._parameters

    @property
    def parameter_names(self):
        return (p.name for p in self.parameters)

    def clone(self, memo=None, **kwargs):
        return self.__class__(
            self.port,
            [p.clone(memo=memo, **kwargs) for p in self.parameters])

    @annotate_xml
    def to_xml(self, document, E, **kwargs):
        xml_writer = ComponentClassXMLWriter(document, E, **kwargs)
        return E(self.nineml_type,
                 *(xml_writer.visit(p) for p in self.parameters),
                 port=self.port)

    @classmethod
    @read_annotations
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable @IgnorePep8
        # FIXME: Ideally Parameter should have from_xml method that calls
        #        the ComponentClassXMLLoader. To do this, the BaseALObject
        #        should be split into
        #        BaseDynamicsObject/BaseConnectionRuleObject/... and then they
        #        can each have a generic from_xml method that calls the right
        #        visitor
        # parameters = from_child_xml(
        #     element, Parameter, document, multiple=True, **kwargs)
        loader = ComponentClassXMLLoader(document, **kwargs)
        xmlns = extract_xmlns(element.tag)
        parameters = []
        for param_elem in element.findall(xmlns + Parameter.nineml_type):
            parameters.append(loader.load_parameter(param_elem))
        return cls(get_xml_attr(element, 'port', document, **kwargs),
                   parameters)


class ConnectionPropertySet(BaseULObject):

    nineml_type = 'ConnectionPropertySet'
    defining_attributes = ('_port', '_properties')

    def __init__(self, port, properties):
        super(ConnectionPropertySet, self).__init__()
        self._port = port
        self._properties = properties

    def __repr__(self):
        return ("ConnectionPropertySet(port={}, properties=[{}])"
                .format(self.port,
                        ', '.join(repr(p) for p in self.properties)))

    @property
    def port(self):
        return self._port

    @property
    def properties(self):
        return self._properties

    def clone(self, memo=None, **kwargs):
        return self.__class__(
            self.port,
            [p.clone(memo=memo, **kwargs) for p in self.properties])


class Synapse(BaseALObject):

    nineml_type = 'Synapse'
    defining_attributes = ('_name', '_dynamics', '_port_connections')

    def __init__(self, name, dynamics, port_connections):
        super(Synapse, self).__init__()
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

    def clone(self, memo=None, **kwargs):
        return self.__class__(
            self.name,
            self.dynamics.clone(memo=memo, **kwargs),
            [pc.clone(memo=memo, **kwargs) for pc in self.port_connections])

    @annotate_xml
    def to_xml(self, document, E, **kwargs):
        return E(self.nineml_type,
                 self.dynamics.to_xml(document, E, **kwargs),
                 *(pc.to_xml(document, E, **kwargs)
                   for pc in self.port_connections),
                 name=self.name)

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        # The only supported op at this stage
        dynamics = from_child_xml(
            element, Dynamics, document, **kwargs)
        analog_port_connections = from_child_xml(
            element, AnalogPortConnection, document, multiple=True,
            allow_none=True, **kwargs)
        event_port_connections = from_child_xml(
            element, EventPortConnection, document, multiple=True,
            allow_none=True, **kwargs)
        return cls(get_xml_attr(element, 'name', document, **kwargs),
                   dynamics, chain(analog_port_connections,
                                   event_port_connections))


class SynapseProperties(BaseULObject):

    nineml_type = 'SynapseProperties'
    defining_attributes = ('_name', '_dynamics_properties',
                           '_port_connections')

    def __init__(self, name, dynamics_properties, port_connections):
        super(SynapseProperties, self).__init__()
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

    @annotate_xml
    def to_xml(self, document, E, **kwargs):
        return E(self.nineml_type,
                 self.dynamics_properties.to_xml(document, E, **kwargs),
                 *(pc.to_xml(document, E, **kwargs)
                   for pc in self.port_connections),
                 name=self.name)

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        # The only supported op at this stage
        dynamics_properties = from_child_xml(
            element, DynamicsProperties, document, **kwargs)
        analog_port_connections = from_child_xml(
            element, AnalogPortConnection, document, multiple=True,
            allow_none=True, **kwargs)
        event_port_connections = from_child_xml(
            element, EventPortConnection, document, multiple=True,
            allow_none=True, **kwargs)
        return cls(get_xml_attr(element, 'name', document, **kwargs),
                   dynamics_properties, chain(analog_port_connections,
                                              event_port_connections))


import pype9.base.document  # @IgnorePep8
