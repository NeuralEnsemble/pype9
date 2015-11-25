"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from itertools import chain
from nineml.user import ComponentArray, Initial
from pype9.exceptions import Pype9RuntimeError
from .values import get_pyNN_value
import os.path
import nineml
from pyNN.random import NumpyRNG
import pyNN.standardmodels
import quantities as pq
from nineml.user.multi import (
    MultiDynamics, MultiDynamicsProperties, append_namespace, BasePortExposure,
    SubDynamics, SubDynamicsProperties)
from nineml.user import DynamicsProperties
from nineml.user.port_connections import EventPortConnection
from nineml.user.network import EventConnectionGroup, AnalogConnectionGroup
from nineml.values import SingleValue


_REQUIRED_SIM_PARAMS = ['timestep', 'min_delay', 'max_delay', 'temperature']


class Network(object):

    def __init__(self, nineml_model, build_mode='lazy',
                 timestep=None, min_delay=None, max_delay=None,
                 temperature=None, rng=None, **kwargs):
        self._nineml = nineml_model
        if isinstance(nineml_model, basestring):
            nineml_model = nineml.read(nineml_model).as_network()
        self._set_simulation_params(timestep=timestep, min_delay=min_delay,
                                    max_delay=max_delay,
                                    temperature=temperature)
        self._rng = rng if rng else NumpyRNG()
        self._component_arrays = {}
        for name, comp_array in self.nineml_model.component_arrays.iteritems():
            self._component_arrays[name] = self.ComponentArrayClass(
                comp_array, rng=self._rng, build_mode=build_mode, **kwargs)
        if build_mode not in ('build_only', 'compile_only'):
            # Set the connectivity objects of the projections to the
            # PyNNConnectivity class
            if nineml_model.connectivity_has_been_sampled():
                raise Pype9RuntimeError(
                    "Connections have already been sampled, please reset them"
                    " using 'resample_connectivity' before constructing "
                    "network")
            nineml_model.resample_connectivity(
                connectivity_class=self.ConnectivityClass)
            self._connection_groups = {}
            for conn_group in nineml_model.connection_groups:
                self._connection_groups[
                    conn_group.name] = self.ConnectionGroupClass(
                        conn_group, rng=self._rng)
            self._finalise_construction()

    def _finalise_construction(self):
        """
        Can be overriden by deriving classes to do any simulator-specific
        finalisation that is required
        """
        pass

    @property
    def component_arrays(self):
        return self._component_arrays

    @property
    def connection_groups(self):
        return self._connection_groups

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
        if (not os.path.isdir(file_prefix) and not file_prefix.endswith('.')
                and not file_prefix.endswith(os.path.sep)):
            file_prefix += '.'
        for comp_array in self.component_arrays.itervalues():
            # @UndefinedVariable
            comp_array.write_data(file_prefix + comp_array.name + '.pkl',
                                  **kwargs)

    def _get_simulation_params(self, **params):
        sim_params = dict([(p.name, pq.Quantity(p.value, p.unit))
                           for p in self.nineml_model.parameters.values()])
        for key in _REQUIRED_SIM_PARAMS:
            if key in params and params[key]:
                sim_params[key] = params[key]
            elif key not in sim_params or not sim_params[key]:
                raise Exception("'{}' parameter was not specified either in "
                                "Network initialisation or NetworkML "
                                "specification".format(key))
        return sim_params

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
                send_port=pc.send_port, receive_port=pc.receive_port)
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
            sub_dynamics_properties=syn_comps,
            port_connections=syn_internal_conns,
            port_exposures=syn_exps)
        port_connections = chain(
            (pc.__class__(sender_role=pc.sender_role,
                          receiver_role='synapse',
                          send_port=pc.send_port,
                          receive_port=append_namespace(
                              pc.receive_port_name,
                              role2name[pc.receiver_role]))
             for pc in receive_conns),
            (pc.__class__(sender_role='synapse',
                          receiver_role=pc.receiver_role,
                          send_port=append_namespace(
                              pc.send_port_name,
                              role2name[pc.sender_role]),
                          receive_port=pc.receive_port)
             for pc in send_conns),
            (pc for pc in projection_model.port_connections
             if (pc.sender_role in ('pre', 'post') and
                 pc.receiver_role in ('pre', 'post'))))
        return synapse, port_connections

    @classmethod
    def nineml_comp_arrays_and_conn_groups(cls, network_model):
        """
        Convert populations and projections into component arrays and
        connection groups
        """
        component_arrays = {}
        connection_groups = {}
        for pop in network_model.populations:
            # Get all the projections that project to/from the given population
            receiving = [p for p in network_model.projections if p.post == pop]
            sending = [p for p in network_model.projections if p.pre == pop]
            # Create a dictionary to hold the cell dynamics and any synapse
            # dynamics that can be flattened into the cell dynamics
            # (i.e. linear ones).
            sub_components = {'cell': pop.cell}
            # All port connections between post-synaptic cell and linear
            # synapses and port exposures to pre-synaptic cell
            internal_conns = []
            exposures = []
            nonlinear_synapses = {}  # holds connections from synapse to post.
            for proj in receiving:
                role2name = {'synapse': proj.name,
                             'post': 'cell'}
                # Flatten response and plasticity into single dynamics class.
                # TODO: this should be no longer necessary when we move to
                # version 2 as response and plasticity elements will be
                # replaced by a synapse element in the standard.
                synapse, proj_conns = cls._flatten_synapse(proj)
                # Get all connections between the synapse and the post-synaptic
                # cell
                synapse_post_conns = [
                    pc for pc in proj_conns
                    if (pc.receiver_role in ('post', 'synapse') and
                        pc.sender_role in ('post', 'synapse'))]
                # Get the properties, which are not single values, as they will
                # have to be varied with each synapse. If there is only one it
                # the weight of the synapse in NEURON and NEST can be used to
                # hold it otherwise it won't be possible to collapse the
                # synapses into a single dynamics object
                non_single_props = [
                    p for p in synapse.properties
                    if not isinstance(p, SingleValue)]
                # If there is only one non-SingleValue property and the synapse
                # is non-linear it can be combined into the dynamics of the
                # post-synaptic cell.
                if (synapse.component_class.is_linear() and
                        len(non_single_props) < 2):
                    sub_components[proj.name] = synapse
                    # Convert port connections between synpase and post-
                    # synaptic cell into internal port connections of a multi-
                    # dynamics object
                    internal_conns.extend(
                        pc.assign_roles(role2name)
                        for pc in synapse_post_conns)
                    # Expose ports that are needed for the pre-synaptic
                    # connections
                    exposures.extend(chain(
                        (BasePortExposure.from_port(
                            pc.receive_port, role2name[pc.receiver_role])
                         for pc in proj_conns if pc.sender_role == 'pre'),
                        (BasePortExposure.from_port(
                            pc.send_port, role2name[pc.sender_role])
                         for pc in proj_conns if pc.receiver_role == 'pre')))
                else:
                    nonlinear_synapses[proj.name] = (synapse,
                                                     synapse_post_conns)
                    # Add exposures for direct connections between pre and post
                    # synaptic cells
                    exposures.extend(chain(
                        (BasePortExposure.from_port(
                            pc.receive_port, 'cell')
                         for pc in proj_conns
                         if (pc.sender_role == 'pre' and
                             pc.receiver_role == 'post')),
                        (BasePortExposure.from_port(
                            pc.send_port, 'cell')
                         for pc in proj_conns
                         if (pc.receiver_role == 'pre' and
                             pc.sender_role == 'post'))))
                # Create a connection group for each port connection of the
                # projection to/from the pre-synaptic cell
                for port_conn in proj_conns:
                    if 'pre' in (port_conn.sender_role,
                                 port_conn.receiver_role):
                        if isinstance(port_conn, EventPortConnection):
                            conn_grp_cls = EventConnectionGroup
                        else:
                            conn_grp_cls = AnalogConnectionGroup
                        if port_conn.sender_role == 'pre':
                            source_port = port_conn.send_port
                            destination_port = append_namespace(
                                port_conn.receive_port, 'cell')
                        else:
                            source_port = append_namespace(
                                port_conn.send_port, 'cell')
                            destination_port = port_conn.receive_port
                        name = ('{}__{}'
                                .format(
                                    proj.name,
                                    port_conn.sender_role,
                                    port_conn.send_port_name,
                                    port_conn.receiver_role,
                                    port_conn.receive_port_name))
                        connection_groups[proj.name] = conn_grp_cls(
                            name,
                            proj.pre.name, proj.post.name,
                            source_port=source_port,
                            destination_port=destination_port,
                            connectivity=proj.connectivity,
                            delay=proj.delay)
            # Add exposures for connections to/from the pre-synaptic cell in
            # populations.
            for proj in sending:
                # Not required after transition to version 2 syntax
                synapse, proj_conns = cls._flatten_synapse(proj)
                exposures.extend(chain(
                    (BasePortExposure.from_port(
                        pc.send_port, 'cell')
                     for pc in proj_conns if pc.sender_role == 'pre'),
                    (BasePortExposure.from_port(
                        pc.receive_port, 'cell')
                     for pc in proj_conns if pc.receiver_role == 'pre')))
            component = MultiDynamicsWithSeparateSynapsesProperties(
                name=pop.name, sub_components=sub_components,
                port_connections=internal_conns, port_exposures=exposures,
                synapses=nonlinear_synapses)
            component_arrays[pop.name] = ComponentArray(pop.name, pop.size,
                                                        component)
        return component_arrays, connection_groups


#             raise NotImplementedError(
#                 "Cannot convert population '{}' to component array as "
#                 "it has a non-linear synapse or multiple non-single "
#                 "properties")

#                 if any(1 for pc in proj_conns
#                        if pc.receiver_role == 'pre'):
#                     raise NotImplementedError(
#                         "Cannot handle reverse connections from synapse/"
#                         "post-synaptic cell to pre-synaptic at this stage")


class MultiDynamicsWithSeparateSynapses(MultiDynamics):

    def __init__(self, name, sub_components, port_connections,
                 port_exposures, synapses):
        super(MultiDynamicsWithSeparateSynapses, self).__init__(
            name=name, sub_components=sub_components,
            port_connections=port_connections, port_exposures=port_exposures)
        self._synapses = synapses

    def synapse(self, name):
        return self._synapses[name]

    @property
    def synapses(self):
        return self._synapses.itervalues()

    @property
    def num_synapses(self):
        return len(self._synapses)

    @property
    def synapse_names(self):
        return self._synapses.iterkeys()


class MultiDynamicsWithSeparateSynapsesProperties(MultiDynamicsProperties):

    def __init__(self, name, sub_dynamics_properties, port_connections,
                 port_exposures, synapses, synapse_connections):
        sub_dynamics = [
            SubDynamics(n, sc.component_class)
            for n, sc in sub_dynamics_properties.iteritems()]
        sub_dynamics_properties = [
            SubDynamicsProperties(n, p)
            for n, p in sub_dynamics_properties.iteritems()]
        component_class = MultiDynamicsWithSeparateSynapses(
            name + '_Dynamics', sub_dynamics,
            port_exposures=port_exposures, port_connections=port_connections,
            synapses=(s.component_class for s in synapses),
            synapse_connections=synapse_connections)
        DynamicsProperties.__init__(
            name, definition=component_class,
            properties=chain(*[p.properties for p in sub_dynamics_properties]))
        self._sub_component_properties = dict(
            (p.name, p) for p in sub_dynamics_properties)
        self._synapses = synapses

    def synapse(self, name):
        return self._synapses[name]

    @property
    def synapses(self):
        return self._synapses.itervalues()

    @property
    def num_synapses(self):
        return len(self._synapses)

    @property
    def synapse_names(self):
        return self._synapses.iterkeys()


class ComponentArray(object):

    def __init__(self, nineml_model, rng, build_mode='lazy', **kwargs):
        if not isinstance(nineml_model, ComponentArray):
            raise Pype9RuntimeError(
                "Expected a component array, found {}".format(nineml_model))
        dynamics = nineml_model.dynamics
        celltype = self.PyNNCellWrapperClass.__init__(
            dynamics, nineml_model.name, build_mode=build_mode, **kwargs)
        if build_mode not in ('build_only', 'compile_only'):
            cellparams = {}
            initial_values = {}
            for prop in chain(dynamics.properties, dynamics.initial_values):
                val = get_pyNN_value(prop, self.UnitHandler, rng)
                if isinstance(prop, Initial):
                    initial_values[prop.name] = val
                else:
                    cellparams[prop.name] = val
            self.PyNNPopulationClass.__init__(
                self, nineml_model.size, celltype, cellparams=cellparams,
                initial_values=initial_values, label=nineml_model.name)


class ConnectionGroup(object):

    def __init__(self, nineml_model, component_arrays, **kwargs):
        # FIXME: Should read the weight from somewhere, if 'connection_weight'
        #        is used in the code generation.
        weight = 1.0
        delay = get_pyNN_value(nineml_model.delay, self.unit_handler,
                               **kwargs)
        # FIXME: Ignores send_port, assumes there is only one...
        self.PyNNProjectionClass.__init__(
            self,
            source=component_arrays[nineml_model.source.name],
            target=component_arrays[nineml_model.destination.name],
            connectivity=nineml_model.connectivity,
            synapse_type=self.SynapseClass(weight=weight, delay=delay),
#             source=nineml_model.source.segment,
            receptor_type=nineml_model.receive_port,
            label=nineml_model.name)
