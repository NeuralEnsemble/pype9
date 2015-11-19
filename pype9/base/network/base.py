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
    MultiDynamics, append_namespace, AnalogReceivePortExposure,
    EventReceivePortExposure, AnalogSendPortExposure, EventSendPortExposure)
from nineml.user.port_connections import EventPortConnection
from nineml.user.network import EventConnectionGroup, AnalogConnectionGroup


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

    def _comp_array_from_pop(self, nineml_population):
        """
        Returns a multi-dynamics object containing the cell and all
        post-synaptic response/plasticity dynamics
        """
        # Get all the projections that project to/from the given population
        receiving = [p for p in self._nineml.projections
                     if p.post == nineml_population]
        sending = [p for p in self._nineml.projections
                   if p.pre == nineml_population]
        # Get all sub-dynamics, port connections and port exposures
        sub_dynamics = {'cell': nineml_population.cell.component_class}
        # =====================================================================
        # Get all the port connections between Response, Plasticity and Post
        # nodes and convert them to MultiDynamics port connections (i.e.
        # referring to sub-component names instead of projection roles)
        # =====================================================================
        port_connections = []
        for proj in receiving:
            sub_dynamics[proj.name + '_psr'] = proj.response.component_class
            sub_dynamics[proj.name + '_pls'] = proj.plasticity.component_class
            # Get all projection port connections that don't project to/from
            # the "pre" population and convert them into local MultiDynamics
            # port connections
            port_connections.extend(
                pc.__class__(
                    sender_name=self._role2dyn(proj.name, pc.sender_role),
                    receiver_name=self._role2dyn(proj.name, pc.receiver_role),
                    send_port=pc.send_port, receive_port=pc.receive_port)
                for pc in proj.port_connections
                if 'pre' not in (pc.sender_role, pc.receiver_role))
        # =====================================================================
        # Get all the ports that are connected to/from the Pre node and insert
        # a port exposure to handle them
        # =====================================================================
        port_exposures = []
        for proj in sending:
            port_exposures.extend(
                AnalogSendPortExposure(component='cell', port=pc.send_port)
                for pc in proj.analog_port_connections
                if 'pre' == pc.sender_role)
            port_exposures.extend(
                EventSendPortExposure(component='cell', port=pc.send_port)
                for pc in proj.event_port_connections
                if 'pre' == pc.sender_role)
            port_exposures.extend(
                AnalogReceivePortExposure(component='cell',
                                          port=pc.receive_port)
                for pc in proj.analog_port_connections
                if 'pre' == pc.receiver_role)
            port_exposures.extend(
                EventReceivePortExposure(component='cell',
                                         port=pc.receive_port)
                for pc in proj.event_port_connections
                if 'pre' == pc.receiver_role)
        for proj in receiving:
            port_exposures.extend(
                AnalogReceivePortExposure(
                    component=self._role2dyn(proj.name, pc.receiver_role),
                    port=pc.receive_port)
                for pc in proj.analog_port_connections
                if 'pre' == pc.sender_role)
            port_exposures.extend(
                EventReceivePortExposure(
                    component=self._role2dyn(proj.name, pc.receiver_role),
                    port=pc.receive_port)
                for pc in proj.event_port_connections
                if 'pre' == pc.sender_role)
            port_exposures.extend(
                AnalogSendPortExposure(
                    component=self._role2dyn(proj.name, pc.sender_role),
                    port=pc.send_port)
                for pc in proj.analog_port_connections
                if 'pre' == pc.receiver_role)
            port_exposures.extend(
                EventSendPortExposure(
                    component=self._role2dyn(proj.name, pc.sender_role),
                    port=pc.send_port)
                for pc in proj.event_port_connections
                if 'pre' == pc.receiver_role)
        comp = MultiDynamics(
            name=nineml_population.name + 'Dynamics',
            sub_components=sub_dynamics, port_connections=port_connections,
            port_exposures=port_exposures)
        return ComponentArray(nineml_population.name, nineml_population.size,
                              comp)

    def _conn_groups_from_proj(self, nineml_projection):
        return (
            _conn_group_cls_from_port_connection(pc)(
                '{}__{}_{}__{}_{}___connection_group'.format(
                    nineml_projection.name, pc.sender_role, pc.send_port_name,
                    pc.receiver_role, pc.receive_port_name),
                nineml_projection.pre.name, nineml_projection.post.name,
                source_port=append_namespace(
                    pc.send_port_name,
                    self._role2dyn(nineml_projection.name, pc.sender_role)),
                destination_port=append_namespace(
                    pc.receive_port_name,
                    self._role2dyn(nineml_projection.name, pc.receiver_role)),
                connectivity=nineml_projection.connectivity,
                delay=nineml_projection.delay)
            for pc in nineml_projection.port_connections
            if 'pre' in (pc.sender_role, pc.receiver_role))


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
            nineml_model.connectivity,
            synapse_type=self.SynapseClass(weight=weight, delay=delay),
            source=nineml_model.source.segment,
            receptor_type=nineml_model.receive_port,
            label=nineml_model.name)


def _conn_group_cls_from_port_connection(port_connection):
    if isinstance(port_connection, EventPortConnection):
        conn_grp_cls = EventConnectionGroup
    else:
        conn_grp_cls = AnalogConnectionGroup
    return conn_grp_cls
