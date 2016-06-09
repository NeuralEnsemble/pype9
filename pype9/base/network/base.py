"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from copy import deepcopy
from collections import namedtuple, defaultdict
from itertools import chain
from nineml.user import Property
from pype9.exceptions import Pype9RuntimeError
from .values import get_pyNN_value
import os.path
import nineml
from nineml import units as un
from pyNN.random import NumpyRNG
import pyNN.standardmodels
from nineml import Document
from nineml.exceptions import NineMLNameError
from nineml.user.multi import (
    MultiDynamicsProperties, append_namespace, BasePortExposure)
from nineml.user.network import (
    ComponentArray as ComponentArray9ML,
    EventConnectionGroup as EventConnectionGroup9ML,
    AnalogConnectionGroup as AnalogConnectionGroup9ML)
from pype9.exceptions import Pype9UnflattenableSynapseException
from .connectivity import InversePyNNConnectivity
from ..cells import (
    MultiDynamicsWithSynapsesProperties, ConnectionPropertySet,
    SynapseProperties)


_REQUIRED_SIM_PARAMS = ['timestep', 'min_delay', 'max_delay', 'temperature']


class Network(object):

    # Name given to the "cell" component of the cell dynamics + linear synapse
    # dynamics multi-dynamics
    cell_dyn_name = 'cell'

    def __init__(self, nineml_model, build_mode='lazy', timestep=None,
                 min_delay=None, max_delay=None, rng=None, **kwargs):
        if isinstance(nineml_model, basestring):
            nineml_model = nineml.read(nineml_model).as_network(
                name=os.path.splitext(os.path.basename(nineml_model))[0])
        elif isinstance(nineml_model, Document):
            if nineml_model.url is not None:
                name = os.path.splitext(os.path.basename(nineml_model.url))[0]
            else:
                name = "Anonymous"
            nineml_model = nineml_model.as_network(name=name)
        self._nineml = deepcopy(nineml_model)
        timestep = timestep if timestep is not None else self.time_step
        min_delay = min_delay if min_delay is not None else self.min_delay
        max_delay = max_delay if max_delay is not None else self.max_delay
        self._set_simulation_params(timestep=timestep, min_delay=min_delay,
                                    max_delay=max_delay, **kwargs)
        self._rng = rng if rng else NumpyRNG()
        if build_mode not in ('build_only', 'compile_only'):
            # Convert
            self.nineml.resample_connectivity(
                connectivity_class=self.ConnectivityClass)
        flat_comp_arrays, flat_conn_groups = self._flatten_to_arrays_and_conns(
            self._nineml)
        self._component_arrays = {}
        code_gen = self.CellCodeGenerator()
        # Get the modification time of the nineml_model
        network_mod_time = code_gen.get_mod_time(nineml_model.url)
        for name, comp_array in flat_comp_arrays.iteritems():
            # Get the latest modification time between the cell dynamics and
            # the network configuration (if the network changes the synapses
            # may change
            # FIXME: This isn't a very satisfying way to detect changes. Perhaps
            #        a better way is just to save the XML the code is generated
            #        from.
            mod_time = max(
                code_gen.get_mod_time(
                    nineml_model.population(name).component_class.url),
                network_mod_time)
            self._component_arrays[name] = self.ComponentArrayClass(
                comp_array, rng=self._rng, build_mode=build_mode,
                build_dir=code_gen.get_build_dir(
                    self.nineml.url, name, group=self.nineml.name),
                mod_time=mod_time, **kwargs)
        self._selections = {}
        for selection in self.nineml.selections:
            # TODO: Assumes that selections are only concatenations (which is
            #       true for 9MLv1.0 but not v2.0)
            self._selections[selection.name] = self.SelectionClass(
                selection, *[self.component_array(p.name)
                             for p in selection.populations])
        if build_mode not in ('build_only', 'compile_only'):
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
                    source = self._component_arrays[conn_group.source]
                except KeyError:
                    source = self._selections[conn_group.source]
                try:
                    destination = self._component_arrays[
                        conn_group.destination]
                except KeyError:
                    destination = self._selections[conn_group.destination]
                self._connection_groups[name] = self.ConnectionGroupClass(
                    conn_group, source=source, destination=destination,
                    rng=self._rng)
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
        return self._component_arrays.itervalues()

    @property
    def connection_groups(self):
        return self._connection_groups.itervalues()

    @property
    def selections(self):
        return self._selections.itervalues()

    def component_array(self, name):
        return self._component_arrays[name]

    def connection_group(self, name):
        return self._connection_groups[name]

    def selection(self, name):
        return self._selections[name]

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
        for comp_array in self.component_arrays.itervalues():
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
            sub_components = {cls.cell_dyn_name: pop.cell}
            # All port connections between post-synaptic cell and linear
            # synapses and port exposures to pre-synaptic cell
            internal_conns = []
            exposures = []
            synapses = []
            connection_property_sets = []
            # FIXME: There has to be a way of avoiding this name clash
            if any(p.name == cls.cell_dyn_name for p in receiving):
                raise Pype9RuntimeError(
                    "Cannot handle projections named '{}' (why would you "
                    "choose such a silly name?;)".format(cls.cell_dyn_name))
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
                role2name = {'post': cls.cell_dyn_name}
                # If the synapse is non-linear it can be combined into the
                # dynamics of the post-synaptic cell.
                try:
                    if not synapse.component_class.is_linear():
                        raise Pype9UnflattenableSynapseException()
                    role2name['synapse'] = proj.name
                    # Extract "connection weights" (any non-singular property
                    # value) from the synapse properties
#                     proj_props = defaultdict(set)
#                     for prop in synapse.properties:
#                         # SingleValue properties can be set as a constant but
#                         # any that vary between synapses will need to be
#                         # treated as a connection "weight"
#                         if not isinstance(prop.value, SingleValue):
#                             # FIXME: Need to check whether the property is
#                             #        used in this on event and not in the
#                             #        time derivatives or on conditions
#                             for on_event in (synapse.component_class.
#                                              all_on_events()):
#                                 proj_props[on_event.src_port_name].add(prop)
#                     # Add port weights for this projection to combined list
#                     for port, props in proj_props.iteritems():
#                         ns_props = [
#                             Property(append_namespace(p.name, proj.name),
#                                      p.quantity) for p in props]
#                         connection_property_sets.append(
#                             ConnectionPropertySet(
#                                 append_namespace(port, proj.name), ns_props))
                    connection_property_sets.extend(
                        cls._extract_connection_property_sets(synapse,
                                                              proj.name))
                    # Add the flattened synapse to the multi-dynamics sub
                    # components
                    sub_components[proj.name] = synapse
                    # Convert port connections between synpase and post-
                    # synaptic cell into internal port connections of a multi-
                    # dynamics object
                    internal_conns.extend(pc.assign_roles(name_map=role2name)
                                          for pc in post_conns)
                    # Expose ports that are needed for the pre-synaptic
                    # connections
#                     exposures.extend(chain(
#                         (BasePortExposure.from_port(
#                             pc.receive_port, role2name[pc.receiver_role])
#                          for pc in proj_conns if pc.sender_role == 'pre'),
#                         (BasePortExposure.from_port(
#                             pc.send_port, role2name[pc.sender_role])
#                          for pc in proj_conns if pc.receiver_role == 'pre')))
                except Pype9UnflattenableSynapseException:
                    # All synapses (of this type) connected to a single post-
                    # synaptic cell cannot be flattened into a single component
                    # of a multi- dynamics object so an individual synapses
                    # must be created for each connection.
                    synapses.append(SynapseProperties(proj.name, synapse,
                                                      post_conns))
                    # Add exposures to the post-synaptic cell for connections
                    # from the synapse
                    exposures.extend(
                        chain(*(pc.expose_ports({'post': cls.cell_dyn_name})
                                for pc in post_conns)))
                # Add exposures for connections to/from the pre synaptic cell
                exposures.extend(
                    chain(*(pc.expose_ports(role2name) for pc in pre_conns)))

#                         (BasePortExposure.from_port(
#                             pc.receive_port, 'cell')
#                          for pc in proj_conns
#                          if (pc.sender_role == 'pre' and
#                              pc.receiver_role == 'post')),
#                         (BasePortExposure.from_port(
#                             pc.send_port, 'cell')
#                          for pc in proj_conns
#                          if (pc.receiver_role == 'pre' and
#                              pc.sender_role == 'post'))))
                role2name['pre'] = cls.cell_dyn_name
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
                    ns_port_conn = port_conn.assign_roles(
                        port_namespaces=role2name)
                    conn_group = ConnectionGroupClass(
                        name,
                        proj.pre.name, proj.post.name,
                        source_port=ns_port_conn.send_port_name,
                        destination_port=ns_port_conn.receive_port_name,
                        connectivity=connectivity,
                        delay=delay)
                    connection_groups[conn_group.name] = conn_group
            # Add exposures for connections to/from the pre-synaptic cell in
            # populations.
            for proj in sending:
                # Not required after transition to version 2 syntax
                synapse, proj_conns = cls._flatten_synapse(proj)
                # Add send and receive exposures to list
                exposures.extend(chain(*(
                    pc.expose_ports({'pre': cls.cell_dyn_name})
                    for pc in proj_conns)))
            dynamics_properties = MultiDynamicsProperties(
                name=pop.name, sub_components=sub_components,
                port_connections=internal_conns, port_exposures=set(exposures))
            component = MultiDynamicsWithSynapsesProperties(
                dynamics_properties, synapses_properties=synapses,
                connection_property_sets=connection_property_sets)
            component_arrays[pop.name] = ComponentArray9ML(pop.name, pop.size,
                                                           component)
        return component_arrays, connection_groups

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

    def __init__(self, nineml_model, rng, build_mode='lazy', **kwargs):
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
            build_mode=build_mode, **kwargs)
        if build_mode not in ('build_only', 'compile_only'):
            cellparams = dict(
                (p.name, get_pyNN_value(p, self.UnitHandler, rng))
                for p in dynamics_properties.properties)
            initial_values = dict(
                (i.name, get_pyNN_value(i, self.UnitHandler, rng))
                for i in dynamics_properties.initial_values)
            # NB: Simulator-specific derived classes extend the corresponding
            # PyNN population class
            self.PyNNPopulationClass.__init__(
                self, nineml_model.size, celltype, cellparams=cellparams,
                initial_values=initial_values, label=nineml_model.name)

    @property
    def name(self):
        return self._nineml.name

    @property
    def nineml(self):
        return self._nineml

    def synapse(self, name):
        return self.nineml.dynamics_properties.synapse(name)

    def __repr__(self):
        return "ComponentArray('{}', size={})".format(self.name, self.size)


class Selection(object):

    def __init__(self, nineml_model, *component_arrays):
        self._nineml = nineml_model
        self._component_arrays = component_arrays
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
        return self._component_arrays

    def component_array(self, name):
        return self._component_array[name]

    @property
    def num_component_arrays(self):
        return len(self._component_arrays)

    @property
    def component_array_names(self):
        return self._component_arrays.keys()

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

    def __init__(self, nineml_model, source, destination, rng):
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
