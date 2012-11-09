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

import os.path

from neuron import h, nrn, load_mechanisms
import pyNN.models
import pyNN.recording
import ninemlp.common.ncml
from ninemlp.neuron.build import compile_nmodl, build_celltype_files
from ninemlp import DEFAULT_BUILD_MODE
from copy import copy
from operator import attrgetter
import numpy as np
import pyNN.neuron.simulator
import weakref

RELATIVE_NMODL_DIR = 'build/nmodl'

## Used to store the directories from which NMODL objects have been loaded to avoid loading them twice
loaded_celltypes = {}


class Segment(nrn.Section): #@UndefinedVariable
    """
    Wraps the basic NEURON section to allow non-NEURON attributes to be added to the segment.
    Additional functionality could be added as needed
    """
    
    class ComponentTranslator(object):
        """
        Acts as a proxy for the true component that was inserted using NEURON's in built 'insert' 
        method. Used as a way to avoid the unique-identifier prefix that is prepended to NeMo 
        parameters, while allowing the cellname prefix to be dropped from the component, thus 
        providing a cleaner interface
        """
        def __init__(self, component, translations):
    
            ## The translation of the parameter names
            super(Segment.ComponentTranslator, self).__setattr__('_component', component)
            super(Segment.ComponentTranslator, self).__setattr__('_translations', translations)            
    
        def __setattr__(self, var, value):
            try:
                setattr(self._component, self._translations[var], value)
            except AttributeError as e:
                raise AttributeError("Component does not have translation for parameter '{}'".format(e))
    
        def __getattr__(self, var):
            try:        
                return getattr(self._component, self._translations[var])
            except AttributeError as e:
                raise AttributeError("Component does not have translation for parameter '{}'".format(e))
    
    def __init__(self, morphl_seg):
        """
        Initialises the Segment including its proximal and distal sections for connecting child segments
        
        @param seg [common.ncml.MorphMLHandler.Segment]: Segment tuple loaded from MorphML (see common.ncml.MorphMLHandler)
        """
        nrn.Section.__init__(self) #@UndefinedVariable
        h.pt3dclear(sec=self)
        self.diam = float(morphl_seg.distal.diam)
        self._distal = np.array((morphl_seg.distal.x, morphl_seg.distal.y, morphl_seg.distal.z))
        h.pt3dadd(morphl_seg.distal.x, morphl_seg.distal.y, morphl_seg.distal.z,
                                                                 morphl_seg.distal.diam, sec=self)
        if morphl_seg.proximal:
            self._set_proximal((morphl_seg.proximal.x, morphl_seg.proximal.y, morphl_seg.proximal.z))
        # Local information, though not sure if I need this here            
        self.id = morphl_seg.id
        self._parent_seg = None
        self._fraction_along = None
        self._children = []

    def _set_proximal(self, proximal):
        """
        Sets the proximal position and calculates the length of the segment
        
        @param proximal [float(3)]: The 3D position of the start of the segment
        """
        self._proximal = np.array(proximal)
        h.pt3dadd(proximal[0], proximal[1], proximal[2], self.diam, sec=self)

    def _connect(self, parent_seg, fraction_along):
        """
        Connects the segment with its parent, setting its proximal position and calculating its length
        if it needs to.
        
        @param parent_seg [Segment]: The parent segment to connect to
        @param fraction_along [float]: The fraction along the parent segment to connect to
        """
        assert(fraction_along >= 0.0 and fraction_along <= 1.0)
        # Connect the segments in NEURON using h.Section's built-in method.
        self.connect(parent_seg, fraction_along, 0)
        # Store the segment's parent just in case
        self._parent_seg = parent_seg
        self._fraction_along = fraction_along
        parent_seg._children.append(self)

    def insert(self, component_name, cell_id=None, translations=None):
        """
        Inserts a mechanism using the in-built NEURON 'insert' method and then constructs a 'Component'
        class to point to the variable parameters of the component using meaningful names
        
        @param component_name [str]: The name of the component to be inserted
        @param cell_id [str]: If the cell_id is provided, then it is used as a prefix to the component (eg. if cell_id='Granule' and component_name='CaHVA', the insert mechanism would be 'Granule_CaHVA'), in line with the naming convention used for NCML mechanisms
        """
        # Prepend the cell_id to the component name if provided
        if cell_id:
            mech_name = cell_id + "_" + component_name
        else:
            mech_name = component_name
        # Insert the mechanism into the segment
        super(Segment, self).insert(mech_name)
        # Map the component (always at position 0.5 as a segment only ever has one "NEURON segment") 
        # to an object in the Segment object. If translations are provided, wrap the component in
        # a Component translator that intercepts getters and setters and redirects them to the 
        # translated values.
        if translations:
            setattr(self, component_name, self.ComponentTranslator(getattr(self(0.5), mech_name), 
                                                                                    translations))
        else:
            setattr(self, component_name, getattr(self(0.5), mech_name))


class NCMLCell(ninemlp.common.ncml.BaseNCMLCell):

    def __init__(self, **parameters):
        self._init_morphology()
        self._init_biophysics()
        # Setup variables used by pyNN
        self.source = self.soma(0.5)._ref_v
        self.source_section = self.soma
        # for recording
        self.spike_times = h.Vector(0)
        self.traces = {}
        self.gsyn_trace = {}
        self.recording_time = 0
        if parameters.get('parent', False):
            # A weak reference is used to avoid a circular reference that would prevent the garbage 
            # collector from being called on the cell class    
            self.parent = weakref.ref(parameters['parent'])

    def __setattr__(self, name, value):
        """
        Any '.'s in the attribute name are treated as delimeters of a nested namespace lookup of
        <segment-name>.<component-name>.<variable-name>. For attributes not in components the 
        component name can be omitted.
        
        @param name [str]: name of the attribute or '.' delimeted string of segment, component and attribute names
        @param value [*]: value of the attribute
        """
        if '.' in name:
            assert name.count('.') <= 2
            namespace = name.split('.')
            for seg in self.groups[namespace[0]]:
                if len(namespace) == 3:
                    assert seg.nseg == 1
                    setattr(getattr(seg, namespace[1]), namespace[2], value)
                else:
                    setattr(seg, namespace[-1], value)
        else:
            super(NCMLCell, self).__setattr__(name, value)

    def _init_morphology(self, barebones_only=True):
        """
        Reads morphology from a MorphML 2 file and creates the appropriate segments in neuron
        
        @param barebones_only [bool]: If set, extra helper fields will be delted after the are required, leaving the "barebones" pyNEURON structure for each nrn.Section
        """
        # Initialise all segments
        self.segments = {}
        self.groups = { '__all__': [] }
        self.root_segment = None
        for morphml_seg in self.morphml_model.segments:
            seg = Segment(morphml_seg)
            self.segments[morphml_seg.id] = seg
            self.groups['__all__'].append(seg)
            setattr(self, morphml_seg.id, seg)
            if not morphml_seg.parent:
                if self.root_segment:
                    raise Exception("Two segments ({0} and {1}) were declared without parents, meaning the neuronal tree is disconnected".format(self.root_segment.id, seg.id))
                self.root_segment = seg
        if not self.root_segment:
            raise Exception("The neuronal tree does not have a root segment, meaning it is connected in a circle (I assume this is not intended)")
        # Connect the segments together
        for morphml_seg in self.morphml_model.segments:
            if morphml_seg.parent:
                self.segments[morphml_seg.id]._connect(self.segments[morphml_seg.parent.id],
                                                                    morphml_seg.parent.fractionAlong)
        # Work out the segment lengths properly accounting for the "fraction_along". This is performed
        # via a tree traversal to ensure that the parents 'proximal' field has already been calculated
        # beforehand
        segment_stack = [self.root_segment]
        while len(segment_stack):
            seg = segment_stack.pop()
            if seg._parent_seg:
                proximal = seg._parent_seg._proximal * (1 - seg._fraction_along) + \
                                                        seg._parent_seg._distal * seg._fraction_along
                seg._set_proximal(proximal)
            segment_stack += seg._children
        # Once the structure is created with the correct morphology the fields appended to the 
        # nrn.Section class can be disposed of (or potentiall kept for later use). Probably a design
        # decision needs to be made here but I am not sure of the best option at this point
        if barebones_only:
            for seg in self.segments.values():
                del seg._proximal
                del seg._distal
                del seg._parent_seg
                del seg._fraction_along
                del seg._children
        # Set up groups of segments for inserting mechanisms
        for group in self.morphml_model.groups:
            self.groups[group.id] = []
            for member_id in group.members:
                try:
                    self.groups[group.id].append(self.segments[member_id])
                except KeyError:
                    raise Exception('Member id %d (referenced in group ''%s'') was not found in \
                                                           loaded segments' % (member_id, group.id))

    def _init_biophysics(self):
        """
        Loop through loaded currents and synapses, and insert them into the relevant sections.
        """
        if len(self.ncml_model.passive_currents) > 1 and \
                                any(not curr.group_id for curr in self.ncml_model.passive_currents):
            raise Exception("Passive currents is duplicated or conflictingly specified (both \
                                with 'segmentGroup'without 'segmentGroup')")
        if len(self.ncml_model.capacitances) > 1 and \
                                any(not curr.group_id for curr in self.ncml_model.capacitances):
            raise Exception("Membrane capacitance is duplicated or conflictingly specified (both \
                                with 'segmentGroup'without 'segmentGroup')")
        if len(self.ncml_model.axial_resistances) > 1 and \
                                any(not curr.group_id for curr in self.ncml_model.axial_resistances):
            raise Exception("Axial resistance is duplicated or conflictingly specified (both \
                                with 'segmentGroup'without 'segmentGroup')")
        #FIXME: ionic currents and reversal potentials should undergo similar checks but they require
        # the species to be checked as well.
        for curr in self.ncml_model.passive_currents:
            for seg in self.groups[curr.group_id]:
                seg.insert('pas')
                seg.pas.g = curr.cond_density.neuron()
        for curr in sorted(self.ncml_model.currents, key=attrgetter('id')):
            if self.component_parameters.has_key(curr.id):
                translations = dict([(key, val[0]) for key, val in 
                                                    self.component_parameters[curr.id].iteritems()])
            else:
                translations = None                
            for seg in self.groups[curr.group_id]:
                try:
                    seg.insert(curr.id, cell_id=self.ncml_model.celltype_id, 
                                                                        translations=translations)
                except ValueError as e:
                    raise Exception('Could not insert {curr_id} into section group {group_id} \
({error})'.format(curr_id=curr.id, group_id=curr.group_id, error=e))
        #Loop through loaded membrane mechanisms and insert them into the relevant sections.
        for cm in self.ncml_model.capacitances:
            for seg in self.groups[cm.group_id]:
                seg.cm = cm.value.neuron()
        #Loop through loaded membrane mechanisms and insert them into the relevant sections.
        for reversal in self.ncml_model.reversal_potentials:
            for seg in self.groups[reversal.group_id]:
                setattr(seg, 'e' + reversal.species, reversal.value.neuron())
        for ra in self.ncml_model.axial_resistances:
            for seg in self.groups[ra.group_id]:
                seg.Ra = ra.value.neuron()
        for syn in self.ncml_model.synapses:
            if syn.type in dir(h):
                SynapseType = getattr(h, syn.type)
            else:
                try:
                    SynapseType = eval(syn.type) #FIXME (TGC): I don't think that this will ever work.
                except:
                    raise Exception ("Could not find synapse '%s' in loaded or built in synapses." % syn.id)
            for seg in self.groups[syn.group_id]:
                receptor = SynapseType(0.5, sec=seg)
                setattr(seg, syn.id, receptor)
                for param in syn.params:
                    setattr(receptor, param.name, param.value.neuron())
        for syn in self.ncml_model.gap_junctions:
            try:
                GapJunction = eval(syn.type)
            except:
                raise Exception ("Could not find synapse '%s' in loaded or built-in synapses." % syn.id)
            for seg in self.groups[syn.group_id]:
                receptor = SynapseType(0.5, sec=seg)
                setattr(seg, syn.id, receptor)
                for param in syn.params:
                    setattr(receptor, param.name, param.value.neuron())

    def memb_init(self):
        # Initialisation of member states goes here
#        for seg in self.segments:
#            seg.v = self.v_init
        pass

    def get_segments(self):
        return self.segments.values()

    def record(self, *args):
        # If one argument is provided assume that it is the pyNN version of this method 
        # (i.e. map to record_spikes)
        if len(args) == 1:
            assert(self.parent is not None)
            self.record_spikes(args[0])
        elif len(args) == 2:
            variable, output = args
            if variable == 'spikes':
                self.record_spikes(1)
            elif variable == 'v':
                self.record_v(1)
            else:
                raise Exception('Unrecognised variable ''{}'' provided as first argument'.format(
                                                                                         variable))
            pyNN.neuron.simulator.recorder_list.append(self.Recorder(self, variable, output))
        else:
            raise Exception ('Wrong number of arguments, expected either 2 or 3 got {}'.format(
                                                                                    len(args) + 1))

    def record_v(self, active):
        if active:
            self.vtrace = h.Vector()
            self.vtrace.record(self.source_section(0.5)._ref_v)
            if not self.recording_time:
                self.record_times = h.Vector()
                self.record_times.record(h._ref_t)
                self.recording_time += 1
        else:
            self.vtrace = None
            self.recording_time -= 1
            if self.recording_time == 0:
                self.record_times = None

    def record_gsyn(self, syn_name, active):
        # how to deal with static and T-M synapses?
        # record both and sum?
        if active:
            self.gsyn_trace[syn_name] = h.Vector()
            self.gsyn_trace[syn_name].record(getattr(self, syn_name)._ref_g)
            if not self.recording_time:
                self.record_times = h.Vector()
                self.record_times.record(h._ref_t)
                self.recording_time += 1
        else:
            self.gsyn_trace[syn_name] = None
            self.recording_time -= 1
            if self.recording_time == 0:
                self.record_times = None

    def record_spikes(self, active):
        """
        Simple remapping of record onto record_spikes as well
        
        @param active [bool]: Whether the recorder is active or not (required by pyNN)
        """
        if active:
            self.rec = h.NetCon(self.source, None, sec=self.source_section)
            self.rec.record(self.spike_times)
        else:
            self.spike_times = h.Vector(0)

    def set_parameters(self, param_dict):
        for name in self.parameter_names:
            setattr(self, name, param_dict[name])

    def get_threshold(self):
        return self.ncml_model.action_potential_threshold.get('v', 0.0)

    # Create recorder to append to simulator.recorder_list
    class Recorder(pyNN.neuron.Recorder):
        def __init__(self, cell, variable, output):
            self.cell = cell
            self.variable = variable
            self.file = output
            self.population = None
        def _get(self, gather=False, compatible_output=True, filter=None): #@UnusedVariable
            if self.variable == 'spikes':
                data = np.empty((0, 2))
                spikes = np.array(self.cell.spike_times)
                spikes = spikes[spikes <= pyNN.neuron.simulator.state.t + 1e-9]
                if len(spikes) > 0:
                    new_data = np.array([np.ones(spikes.shape) * 0.0, spikes]).T
                    data = np.concatenate((data, new_data))
            elif self.variable == 'v':
                data = np.empty((0, 3))
                v = np.array(self.cell.vtrace)
                t = np.array(self.cell.record_times)
                new_data = np.array([np.ones(v.shape) * 0.0, t, v]).T
                data = np.concatenate((data, new_data))
            if gather and pyNN.neuron.simulator.state.num_processes > 1:
                data = pyNN.recording.gather(data)
            return data

class NCMLMetaClass(ninemlp.common.ncml.BaseNCMLMetaClass):
    """
    Metaclass for building NineMLCellType subclasses
    Called by nineml_celltype_from_model
    """
    def __new__(cls, name, bases, dct):
        #The __init__ function for the created class  
        def cellclass__init__(self, parameters={}):
            pyNN.models.BaseCellType.__init__(self, parameters)
            NCMLCell.__init__(self, **parameters)
        def modelclass__init__(self, **parameters):
            cellclass__init__(self, parameters)
        dct['__init__'] = cellclass__init__
        cellclass = super(NCMLMetaClass, cls).__new__(cls, name, bases, dct)
        dct['__init__'] = modelclass__init__
        cellclass.model = super(NCMLMetaClass, cls).__new__(cls, name, bases, dct)
        cls._validate_recordable(cellclass) #FIXME: This is a bit of a hack
        return cellclass

    @staticmethod
    def _validate_recordable(cell_type):
        """
        This is a bit of a hack method, because I can't work out how to extract from the NMODL
        files only the variables that are actually recordable, so I test them here and remove
        the ones that don't work
        
        @param cell_type: The NCML cell class that needs its recordable variable validated
        """
        test_cell = cell_type()
        test_seg = test_cell.source_section(0.5)
        recordable = copy(cell_type.recordable)
        for var in recordable:
            # Check to see if the variable is part of the common recordables or is an attribute
            # of the test segment. Also remove all reversal potentials (assumed to be all attributes
            # starting with 'e') as they are unlikely to change.
            if (var not in ninemlp.common.ncml.BaseNCMLMetaClass.COMMON_RECORDABLE and \
                                            not hasattr(test_seg, var)) or var.startswith('e'):
                cell_type.recordable.remove(var)


    @classmethod
    def _construct_recordable(cls):
        """
        Constructs the dictionary of recordable parameters from the NCML model
        """
        recordable = copy(ninemlp.common.ncml.BaseNCMLMetaClass.COMMON_RECORDABLE)
        mech_path = cls.dct['mech_path']
        variables = []
        mech_states = {}
        for filename in os.listdir(mech_path):
            split_filename = filename.split('.')
            mech_id = '.'.join(split_filename[0:-1])
            cell_name = mech_id.split('_')[0]
            mech_name = '_'.join(mech_id.split('_')[1:])
            ext = split_filename[-1]
            if cell_name == cls.name and ext == 'mod':
                mod_file_path = os.path.join(mech_path, filename)
                try:
                    mod_file = open(mod_file_path)
                except:
                    raise Exception('Could not open mod file %s for inspection' % mod_file_path)
                in_assigned_block = False
                in_state_block = False
                assigned = []
                states = []
                for line in mod_file:
                    if 'STATE' in line:
                        in_state_block = True
                    elif 'ASSIGNED' in line:
                        in_assigned_block = True
                    elif in_assigned_block:
                        if '}' in line:
                            in_assigned_block = False
                        else:

                            var = line.strip()
                            if var:
                                assigned.append(var)
                    elif in_state_block:
                        if '}' in line:
                            in_state_block = False
                        else:
                            state = line.strip()
                            if state:
                                states.append(state)
                for var in assigned:
                    if var not in recordable:
                        recordable.append(var)
                        variables.append(var)
                for state in states:
                    recordable.append(mech_name + "::" + state)
                    if mech_states.has_key(mech_name):
                        mech_states[mech_name].append(state)
                    else:
                        mech_states[mech_name] = [state]
        # These didn't really work as I had hoped because there are a lot of mechanisms added to the 
        # NMODL files that really shouldn't be, and they are not even accessible through pyNEURON
        # anyway. So these are just included in the class out of interest more than anything 
        # practical now.
        cls.dct['state_variables'] = variables
        cls.dct['mechanism_states'] = mech_states
        return recordable


def load_cell_type(celltype_name, ncml_path, build_mode=DEFAULT_BUILD_MODE, silent=False):
    if loaded_celltypes.has_key(celltype_name):
        celltype, prev_ncml_path = loaded_celltypes[celltype_name]
        if prev_ncml_path != ncml_path:
            raise Exception('A NCML ''{celltype_name}'' cell type has already been loaded from a \
different location, ''{previous}'', than the one provided ''{this}'''.format(
                             celltype_name=celltype_name, previous=prev_ncml_path, this=ncml_path))
    else:
        dct = {}
        dct['ncml_model'] = ninemlp.common.ncml.read_NCML(celltype_name, ncml_path)
        dct['morphml_model'] = ninemlp.common.ncml.read_MorphML(celltype_name, ncml_path)
        build_options = dct['ncml_model'].build_options['nemo']['neuron']
        install_dir, dct['component_parameters'] = build_celltype_files(celltype_name, ncml_path,
                                                                build_mode=build_mode,
                                                                method=build_options.method,
                                                                kinetics=build_options.kinetics,
                                                                silent_build=silent)
        load_mechanisms(install_dir)
        dct['mech_path'] = install_dir
        celltype = NCMLMetaClass(str(celltype_name), (pyNN.models.BaseCellType, NCMLCell), dct)
        # Save cell type in case it needs to be used again
        loaded_celltypes[celltype_name] = (celltype, ncml_path)
    return celltype


if __name__ == "__main__":
    import pprint
    Purkinje = load_cell_type("Purkinje",
                               "/home/tclose/cerebellar/xml/cerebellum/cells/Purkinje.xml")
    purkinje = Purkinje({})
    pprint.pprint(purkinje)
