"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from collections import namedtuple, defaultdict
from itertools import chain
import quantities as pq
import neo
from nineml.user import Property
from pype9.exceptions import Pype9RuntimeError
from .values import get_pyNN_value
import os.path
import nineml
from nineml import units as un
from pyNN.parameters import Sequence
import pyNN.standardmodels
from nineml import Document
from nineml.exceptions import NineMLNameError
from nineml.user.multi import (
    MultiDynamicsProperties, append_namespace, BasePortExposure)
from nineml.abstraction import StateVariable
from nineml.user import (
    ComponentArray as ComponentArray9ML,
    EventConnectionGroup as EventConnectionGroup9ML,
    AnalogConnectionGroup as AnalogConnectionGroup9ML,
    Selection as Selection9ML,
    Concatenate as Concatenate9ML)
from pype9.exceptions import Pype9UnflattenableSynapseException
from .connectivity import InversePyNNConnectivity
from ..cells import (
    MultiDynamicsWithSynapsesProperties, ConnectionPropertySet,
    SynapseProperties)
from pype9.exceptions import Pype9UsageError, Pype9NameError


_REQUIRED_SIM_PARAMS = ['timestep', 'min_delay', 'max_delay', 'temperature']


class Network(object):
    """
    Constructs a network simulation, generating and compiling dynamics classes
    as required (depending on the 'build_mode' option). The populations and
    projections of the network are flattened so that the synapse projections
    are included in the cell dynamics and the connection groups are just
    static connections.

    Parameters
    ----------
    nineml_model : nineml.Network | nineml.Document | URL
        A 9ML-Python model of a network (or Document containing
        populations and projections for 9MLv1) or a URL referring to a 9ML
        model.
    build_mode : str
        The strategy used to build and compile the model. Can be one of
        ::class::BaseCodeGenerator.BUILD_MODE_OPTIONS
    build_dir : str (directory path)
        The directory in which to build the simulator-native code. If None
        a build directory is generated.
    """

    # Name given to the "cell" component of the cell dynamics + linear synapse
    # dynamics multi-dynamics
    CELL_COMP_NAME = 'cell'

    def __init__(self, nineml_model, build_mode='lazy', build_dir=None,
                 **kwargs):
        if isinstance(nineml_model, basestring):
            nineml_model = nineml.read(nineml_model).as_network(
                name=os.path.splitext(os.path.basename(nineml_model))[0])
        elif isinstance(nineml_model, Document):
            if nineml_model.url is not None:
                name = os.path.splitext(os.path.basename(nineml_model.url))[0]
            else:
                name = "Anonymous"
            nineml_model = nineml_model.as_network(name=name)
        self._nineml = nineml_model.clone()
        # Get RNG for random distribution values and connectivity
        rng = self.Simulation.active().properties_rng
        if build_mode != 'build_only':
            self.nineml.resample_connectivity(
                connectivity_class=self.ConnectivityClass, rng=rng)
        (flat_comp_arrays, flat_conn_groups,
         flat_selections) = self._flatten_to_arrays_and_conns(self._nineml)
        self._component_arrays = {}
        code_gen = self.CellCodeGenerator()
        # Build the PyNN populations
        for name, comp_array in flat_comp_arrays.iteritems():
            if build_dir is None:
                array_build_dir = code_gen.get_build_dir(
                    self.nineml.url, name, group=self.nineml.name)
            else:
                array_build_dir = os.path.join(build_dir, name)
            self._component_arrays[name] = self.ComponentArrayClass(
                comp_array, build_mode=build_mode, build_dir=array_build_dir,
                **kwargs)
        self._selections = {}
        # Build the PyNN Selections
        for selection in flat_selections.itervalues():
            # TODO: Assumes that selections are only concatenations (which is
            #       true for 9MLv1.0 but not v2.0)
            self._selections[selection.name] = self.SelectionClass(
                selection, *[self.component_array(p.name)
                             for p in selection.populations])
        if build_mode != 'build_only':
            # Set the connectivity objects of the projections to the
            # PyNNConnectivity class
            if self.nineml.connectivity_has_been_sampled():
                raise Pype9RuntimeError(
                    "Connections have already been sampled, please reset them"
                    " using 'resample_connectivity' before constructing "
                    "network")
            self._connection_groups = {}
            for name, conn_group in flat_conn_groups.iteritems():
                try:
                    source = self._component_arrays[conn_group.source.name]
                except KeyError:
                    source = self._selections[conn_group.source.name]
                try:
                    destination = self._component_arrays[
                        conn_group.destination.name]
                except KeyError:
                    destination = self._selections[conn_group.destination.name]
                self._connection_groups[name] = self.ConnectionGroupClass(
                    conn_group, source=source, destination=destination)
            self._finalise_construction()

    def _finalise_construction(self):
        """
        Can be overriden by deriving classes to do any simulator-specific
        finalisation that is required
        """
        pass

    @property
    def nineml(self):
        return self._nineml

    @property
    def component_arrays(self):
        "Iterate through component arrays"
        return self._component_arrays.itervalues()

    @property
    def connection_groups(self):
        "Iterate through connection_groups"
        return self._connection_groups.itervalues()

    @property
    def selections(self):
        "Iterate through selections"
        return self._selections.itervalues()

    def component_array(self, name):
        """
        Returns the component array matching the given name

        Parameters
        ----------
        name : str
            Name of the component array
        """
        try:
            return self._component_arrays[name]
        except KeyError:
            raise Pype9NameError(
                "No component array named '{}' (possible '{}')"
                .format(name, "', '".join(self.component_array_names)))

    def connection_group(self, name):
        """
        Returns the connection group matching the given name

        Parameters
        ----------
        name : str
            Name of the component array
        """
        try:
            return self._connection_groups[name]
        except KeyError:
            raise Pype9NameError(
                "No connection group named '{}' (possible '{}')"
                .format(name, "', '".join(self.connection_group_names)))

    def selection(self, name):
        """
        Returns the selection matching the given name

        Parameters
        ----------
        name : str
            Name of the selection
        """
        try:
            return self._selections[name]
        except KeyError:
            raise Pype9NameError(
                "No selection named '{}' (possible '{}')"
                .format(name, "', '".join(self.selection_names)))

    @property
    def num_component_arrays(self):
        return len(self._component_arrays)

    @property
    def num_connection_groups(self):
        return len(self._connection_groups)

    @property
    def num_selections(self):
        return len(self._selections)

    @property
    def component_array_names(self):
        return self._component_arrays.keys()

    @property
    def connection_group_names(self):
        return self._connection_groups.keys()

    @property
    def selection_names(self):
        return self._selections.keys()

    def save_connections(self, output_dir):
        """
        Saves generated connections to output directory

        @param output_dir:
        """
        for conn_grp in self.connection_groups.itervalues():
            if isinstance(conn_grp.synapse_type,
                          pyNN.standardmodels.synapses.ElectricalSynapse):
                attributes = 'weight'
            else:
                attributes = 'all'
            conn_grp.save(attributes, os.path.join(
                output_dir, conn_grp.label + '.proj'), format='list',
                gather=True)

    def record(self, variable):
        """
        Record variable from complete network
        """
        for comp_array in self.component_arrays:
            comp_array.record(variable)

    def write_data(self, file_prefix, **kwargs):
        """
        Record all spikes generated in the network

        @param filename: The prefix for every population files before the
                         popluation name. The suffix '.spikes' will be
                         appended to the filenames as well.
        """
        # Add a dot to separate the prefix from the population label if it
        # doesn't already have one and isn't a directory
        if (not os.path.isdir(file_prefix) and
            not file_prefix.endswith('.') and
              not file_prefix.endswith(os.path.sep)):
            file_prefix += '.'
        for comp_array in self.component_arrays.itervalues():
            # @UndefinedVariable
            comp_array.write_data(file_prefix + comp_array.name + '.pkl',
                                  **kwargs)

    @classmethod
    def _flatten_synapse(cls, projection_model):
        """
        Flattens the reponse and plasticity dynamics into a single synapse
        element (will be 9MLv2 format) and updates the port connections
        to match the changed object.
        """
        role2name = {'response': 'psr', 'plasticity': 'pls'}
        syn_comps = {
            role2name['response']: projection_model.response,
            role2name['plasticity']: projection_model.plasticity}
        # Get all projection port connections that don't project to/from
        # the "pre" population and convert them into local MultiDynamics
        # port connections of the synapse
        syn_internal_conns = (
            pc.__class__(
                sender_name=role2name[pc.sender_role],
                receiver_name=role2name[pc.receiver_role],
                send_port=pc.send_port_name, receive_port=pc.receive_port_name)
            for pc in projection_model.port_connections
            if (pc.sender_role in ('plasticity', 'response') and
                pc.receiver_role in ('plasticity', 'response')))
        receive_conns = [pc for pc in projection_model.port_connections
                         if (pc.sender_role in ('pre', 'post') and
                             pc.receiver_role in ('plasticity', 'response'))]
        send_conns = [pc for pc in projection_model.port_connections
                      if (pc.sender_role in ('plasticity', 'response') and
                          pc.receiver_role in ('pre', 'post'))]
        syn_exps = chain(
            (BasePortExposure.from_port(pc.send_port,
                                        role2name[pc.sender_role])
             for pc in send_conns),
            (BasePortExposure.from_port(pc.receive_port,
                                        role2name[pc.receiver_role])
             for pc in receive_conns))
        synapse = MultiDynamicsProperties(
            name=(projection_model.name + '_syn'),
            sub_components=syn_comps,
            port_connections=syn_internal_conns,
            port_exposures=syn_exps)
        port_connections = list(chain(
            (pc.__class__(sender_role=pc.sender_role,
                          receiver_role='synapse',
                          send_port=pc.send_port_name,
                          receive_port=append_namespace(
                              pc.receive_port_name,
                              role2name[pc.receiver_role]))
             for pc in receive_conns),
            (pc.__class__(sender_role='synapse',
                          receiver_role=pc.receiver_role,
                          send_port=append_namespace(
                              pc.send_port_name,
                              role2name[pc.sender_role]),
                          receive_port=pc.receive_port_name)
             for pc in send_conns),
            (pc for pc in projection_model.port_connections
             if (pc.sender_role in ('pre', 'post') and
                 pc.receiver_role in ('pre', 'post')))))
        # A bit of a hack in order to bind the port_connections
        dummy_container = namedtuple('DummyContainer', 'pre post synapse')(
            projection_model.pre, projection_model.post, synapse)
        for port_connection in port_connections:
            port_connection.bind(dummy_container, to_roles=True)
        return synapse, port_connections

    @classmethod
    def _flatten_to_arrays_and_conns(cls, network_model):
        """
        Convert populations and projections into component arrays and
        connection groups
        """
        component_arrays = {}
        connection_groups = {}
        # Create flattened component with all synapses combined with the post-
        # synaptic cell dynamics using MultiDynamics
        for pop in network_model.populations:
            # Get all the projections that project to/from the given population
            receiving = [p for p in network_model.projections
                         if (pop == p.post or
                             (p.post.nineml_type == 'Selection' and
                              pop in p.post.populations))]
            sending = [p for p in network_model.projections
                       if (pop == p.pre or
                           (p.pre.nineml_type == 'Selection' and
                            pop in p.pre.populations))]
            # Create a dictionary to hold the cell dynamics and any synapse
            # dynamics that can be flattened into the cell dynamics
            # (i.e. linear ones).
            sub_components = {cls.CELL_COMP_NAME: pop.cell}
            # All port connections between post-synaptic cell and linear
            # synapses and port exposures to pre-synaptic cell
            internal_conns = []
            exposures = set()
            synapses = []
            connection_property_sets = []
            # FIXME: There has to be a way of avoiding this name clash
            if any(p.name == cls.CELL_COMP_NAME for p in receiving):
                raise Pype9RuntimeError(
                    "Cannot handle projections named '{}' (why would you "
                    "choose such a silly name?;)".format(cls.CELL_COMP_NAME))
            for proj in receiving:
                # Flatten response and plasticity into single dynamics class.
                # TODO: this should be no longer necessary when we move to
                # version 2 as response and plasticity elements will be
                # replaced by a synapse element in the standard. It will need
                # be copied at this point though as it is modified
                synapse, proj_conns = cls._flatten_synapse(proj)
                # Get all connections to/from the pre-synaptic cell
                pre_conns = [pc for pc in proj_conns
                             if 'pre' in (pc.receiver_role, pc.sender_role)]
                # Get all connections between the synapse and the post-synaptic
                # cell
                post_conns = [pc for pc in proj_conns if pc not in pre_conns]
                # Mapping of port connection role to sub-component name
                role2name = {'post': cls.CELL_COMP_NAME}
                # If the synapse is non-linear it can be combined into the
                # dynamics of the post-synaptic cell.
                try:
                    if not synapse.component_class.is_linear():
                        raise Pype9UnflattenableSynapseException()
                    role2name['synapse'] = proj.name
                    # Extract "connection weights" (any non-singular property
                    # value) from the synapse properties
                    connection_property_sets.extend(
                        cls._extract_connection_property_sets(synapse,
                                                              proj.name))
                    # Add the flattened synapse to the multi-dynamics sub
                    # components
                    sub_components[proj.name] = synapse
                    # Convert port connections between synpase and post-
                    # synaptic cell into internal port connections of a multi-
                    # dynamics object
                    internal_conns.extend(pc.assign_names_from_roles(role2name)
                                          for pc in post_conns)
                    # Expose ports that are needed for the pre-synaptic
                    # connections
                except Pype9UnflattenableSynapseException:
                    # All synapses (of this type) connected to a single post-
                    # synaptic cell cannot be flattened into a single component
                    # of a multi- dynamics object so an individual synapses
                    # must be created for each connection.
                    synapses.append(SynapseProperties(proj.name, synapse,
                                                      post_conns))
                    # Add exposures to the post-synaptic cell for connections
                    # from the synapse
                    exposures.update(
                        chain(*(pc.expose_ports({'post': cls.CELL_COMP_NAME})
                                for pc in post_conns)))
                # Add exposures for connections to/from the pre synaptic cell
                exposures.update(
                    chain(*(pc.expose_ports(role2name) for pc in pre_conns)))
                role2name['pre'] = cls.CELL_COMP_NAME
            # Add exposures for connections to/from the pre-synaptic cell in
            # populations.
            for proj in sending:
                # Not required after transition to version 2 syntax
                synapse, proj_conns = cls._flatten_synapse(proj)
                # Add send and receive exposures to list
                exposures.update(chain(*(
                    pc.expose_ports({'pre': cls.CELL_COMP_NAME})
                    for pc in proj_conns)))
            # Add all cell ports as multi-component exposures that aren't
            # connected internally in case the user would like to save them or
            # play data into them
            internal_cell_ports = set(chain(
                (pc.send_port_name for pc in internal_conns
                 if pc.sender_name == cls.CELL_COMP_NAME),
                (pc.receive_port_name for pc in internal_conns
                 if pc.receiver_name == cls.CELL_COMP_NAME)))
            exposures.update(
                BasePortExposure.from_port(p, cls.CELL_COMP_NAME)
                for p in pop.cell.ports if p.name not in internal_cell_ports)
            dynamics_properties = MultiDynamicsProperties(
                name=pop.name + '_cell', sub_components=sub_components,
                port_connections=internal_conns, port_exposures=exposures)
            component = MultiDynamicsWithSynapsesProperties(
                dynamics_properties.name,
                dynamics_properties, synapses_properties=synapses,
                connection_property_sets=connection_property_sets)
            array_name = pop.name
            component_arrays[array_name] = ComponentArray9ML(
                array_name, pop.size, component)
        selections = {}
        for sel in network_model.selections:
            selections[sel.name] = Selection9ML(
                sel.name, Concatenate9ML(*(component_arrays[p.name]
                                           for p in sel.populations)))
        arrays_and_selections = dict(
            chain(component_arrays.iteritems(), selections.iteritems()))
        # Create ConnectionGroups from each port connection in Projection
        for proj in network_model.projections:
            _, proj_conns = cls._flatten_synapse(proj)
            # Get all connections to/from the pre-synaptic cell
            pre_conns = [pc for pc in proj_conns
                         if 'pre' in (pc.receiver_role, pc.sender_role)]
            # Create a connection group for each port connection of the
            # projection to/from the pre-synaptic cell
            for port_conn in pre_conns:
                ConnectionGroupClass = (
                    EventConnectionGroup9ML
                    if port_conn.communicates == 'event'
                    else AnalogConnectionGroup9ML)
                if len(pre_conns) > 1:
                    name = ('__'.join((proj.name,
                                       port_conn.sender_role,
                                       port_conn.send_port_name,
                                       port_conn.receiver_role,
                                       port_conn.receive_port_name)))
                else:
                    name = proj.name
                if port_conn.sender_role == 'pre':
                    connectivity = proj.connectivity
                    # If a connection from the pre-synaptic cell the delay
                    # is included
                    # TODO: In version 2 all port-connections will have
                    # their own delays
                    delay = proj.delay
                else:
                    # If a "reverse connection" to the pre-synaptic cell
                    # the connectivity needs to be inverted
                    connectivity = InversePyNNConnectivity(
                        proj.connectivity)
                    delay = 0.0 * un.s
                # Append sub-component namespaces to the source/receive
                # ports
                ns_port_conn = port_conn.append_namespace_from_roles(
                    {'post': cls.CELL_COMP_NAME,
                     'pre': cls.CELL_COMP_NAME,
                     'synapse': proj.name})
                conn_group = ConnectionGroupClass(
                    name,
                    arrays_and_selections[proj.pre.name],
                    arrays_and_selections[proj.post.name],
                    source_port=ns_port_conn.send_port_name,
                    destination_port=ns_port_conn.receive_port_name,
                    connectivity=connectivity,
                    delay=delay)
                connection_groups[conn_group.name] = conn_group
        return component_arrays, connection_groups, selections

    @classmethod
    def _extract_connection_property_sets(cls, dynamics_properties, namespace):
        """
        Identifies properties in the provided DynmaicsProperties that can be
        treated as a property of the connection (i.e. are not referenced
        anywhere except within the OnEvent blocks event port).
        """
        component_class = dynamics_properties.component_class
        varying_params = set(
            component_class.parameter(p.name)
            for p in dynamics_properties.properties
            if p.value.nineml_type != 'SingleValue')
        # Get list of ports refereneced (either directly or indirectly) by
        # time derivatives and on-conditions
        not_permitted = set(p.name for p in component_class.required_for(
            chain(component_class.all_time_derivatives(),
                  component_class.all_on_conditions())).parameters)
        # If varying params intersects parameters that are referenced in time
        # derivatives they can not be redefined as connection parameters
        if varying_params & not_permitted:
            raise Pype9UnflattenableSynapseException()
        conn_params = defaultdict(set)
        for on_event in component_class.all_on_events():
            on_event_params = set(component_class.required_for(
                on_event.state_assignments).parameters)
            conn_params[on_event.src_port_name] |= (varying_params &
                                                    on_event_params)
        return [
            ConnectionPropertySet(
                append_namespace(prt, namespace),
                [Property(append_namespace(p.name, namespace),
                          dynamics_properties.property(p.name).quantity)
                 for p in params])
            for prt, params in conn_params.iteritems() if params]

#             raise NotImplementedError(
#                 "Cannot convert population '{}' to component array as "
#                 "it has a non-linear synapse or multiple non-single "
#                 "properties")

#         # Get the properties, which are not single values, as they
#         # will have to be varied with each synapse. If there is
#         # only one it the weight of the synapse in NEURON and NEST
#         # can be used to hold it otherwise it won't be possible to
#         # collapse the synapses into a single dynamics object
#         non_single_props = [
#             p for p in synapse.properties
#             if not isinstance(p.value, SingleValue)]


class ComponentArray(object):
    """
    Component array object corresponds to a NineML type to be introduced in
    NineMLv2 (see https://github.com/INCF/nineml/issues/46), which consists of
    a dynamics class and a size. Populations and the synapses on incoming
    projections.

    Parameters
    ----------
    nineml_model : nineml.ComponentArray
        Component array nineml
    build_mode : str
        The build/compilation strategy for rebuilding the generated code, can
        be one of 'lazy', 'force', 'build_only', 'require'.
    """

    def __init__(self, nineml_model, build_mode='lazy', **kwargs):
        if not isinstance(nineml_model, ComponentArray9ML):
            raise Pype9RuntimeError(
                "Expected a component array, found {}".format(nineml_model))
        self._nineml = nineml_model
        dynamics_properties = nineml_model.dynamics_properties
        dynamics = dynamics_properties.component_class
        celltype = self.PyNNCellWrapperMetaClass(
            name=nineml_model.name, component_class=dynamics,
            default_properties=dynamics_properties,
            initial_state=list(dynamics_properties.initial_values),
            initial_regime=dynamics_properties.initial_regime,
            build_mode=build_mode, **kwargs)
        if build_mode != 'build_only':
            rng = self.Simulation.active().properties_rng
            cellparams = dict(
                (p.name, get_pyNN_value(p, self.UnitHandler, rng))
                for p in dynamics_properties.properties)
            initial_values = dict(
                (i.name, get_pyNN_value(i, self.UnitHandler, rng))
                for i in dynamics_properties.initial_values)
            initial_values['_regime'] = celltype.model.regime_index(
                dynamics_properties.initial_regime)
            # NB: Simulator-specific derived classes extend the corresponding
            # PyNN population class
            self.PyNNPopulationClass.__init__(
                self, nineml_model.size, celltype, cellparams=cellparams,
                initial_values=initial_values,
                label=nineml_model.name)
            self._inputs = {}
        self._t_stop = None
        self.Simulation.active().register_array(self)

    @property
    def name(self):
        return self._nineml.name

    @property
    def nineml(self):
        return self._nineml

    @property
    def component_class(self):
        return self.nineml.component_class

    def synapse(self, name):
        return self.nineml.dynamics_properties.synapse(name)

    def __repr__(self):
        return "ComponentArray('{}', size={})".format(self.name, self.size)

    def play(self, port_name, signal, properties=[]):
        """
        Plays an analog signal or train of events into a port of the dynamics
        array.

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
        port = self.celltype.model.component_class.receive_port(port_name)
        if port.nineml_type in ('EventReceivePort',
                                'EventReceivePortExposure'):
            # Shift the signal times to account for the minimum delay and
            # match the NEURON implementation
            try:
                spike_trains = Sequence(pq.Quantity(signal, 'ms') -
                                        self._min_delay * pq.ms)
                source_size = 1
            except ValueError:  # Assume multiple signals
                spike_trains = []
                for spike_train in signal:
                    spike_train = (pq.Quantity(spike_train, 'ms') -
                                   self._min_delay * pq.ms)
                    if any(spike_train <= 0.0):
                        raise Pype9RuntimeError(
                            "Some spike times are less than device delay ({}) "
                            "and so can't be played into cell ({})".format(
                                self._min_delay,
                                ', '.join(str(st) for st in spike_train[
                                    spike_train < self._min_delay])))
                    spike_trains.append(Sequence(spike_train))
                source_size = len(spike_trains)
            input_pop = self.PyNNPopulationClass(
                source_size, self.SpikeSourceArray,
                cellparams={'spike_times': spike_trains},
                label='{}-{}-input'.format(self.name, port_name))
#             self.celltype.model()._check_connection_properties(port_name,
#                                                                properties)
            if len(properties) > 1:
                raise NotImplementedError(
                    "Cannot handle more than one connection property per port")
            elif properties:
                weight = self.UnitHandler.scale_value(properties[0].quantity)
            else:
                weight = 1.0  # The weight var is not used
            connector = (self.OneToOneConnector()
                         if source_size > 1 else self.AllToAllConnector())
            input_proj = self.PyNNProjectionClass(
                input_pop, self, connector,
                self.SynapseClass(weight=weight, delay=self._min_delay),
                receptor_type=port_name,
                label='{}-{}-input_projection'.format(self.name, port_name))
            self._inputs[port_name] = (input_pop, input_proj)
        elif port.nineml_type in ('AnalogReceivePort', 'AnalogReducePort',
                                  'AnalogReceivePortExposure',
                                  'AnalogReducePortExposure'):
            raise NotImplementedError
#             # Signals are played into NEST cells include a delay (set to be the
#             # minimum), which is is subtracted from the start of the signal so
#             # that the effect of the signal aligns with other simulators
#             self._inputs[port_name] = nest.Create(
#                 'step_current_generator', 1,
#                 {'amplitude_values': pq.Quantity(signal, 'pA'),
#                  'amplitude_times': (
#                     pq.Quantity(signal.times, 'ms') -
#                     controller.device_delay * pq.ms),
#                  'start': float(pq.Quantity(signal.t_start, 'ms')),
#                  'stop': float(pq.Quantity(signal.t_stop, 'ms'))})
#             nest.Connect(self._inputs[port_name], self._cell,
#                          syn_spec={
#                              "receptor_type": self._receive_ports[port_name],
#                              'delay': controller.device_delay})
        else:
            raise Pype9RuntimeError(
                "Unrecognised port type '{}' to play signal into".format(port))

    def _get_port_details(self, port_name):
        """
        Return the communication type of the corresponding port and its fully
        qualified name in the cell-synapse namespace (e.g. the 'spike_output'
        port in the cell namespace will be 'spike_output__cell')

        Parameters
        ----------
        port_name : str
            Name of the port or state variable

        Returns
        -------
        communicates : str
            Either 'event' or 'analog' depending on the type of port port_name
            corresponds to
        record_name : str
            Name of the port fully qualified in the joint cell-synapse
            namespace
        """
        # TODO: Need to add a check that the port was recorded
        component_class = self.celltype.model.component_class
        port = None
        for name in (port_name, port_name + '__cell'):
            try:
                port = component_class.send_port(name)
            except NineMLNameError:
                try:
                    port = component_class.state_variable(name)
                except NineMLNameError:
                    pass
        if port is None:
            raise Pype9UsageError(
                "Unknown port or state-variable '{}' for '{}' "
                "component array (available '{}').".format(
                    port_name, self.name, "', '".join(chain(
                        component_class.send_port_names,
                        component_class.sub_component(
                            'cell').send_port_names))))
        if isinstance(port, StateVariable):
            communicates = 'analog'
        else:
            communicates = port.communicates
        return communicates, port.name

    def record(self, port_name):
        """
        Records the port or state variable

        Parameters
        ----------
        port_name : str
            Name of the port to record
        """

    def recording(self, port_name):
        """
        Returns the recorded data for the given port name

        Parameters
        ----------
        port_name : str
            The name of the port (or state-variable) to retrieve the recorded
            data for

        Returns
        -------
        recording : neo.Segment
            The recorded data in a neo.Segment
        """

        pyNN_data = self.get_data().segments[0]
        recording = neo.Segment()
        communicates, _ = self._get_port_details(port_name)
        if communicates == 'event':
            for st in pyNN_data.spiketrains:
                if st.annotations:
                    recording.spiketrains.append(st)
        else:
            for asig in pyNN_data.analogsignals:
                if asig.annotations:
                    recording.analogsignals.append(asig)
        return recording

    def _kill(self, t_stop):
        """
        Caches all recording data and sets all references to the actual
        simulator object to None ahead of a simulator reset. This allows
        data to be accessed after a simulation has completed, and potentially
        a new simulation to have been started.
        """
        self._t_stop = t_stop

    @property
    def is_dead(self):
        return self._t_stop is None


class Selection(object):
    """
    A selection of cells from one or multiple component arrays. Used to
    connect ConnectionGroup.

    Parameters
    ----------
    nineml_model : nineml.Selection
        The NineML Selection object
    component_arrays : list(nineml.ComponentArray)
        List of component arrays included in the selection.
    """

    def __init__(self, nineml_model, *component_arrays):
        self._nineml = nineml_model
        self._component_arrays = dict(
            (ca.name, ca) for ca in component_arrays)
        self.PyNNAssemblyClass.__init__(
            self, *component_arrays, label=nineml_model.name)

    @property
    def name(self):
        return self.nineml.name

    @property
    def nineml(self):
        return self._nineml

    @property
    def component_arrays(self):
        return self._component_arrays.itervalues()

    def component_array(self, name):
        return self._component_arrays[name]

    @property
    def num_component_arrays(self):
        return len(self._component_arrays)

    @property
    def component_array_names(self):
        return self._component_arrays.iterkeys()

    def synapse(self, name):
        try:
            synapses = set(ca.nineml.dynamics_properties.synapse(name)
                           for ca in self.component_arrays)
        except NineMLNameError:
            raise NineMLNameError(
                "Could not return synapse '{}' because it is missing from "
                "one or more of the component arrays in '{}' Selection"
                .format(name, self.name))
        if len(synapses) > 1:
            raise Pype9RuntimeError(
                "'{}' varies ({}) between component arrays in '{}' Selection"
                .format(name, ', '.join(str(s) for s in synapses), self.name))
        return next(iter(synapses))  # Return the only synapse

    def __repr__(self):
        return "Selection('{}', component_arrays=('{}')".format(
            self.name, "', '".join(self.component_array_names))


class ConnectionGroup(object):
    """
    ConnectionGroup object corresponds to a NineML type to be introduced in
    NineMLv2 (see https://github.com/INCF/nineml/issues/46), which consists of
    a dynamics class and a size. Only consists of references to ports on the
    source and destination ComponentArrays|Selections and connectivity.

    Parameters
    ----------
    nineml_model : nineml.ConnectionGroup
        Component array nineml
    source : ComponentArray
        Source component array
    destination : ComponentArray
        Destination component array
    """

    def __init__(self, nineml_model, source, destination):
        rng = self.Simulation.active().properties_rng
        if not isinstance(nineml_model, EventConnectionGroup9ML):
            raise Pype9RuntimeError(
                "Expected a connection group model, found {}"
                .format(nineml_model))
        try:
            (synapse, conns) = destination.synapse(nineml_model.name)
            if conns is not None:
                raise NotImplementedError(
                    "Nonlinear synapses, as used in '{}' are not currently "
                    "supported".format(nineml_model.name))
            if synapse.num_local_properties == 1:
                # Get the only local property that varies with the synapse
                # (typically the synaptic weight but does not have to be)
                weight = get_pyNN_value(next(synapse.local_properties),
                                        self.UnitHandler, rng)
            elif not synapse.num_local_properties:
                weight = 0.0
            else:
                raise NotImplementedError(
                    "Currently only supports one property that varies with "
                    "each synapse")
        except NineMLNameError:
            # FIXME: Should refactor "WithSynapses" code to "CellAndSynapses"
            #        class which inherits most of its functionality from
            #        MultiDynamics to ensure that every connection has a
            #        "synapse" even if it is just a simple port exposure
            # Synapse dynamics properties didn't have any properties that vary
            # between synapses so wasn't included
            weight = 0.0
        self._nineml = nineml_model
        delay = get_pyNN_value(nineml_model.delay, self.UnitHandler, rng)
        # FIXME: Ignores send_port, assumes there is only one...
        # NB: Simulator-specific derived classes extend the corresponding
        # PyNN population class
        self.PyNNProjectionClass.__init__(
            self,
            presynaptic_population=source,
            postsynaptic_population=destination,
            connector=nineml_model.connectivity,
            synapse_type=self.SynapseClass(weight=weight, delay=delay),
            receptor_type=nineml_model.destination_port,
            label=nineml_model.name)

    @property
    def name(self):
        return self._nineml.name

    @property
    def connectivity(self):
        return self._connector

    def __repr__(self):
        return ("ConnectionGroup('{}', source='{}', destination='{}', "
                "connectivity='{}')".format(self.name, self.pre.name,
                                            self.post.name,
                                            self.connectivity))
