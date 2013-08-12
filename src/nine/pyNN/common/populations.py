import os.path
import numpy
import pyNN.parameters
import nine.structure.space
import nine.pyNN.structure
from pyNN.random import RandomDistribution

NINEML_STRUCTURES = {'Perturbed2DGrid': nine.pyNN.structure.Perturbed2DGrid}

class Population(object):

    @classmethod
    def factory(cls, model9ml, dirname, pop_dir, rng, verbose=False, 
                build_mode='lazy', silent_build=False, solver_name='cvode'):
        
        # This is a temporary hack until the cell models are fully converted to the 9ml format
        celltype_name = os.path.splitext(os.path.basename(model9ml.prototype.definition.url))[0]
        if '_' in celltype_name:
            name_parts = celltype_name.split('_')
            for i, p in enumerate(name_parts):
                name_parts[i] = p.capitalize()
            celltype_name = ''.join(name_parts)
        try:
            celltype = cls._pyNN_standard_celltypes[celltype_name]
        except KeyError:
#             try:
            celltype = cls._NineCellMetaClass(
                                    '.'.join(os.path.basename(celltype_name).split('.')[:-1]),
                                    os.path.join(dirname, celltype_name), 
                                    morph_id=morph_id,
                                    build_mode=build_mode,
                                    silent=silent_build,
                                    solver_name=solver_name)
#             except IOError:
#                 raise Exception("Cell_type_name '{}' was not found or " 
#                                 "in standard models".format(celltype_name))
        if build_mode not in ('build_only', 'compile_only'):
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
                            structure = nine.structure.space.Grid2D(aspect_ratio=float(args['aspect_ratio']), 
                                                                dx=float(args['dx']), dy=float(args['dy']), 
                                                                x0=float(args['x0']), y0=float(args['y0']), 
                                                                z=float(args['z']))
                        elif somas.pattern == 'Grid3D':
                            structure = nine.structure.space.Grid3D(aspect_ratioXY=float(args['aspect_ratioXY']), 
                                                          aspect_ratioXZ=float(args['aspect_ratioXZ']), 
                                                          dx=float(args['dx']), dy=float(args['dy']), 
                                                          dz=float(args['dz']), x0=float(args['x0']), 
                                                          y0=float(args['y0']), z0=float(args['z0']))
                        elif somas.pattern == 'UniformWithinBox':
                            boundary = pyNN.space.Cuboid(float(args['length']), float(args['width']), 
                                                               float(args['height']))
                            origin = (float(args['x']), float(args['y']), float(args['z']))
                            structure = pyNN.space.RandomStructure(boundary, origin, rng=rng)                        
                        elif somas.pattern == 'UniformWithinSphere':
                            boundary = pyNN.space.Sphere(float(args['radius']))
                            origin = (float(args['x']), float(args['y']), float(args['z']))
                            structure = pyNN.space.RandomStructure(boundary, origin, rng=rng)
                        else:
                            raise Exception("Unrecognised pattern '{}' for 'Distributed population "
                                            "structure type".format(somas.pattern))
                        for distr in somas.distributions:
                            try:
                                structure.apply_distribution(distr.attr, distr.type, distr.args, rng=rng)
                            except AttributeError:
                                raise Exception("Chosen structure type '{}' does not permit "
                                                "distributions".format(somas.pattern))
                    else:
                        raise Exception("Layout tags are required for structure of type "
                                        "'Distributed'") 
                elif structure_params.type == "MorphologyBased":
                    forest = nine.structure.morphology.Forest(os.path.join(dirname, 
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
                            positions = rng.rand(size, 3)
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
                        if pop_id not in os.listdir(pop_dir):
                            raise Exception("Population id '{}' was not found in search " 
                                            "path ({}).".format(pop_id, pop_dir))
                        pos_file = os.path.normpath(os.path.join(pop_dir, pop_id))
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
            pop = cls(size, celltype, cellparams=cellparams, structure=structure, label=label)
            if structure is None and positions is not None:
                pop._set_positions(positions, morphologies)
            pop._randomly_distribute_params(cell_param_distrs, rng=rng)
            pop._randomly_distribute_initial_conditions(initial_conditions, rng=rng)
            return pop
        
    def _randomly_distribute_params(self, cell_param_distrs, rng):
        # Set distributed parameters
        distributed_params = []
        for param, distr_type, units, seg_group, component, args in cell_param_distrs: #@UnusedVariable: Can't work out how to use units effectively at the moment because args may include parameters that don't have units, so ignoring it for now but will hopefully come back to it
            if param in distributed_params:
                raise Exception("Parameter '{}' has two (or more) distributions specified for it " 
                                "in {} population".format(param, self.id))
            # Create random distribution object
            rand_distr = RandomDistribution(distribution=distr_type, parameters=args, rng=rng)
            self.rset(param, rand_distr, component=component, seg_group=seg_group)
            # Add param to list of completed param distributions to check for duplicates
            distributed_params.append(param)

    def _randomly_distribute_initial_conditions(self, initial_conditions, rng):
        # Set distributed parameters
        distributed_conditions = []
        for variable, distr_type, units, seg_group, component, args in initial_conditions: #@UnusedVariable: Can't work out how to use units effectively at the moment because args may include variables that don't have units, so ignoring it for now but will hopefully come back to it
            if variable in distributed_conditions:
                raise Exception("Parameter '{}' has two (or more) distributions specified for it " 
                                "in {} population".format(variable, self.id))
            # Create random distribution object
            rand_distr = RandomDistribution(distribution=distr_type, parameters=args, rng=rng)
            self.initialize_variable(variable, rand_distr, component=component, seg_group=seg_group)
            # Add variable to list of completed variable distributions to check for duplicates
            distributed_conditions.append(variable)

    def set_poisson_spikes(self, rate, start_time, end_time, rng):
        """
        Sets up a train of poisson spike times for a SpikeSourceArray population
        
        @param rate: Rate of the poisson spike train (Hz)
        @param start_time: Start time of the stimulation (ms)
        @param end_time: The end time of the stimulation (ms)
        @param rng: A numpy random state
        """
        if self.get_celltype().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for 'SpikeSourceArray' " 
                            "populations.")
        # If rate is set to zero do nothing
        if rate:
            mean_interval = 1000.0 / rate
            stim_range = end_time - start_time
            if stim_range >= 0.0:
                estimated_num_spikes = stim_range / mean_interval
                # Add extra spikes to make sure spike train doesn't stop short
                estimated_num_spikes = int(estimated_num_spikes + 
                                           numpy.exp(-estimated_num_spikes / 10.0) * 10.0)
                spike_intervals = rng.exponential(mean_interval,
                                                           size=(self.size, estimated_num_spikes))
                spike_times = numpy.cumsum(spike_intervals, axis=1) + start_time
                # FIXME: Should ensure that spike times don't exceed 'end_time' and make it at least until then.
                self.set(spike_times=[pyNN.parameters.Sequence(train) for train in spike_times])
            else:
                print ("Warning, stimulation start time ({}) is after stimulation end time ({})"
                      .format(start_time, end_time))

    def set_spikes(self, spike_times):
        """
        Sets up a train of poisson spike times for a SpikeSourceArray population
        
        @param rate: Rate of the poisson spike train
        @param start_time: Start time of the stimulation
        @param end_time: The end time of the stimulation.
        """
        if self.get_celltype().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for 'SpikeSourceArray' " 
                            "populations.")
        self.tset('spike_times', spike_times)
        
    def set_spatially_dependent_spikes(self):
        pass 

    def get_celltype(self):
        """
        Returns the cell type of the population
        """
        return type(self.celltype)

    def _set_positions(self, positions, morphologies=None):
        super(Population, self)._set_positions(positions)
        self.morphologies = morphologies