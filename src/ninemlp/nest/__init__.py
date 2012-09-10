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
import numpy
import pyNN.nest.standardmodels.cells
import pyNN.nest.connectors
import ninemlp.common.brep
import ncml
from ninemlp import _BUILD_MODE
from pyNN.nest import setup, run, reset, end, get_time_step, get_current_time, get_min_delay, get_max_delay, rank, num_processes
from pyNN.common.control import build_state_queries
import pyNN.nest.simulator

get_current_time, get_time_step, get_min_delay, get_max_delay, num_processes, rank = build_state_queries(pyNN.nest.simulator)

RELATIVE_BREP_BUILD_DIR = './build'

class Population(pyNN.nest.Population):

    def __init__(self, label, size, cell_type, params={}, build_mode=_BUILD_MODE):
        """
        Initialises the population after reading the population parameters from file
        """
        if build_mode == 'compile_only':
            print "Warning! '--compile' option was set to 'compile_only', meaning the population '%s' was not constructed and only the NMODL files were compiled."
        else:
            pyNN.nest.Population.__init__(self, size, cell_type,
                                                  params, structure=None, label=label)

    def set_param(self, cell_id, param, value, component=None, section=None):
        raise NotImplementedError('set_param has not been implemented for Population class yet')




class Projection(pyNN.nest.Projection):

    def __init__(self, pre, dest, label, connector, source=None, target=None, build_mode=_BUILD_MODE):
        self.label = label
        if build_mode == 'compile_only':
            print "Warning! '--compile' option was set to 'compile_only', meaning the projection '%s' was not constructed." % label
        else:
            pyNN.nest.Projection.__init__(self, pre, dest, connector, label=label, source=source,
                                                                                      target=target)


class Network(ninemlp.common.Network):

    def __init__(self, filename, cell_search_path, build_mode=_BUILD_MODE):
        self._pyNN_module = pyNN.nest
        self._ncml_module = ncml
        self._Population_class = Population
        self._Projection_class = Projection
        ninemlp.common.Network.__init__(self, filename, cell_search_path, build_mode=build_mode)

    def _get_target_str(self, synapse, segment=None):
        return synapse

    def _convert_units(self, value_str, units=None):
        if ' ' in value_str:
            if units:
                raise Exception("Units defined in both argument ('%s') and value string ('%s')" % (units, value_str))
            (value, units) = value_str.split()
        else:
            value = value_str
            units = None
        try:
            value = float(value)
        except:
            raise Exception("Incorrectly formatted value string '%s', should be a number optionally followed by a space and units (eg. '1.5 Hz')" % value_str)

        raise Exception("Unrecognised units '%s'" % units)


if __name__ == "__main__":
    pass

