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
# This is required to ensure that the right MPI variables are set before NEURON is initiated
from __future__ import absolute_import 
try:
    from mpi4py import MPI # @UnresolvedImport @UnusedImport
except:
    pass
import nineline.pyNN.common
from pyNN.neuron import setup, run, reset, end, get_time_step, get_current_time, get_min_delay, \
                        get_max_delay, rank, num_processes, record, record_v, record_gsyn, \
                        StepCurrentSource, DCSource, NoisyCurrentSource #@UnusedVariable
from pyNN.common.control import build_state_queries
import pyNN.neuron.standardmodels
import pyNN.neuron.simulator as simulator
import neuron
from nineline.pyNN.nest.cells import NinePyNNCellMetaClass
from nineline.cells.neuron import NineCell
import logging

logger = logging.getLogger("PyNN")

get_current_time, get_time_step, get_min_delay, \
        get_max_delay, num_processes, rank = build_state_queries(simulator)


class Population(pyNN.neuron.Population, nineline.pyNN.common.Population):

    _pyNN_standard_celltypes = dict([(cellname, getattr(pyNN.neuron.standardmodels.cells, cellname))
                                     for cellname in pyNN.neuron.list_standard_models()])
    _NineCellMetaClass = NinePyNNCellMetaClass

#    #FIXME: I think this should be deleted
#    def set_param(self, cell_id, param, value, component=None, section=None):
#        raise NotImplementedError('set_param has not been implemented for Population class yet')

    def rset(self, param, rand_distr, component=None, seg_group=None):
        param_scope = [NineCell.group_varname(seg_group)]
        if component:
            param_scope.append(component)
        param_scope.append(param)
        pyNN.neuron.Population.rset(self, '.'.join(param_scope), rand_distr)

    def initialize_variable(self, variable, rand_distr, component=None, seg_group=None):
        variable_scope = [NineCell.group_varname(seg_group)]
        if component:
            variable_scope.append(component)
        variable_scope.append(variable)
        pyNN.neuron.Population.initialize(self, **{'.'.join(variable_scope): rand_distr})

#    def can_record(self, variable):
#        """
#        Overloads that from pyNN.common.BasePopulation to allow section names and positions to 
#        be passed.
#        """
#        if hasattr(self.celltype, 'memb_model'): # If cell is generated from NCML file
#            match = pyNN.neuron.recording.recordable_pattern.match(variable)
#            if match:
#                parts = match.groupdict()
#                if parts['var'] not in self.celltype.recordable:
#                    return False
#                if parts['section']: # Check to see if section exists
#                    if not hasattr(self.celltype, parts['section']):
#                        return False
#                if parts.has_key('position'): # Check to see if the position is between 0-1
#                    pos = float(parts['position'])
#                    if pos < 0.0 or pos > 1.0:
#                        raise Exception("Position parameter in recording string, {}, is out of "
#                                        "range (0.0-1.0)".format(pos))
#                return True
#            else:
#                raise Exception("Could not parse variable name '%s'" % variable)
#        else:
#            return pyNN.neuron.Population.can_record(self, variable)


class Projection(pyNN.neuron.Projection, nineline.pyNN.common.Projection):

    _synapses_module = nineline.pyNN.neuron.synapses

    @classmethod
    def get_min_delay(self):
        return get_min_delay()

    @classmethod
    def _convert_units(cls, value_str, units=None):
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

class Network(nineline.pyNN.common.Network):

    _Population = Population
    _Projection = Projection

    def __init__(self, filename, build_mode='lazy', timestep=None, min_delay=None,
                                 max_delay=None, temperature=None, silent_build=False, flags=[],
                                 solver_name=None, rng=None):
        self.get_min_delay = get_min_delay # Sets the 'get_min_delay' function for use in the network init
        #Call the base function initialisation function.
        nineline.pyNN.common.Network.__init__(self, filename, build_mode=build_mode, timestep=timestep,
                                          min_delay=min_delay, max_delay=max_delay,
                                          temperature=temperature, silent_build=silent_build, 
                                          flags=flags, solver_name=solver_name, rng=rng)




    def _set_simulation_params(self, **params):
        """
        Sets the simulation parameters either from the passed parameters or from the nineml
        description
        
        @param params[**kwargs]: Parameters that are either passed to the pyNN setup method or set \
                                 explicitly
        """
        p = self._get_simulation_params(**params)
        setup(p['timestep'], p['min_delay'], p['max_delay'])
        neuron.h.celsius = p['temperature']

if __name__ == "__main__":

    net = Network('/home/tclose/Projects/Cerebellar/xml/cerebellum/test.xml')

    print 'done'

