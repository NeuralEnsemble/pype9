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
from ninemlp import SRC_PATH, BUILD_MODE
from ninemlp.utilities.nmodl import build as build_nmodl
build_nmodl(os.path.join(SRC_PATH, 'pyNN', 'neuron', 'nmodl'), build_mode=BUILD_MODE)
import pyNN.neuron.standardmodels.cells
import pyNN.neuron.connectors
import pyNN.neuron.recording
import ninemlp.common
import ninemlp.common.geometry
import ncml
from pyNN.neuron import setup, run, reset, end, get_time_step, get_current_time, get_min_delay, get_max_delay, rank, num_processes, record, record_v, record_gsyn
import pyNN.neuron as sim
from pyNN.common.control import build_state_queries
import pyNN.neuron.simulator
import neuron

get_current_time, get_time_step, get_min_delay, get_max_delay, num_processes, rank = build_state_queries(pyNN.neuron.simulator)

class Population(pyNN.neuron.Population):

    def __init__(self, label, size, cell_type, params={}, build_mode=BUILD_MODE):
        """
        Initialises the population after reading the population parameters from file
        @param label: the label assigned to the population (its NINEML id)
        @param size: the size of the population
        @param cell_type: The cell model used to instantiate the population.
        @param params: the parameters passed to the cell model (Note that at this stage the same \
                        parameters are passed to every cell in the model)
        @param build_mode: Specifies whether cell models, or in NEURON's case, cell mechanisms need to be \
                      built. This is actually performed when the cell_type is loaded but if build_mode is \
                      set to 'compile_only' then the population isn't actually constructed and only the NMODL \ 
                      files are compiled.
        """
        if build_mode == 'compile_only':
            print "Warning! '--compile' option was set to 'compile_only', meaning the Population '%s' was not constructed and only the NMODL files were compiled." % label
        else:
            pyNN.neuron.Population.__init__(self, size, cell_type, params, structure=None, label=label)


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
                if parts.has_key('position'): # Check to see if the position is between 0-1
                    pos = float(parts['position'])
                    if pos < 0.0 or pos > 1.0:
                        raise Exception("Position parameter in recording string, %f, is out of range (0.0-1.0)" % pos)
                if parts['section']: # Check to see if section exists
                    if parts['section'] not in [seg.id for seg in self.celltype.morphml_model.segments]:
                        return False
                return True
            else:
                raise Exception("Could not parse variable name '%s'" % variable)
        else:
            return pyNN.neuron.Population.can_record(self, variable)

    def record(self, variable, filename, section='soma', position=0.5):
        """
        Record spikes to a file. source can be an individual cell, a Population,
        PopulationView or Assembly.
        """
        if variable == 'spikes':
            variable_str = variable
        else:
            variable_str = '{section}({position}).{variable}'.format(section=section, 
                                                              position=position, variable=variable)
        self._record(variable_str, to_file=filename)
        # recorder_list is used by end()
        if self.recorders[variable_str] not in pyNN.neuron.simulator.recorder_list:
            pyNN.neuron.simulator.recorder_list.append(self.recorders[variable_str])  # this is a bit hackish - better to add to Population.__del__?

    def record_all(self, file_prefix):
        """
        Records all available variables
        
        @param file_prefix: The file path prefix that the output files will be written to. Each file will be appended the post fix .<var-name>.
        """
        for var in self.celltype.recordable:
            self.record(var, file_prefix + '.' + var)

class Projection(pyNN.neuron.Projection):

    def __init__(self, pre, dest, label, connector, source=None, target=None, build_mode=BUILD_MODE):
        self.label = label
        if build_mode == 'compile_only':
            print "Warning! '--compile' option was set to 'compile_only', meaning the projection '%s' was not constructed." % label
        else:
            pyNN.neuron.Projection.__init__(self, pre, dest, connector, label=label, source=source,
                                                                                      target=target)


class Network(ninemlp.common.Network):

    def __init__(self, filename, build_mode=BUILD_MODE):
        self._pyNN_module = pyNN.neuron
        self._ncml_module = ncml
        self._Population_class = Population
        self._Projection_class = Projection
        self.get_min_delay = get_min_delay
        #Call the base function initialisation function.
        ninemlp.common.Network.__init__(self, filename, build_mode=build_mode)
        if self.networkML.sim_params.has_key('temperature'):
            neuron.h.celsius = self.networkML.sim_params['temperature']
        else:
            neuron.h.celsius = ninemlp.common.Network.TEMPERATURE_DEFAULT

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


    def _get_target_str(self, synapse, segment=None):
        # FIXME: This should probably not be hard-coded like this as it this is
        # a id specified by the "user". Maybe should be included in the NINEML
        # description as a separate tag, which then saves the name of the "soma"
        # segment.
        if not segment:
            segment = "soma"
        return segment + "." + synapse


if __name__ == "__main__":

    net = Network('/home/tclose/Projects/Cerebellar/xml/cerebellum/test.xml')

    print 'done'

