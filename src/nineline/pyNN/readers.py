from __future__ import absolute_import
import os.path
import collections
import xml.sax
from nineline import XMLHandler

RANDOM_DISTR_PARAMS = {'uniform': ('low', 'high'),
                       'normal': ('mean', 'stddev')}

class NetworkMLHandler(XMLHandler):

    Network = collections.namedtuple('Network', 'id sim_params populations projections free_params')
    Population = collections.namedtuple('Population', ('id', 'celltype', 'morph_id', 'size',
                                                       'structure', 'cell_params',
                                                       'initial_conditions', 'flags', 'not_flags'))
    Projection = collections.namedtuple('Projection', 'id pre post connection weight delay '
                                                      'synapse_family flags not_flags')
    Structure = collections.namedtuple('Structure', 'type somas args')
    StructureLayout = collections.namedtuple('StructureLayout', 'pattern args distributions')
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
            self.pop_structure = None
            self.pop_cell_params = self.CustomAttributes({}, [])
            self.pop_initial_conditions = self.CustomAttributes({}, [])
            # Split the flags attribute on ',' and remove empty values (the use of filter)            
            self.pop_flags = filter(None, attrs.get('flags', '').replace(' ', '').split(','))
            self.pop_not_flags = filter(None, attrs.get('not_flags', '').replace(' ', '').split(','))
        elif self._opening(tag_name, attrs, 'structure', parents=['population']):
            if self.pop_structure:
                raise Exception("The structure is specified twice in population '{}'".
                                format(self.pop_id))
            args = dict(attrs)
            self.pop_structure_type = args.pop('type')
            self.pop_structure_somas = None
            self.pop_structure_args = args
        elif self._opening(tag_name, attrs, 'somas', parents=['population', 'structure']):
            args = dict(attrs)
            pattern = args.pop('pattern')
            self.pop_structure_somas = self.StructureLayout(pattern, args, [])
        elif self._opening(tag_name, attrs, 'cellParameters', parents=['population']): pass
        elif self._opening(tag_name, attrs, 'initialConditions', parents=['population']): pass
        elif self._opening(tag_name, attrs, 'const', parents=['population', 'cellParameters']):
            self.pop_cell_params.constants[attrs['name']] = float(attrs['value']) # FIXME: Units are ignored here
        elif self._opening(tag_name, attrs, 'const', parents=['population', 'initialConditions']):
            self.pop_cell_params.constants[attrs['name']] = float(attrs['value']) # FIXME: Units are ignored here            
        elif (self._opening(tag_name, attrs, 'distribution', parents=['population',
                                                                      'cellParameters']) or
              self._opening(tag_name, attrs, 'distribution', parents=['population',
                                                                      'initialConditions']) or
              self._opening(tag_name, attrs, 'distribution', parents=['population',
                                                                      'structure',
                                                                      'somas'])):
            args = dict(attrs)
            attribute = args.pop('attr')
            distr_type = args.pop('type')
            units = args.pop('units') if args.has_key('units') else None
            component = args.pop('component') if args.has_key('component') else None
            segmentGroup = args.pop('segmentGroup') if args.has_key('segmentGroup') else None
            try:
                distr_param_keys = RANDOM_DISTR_PARAMS[distr_type]
            except KeyError:
                raise Exception ("Unrecognised distribution type '{type}' used to distribute " 
                                 "cell attribute '{attribute}' in population '{pop}'"
                                 .format(type=distr_type, attribute=attribute, pop=self.id))
            try:
                distr_params = [float(args[arg]) for arg in distr_param_keys]
            except KeyError as e:
                raise Exception ("Missing attribute '{distr_params}' for '{type}' distribution " 
                                 "used to distribute cell attribute '{attribute}' in population " 
                                 "'{pop}'".format(distr_params=e, type=distr_type,
                                                  attribute=attribute, pop=self.id))
            distr = self.Distribution(attribute, distr_type, units, segmentGroup, component,
                                      distr_params)
            if self._open_components[-2] == 'cellParameters':
                self.pop_cell_params.distributions.append(distr)
            elif self._open_components[-2] == 'initialConditions':
                self.pop_initial_conditions.distributions.append(distr)
            elif self._open_components[-2] == 'somas':
                self.pop_structure_somas.distributions.append(distr)                
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
            self.proj_flags = filter(None,
                                     attrs.get('flags', '').replace(' ', '').split(','))
            self.proj_not_flags = filter(None,
                                         attrs.get('not_flags', '').replace(' ', '').split(','))
        elif self._opening(tag_name, attrs, 'source', parents=['projection']):
            if self.proj_pre:
                raise Exception("The pre is specified twice in projection {}'".format(self.proj_id))
            self.proj_pre = self.Source(attrs['id'],
                                        attrs.get('terminal', None),
                                        attrs.get('segment', None))
        elif self._opening(tag_name, attrs, 'destination', parents=['projection']):
            if self.proj_post:
                raise Exception("The destination is specified twice in projection'{}'"
                                .format(self.proj_id))
            self.proj_post = self.Destination(attrs['id'],
                                              attrs.get('synapse', None),
                                              attrs.get('segment', None))
        elif self._opening(tag_name, attrs, 'connection', parents=['projection']):
            if self.proj_connection:
                raise Exception("The connection is specified twice in projection '{}'"
                                .format(self.proj_id))
            args = dict(attrs)
            pattern = args.pop('pattern')
            self.proj_connection = self.Connection(pattern, args)
        elif self._opening(tag_name, attrs, 'weight', parents=['projection']):
            if self.proj_weight:
                raise Exception("The weight is specified twice in projection '{}'"
                                .format(self.proj_id))
            args = dict(attrs)
            pattern = args.pop('pattern')
            self.proj_weight = self.Weight(pattern, args)
        elif self._opening(tag_name, attrs, 'delay', parents=['projection']):
            if self.proj_delay:
                raise Exception("The delay is specified twice in projection '{}'"
                                .format(self.proj_id))
            args = dict(attrs)
            pattern = args.pop('pattern')
            self.proj_delay = self.Delay(pattern, args)

    def endElement(self, name):
        if self._closing(name, 'population', parents=['network']):
            if self.pop_size > -1 and self.pop_structure and self.pop_structure.type == 'Extension':
                raise Exception("Population 'size' attribute cannot be used in conjunction with " 
                                "the 'Extension' type structures because the size of the population"
                                "is determined from the extension")
            self.network.populations.append(self.Population(self.pop_id,
                                                    self.pop_cell,
                                                    self.pop_morph_id,
                                                    self.pop_size,
                                                    self.pop_structure,
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
        elif self._closing(name, 'structure', parents=['population']):
            self.pop_structure = self.Structure(self.pop_structure_type, self.pop_structure_somas,
                                                self.pop_structure_args)
        XMLHandler.endElement(self, name)
# 
# 
# def read_nineml(filename):
#     """
#     Extracts the network specified in the given file and returns a NetworkMLHandler with the parsed 
#     network specification.
#     
#     @param filename: The location of the NINEML-Network file to read the network from.
#     """
#     parser = xml.sax.make_parser()
#     handler = NetworkMLHandler()
#     parser.setContentHandler(handler)
#     parser.parse(os.path.normpath(filename))
#     return handler.network
