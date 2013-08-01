import numpy
import os.path
import warnings
import math
import pyNN.connectors
import pyNN.space
import pyNN.parameters
from nine.cells import seg_varname
from pyNN.random import RandomDistribution, NumpyRNG
import nine.trees.point2point as point2point
import nine.trees.morphology as morphology
import nine.trees.space
from .readers import read_networkML

## The location relative to the NINEML-Network file to look for the folder containing the cell descriptions. Should eventually be replaced with a specification in the NINEML-Network declaration itself.
RELATIVE_NCML_DIR = "./ncml"

## The location relative to the NINEML-Network file to look for the folder containing the BRep connectivity descriptions. Should eventually be replaced with a specification in the NINEML-Network declaration itself.
RELATIVE_BREP_DIR = "./brep"

BASIC_PYNN_CONNECTORS = ['AllToAll', 'OneToOne']

_REQUIRED_SIM_PARAMS = ['timestep', 'min_delay', 'max_delay', 'temperature']

class Network(object):
    
    class ProjectionToCloneNotCreatedYetException(Exception): pass

    def __init__(self, filename, build_mode='lazy', timestep=None, min_delay=None,
                 max_delay=None, temperature=None, silent_build=False, flags=[], rng=None, 
                 solver_name='cvode'):
        self.load_network(filename, build_mode=build_mode, timestep=timestep,
                                 min_delay=min_delay, max_delay=max_delay, temperature=temperature,
                                 silent_build=silent_build, flags=flags, rng=rng, 
                                 solver_name=solver_name)

    @classmethod
    def _get_target_str(cls, synapse, segment=None):
        if not segment:
            segment = "source_section"
        return seg_varname(segment) + "." + synapse

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
                    raise Exception("Incorrect number of elements ({}) in flag tuple '{}', " 
                                    "should be 2 (name or name and value)".format(len(flag), flag))
                assert(type(name) == str)
                assert(type(value) == bool)
            if name not in self.flags:
                raise Exception ("Did not find the passed flag '{}' in the Network ML description "
                                 "({})".format(name, self.flags))
            self.flags[name] = value

    def check_flags(self, p):
        try:
            return (all([self.flags[flag] for flag in p.flags]) and
                    all([not self.flags[flag] for flag in p.not_flags]))
        except KeyError as e:
                raise Exception ("Did not find flag '{flag}' used in '{id}' in freeParameters "
                                 "block of NetworkML description".format(flag=e, id=p.id))

    def load_network(self, filename, build_mode='lazy', verbose=False, timestep=None,
                                                min_delay=None, max_delay=None, temperature=None,
                                                silent_build=False, flags=[], rng=None, 
                                                solver_name='cvode'):
        self.networkML = read_networkML(filename)
        self._set_simulation_params(timestep=timestep, min_delay=min_delay, max_delay=max_delay,
                                                                            temperature=temperature)
        self.dirname = os.path.dirname(filename)
        self.pop_dir = os.path.join(self.dirname, RELATIVE_BREP_DIR, 'build', 'populations')
        self.proj_dir = os.path.join(self.dirname, RELATIVE_BREP_DIR, 'build', 'projections')
        self.build_mode = build_mode
        self.label = self.networkML.id
        self._populations = {}
        self._projections = {}
        self.set_flags(flags)
        self._rng = rng if rng else NumpyRNG()
        for pop in self.networkML.populations:
            if self.check_flags(pop):
                self._populations[pop.id] = self._create_population(pop.id,
                                                                    pop.size,
                                                                    pop.cell_type,
                                                                    pop.morph_id,
                                                                    pop.structure,
                                                                    pop.cell_params.constants,
                                                                    pop.cell_params.distributions,
                                                                    pop.initial_conditions.distributions,
                                                                    verbose,
                                                                    silent_build,
                                                                    solver_name=solver_name)
        if build_mode == 'build_only' or build_mode == 'compile_only':
            print ("Finished compiling network, now exiting (use try: ... except SystemExit: ... " 
                   "if you want to do something afterwards)")
            raise SystemExit(0)
        for proj in self.networkML.projections:
            if self.check_flags(proj):
                try:
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
                except self.ProjectionToCloneNotCreatedYetException:
                    self.Network.projections.append(proj)
                    
        self._finalise_construction()

    def _finalise_construction(self):
        """
        Can be overloaded to do any simulator specific finalisation that is required
        """
        pass

    def _create_population(self, label, size, cell_type_name, morph_id, structure_params, cell_params,
                           cell_param_distrs, initial_conditions, verbose, silent_build, 
                           solver_name='cvode'):
        if cell_type_name in dir(self._pyNN_module.standardmodels.cells):
            # This is not as simple as it may have been, as a simple getattr on 
            # pyNN.nest.standardmodels.cells returns the pyNN.standardmodels.cells instead.
            _temp_import = __import__('{}.standardmodels.cells'.format(self._pyNN_module.__name__),
                                       globals(), locals(), [cell_type_name], 0)
            cell_type = getattr(_temp_import, cell_type_name)
        else:
            try:
                cell_type = self._nine_cells_module.load_celltype(
                                        '.'.join(os.path.basename(cell_type_name).split('.')[:-1]),
                                        os.path.join(self.dirname, cell_type_name), 
                                        morph_id=morph_id,
                                        build_mode=self.build_mode,
                                        silent=silent_build,
                                        solver_name=solver_name)
            except IOError:
                raise Exception("Cell_type_name '{}' was not found or " 
                                "in standard models".format(cell_type_name))
        # Set default for populations without morphologies
        positions = None
        structure = None
        morphologies = None
        if structure_params:
            if structure_params.type == 'Distributed':
                somas = structure_params.somas
                if somas:
                    args = somas.args                    
                    if somas.pattern == 'Grid2D':
                        structure = nine.trees.space.Grid2D(aspect_ratio=float(args['aspect_ratio']), 
                                                      dx=float(args['dx']), dy=float(args['dy']), 
                                                      x0=float(args['x0']), y0=float(args['y0']), 
                                                      z=float(args['z']))
                    elif somas.pattern == 'Grid3D':
                        structure = nine.trees.space.Grid3D(aspect_ratioXY=float(args['aspect_ratioXY']), 
                                                      aspect_ratioXZ=float(args['aspect_ratioXZ']), 
                                                      dx=float(args['dx']), dy=float(args['dy']), 
                                                      dz=float(args['dz']), x0=float(args['x0']), 
                                                      y0=float(args['y0']), z0=float(args['z0']))
                    elif somas.pattern == 'UniformWithinBox':
                        boundary = pyNN.space.Cuboid(float(args['length']), float(args['width']), 
                                                           float(args['height']))
                        origin = (float(args['x']), float(args['y']), float(args['z']))
                        structure = pyNN.space.RandomStructure(boundary, origin, rng=self._rng)                        
                    elif somas.pattern == 'UniformWithinSphere':
                        boundary = pyNN.space.Sphere(float(args['radius']))
                        origin = (float(args['x']), float(args['y']), float(args['z']))
                        structure = pyNN.space.RandomStructure(boundary, origin, rng=self._rng)
                    else:
                        raise Exception("Unrecognised pattern '{}' for 'Distributed population "
                                        "structure type".format(somas.pattern))
                    for distr in somas.distributions:
                        try:
                            structure.apply_distribution(distr.attr, distr.type, distr.args, rng=self._rng)
                        except AttributeError:
                            raise Exception("Chosen structure type '{}' does not permit "
                                            "distributions".format(somas.pattern))
                else:
                    raise Exception("Layout tags are required for structure of type "
                                    "'Distributed'") 
            elif structure_params.type == "MorphologyBased":
                forest = morphology.Forest(os.path.join(self.dirname, 
                                                        structure_params.args['morphology']))
                if structure_params.somas:
                    pattern = structure_params.somas.pattern
                    args = structure_params.somas.args
                    if pattern == 'Tiled':
                        forest.align_min_bound_to_origin()
                        base_offset = args.get('offset', numpy.zeros(3))
                        tiling = numpy.array((args.get('x', 1), args.get('y', 1), args.get('z', 1)),
                                             dtype=int)
                        soma_positions = [tree.soma_position() for tree in forest]
                        positions = numpy.zeros((3, len(forest) * tiling.prod()))
                        morphologies = []
                        pos_count = 0
                        for z in xrange(tiling[0]):
                            for y in xrange(tiling[1]):
                                for x in xrange(tiling[2]):
                                    offset = base_offset + forest.max_bounds * (x, y, z)
                                    for tree in forest:
                                        morphologies.append(tree.displaced_tree(offset))
                                    positions[:, pos_count:(pos_count + len(forest))] = \
                                            numpy.transpose(soma_positions + offset)
                    elif pattern == 'DistributedSoma':
                        forest.collapse_to_origin()
                        low = numpy.array((args['low_x'], args['low_y'], args['low_z']), dtype=float)
                        high = numpy.array((args['high_x'], args['high_y'], args['high_z']), dtype=float)
                        size = int(args['size'])
                        span = high - low
                        positions = self._rng.rand(size, 3)
                        positions *= span
                        positions += low
                        positions = positions.transpose()
                        morphologies = []
                        for i in range(size):
                            morphologies.append(forest[i % len(forest)].displaced_tree(positions[:, i]))
                    else:
                        raise Exception("Unrecognised structure_params pattern '{}' in '{}' population"
                                        .format(structure_params.pattern, label))
                    size = len(morphologies)
            elif structure_params.type == "Extension":
                engine = structure_params.args.pop("engine")
                if engine == "Brep":
                    pop_id = structure_params.args['id']
                    if pop_id not in os.listdir(self.pop_dir):
                        raise Exception("Population id '{}' was not found in search " 
                                        "path ({}).".format(pop_id, self.pop_dir))
                    pos_file = os.path.normpath(os.path.join(self.pop_dir, pop_id))
                    try:
                        positions = numpy.loadtxt(pos_file)
                        positions = numpy.transpose(positions)
                        size = positions.shape[1]
                    except:
                        raise Exception("Could not load Brep positions from file '{}'"
                                        .format(pos_file))
                else:
                    raise Exception("Unrecognised external structure_params engine, '{}'".format(engine))
            else:
                raise Exception("Not implemented error, support for built-in structure_params management is "
                                "not done yet.")
        # Actually create the population
        pop = self._Population(label, size, cell_type, params=cell_params,
                                                                        build_mode=self.build_mode)
        # Set structure_params
        if not (self.build_mode == 'build_only' or self.build_mode == 'compile_only'):
            if structure is not None:
                pop._set_structure(structure)
            elif positions is not None:
                pop._set_positions(positions, morphologies)
            pop._randomly_distribute_params(cell_param_distrs, rng=self._rng)
            pop._randomly_distribute_initial_conditions(initial_conditions, rng=self._rng)
        return pop

    def _get_connection_param_expr(self, label, param, min_value=0.0):
        if isinstance(param, float) or param is None:
            param_expr = param
        elif self.is_value_str(param):
            param_expr = self._convert_units(param)
        elif hasattr(param, 'pattern'):
            if param.pattern == "Constant":
                param_expr = self._convert_units(param.args['value'])
            elif param.pattern == 'DisplacementBased':
                expr_name = param.args.pop('geometry')
                GeometricExpression = getattr(point2point, expr_name)
                try:
                    param_expr = pyNN.connectors.DisplacementDependentProbabilityConnector.\
                                     DisplacementExpression(GeometricExpression(min_value=min_value,
                                     **self._convert_all_units(param.args)))
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
                           synapse_family, verbose, allow_self_connections=False):
        # Set expressions for connection weights and delays
        weight_expr = self._get_connection_param_expr(label, weight)
        if synapse_family == 'Electrical':
            allow_self_connections='NoMutual'
        else:
            delay_expr = self._get_connection_param_expr(label, delay,
                                                         min_value=self.get_min_delay())
        # Set up other required connector args
        other_connector_args = {}
        if connection.pattern != "OneToOne":
            other_connector_args['allow_self_connections'] = allow_self_connections
        # Create the "Connector" class to connect up the projection
        if connection.pattern == 'DisplacementBased':
            expression = connection.args.pop('geometry')
            if not hasattr(point2point, expression):
                raise Exception("Unrecognised distance expression '{}'".format(expression))
            try:
                GeometricExpression = getattr(point2point, expression)
                connect_expr = GeometricExpression(**self._convert_all_units(connection.args))
            except TypeError as e:
                raise Exception("Could not initialise distance expression class '{}' from given " 
                                "arguments '{}' for projection '{}'\n('{}')"
                                .format(expression, connection.args, label, e))
            connector = self._pyNN_module.connectors.DisplacementDependentProbabilityConnector(
                                    connect_expr, **other_connector_args)
        elif connection.pattern == 'MorphologyBased':
            kernel_name = connection.args.pop('kernel')
            if not hasattr(morphology, kernel_name + 'Kernel'):
                raise Exception("Unrecognised distance expression '{}'".format(kernel_name))
            try:
                Kernel = getattr(morphology, kernel_name + 'Kernel')
                kernel = Kernel(**self._convert_all_units(connection.args))
            except TypeError as e:
                raise Exception("Could not initialise distance expression class '{}' from given " 
                                "arguments '{}' for projection '{}'\n('{}')"
                                .format(kernel_name, connection.args, label, e))
            connector = nine.trees.morphology.MorphologyBasedProbabilityConnector(
                                                                    kernel, **other_connector_args)
        # If connection pattern is external, load the weights and delays from a file in PyNN
        # FromFileConnector format and then create a FromListConnector connector. Some additional
        # preprocessing is performed here, which is why the FromFileConnector isn't used directly.
        elif connection.pattern == "Extension":
            proj_id = connection.args['id']
            if proj_id not in os.listdir(self.proj_dir):
                raise Exception("Connection id '{}' was not found in search path ({}).".
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
                    warnings.warn("{} out of {} connections are below the minimum delay in "
                                  "projection '{}'. They will be bounded to the minimum delay "
                                  "({})".format(len(below_min_indices), len(delays), label,
                                                self.get_min_delay()))
                # Bound loaded delays by specified minimum delay                        
                delays[below_min_indices] = self.get_min_delay()
            connector = self._pyNN_module.connectors.FromListConnector(connection_matrix,
                                                                       **other_connector_args)
        # Use in-built pyNN connectors for simple patterns such as AllToAll and OneToOne
        # NB: At this stage the pattern name is tied to the connector name in pyNN but could be
        # decoupled from this at some point (but I am not sure you would want to)
        elif connection.pattern == 'Clone':
            orig_proj_id = connection.args['projection']
            try:
                orig_proj = self.get_projection(orig_proj_id)
            except KeyError:
                if orig_proj_id in [p.id for p in self.networkML.projections]:
                    raise self.ProjectionToCloneNotCreatedYetException
                else:
                    raise Exception("Projection '{}' attempted to clone connectivity patterns from "
                                    "'{}', which was not found.".format(label, orig_proj_id))
            connector = self._pyNN_module.connectors.CloneConnector(orig_proj, **other_connector_args)
        elif connection.pattern + 'Connector' in dir(pyNN.connectors):
            ConnectorClass = getattr(self._pyNN_module.connectors,
                                     '{}Connector'.format(connection.pattern))
            connection.args.update(other_connector_args)
            connector = ConnectorClass(**connection.args)
        else:
            raise Exception("Unrecognised pattern type '{}'".format(connection.pattern))
        # Initialise the rest of the projection object and return
        if synapse_family == 'Chemical':
            synapse = self._pyNN_module.StaticSynapse(weight=weight_expr, delay=delay_expr)
            source_terminal = source.terminal
            if target.synapse is None:
                receptor_type = 'excitatory'
            else:
                receptor_type = self._get_target_str(target.synapse, target.segment)
        elif synapse_family == 'Electrical':    
            synapse = self._pyNN_module.ElectricalSynapse(weight=weight_expr)
            source_terminal = source.segment + '_seg'
            receptor_type = target.segment + '_seg.gap'
        else:
            raise Exception("Unrecognised synapse family type '{}'".format(synapse_family))
        projection = self._Projection(pre, dest, label, connector, synapse_type=synapse,
                                            source=source_terminal, target=receptor_type,
                                            build_mode=self.build_mode, rng=self._rng)
        return projection

    def _get_simulation_params(self, **params):
        sim_params = self.networkML.sim_params
        for key in _REQUIRED_SIM_PARAMS:
            if params.has_key(key) and params[key]:
                sim_params[key] = params[key]
            elif not sim_params.has_key(key) or not sim_params[key]:
                raise Exception ("'{}' parameter was not specified either in Network " 
                                 "initialisation or NetworkML specification".format(key))
        return sim_params

    def _convert_units(self, value_str, units=None):
        raise NotImplementedError("_convert_units needs to be implemented by simulator specific " 
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
            if isinstance(proj.synapse_type, pyNN.standardmodels.synapses.ElectricalSynapse):
                attributes = 'weight'
            else:
                attributes = 'all'
            proj.save(attributes, os.path.join(output_dir, proj.label + '.proj'), format='list', gather=True)

    def save_positions(self, output_dir):
        """
        Saves generated cell positions to output directory
        
        @param output_dir:
        """
        for pop in self.all_populations():
            pop.save_positions(os.path.join(output_dir, pop.label) + '.pop')

    def record_spikes(self):
        """
        Record all spikes generated in the network (to be saved to file with Network.print_spikes)
        """
        for pop in self.all_populations():
            pop.record('spikes') #@UndefinedVariable           

    def print_spikes(self, file_prefix):
        """
        Record all spikes generated in the network
        
        @param filename: The prefix for every population files before the popluation name. The \
                         suffix '.spikes' will be appended to the filenames as well.
        """
        # Add a dot to separate the prefix from the population label if it doesn't already have one
        # and isn't a directory
        if (not os.path.isdir(file_prefix) and not file_prefix.endswith('.')
                and not file_prefix.endswith(os.path.sep)):
            file_prefix += '.'
        for pop in self.all_populations():
            pop.write_data(file_prefix + pop.label + '.spikes.pkl', 'spikes') #@UndefinedVariable                

    def write_data(self, file_prefix, **kwargs):
        """
        Record all spikes generated in the network
        
        @param filename: The prefix for every population files before the popluation name. The \
                         suffix '.spikes' will be appended to the filenames as well.
        """
        # Add a dot to separate the prefix from the population label if it doesn't already have one
        # and isn't a directory
        if (not os.path.isdir(file_prefix) and not file_prefix.endswith('.')
                and not file_prefix.endswith(os.path.sep)):
            file_prefix += '.'
        for pop in self.all_populations():
            pop.write_data(file_prefix + pop.label + '.pkl', **kwargs) #@UndefinedVariable
