"""

  This package mirrors the one in pyNN

  @file __init__.py
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import os
from collections import namedtuple
import numpy
from ninemlp import SRC_PATH, DEFAULT_BUILD_MODE, pyNN_build_mode
from ninemlp.neuron.build import compile_nmodl
compile_nmodl(os.path.join(SRC_PATH, 'pyNN', 'neuron', 'nmodl'), build_mode=pyNN_build_mode,
              silent=True)
import ninemlp.common
from ninemlp.common import seg_varname
from ninemlp.neuron.ncml import NCMLCell
import pyNN.common
import pyNN.neuron.standardmodels.cells
import pyNN.neuron.connectors
import pyNN.neuron.recording
import ncml
from pyNN.neuron import setup, run, reset, end, get_time_step, get_current_time, get_min_delay, \
                        get_max_delay, rank, num_processes, record, record_v, record_gsyn, \
                        StepCurrentSource, ACSource, DCSource, NoisyCurrentSource, errors, core
import pyNN.neuron as sim
from pyNN.common.control import build_state_queries
import pyNN.neuron.simulator as simulator
import neuron
from neuron import h

get_current_time, get_time_step, get_min_delay, \
        get_max_delay, num_processes, rank = build_state_queries(simulator)

class Population(ninemlp.common.Population, pyNN.neuron.Population):

    def __init__(self, label, size, cell_type, params={}, build_mode=DEFAULT_BUILD_MODE):
        """
        Initialises the population after reading the population parameters from file
        @param label: the label assigned to the population (its NINEML id)
        @param size: the size of the population
        @param cell_type: The cell model used to instantiate the population.
        @param params: the parameters passed to the cell model (Note that at this stage the same \
                        parameters are passed to every cell in the model)
        @param build_mode: Specifies whether cell models, or in NEURON's case, cell mechanisms need\
                            to be built. This is actually performed when the cell_type is loaded \
                           but if build_mode is set to 'build_only' then the population isn't \
                           actually constructed and only the NMODL files are compiled.
        """
        if build_mode == 'build_only' or build_mode == 'compile_only':
            print "Warning! '--compile' option was set to 'build_only' or 'compile_only', " \
                  "meaning the Population '{}' was not constructed and only the NMODL files " \
                  "were compiled.".format(label)
        else:
            # If cell_type is of NCML type append the population as a parent parameter for its 
            # constructor
            if issubclass(cell_type, NCMLCell):
                params = params.copy()
                params['parent'] = self
            pyNN.neuron.Population.__init__(self, size, cell_type, params, structure=None,
                                            label=label)


    #FIXME: I think this should be deleted
    def set_param(self, cell_id, param, value, component=None, section=None):
        raise NotImplementedError('set_param has not been implemented for Population class yet')


    def can_record(self, variable):
        """
        Overloads that from pyNN.common.BasePopulation to allow section names and positions to 
        be passed.
        """
        if hasattr(self.celltype, 'ncml_model'): # If cell is generated from NCML file
            match = pyNN.neuron.recording.recordable_pattern.match(variable)
            if match:
                parts = match.groupdict()
                if parts['var'] not in self.celltype.recordable:
                    return False
                if parts['section']: # Check to see if section exists
                    if not hasattr(self.celltype, parts['section']):
                        return False
                if parts.has_key('position'): # Check to see if the position is between 0-1
                    pos = float(parts['position'])
                    if pos < 0.0 or pos > 1.0:
                        raise Exception("Position parameter in recording string, {}, is out of "
                                        "range (0.0-1.0)".format(pos))
                return True
            else:
                raise Exception("Could not parse variable name '%s'" % variable)
        else:
            return pyNN.neuron.Population.can_record(self, variable)


class Projection(pyNN.neuron.Projection):

    def __init__(self, pre, dest, label, connector, source=None, target=None,
                 build_mode=DEFAULT_BUILD_MODE):
        self.label = label
        if build_mode == 'build_only' or build_mode == 'compile_only':
            print "Warning! '--compile' option was set to 'build_only', meaning the projection " \
                  "'{}' was not constructed.".format(label)
        else:
            pyNN.neuron.Projection.__init__(self, pre, dest, connector, label=label, source=source,
                                                                                      target=target)


class ElectricalSynapseProjection(Projection):

    ## A named tuple to hold a record of the generated electrical synapse connections
    Connection = namedtuple('Connection', 'cell1 segment1 cell2 segment2')

    ## This holds the last reserved GID used to connect the source and target variables. It is incremented each time a Projection is initialised by the amount needed to hold an all-to-all connection
    gid_count = 0

    def __init__(self, pre, dest, label, connector, source=None, target=None,
                 build_mode=DEFAULT_BUILD_MODE):
        """
        @param rectified [bool]: Whether the gap junction is rectified (only one direction)
        """
        ## Start of unique variable-GID range assigned for this projection (ends at gid_count + pre.size * dest.size * 2)
        self.gid_start = self.__class__.gid_count
        self.__class__.gid_count += pre.size * dest.size * 2
        Projection.__init__(self, pre, dest, label, connector, source, target, build_mode)


    def _divergent_connect(self, source, targets, weights, delays=None): #@UnusedVariable
        """
        Connect a neuron to one or more other neurons with a static connection.
        
        @param source [pyNN.common.IDmixin]: the ID of the pre-synaptic cell.
        @param [list(pyNN.common.IDmixin)]: a list/1D array of post-synaptic cell IDs, or a single ID.
        @param [list(float) or float]: Connection weight(s). Must have the same length as `targets`.
        @param delays [Null]: This is actually ignored but only included to match the same signature\
 as the Population._divergent_connect method
        """
        if not isinstance(source, int) or source > simulator.state.gid_counter or source < 0:
            errmsg = "Invalid source ID: {} (gid_counter={})".format(source,
                                                                     simulator.state.gid_counter)
            raise errors.ConnectionError(errmsg)
        if not core.is_listlike(targets):
            targets = [targets]
        if isinstance(weights, float):
            weights = [weights]
        assert len(targets) > 0
        for target in targets:
            if not isinstance(target, pyNN.common.IDMixin):
                raise errors.ConnectionError("Invalid target ID: {}".format(target))
        assert len(targets) == len(weights), "{} {}".format(len(targets), len(weights))
        self._resolve_synapse_type()
        # NB: In this case self.synapse_type and self.source will actually be the names of the 
        # respective segments. The names are inherited from the pyNN class, and thus a little
        # confusing so I rename them here in the local scope to try to make it a little clearer.
        source_segname = self.source
        target_segname = self.synapse_type
        for target, weight in zip(targets, weights):
            # Check connection information to avoid duplicates if the connection is not "rectified"
            # (one-way), where there is a gap junction connecting from one cell1 to cell2 and then 
            # another cell2 to cell1 (because the connections are mutual)
            if self.Connection(target, target_segname, 
                               source, source_segname) not in self.connections:
                # Generate unique but reproducible
                pre_post_id = (self.pre.id_to_index(source) * len(self.post) + \
                               self.post.id_to_index(target) + self.gid_start) * 2
                post_pre_id = pre_post_id + 1
                # Create a connection list containing the two connections going in both directions
                conn_list = (((source, source_segname), (target, target_segname), pre_post_id),
                             ((target, target_segname), (source, source_segname), post_pre_id))
                for (pre_cell, pre_seg), (post_cell, post_seg), var_gid in conn_list:
                    if pre_cell.local:
                        if pre_seg:
                            segment = pre_cell._cell.segments[pre_seg.split('.')[0]]
                        else:
                            segment = pre_cell.source_section
                        # Connect the pre cell voltage to the target var
                        simulator.state.parallel_context.source_var(segment(0.5)._ref_v, var_gid) #@UndefinedVariableFromImport              
                    if post_cell.local:
                        if post_seg:
                            segment = post_cell._cell.segments[self.synapse_type]
                        else:
                            segment = post_cell.source_section
                        # Create the gap_junction and set its weight
                        gap_junction = h.Gap(0.5, sec=segment)
                        gap_junction.g = weight
                        # Store gap junction in a list so it doesn't get collected by the garbage 
                        # collector
                        segment._gap_junctions.append(gap_junction)
                        # Connect the gap junction with the source_var
                        simulator.state.parallel_context.target_var(gap_junction._ref_vgap, var_gid) #@UndefinedVariableFromImport
                # Save connection information to avoid duplicates, where the same cell connects
                # from one cell1 to cell2 and then cell2 to cell1 (because all connections are mutual)
                self.connections.append(self.Connection(source, self.source, target,
                                                        self.synapse_type))

    def _convergent_connect(self, sources, target, weights, delays):
        raise NotImplementedError


class Network(ninemlp.common.Network):

    def __init__(self, filename, build_mode=DEFAULT_BUILD_MODE, timestep=None, min_delay=None,
                                 max_delay=None, temperature=None, silent_build=False, flags=[]):
        self._pyNN_module = pyNN.neuron
        self._ncml_module = ncml
        self._Population_class = Population
        self._Projection_class = Projection
        self._ElectricalSynapseProjection_class = ElectricalSynapseProjection
        self.get_min_delay = get_min_delay # Sets the 'get_min_delay' function for use in the network init
        #Call the base function initialisation function.
        ninemlp.common.Network.__init__(self, filename, build_mode=build_mode, timestep=timestep,
                                        min_delay=min_delay, max_delay=max_delay,
                                    temperature=temperature, silent_build=silent_build, flags=flags)

    def _convert_units(self, value_str, units=None):
        if ' ' in value_str:
            if units:
                raise Exception("Units defined in both argument ('{}') and value string ('{}')"
                                .format(units, value_str))
            (value, units) = value_str.split()
        else:
            value = value_str
            units = None
        try:
            value = float(value)
        except:
            raise Exception("Incorrectly formatted value string '{}', should be a number optionally"
                            " followed by a space and units (eg. '1.5 Hz')".format(value_str))
        if not units:
            return value
        elif units == "Hz":
            return value
        elif units == "um":
            return value
        elif units == "ms":
            return value
        elif units == "us":
            return value * 1e-3
        elif units == "us/um":
            return value * 1e-3
        elif units == 'uS':
            return value
        elif units == 'mS':
            return value * 1e+3
        elif units == 'nS':
            return value * 1e-3
        elif units == 'pS':
            return value * 1e-6
        elif units == 'MOhm':
            return value
        elif units == 'Ohm/cm':
            return value
        elif units == 'S/cm2':
            return value
        else:
            raise Exception("Unrecognised units '%s'" % units)


    def _set_simulation_params(self, **params):
        """
        Sets the simulation parameters either from the passed parameters or from the networkML
        description
        
        @param params[**kwargs]: Parameters that are either passed to the pyNN setup method or set \
                                 explicitly
        """
        p = self._get_simulation_params(**params)
        setup(p['timestep'], p['min_delay'], p['max_delay'])
        neuron.h.celsius = p['temperature']


    def _get_target_str(self, synapse, segment=None):
        if not segment:
            segment = "source_section"
        return seg_varname(segment) + "." + synapse

    def _finalise_construction(self):
        includes_electrical = False
        for proj in self.all_projections():
            if isinstance(proj, ElectricalSynapseProjection):
                includes_electrical = True
        if includes_electrical:
            simulator.state.parallel_context.setup_transfer() #@UndefinedVariableFromImport

if __name__ == "__main__":

    net = Network('/home/tclose/Projects/Cerebellar/xml/cerebellum/test.xml')

    print 'done'

