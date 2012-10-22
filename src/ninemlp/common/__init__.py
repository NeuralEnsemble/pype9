"""

  This package combines the common.ncml with existing pyNN classes

  @file ncml.py
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
import numpy
import collections
import xml.sax
import os.path
from ninemlp import DEFAULT_BUILD_MODE
import geometry
import pyNN.connectors
import warnings
import math

## The location relative to the NINEML-Network file to look for the folder containing the cell descriptions. Should eventually be replaced with a specification in the NINEML-Network declaration itself.
RELATIVE_NCML_DIR = "./ncml"

## The location relative to the NINEML-Network file to look for the folder containing the BRep connectivity descriptions. Should eventually be replaced with a specification in the NINEML-Network declaration itself.
RELATIVE_BREP_DIR = "./brep"

BASIC_PYNN_CONNECTORS = ['AllToAll', 'OneToOne']

_REQUIRED_SIM_PARAMS = ['timestep', 'min_delay', 'max_delay', 'temperature']

class ValueWithUnits(object):

    def __init__(self, value, units):
        self.value = float(eval(value))
        self.units = units

    def neuron(self):
        if self.units == None:
            return self.value
        elif self.units == 'ms':
            return self.value
        elif self.units == 'uF_per_cm2':
            return self.value
        elif self.units == 'mV':
            return self.value
        elif self.units == 'ohm_cm':
            return self.value
        elif self.units == 'S_per_m2':
            return self.value
        else:
            raise Exception("Unrecognised units '" + self.units + "' (A conversion from these units \
                            to the standard NEURON units needs to be added to \
                            'ninemlp.common.ncml.neuron_value' function).")

class XMLHandler(xml.sax.handler.ContentHandler):

    def __init__(self):
        self._open_components = []
        self._required_attrs = []

    def characters(self, data):
        pass

    def endElement(self, name):
        """
        Closes a component, removing its name from the _open_components list. 
        
        WARNING! Will break if there are two tags with the same name, with one inside the other and 
        only the outer tag is opened and the inside tag is differentiated by its parents
        and attributes (this would seem an unlikely scenario though). The solution in this case is 
        to open the inside tag and do nothing. Otherwise opening and closing all components 
        explicitly is an option.
        """
        if self._open_components and name == self._open_components[-1]:
            self._open_components.pop()
            self._required_attrs.pop()

    def _opening(self, tag_name, attr, ref_name, parents=[], required_attrs=[]):
        if tag_name == ref_name and \
          (not parents or parents == self._open_components[-len(parents):]) and \
          all([(attr[key] == val or val == None) for key, val in required_attrs]):
            self._open_components.append(ref_name)
            self._required_attrs.append(required_attrs)
            return True
        else:
            return False

    def _closing(self, tag_name, ref_name, parents=[], required_attrs=[]):
        if tag_name == ref_name and \
          (not parents or parents == self._open_components[-len(parents) - 1:-1]) and \
          self._required_attrs[-1] == required_attrs:
            return True
        else:
            return False


class NetworkMLHandler(XMLHandler):

    Network = collections.namedtuple('Network', 'id sim_params populations projections free_params')
    Population = collections.namedtuple('Population', 'id cell_type size layout cell_params flags not_flags')
    Projection = collections.namedtuple('Projection', 'id pre post connection weight delay flags not_flags')
    Layout = collections.namedtuple('Layout', 'type args')
    CellParameters = collections.namedtuple('CellParameters', 'constants distributions')
    CellParameterDistr = collections.namedtuple('CellParameterDistr', 'param type component args')
    Connection = collections.namedtuple('Connection', 'pattern args')
    Weight = collections.namedtuple('Weight', 'pattern args')
    Delay = collections.namedtuple('Delay', 'pattern args')
    Source = collections.namedtuple('Source', 'pop_id terminal section')
    Destination = collections.namedtuple('Destination', 'pop_id synapse segment')
    FreeParameters = collections.namedtuple('FreeParameters', 'flags scalars')

    def __init__(self):
        XMLHandler.__init__(self)

    def startElement(self, tag_name, attrs):
        if self._opening(tag_name, attrs, 'network'):
            self.network = self.Network(attrs['id'], {}, [], [], self.FreeParameters({}, {}))
        elif self._opening(tag_name, attrs, 'freeParameters', parents=['network']): pass
        elif self._opening(tag_name, attrs, 'flags', parents=['freeParameters']): pass
        elif self._opening(tag_name, attrs, 'flag', parents=['flags']):
            if attrs['default'] == 'True':
                self.network.free_params.flags[attrs['id']] = True
            else:
                self.network.free_params.flags[attrs['id']] = False
        elif self._opening(tag_name, attrs, 'simulationDefaults'): pass
        elif self._opening(tag_name, attrs, 'temperature', parents=['simulationDefaults']):
            self.network.sim_params['temperature'] = float(attrs['value'])
        elif self._opening(tag_name, attrs, 'timeStep', parents=['simulationDefaults']):
            self.network.sim_params['timestep'] = float(attrs['value'])
        elif self._opening(tag_name, attrs, 'minDelay', parents=['simulationDefaults']):
            self.network.sim_params['min_delay'] = float(attrs['value'])
        elif self._opening(tag_name, attrs, 'maxDelay', parents=['simulationDefaults']):
            self.network.sim_params['max_delay'] = float(attrs['value'])
        elif self._opening(tag_name, attrs, 'population', parents=['network']):
            self.pop_id = attrs['id']
            self.pop_cell = attrs['cell']
            self.pop_size = int(attrs.get('size', '-1'))
            self.pop_layout = None
            self.pop_cell_params = self.CellParameters({}, [])
            # Split the flags attribute on ',' and remove empty values (the use of filter)            
            self.pop_flags = filter(None, attrs.get('flags', '').replace(' ', '').split(','))
            self.pop_not_flags = filter(None, attrs.get('not_flags', '').replace(' ', '').split(','))
        elif self._opening(tag_name, attrs, 'layout', parents=['population']):
            if self.pop_layout:
                raise Exception("The layout is specified twice in population '%s'" % self.pop_id)
            args = dict(attrs)
            layout_type = args.pop('type')
            self.pop_layout = self.Layout(layout_type, args)
        elif self._opening(tag_name, attrs, 'cellParameters', parents=['population']): pass
        elif self._opening(tag_name, attrs, 'const', parents=['population', 'cellParameters']):
            self.pop_cell_params.constants[attrs['name']] = float(attrs['value']) # FIXME: Units are ignored here
        elif self._opening(tag_name, attrs, 'distribution', parents=['population', 'cellParameters']):
            args = dict(attrs)
            name = args.pop('name')
            distr_type = args.pop('type')
            if args.has_key('component'):
                component = args.pop('component')
            else:
                component = None
            self.pop_cell_params.distributions.append(self.CellParameterDistr(name, distr_type,
                                                                                   component, args))
        elif self._opening(tag_name, attrs, 'arg', parents=['param_dist']):
            self.populations[-1].param_dists[-1].args[attrs['name']] = float(attrs['value'])
        elif self._opening(tag_name, attrs, 'projection', parents=['network']):
            self.proj_id = attrs['id']
            self.proj_pre = None
            self.proj_post = None
            self.proj_connection = None
            self.proj_weight = attrs.get('weight', None)
            self.proj_delay = attrs.get('delay', None)
            # Split the flags attribute on ',' and remove empty values (the use of filter)
            self.proj_flags = filter(None, attrs.get('flags', '').replace(' ', '').split(','))
            self.proj_not_flags = filter(None, attrs.get('not_flags', '').replace(' ', '').split(','))
        elif self._opening(tag_name, attrs, 'source', parents=['projection']):
            if self.proj_pre:
                raise Exception("The pre is specified twice in projection %s'" % self.proj_id)
            self.proj_pre = self.Source(attrs['id'],
                                        attrs.get('terminal', None),
                                        attrs.get('section', None))
        elif self._opening(tag_name, attrs, 'destination', parents=['projection']):
            if self.proj_post:
                raise Exception("The destination is specified twice in projection'%s'" % self.proj_id)
            self.proj_post = self.Destination(attrs['id'],
                                              attrs.get('synapse', None),
                                              attrs.get('segment', None))
        elif self._opening(tag_name, attrs, 'connection', parents=['projection']):
            if self.proj_connection:
                raise Exception("The connection is specified twice in projection '%s'" % self.proj_id)
            args = dict(attrs)
            pattern = args.pop('pattern')
            self.proj_connection = self.Connection(pattern, args)
        elif self._opening(tag_name, attrs, 'weight', parents=['projection']):
            if self.proj_weight:
                raise Exception("The weight is specified twice in projection '%s'" % self.proj_id)
            args = dict(attrs)
            pattern = args.pop('pattern')
            self.proj_weight = self.Weight(pattern, args)
        elif self._opening(tag_name, attrs, 'delay', parents=['projection']):
            if self.proj_delay:
                raise Exception("The delay is specified twice in projection '%s'" % self.proj_id)
            args = dict(attrs)
            pattern = args.pop('pattern')
            self.proj_delay = self.Delay(pattern, args)

    def endElement(self, name):
        if self._closing(name, 'population', parents=['network']):
            if self.pop_size > -1 and self.pop_layout:
                raise Exception("Population 'size' attribute cannot be used in conjunction with the\
 'layout' member (with layouts, the size is determined from the arguments to the structure)")
            self.network.populations.append(self.Population(self.pop_id,
                                                    self.pop_cell,
                                                    self.pop_size,
                                                    self.pop_layout,
                                                    self.pop_cell_params,
                                                    self.pop_flags,
                                                    self.pop_not_flags))
        elif self._closing(name, 'projection', parents=['network']):
            self.network.projections.append(self.Projection(self.proj_id,
                                                    self.proj_pre,
                                                    self.proj_post,
                                                    self.proj_connection,
                                                    self.proj_weight,
                                                    self.proj_delay,
                                                    self.proj_flags,
                                                    self.proj_not_flags))
        XMLHandler.endElement(self, name)


def read_networkML(filename):
    """
    Extracts the network specified in the given file and returns a NetworkMLHandler with the parsed 
    network specification.
    
    @param filename: The location of the NINEML-Network file to read the network from.
    """
    parser = xml.sax.make_parser()
    handler = NetworkMLHandler()
    parser.setContentHandler(handler)
    parser.parse(os.path.normpath(filename))
    return handler.network


class Network(object):

    def __init__(self, filename, build_mode=DEFAULT_BUILD_MODE, timestep=None,
                                                min_delay=None, max_delay=None, temperature=None,
                                                silent_build=False, flags=[]):
        assert  hasattr(self, "_pyNN_module") and \
                hasattr(self, "_ncml_module") and \
                hasattr(self, "_Population_class") and \
                hasattr(self, "_Projection_class") and \
                hasattr(self, "get_min_delay")
        self.load_network(filename, build_mode=build_mode, timestep=timestep,
                                 min_delay=min_delay, max_delay=max_delay, temperature=temperature,
                                 silent_build=silent_build, flags=flags)

    def set_flags(self, flags):
        self.flags = self.networkML.free_params.flags
        for flag in flags:
            if type(flag) == str:
              name = flag
              value = True
            elif type(flag) == tuple:
                if len(flag) == 2:
                    name, value = flag
                else:
                    raise Exception("Incorrect number of elements ({}) in flag tuple '{}', should be 2\
 (name or name and value)".format(len(flag), flag))
            assert(type(name)==str)
            assert(type(value)==bool)
            if name not in self.flags:
                raise Exception ("Did not find the passed flag '{}' in the Network ML description"
                                                                                .format(name))                
            self.flags[name] = flag[value]

    def check_flags(self, p):
        try:
            return all([self.flags[flag] for flag in p.flags]) and \
                                            all([not self.flags[flag] for flag in p.not_flags])
        except KeyError as e:
                raise Exception ('Did not find flag ''{flag}'' used in ''{id}'' in freeParameters \
block of NetworkML description'.format(flag=e, id=p.id))
                
    def load_network(self, filename, build_mode=DEFAULT_BUILD_MODE, verbose=False, timestep=None,
                                                min_delay=None, max_delay=None, temperature=None,
                                                silent_build=False, flags=[]):
        self.networkML = read_networkML(filename)
        self._set_simulation_params(timestep=timestep, min_delay=min_delay, max_delay=max_delay,
                                                                            temperature=temperature)
        dirname = os.path.dirname(filename)
        self.cells_dir = os.path.join(dirname, RELATIVE_NCML_DIR)
        self.pop_dir = os.path.join(dirname, RELATIVE_BREP_DIR, 'build', 'populations')
        self.proj_dir = os.path.join(dirname, RELATIVE_BREP_DIR, 'build', 'projections')
        self.build_mode = build_mode
        self.label = self.networkML.id
        self._populations = {}
        self._projections = {}
        self.set_flags(flags)
        for pop in self.networkML.populations:
            if self.check_flags(pop):
                self._populations[pop.id] = self._create_population(pop.id,
                                                                    pop.size,
                                                                    pop.cell_type,
                                                                    pop.layout,
                                                                    pop.cell_params.constants,
                                                                    pop.cell_params.distributions,
                                                                    verbose,
                                                                    silent_build)
        for proj in self.networkML.projections:
            if self.check_flags(proj):
                self._projections[proj.id] = self._create_projection(
                                                             proj.id,
                                                             self._populations[proj.pre.pop_id],
                                                             self._populations[proj.post.pop_id],
                                                             proj.connection,
                                                             proj.pre,
                                                             proj.post,
                                                             proj.weight,
                                                             proj.delay,
                                                             verbose)
        if build_mode == 'compile_only':
            print 'Finished compiling network, now exiting (use try: ... except SystemExit: ... \
if you want to do something afterwards)'
            raise SystemExit(0)

    def _create_population(self, label, size, cell_type_name, layout, cell_params, cell_param_dists,
                                                                            verbose, silent_build):
        if cell_type_name + ".xml" in os.listdir(self.cells_dir):
            cell_type = self._ncml_module.load_cell_type(cell_type_name,
                                            os.path.join(self.cells_dir, cell_type_name + ".xml"),
                                            build_mode=self.build_mode,
                                            silent=silent_build)
        elif cell_type_name in dir(self._pyNN_module.standardmodels.cells):
            # This is not as simple as it may have been, as a simple getattr on 
            # pyNN.nest.standardmodels.cells returns the pyNN.standardmodels.cells instead.
            _temp_import = __import__('%s.standardmodels.cells' % self._pyNN_module.__name__,
                                       globals(), locals(), [cell_type_name], 0)
            cell_type = getattr(_temp_import, cell_type_name)
        else:
            raise Exception("Cell_type_name '%s' was not found in search directory ('%s') or in \
                                            standard models" % (cell_type_name, self.cells_dir))

        if layout:
            if layout.type == "Extension":
                engine = layout.args.pop("engine")
                if engine == "Brep":
                    pop_id = layout.args['id']
                    if pop_id not in os.listdir(self.pop_dir):
                        raise Exception("Population id '%s' was not found in search path (%s)." %
                                                                            (pop_id, self.pop_dir))
                    pos_file = os.path.normpath(os.path.join(self.pop_dir, pop_id))
                    try:
                        positions = numpy.loadtxt(pos_file)
                        positions = numpy.transpose(positions)
                        size = positions.shape[1]
                    except:
                        raise Exception("Could not load Brep positions from file '%s'" % pos_file)
                else:
                    raise Exception("Unrecognised external layout engine, '%s'" % engine)
            else:
                raise Exception("Not implemented error, support for built-in layout management is not done yet.")
        pop = self._Population_class(label, size, cell_type, params=cell_params,
                                                                        build_mode=self.build_mode)
        if layout and self.build_mode != 'compile_only':
            pop._set_positions(positions)
        #TODO: Set parameter distributions here
        return pop

    def _create_projection(self, label, pre, dest, connection, source, target, weight, delay, verbose):
        if pre == dest:
            allow_self_connections = False
        else:
            allow_self_connections = True
        if connection.pattern == 'DistanceBased':
            expression = connection.args.pop('geometry')
            if not hasattr(geometry, expression):
                raise Exception("Unrecognised distance expression '%s'" % expression)
            try:
                GeometricExpression = getattr(geometry, expression)
                connect_expr = GeometricExpression(**self._convert_all_units(connection.args))
            except TypeError as e:
                raise Exception("Could not initialise distance expression class '%s' from given \
arguments '%s' ('%s')" % (expression, connection.args, e))
            if self.is_value_str(weight): # If weight is a string containing a simple value and units
                weight = self._convert_units(weight)
            elif hasattr(weight, 'pattern'):
                if weight.pattern == 'DistanceBased':
                    GeometricExpression = getattr(geometry, weight.args.pop('geometry'))
                    weight_expr = GeometricExpression(**self._convert_all_units(weight.args))
                else:
                    raise Exception("Invalid weight pattern ('%s') for DistanceBased connectivity"
                                                                                % weight.pattern)
            else:
                raise Exception("Could not parse weight specification '%s'" % weight)
            if self.is_value_str(delay): # If delay is a string containing a simple value and units
                delay = self._convert_units(delay)
            elif hasattr(delay, 'pattern'):
                if delay.pattern == 'DistanceBased':
                    GeometricExpression = getattr(geometry, delay.args.pop('geometry'))
                    delay_expr = GeometricExpression(min_value=self.get_min_delay(),
                                                     **self._convert_all_units(delay.args))
                else:
                    raise Exception("Invalid delay pattern ('%s') for DistanceBased connectivity"
                                                                                    % delay.pattern)
            elif target.synapse == "Gap": #FIXME: Dirty Hack
                delay_expr = 1.0
            else:
                raise Exception("Could not parse weight specification '%s'" % weight)
            connector = self._pyNN_module.connectors.DistanceDependentProbabilityConnector(
                                    connect_expr, allow_self_connections=allow_self_connections,
                                    weights=weight_expr, delays=delay_expr)
        elif connection.pattern == "Extension":
            engine = connection.args.pop('engine') # TODO: The following lines of processing 
            if engine == "Brep":                   # shouldn't happen here, it should be part of the 
                proj_id = connection.args['id']    # external engine.
                if proj_id not in os.listdir(self.proj_dir):
                    raise Exception("Connection id '%s' was not found in search path (%s)." %
                                                                        (proj_id, self.proj_dir))
                # The load step can take a while and isn't necessary when compiling so can be skipped.
                if self.build_mode != 'compile_only':
                    connection_matrix = numpy.loadtxt(os.path.join(self.proj_dir, connection.args['id']))
                else:
                    connection_matrix = numpy.ones((1, 4))
                if weight:
                    connection_matrix[:, 2] = self._convert_units(weight)
                if delay:
                    connection_matrix[:, 3] = self._convert_units(delay)
                delays = connection_matrix[:, 3] # Get view onto delays in connection matrix for readability
                below_min_indices = numpy.where(delays < self.get_min_delay())
                if len(below_min_indices):
                    if verbose:
                        warnings.warn("%d out of %d connections are below the minimum delay in \
                                        projection '%s'. They will be bounded to the minimum delay \
                                        (%d)" % (len(below_min_indices), len(delays), label),
                                                                               self.get_min_delay())
                    delays[below_min_indices] = self.get_min_delay() # Bound loaded delays by specified minimum delay
                connector = self._pyNN_module.connectors.FromListConnector(connection_matrix)
            else:
                raise Exception ("Unrecognised external engine '%s'" % engine)
        elif connection.pattern + 'Connector' in dir(pyNN.connectors):
            if weight.pattern == "Constant":
                weight = self._convert_units(weight.args['value'])
            else:
                raise Exception("Unrecognised weight pattern '%s'" % weight.pattern)
            if delay.pattern == "Constant":
                delay = self._convert_units(delay.args['value'])
            else:
                raise Exception("Unrecognised delay pattern '%s'" % delay.pattern)
            ConnectorClass = getattr(self._pyNN_module.connectors, '%sConnector' % connection.pattern)
            if ConnectorClass == pyNN.connectors.OneToOneConnector:
                connector_specific_args = {}
            else:
                connector_specific_args = {'allow_self_connections' : allow_self_connections}
            connector = ConnectorClass(weights=weight, delays=delay, **connector_specific_args)
        else:
            raise Exception("Unrecognised pattern type '%s'" % connection.pattern)
        return self._Projection_class(pre, dest, label, connector, source=source.terminal,
                                      target=self._get_target_str(target.synapse, target.segment),
                                      build_mode=self.build_mode)

    def _get_simulation_params(self, **params):
        sim_params = self.networkML.sim_params
        for key in _REQUIRED_SIM_PARAMS:
            if params.has_key(key) and params[key]:
                sim_params[key] = params[key]
            elif not sim_params.has_key(key) or not sim_params[key]:
                raise Exception ("'{}' parameter was not specified either in Network initialisation \
or NetworkML specification".format(key))
        return sim_params


    def _convert_units(self, value_str, units=None):
        raise NotImplementedError("_convert_units needs to be implemented by simulator specific Network class")

    def _convert_all_units(self, values_dict):
        for key, val in values_dict.items():
            values_dict[key] = self._convert_units(val)
        return values_dict

    def is_value_str(self, value_str):
        try:
            self._convert_units(value_str)
            return True
        except:
            return False

    def _get_target_str(self, synapse, segment=None):
        raise NotImplementedError("_get_target_str needs to be implemented by simulator specific Network class")

    def get_population(self, label):
        try:
            return self._populations[label]
        except KeyError:
            raise KeyError("Network does not have population with label '" + label + "'.")

    def get_projection(self, label):
        try:
            return self._projections[label]
        except KeyError:
            raise KeyError("Network does not have projection with label '" + label + "'.")

    def list_population_names(self):
        return self._populations.keys()

    def list_projection_names(self):
        return self._projections.keys()

    def all_populations(self):
        return self._populations.values()

    def all_projections(self):
        return self._projections.values()

    def describe(self):
        """
        Describes all populations and projections within the network
        """
        print "Populations:"
        for pop in self.all_populations():
            print pop.describe()

        print "Projections:"
        for proj in self.all_projections():
            print proj.describe()

    def save_connections(self, output_dir):
        """
        Saves generated connections to output directory
        
        @param output_dir:
        """
        for proj in self.all_projections():
            proj.saveConnections(os.path.join(output_dir, proj.label))

    def record_all_spikes(self, file_prefix):
        """
        Record all spikes generated in the network
        
        @param filename: The prefix for every population files before the popluation name. The suffix '.spikes' will be appended to the filenames as well.
        """
        # Add a dot to separate the prefix from the population label if it doesn't already have one
        # and isn't a directory
        if not os.path.isdir(file_prefix) and not file_prefix.endswith('.'):
            file_prefix += '.'
        for pop in self.all_populations():
            pop.record('spikes', file_prefix + pop.label + '.spikes') #@UndefinedVariable                

class Population(object):

    def set_poisson_spikes(self, rate, start_time, end_time):
        """
        Sets up a train of poisson spike times for a SpikeSourceArray population
        
        @param rate: Rate of the poisson spike train
        @param start_time: Start time of the stimulation
        @param end_time: The end time of the stimulation.
        """
        if self.get_cell_type().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for 'SpikeSourceArray' populations.")
        mean_interval = 1000 / rate # Convert from Hz to ms
        stim_range = end_time - start_time
        if stim_range >= 0.0:
            estimated_num_spikes = stim_range / mean_interval
            # Add extra spikes to make sure spike train doesn't stop short
            estimated_num_spikes = int(estimated_num_spikes + math.exp(-estimated_num_spikes / 10.0) * 10.0)
            spike_intervals = numpy.random.exponential(mean_interval, size=(self.size, estimated_num_spikes))
            spike_times = numpy.cumsum(spike_intervals, axis=1) + start_time
            # FIXME: Should ensure that spike times don't exceed 'end_time' and make it at least until then.
            self.tset('spike_times', spike_times)
        else:
            print "Warning, stimulation start time (%f) is after stimulation end time (%f)" % \
                                                                            (start_time, end_time)

    def set_spikes(self, spike_times):
        """
        Sets up a train of poisson spike times for a SpikeSourceArray population
        
        @param rate: Rate of the poisson spike train
        @param start_time: Start time of the stimulation
        @param end_time: The end time of the stimulation.
        """
        if self.get_cell_type().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for 'SpikeSourceArray' populations.")
        self.tset('spike_times', spike_times)

    def get_cell_type(self):
        """
        Returns the cell type of the population
        """
        return type(self.celltype)


if __name__ == "__main__":

    import pprint

    ## Generated when this module is called directly for testing purposes.
    parsed_network = read_networkML("/home/tclose/cerebellar/xml/cerebellum/test.xml")
    print 'Network: ' + parsed_network.network_id
    pprint.pprint(parsed_network.populations)
    pprint.pprint(parsed_network.projections)
