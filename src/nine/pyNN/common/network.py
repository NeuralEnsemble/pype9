import os.path
from pyNN.random import NumpyRNG
import pyNN.standardmodels
from ..readers import read_networkML
import nine.pyNN.common

## The location relative to the NINEML-Network file to look for the folder containing the cell descriptions. Should eventually be replaced with a specification in the NINEML-Network declaration itself.
RELATIVE_NCML_DIR = "./ncml"

## The location relative to the NINEML-Network file to look for the folder containing the BRep connectivity descriptions. Should eventually be replaced with a specification in the NINEML-Network declaration itself.
RELATIVE_BREP_DIR = "./brep"

BASIC_PYNN_CONNECTORS = ['AllToAll', 'OneToOne']

_REQUIRED_SIM_PARAMS = ['timestep', 'min_delay', 'max_delay', 'temperature']

class Network(object):
    

    def __init__(self, filename, build_mode='lazy', timestep=None, min_delay=None,
                 max_delay=None, temperature=None, silent_build=False, flags=[], rng=None, 
                 solver_name='cvode'):
        self.load_network(filename, build_mode=build_mode, timestep=timestep,
                                 min_delay=min_delay, max_delay=max_delay, temperature=temperature,
                                 silent_build=silent_build, flags=flags, rng=rng, 
                                 solver_name=solver_name)

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
                self._populations[pop.id] = self._Population.factory(pop.id,
                                                                    pop.size,
                                                                    pop.cell_type,
                                                                    pop.morph_id,
                                                                    pop.structure,
                                                                    pop.cell_params.constants,
                                                                    pop.cell_params.distributions,
                                                                    pop.initial_conditions.distributions,
                                                                    self.dirname,
                                                                    self.pop_dir,
                                                                    self._rng,
                                                                    verbose,
                                                                    build_mode,
                                                                    silent_build,
                                                                    solver_name=solver_name)
        if build_mode == 'build_only' or build_mode == 'compile_only':
            print ("Finished compiling network, now exiting (use try: ... except SystemExit: ... " 
                   "if you want to do something afterwards)")
            raise SystemExit(0)
        for proj in self.networkML.projections:
            if self.check_flags(proj):
                try:
                    self._projections[proj.id] = self._Projection.factory(
                                                                 proj.id,
                                                                 self._populations[proj.pre.pop_id],
                                                                 self._populations[proj.post.pop_id],
                                                                 proj.connection,
                                                                 proj.pre,
                                                                 proj.post,
                                                                 proj.weight,
                                                                 proj.delay,
                                                                 proj.synapse_family,
                                                                 self.proj_dir,
                                                                 self._rng,
                                                                 build_mode,
                                                                 self._projections,
                                                                 verbose)
                except nine.pyNN.common.Projection.ProjectionToCloneNotCreatedYetException as e:
                    if e.orig_proj_id in [p.id for p in self.networkML.projections]:
                        self.Network.projections.append(proj)
                    else:
                        raise Exception("Projection '{}' attempted to clone connectivity patterns " 
                                        "from '{}', which was not found in network."
                                        .format(proj.id, e.orig_proj_id))
        self._finalise_construction()

    def _finalise_construction(self):
        """
        Is overriden by deriving classes to do any simulator-specific finalisation that is required
        """
        pass

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
