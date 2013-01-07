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
# Generic imports
import re
import numpy
import collections
import os.path
import xml.sax
from inspect import getmro
import warnings
import math
# Specific imports
import pyNN.connectors
from pyNN.random import RandomDistribution
from ninemlp import DEFAULT_BUILD_MODE, XMLHandler
import ninemlp.connectivity.point2point as point2point

## The location relative to the NINEML-Network file to look for the folder containing the cell descriptions. Should eventually be replaced with a specification in the NINEML-Network declaration itself.
RELATIVE_NCML_DIR = "./ncml"

## The location relative to the NINEML-Network file to look for the folder containing the BRep connectivity descriptions. Should eventually be replaced with a specification in the NINEML-Network declaration itself.
RELATIVE_BREP_DIR = "./brep"

BASIC_PYNN_CONNECTORS = ['AllToAll', 'OneToOne']

_REQUIRED_SIM_PARAMS = ['timestep', 'min_delay', 'max_delay', 'temperature']

RANDOM_DISTR_PARAMS = {'uniform': ('low', 'high'),
                       'normal': ('mean', 'stddev')}

def group_varname(group_id):
    if group_id:
        varname = group_id + "_group"
    else:
        varname = "all_segs"
    return varname

def seg_varname(seg_id):
    return seg_id + "_seg"


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
            raise Exception("Unrecognised units '{}' (A conversion from these units \
                            to the standard NEURON units needs to be added to \
                            'ninemlp.common.ncml.neuron_value' function).".format(self.units))


class NetworkMLHandler(XMLHandler):

    Network = collections.namedtuple('Network', 'id sim_params populations projections free_params')
    Population = collections.namedtuple('Population', ('id', 'cell_type', 'morph_id', 'size',
                                                       'layout', 'cell_params',
                                                       'initial_conditions', 'flags', 'not_flags'))
    Projection = collections.namedtuple('Projection', 'id pre post connection weight delay '
                                                      'synapse_family flags not_flags')
    Layout = collections.namedtuple('Layout', 'type args')
    CustomAttributes = collections.namedtuple('CustomAttributes', 'constants distributions')
    Distribution = collections.namedtuple('Distribution', 'attr type units seg_group component '
                                                          'args')
    Connection = collections.namedtuple('Connection', 'pattern args')
    Weight = collections.namedtuple('Weight', 'pattern args')
    Delay = collections.namedtuple('Delay', 'pattern args')
    Source = collections.namedtuple('Source', 'pop_id terminal segment')
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
            self.pop_morph_id = attrs.get('morphology', None)
            self.pop_size = int(attrs.get('size', '-1'))
            self.pop_layout = None
            self.pop_cell_params = self.CustomAttributes({}, [])
            self.pop_initial_conditions = self.CustomAttributes({}, [])
            # Split the flags attribute on ',' and remove empty values (the use of filter)            
            self.pop_flags = filter(None, attrs.get('flags', '').replace(' ', '').split(','))
            self.pop_not_flags = filter(None, attrs.get('not_flags', '').replace(' ', '').split(','))
        elif self._opening(tag_name, attrs, 'layout', parents=['population']):
            if self.pop_layout:
                raise Exception("The layout is specified twice in population '{}'".\
                                format(self.pop_id))
            args = dict(attrs)
            layout_type = args.pop('type')
            self.pop_layout = self.Layout(layout_type, args)
        elif self._opening(tag_name, attrs, 'cellParameters', parents=['population']): pass
        elif self._opening(tag_name, attrs, 'initialConditions', parents=['population']): pass
        elif self._opening(tag_name, attrs, 'const', parents=['population', 'cellParameters']):
            self.pop_cell_params.constants[attrs['name']] = float(attrs['value']) # FIXME: Units are ignored here
        elif self._opening(tag_name, attrs, 'const', parents=['population', 'initialConditions']):
            self.pop_cell_params.constants[attrs['name']] = float(attrs['value']) # FIXME: Units are ignored here            
        elif self._opening(tag_name, attrs, 'distribution', parents=['population',
                                                                     'cellParameters']) or \
                self._opening(tag_name, attrs, 'distribution', parents=['population',
                                                                     'initialConditions']):
            args = dict(attrs)
            attribute = args.pop('attr')
            distr_type = args.pop('type')
            units = args.pop('units') if args.has_key('units') else None
            component = args.pop('component') if args.has_key('component') else None
            segmentGroup = args.pop('segmentGroup') if args.has_key('segmentGroup') else None
            try:
                distr_param_keys = RANDOM_DISTR_PARAMS[distr_type]
            except KeyError:
                raise Exception ("Unrecognised distribution type '{type}' used to distribute " \
                                 "cell attribute '{attribute}' in population '{pop}'"\
                                 .format(type=distr_type, attribute=attribute, pop=self.id))
            try:
                distr_params = [args[arg] for arg in distr_param_keys]
            except KeyError as e:
                raise Exception ("Missing attribute '{distr_params}' for '{type}' distribution " \
                                 "used to distribute cell attribute '{attribute}' in population " \
                                 "'{pop}'".format(distr_params=e, type=distr_type,
                                                  attribute=attribute, pop=self.id))
            distr = self.Distribution(attribute, distr_type, units, segmentGroup, component,
                                      distr_params)
            if self._open_components[-2] == 'cellParameters':
                self.pop_cell_params.distributions.append(distr)
            elif self._open_components[-2] == 'initialConditions':
                self.pop_initial_conditions.distributions.append(distr)
            else:
                assert False
        elif self._opening(tag_name, attrs, 'projection', parents=['network']):
            self.proj_id = attrs['id']
            self.proj_pre = None
            self.proj_post = None
            self.proj_connection = None
            self.proj_weight = attrs.get('weight', None)
            self.proj_delay = attrs.get('delay', None)
            self.proj_synapse_family = attrs.get('synapseFamily', 'Chemical')
            # Split the flags attribute on ',' and remove empty values (the use of filter)
            self.proj_flags = filter(None, \
                                     attrs.get('flags', '').replace(' ', '').split(','))
            self.proj_not_flags = filter(None, \
                                         attrs.get('not_flags', '').replace(' ', '').split(','))
        elif self._opening(tag_name, attrs, 'source', parents=['projection']):
            if self.proj_pre:
                raise Exception("The pre is specified twice in projection {}'".format(self.proj_id))
            self.proj_pre = self.Source(attrs['id'],
                                        attrs.get('terminal', None),
                                        attrs.get('segment', None))
        elif self._opening(tag_name, attrs, 'destination', parents=['projection']):
            if self.proj_post:
                raise Exception("The destination is specified twice in projection'{}'"\
                                .format(self.proj_id))
            self.proj_post = self.Destination(attrs['id'],
                                              attrs.get('synapse', None),
                                              attrs.get('segment', None))
        elif self._opening(tag_name, attrs, 'connection', parents=['projection']):
            if self.proj_connection:
                raise Exception("The connection is specified twice in projection '{}'"\
                                .format(self.proj_id))
            args = dict(attrs)
            pattern = args.pop('pattern')
            self.proj_connection = self.Connection(pattern, args)
        elif self._opening(tag_name, attrs, 'weight', parents=['projection']):
            if self.proj_weight:
                raise Exception("The weight is specified twice in projection '{}'"\
                                .format(self.proj_id))
            args = dict(attrs)
            pattern = args.pop('pattern')
            self.proj_weight = self.Weight(pattern, args)
        elif self._opening(tag_name, attrs, 'delay', parents=['projection']):
            if self.proj_delay:
                raise Exception("The delay is specified twice in projection '{}'"\
                                .format(self.proj_id))
            args = dict(attrs)
            pattern = args.pop('pattern')
            self.proj_delay = self.Delay(pattern, args)

    def endElement(self, name):
        if self._closing(name, 'population', parents=['network']):
            if self.pop_size > -1 and self.pop_layout:
                raise Exception("Population 'size' attribute cannot be used in conjunction with " \
                                "the 'layout' member (with layouts, the size is determined from " \
                                "the arguments to the structure)")
            self.network.populations.append(self.Population(self.pop_id,
                                                    self.pop_cell,
                                                    self.pop_morph_id,
                                                    self.pop_size,
                                                    self.pop_layout,
                                                    self.pop_cell_params,
                                                    self.pop_initial_conditions,
                                                    self.pop_flags,
                                                    self.pop_not_flags))
        elif self._closing(name, 'projection', parents=['network']):
            self.network.projections.append(self.Projection(self.proj_id,
                                                    self.proj_pre,
                                                    self.proj_post,
                                                    self.proj_connection,
                                                    self.proj_weight,
                                                    self.proj_delay,
                                                    self.proj_synapse_family,
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

    def __init__(self, filename, build_mode=DEFAULT_BUILD_MODE, timestep=None, min_delay=None,
                 max_delay=None, temperature=None, silent_build=False, flags=[]):
        assert  hasattr(self, "_pyNN_module") and \
                hasattr(self, "_ncml_module") and \
                hasattr(self, "_Population_class") and \
                hasattr(self, "_Projection_class") and \
                hasattr(self, "_ElectricalSynapseProjection_class") and \
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
                    raise Exception("Incorrect number of elements ({}) in flag tuple '{}', " \
                                    "should be 2 (name or name and value)".format(len(flag), flag))
                assert(type(name) == str)
                assert(type(value) == bool)
            if name not in self.flags:
                raise Exception ("Did not find the passed flag '{}' in the Network ML description "\
                                 "({})".format(name, self.flags))
            self.flags[name] = value

    def check_flags(self, p):
        try:
            return all([self.flags[flag] for flag in p.flags]) and \
                                            all([not self.flags[flag] for flag in p.not_flags])
        except KeyError as e:
                raise Exception ("Did not find flag '{flag}' used in '{id}' in freeParameters "\
                                 "block of NetworkML description".format(flag=e, id=p.id))

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
                                                                    pop.morph_id,
                                                                    pop.layout,
                                                                    pop.cell_params.constants,
                                                                    pop.cell_params.distributions,
                                                                    pop.initial_conditions.distributions,
                                                                    verbose,
                                                                    silent_build)
        if build_mode == 'build_only' or build_mode == 'compile_only':
            print "Finished compiling network, now exiting (use try: ... except SystemExit: ... " \
                    "if you want to do something afterwards)"
            raise SystemExit(0)                
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
                                                             proj.synapse_family,
                                                             verbose)
        self._finalise_construction()

    def _finalise_construction(self):
        """
        Can be overloaded to do any simulator specific finalisation that is required
        """
        pass
    
    def _create_population(self, label, size, cell_type_name, morph_id, layout, cell_params,
                           cell_param_distrs, initial_conditions, verbose, silent_build):
        if cell_type_name + ".xml" in os.listdir(self.cells_dir):
            cell_type = self._ncml_module.load_cell_type(cell_type_name,
                                            os.path.join(self.cells_dir, cell_type_name + ".xml"),
                                            morph_id=morph_id,
                                            build_mode=self.build_mode,
                                            silent=silent_build)
        elif cell_type_name in dir(self._pyNN_module.standardmodels.cells):
            # This is not as simple as it may have been, as a simple getattr on 
            # pyNN.nest.standardmodels.cells returns the pyNN.standardmodels.cells instead.
            _temp_import = __import__('{}.standardmodels.cells'.format(self._pyNN_module.__name__),
                                       globals(), locals(), [cell_type_name], 0)
            cell_type = getattr(_temp_import, cell_type_name)
        else:
            raise Exception("Cell_type_name '{}' was not found in search directory ('{}') or in " \
                            "standard models".format(cell_type_name, self.cells_dir))
        if layout:
            if layout.type == "Extension":
                engine = layout.args.pop("engine")
                if engine == "Brep":
                    pop_id = layout.args['id']
                    if pop_id not in os.listdir(self.pop_dir):
                        raise Exception("Population id '{}' was not found in search " \
                                        "path ({}).".format(pop_id, self.pop_dir))
                    pos_file = os.path.normpath(os.path.join(self.pop_dir, pop_id))
                    try:
                        positions = numpy.loadtxt(pos_file)
                        positions = numpy.transpose(positions)
                        size = positions.shape[1]
                    except:
                        raise Exception("Could not load Brep positions from file '{}'"\
                                        .format(pos_file))
                else:
                    raise Exception("Unrecognised external layout engine, '{}'".format(engine))
            else:
                raise Exception("Not implemented error, support for built-in layout management is "\
                                "not done yet.")
        # Actually create the population
        pop = self._Population_class(label, size, cell_type, params=cell_params,
                                                                        build_mode=self.build_mode)
        # Set layout
        if not (self.build_mode == 'build_only' or self.build_mode == 'compile_only'):
            if layout:
                pop._set_positions(positions)
            pop._randomly_distribute_params(cell_param_distrs)
            pop._randomly_distribute_initial_conditions(initial_conditions)
        return pop

    def _get_connection_param_expr(self, label, param, min_value=0.0):
        if isinstance(param, float) or param is None:
            param_expr = param
        elif self.is_value_str(param):
            param_expr = self._convert_units(param)
        elif hasattr(param, 'pattern'):
            if param.pattern == "Constant":
                param_expr = self._convert_units(param.args['value'])
            elif param.pattern == 'DistanceBased':
                expr_name = param.args.pop('geometry')
                GeometricExpression = getattr(point2point, expr_name)
                try:
                    param_expr = GeometricExpression(min_value=min_value,
                                                     **self._convert_all_units(param.args))
                except TypeError as e:
                    raise Exception("Could not initialise distance expression class '{}' from "
                                    "given arguments '{}' for projection '{}'\n('{}')"
                                    .format(expr_name, param.args, label, e))
            else:
                raise Exception("Invalid parameter pattern ('{}') for projection '{}'".
                                format(param.pattern, label))
        else:
            raise Exception("Could not parse parameter specification '{}' for projection '{}'"
                            .format(param, label))
        return param_expr

    def _create_projection(self, label, pre, dest, connection, source, target, weight, delay,
                           synapse_family, verbose):
        if pre == dest:
            allow_self_connections = False
        else:
            allow_self_connections = True
        # Set expressions for connection weights and delays
        weight_expr = self._get_connection_param_expr(label, weight)
        if synapse_family == 'Electrical':
            # Delay is not required by Gap junctions so just set to something innocuous here
            delay_expr = 1.0 
        else:
            delay_expr = self._get_connection_param_expr(label, delay,
                                                         min_value=self.get_min_delay())
        # Set connection probability     
        if connection.pattern == 'DistanceBased':
            expression = connection.args.pop('geometry')
            if not hasattr(point2point, expression):
                raise Exception("Unrecognised distance expression '{}'".format(expression))
            try:
                GeometricExpression = getattr(point2point, expression)
                connect_expr = GeometricExpression(**self._convert_all_units(connection.args))
            except TypeError as e:
                raise Exception("Could not initialise distance expression class '{}' from given " \
                                "arguments '{}' for projection '{}'\n('{}')"
                                .format(expression, connection.args, label, e))
            connector = self._pyNN_module.connectors.DistanceDependentProbabilityConnector(
                                    connect_expr, allow_self_connections=allow_self_connections,
                                    weights=weight_expr, delays=delay_expr)
        # If connection pattern is external, load the weights and delays from a file in PyNN
        # FromFileConnector format and then create a FromListConnector connector. Some additional
        # preprocessing is performed here, which is why the FromFileConnector isn't used directly.
        elif connection.pattern == "Extension":
            proj_id = connection.args['id']
            if proj_id not in os.listdir(self.proj_dir):
                raise Exception("Connection id '{}' was not found in search path ({}).".\
                                format(proj_id, self.proj_dir))
            # The load step can take a while and isn't necessary when compiling so can be 
            # skipped.
            if self.build_mode != 'build_only':
                connection_matrix = numpy.loadtxt(os.path.join(self.proj_dir,
                                                               connection.args['id']))
            else:
                connection_matrix = numpy.ones((1, 4))
            if isinstance(weight_expr, float):
                connection_matrix[:, 2] = weight_expr
            if isinstance(delay_expr, float):
                connection_matrix[:, 3] = delay_expr
            # Get view onto delays in connection matrix for readability                    
            delays = connection_matrix[:, 3]
            below_min_indices = numpy.where(delays < self.get_min_delay())
            if len(below_min_indices):
                if verbose:
                    warnings.warn("{} out of {} connections are below the minimum delay in \
                                    projection '{}'. They will be bounded to the minimum delay \
                                    ({})".format(len(below_min_indices), len(delays), label),
                                                 self.get_min_delay())
                # Bound loaded delays by specified minimum delay                        
                delays[below_min_indices] = self.get_min_delay()
            connector = self._pyNN_module.connectors.FromListConnector(connection_matrix)
        # Use in-built pyNN connectors for simple patterns such as AllToAll and OneToOne
        # NB: At this stage the pattern name is tied to the connector name in pyNN but could be
        # decoupled from this at some point (but I am not sure you would want to)
        elif connection.pattern + 'Connector' in dir(pyNN.connectors):
            ConnectorClass = getattr(self._pyNN_module.connectors,
                                     '{}Connector'.format(connection.pattern))
            if ConnectorClass == pyNN.connectors.OneToOneConnector:
                connector_specific_args = {}
            else:
                connector_specific_args = {'allow_self_connections' : allow_self_connections}
            connector = ConnectorClass(weights=weight_expr, delays=delay_expr,
                                       **connector_specific_args)
        else:
            raise Exception("Unrecognised pattern type '{}'".format(connection.pattern))
        # Initialise the projection object and return
        with warnings.catch_warnings(record=True) as warnings_list:
            warnings.simplefilter("always", category=point2point.InsufficientTargetsWarning)
            if synapse_family == 'Chemical':
                projection = self._Projection_class(pre, dest, label, connector, 
                                                    source=source.terminal, 
                                                    target=self._get_target_str(target.synapse, 
                                                                                target.segment),
                                                    build_mode=self.build_mode)
            elif synapse_family == 'Electrical':
                if not self._ElectricalSynapseProjection_class:
                    raise Exception("The selected simulator doesn't currently support electrical "
                                    "synapse projections")
                projection = self._ElectricalSynapseProjection_class(pre, dest, label, connector, 
                                                                     source=source.segment, 
                                                                     target=target.segment,
                                                                     build_mode=self.build_mode)            
            else:
                raise Exception("Unrecognised synapse family type '{}'".format(synapse_family))
            # Collate raised "InsufficientTargets" warnings into a single warning message for better
            # readibility.
            insufficient_targets_str = ""            
            if warnings_list:
                for w in warnings_list:
                    if w.category == point2point.InsufficientTargetsWarning:
                        req_number, mask_size = re.findall("\([^\)]*\)", str(w.message))
                        insufficient_targets_str += " {},".format(mask_size[2:-1])
        if insufficient_targets_str:
            print "Could not satisfy all connection targets in projection '{}' " \
                  "because the requested number of connections, {}, exceeded the size of " \
                  "the generated masks of sizes:{}. The number of connections was reset to the " \
                  "size of the respective masks in these cases.\n".format(label, req_number[2:-1], 
                                                                          insufficient_targets_str[:-1])
        return projection

    def _get_simulation_params(self, **params):
        sim_params = self.networkML.sim_params
        for key in _REQUIRED_SIM_PARAMS:
            if params.has_key(key) and params[key]:
                sim_params[key] = params[key]
            elif not sim_params.has_key(key) or not sim_params[key]:
                raise Exception ("'{}' parameter was not specified either in Network " \
                                 "initialisation or NetworkML specification".format(key))
        return sim_params

    def _convert_units(self, value_str, units=None):
        raise NotImplementedError("_convert_units needs to be implemented by simulator specific " \
                                  "Network class")

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
        raise NotImplementedError("_get_target_str needs to be implemented by simulator specific " \
                                  "Network class")

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

    def record_spikes(self):
        """
        Record all spikes generated in the network (to be saved to file with Network.print_spikes)
        """
        for pop in self.all_populations():
            pop.record() #@UndefinedVariable                

    def print_spikes(self, file_prefix):
        """
        Record all spikes generated in the network
        
        @param filename: The prefix for every population files before the popluation name. The \
                         suffix '.spikes' will be appended to the filenames as well.
        """
        # Add a dot to separate the prefix from the population label if it doesn't already have one
        # and isn't a directory
        if not os.path.isdir(file_prefix) and not file_prefix.endswith('.') \
                and not file_prefix.endswith(os.path.sep):
            file_prefix += '.'
        for pop in self.all_populations():
            pop.printSpikes(file_prefix + pop.label + '.spikes') #@UndefinedVariable                

class Population(object):

    def _randomly_distribute_params(self, cell_param_distrs):
        # Set distributed parameters
        distributed_params = []
        for param, distr_type, units, seg_group, component, args in cell_param_distrs: #@UnusedVariable: Can't work out how to use units effectively at the moment because args may include parameters that don't have units, so ignoring it for now but will hopefully come back to it
            if param in distributed_params:
                raise Exception("Parameter '{}' has two (or more) distributions specified for it " \
                                "in {} population".format(param, self.id))
            # Create random distribution object
            rand_distr = RandomDistribution(distribution=distr_type, parameters=args)
            # If is an NCML type cell
            if self.celltype.__module__.startswith('ninemlp'):
                param_scope = [group_varname(seg_group)]
                if component:
                    param_scope.append(component)
                param_scope.append(param)
                self.rset('.'.join(param_scope), rand_distr)
            else:
                if seg_group:
                    raise Exception("segmentGroup attribute of parameter distribution '{}' can " \
                                    "be specified for cells described using NCML, not '{}' cell " \
                                    "types".format(param, self.celltype.__class__.__name__))
                if component:
                    raise Exception("component attribute of parameter distribution '{}' can only " \
                                    "be specified for cells described using NCML, not '{}' cell " \
                                    "types".format(param, self.celltype.__class__.__name__))
                self.rset(param, rand_distr)
            # Add param to list of completed param distributions to check for duplicates
            distributed_params.append(param)

    def _randomly_distribute_initial_conditions(self, initial_conditions):
        # Set distributed parameters
        distributed_conditions = []
        for variable, distr_type, units, seg_group, component, args in initial_conditions: #@UnusedVariable: Can't work out how to use units effectively at the moment because args may include variables that don't have units, so ignoring it for now but will hopefully come back to it
            if variable in distributed_conditions:
                raise Exception("Parameter '{}' has two (or more) distributions specified for it " \
                                "in {} population".format(variable, self.id))
            # Create random distribution object
            rand_distr = RandomDistribution(distribution=distr_type, parameters=args)
            # If is an NCML type cell
            if self.celltype.__module__.startswith('ninemlp'):
                variable_scope = [group_varname(seg_group)]
                if component:
                    variable_scope.append(component)
                variable_scope.append(variable)
                self.initialize('.'.join(variable_scope), rand_distr)
            else:
                if seg_group:
                    raise Exception("segmentGroup attribute of parameter distribution '{}' can " \
                                    "only be specified for cells described using NCML, not '{}' " \
                                    "cell types".format(variable, self.celltype.__class__.__name__))
                if component:
                    raise Exception("component attribute of parameter distribution '{}' can only " \
                                    "be specified for cells described using NCML, not '{}' cell " \
                                    "types".format(variable, self.celltype.__class__.__name__))
                self.initialise(variable, rand_distr)
            # Add variable to list of completed variable distributions to check for duplicates
            distributed_conditions.append(variable)

    def set_poisson_spikes(self, rate, start_time, end_time):
        """
        Sets up a train of poisson spike times for a SpikeSourceArray population
        
        @param rate: Rate of the poisson spike train (Hz)
        @param start_time: Start time of the stimulation (ms)
        @param end_time: The end time of the stimulation (ms)
        """
        if self.get_cell_type().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for 'SpikeSourceArray' " \
                            "populations.")
        mean_interval = 1000 / rate # Convert from Hz to ms
        stim_range = end_time - start_time
        if stim_range >= 0.0:
            estimated_num_spikes = stim_range / mean_interval
            # Add extra spikes to make sure spike train doesn't stop short
            estimated_num_spikes = int(estimated_num_spikes + \
                                       math.exp(-estimated_num_spikes / 10.0) * 10.0)
            spike_intervals = numpy.random.exponential(mean_interval,
                                                       size=(self.size, estimated_num_spikes))
            spike_times = numpy.cumsum(spike_intervals, axis=1) + start_time
            # FIXME: Should ensure that spike times don't exceed 'end_time' and make it at least until then.
            self.tset('spike_times', spike_times)
        else:
            print "Warning, stimulation start time ({}) is after stimulation end time ({})".\
                    format(start_time, end_time)

    def set_spikes(self, spike_times):
        """
        Sets up a train of poisson spike times for a SpikeSourceArray population
        
        @param rate: Rate of the poisson spike train
        @param start_time: Start time of the stimulation
        @param end_time: The end time of the stimulation.
        """
        if self.get_cell_type().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for 'SpikeSourceArray' " \
                            "populations.")
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
