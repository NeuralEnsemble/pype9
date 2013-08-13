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
from __future__ import absolute_import
from operator import attrgetter
import numpy
import weakref
from neuron import h, nrn, load_mechanisms
from nineline.cells.build.neuron import build_celltype_files
import nineline.cells.readers

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
            ## The true component object that was created by the pyNEURON 'insert' method
            super(Segment.ComponentTranslator, self).__setattr__('_component', component)
            ## The translation of the parameter names            
            super(Segment.ComponentTranslator, self).__setattr__('_translations', translations)

        def __dir__(self):
            return self._translations.keys()

        def __setattr__(self, var, value):
            try:
                setattr(self._component, self._translations[var], value)
            except KeyError as e:
                raise AttributeError("Component does not have translation for parameter '{}'"\
                                     .format(e))

        def __getattr__(self, var):
            try:
                return getattr(self._component, self._translations[var])
            except KeyError as e:
                raise AttributeError("Component does not have translation for parameter '{}'"\
                                     .format(e))

    def __init__(self, morphl_seg):
        """
        Initialises the Segment including its proximal and distal sections for connecting child 
        segments
        
        @param seg [common.ncml.MorphMLHandler.Segment]: Segment tuple loaded from MorphML \
                                                         (see common.ncml.MorphMLHandler)
        """
        nrn.Section.__init__(self) #@UndefinedVariable
        h.pt3dclear(sec=self)
        self.diam = float(morphl_seg.distal.diam)
        self._distal = numpy.array((morphl_seg.distal.x, morphl_seg.distal.y, morphl_seg.distal.z))
        h.pt3dadd(morphl_seg.distal.x, morphl_seg.distal.y, morphl_seg.distal.z,
                  morphl_seg.distal.diam, sec=self)
        if morphl_seg.proximal:
            self._set_proximal((morphl_seg.proximal.x, morphl_seg.proximal.y,
                                morphl_seg.proximal.z))
        # Set initialisation variables here    
        self.v_init = nineline.cells.DEFAULT_V_INIT
        # A list to store any gap junctions in
        self._gap_junctions = []
        # Local information, though not sure if I need this here
        self.id = morphl_seg.id
        self._parent_seg = None
        self._fraction_along = None
        self._children = []

    def __getattr__(self, var):
        """
        Any '.'s in the attribute var are treated as delimeters of a nested varspace lookup. This 
        is done to allow pyNN's population.tset method to set attributes of cell components.
        
        @param var [str]: var of the attribute or '.' delimeted string of segment, component and \
                          attribute vars
        """
        if '.' in var:
            components = var.split('.', 1)
            return getattr(getattr(self, components[0]), components[1])
        else:
            return getattr(self(0.5), var)

    def __setattr__(self, var, val):
        """
        Any '.'s in the attribute var are treated as delimeters of a nested varspace lookup.
        This is done to allow pyNN's population.tset method to set attributes of cell components.
        
        @param var [str]: var of the attribute or '.' delimeted string of segment, component and \
                          attribute vars
        @param val [*]: val of the attribute
        """
        if '.' in var:
            components = var.split('.', 1)
            setattr(getattr(self, components[0]), components[1], val)
        else:
            super(Segment, self).__setattr__(var, val)

    def _set_proximal(self, proximal):
        """
        Sets the proximal position and calculates the length of the segment
        
        @param proximal [float(3)]: The 3D position of the start of the segment
        """
        self._proximal = numpy.array(proximal)
        h.pt3dadd(proximal[0], proximal[1], proximal[2], self.diam, sec=self)

    def _connect(self, parent_seg, fraction_along):
        """
        Connects the segment with its parent, setting its proximal position and calculating its
        length if it needs to.
        
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
        Inserts a mechanism using the in-built NEURON 'insert' method and then constructs a 
        'Component' class to point to the variable parameters of the component using meaningful 
        names
        
        @param component_name [str]: The name of the component to be inserted
        @param cell_id [str]: If the cell_id is provided, then it is used as a prefix to the \
                              component (eg. if cell_id='Granule' and component_name='CaHVA', the \
                              insert mechanism would be 'Granule_CaHVA'), in line with the naming \
                              convention used for NCML mechanisms
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
            super(Segment, self).__setattr__(component_name,
                                             self.ComponentTranslator(getattr(self(0.5), mech_name),
                                                                      translations))
        else:
            super(Segment, self).__setattr__(component_name, getattr(self(0.5), mech_name))


class SegmentGroup(object):

    def __init__(self):
        super(SegmentGroup, self).__setattr__('_segments', [])
        super(SegmentGroup, self).__setattr__('default', None)

    def __iter__(self):
        return iter(self._segments)

    def __len__(self):
        return len(self._segments)

    def __getitem__(self, index):
        return self._segments[index]

    def __setitem__(self, index, value):
        self._segments[index] = value

    def __dir__(self):
        return dir(self.default)

    def append(self, segment, is_default=False):
        assert isinstance(segment, Segment)
        if is_default or not self.default:
            super(SegmentGroup, self).__setattr__('default', segment)
        self._segments.append(segment)

    def __setattr__(self, var, value):
        """
        Set the attribute for all segments in this group
        """
        for seg in self:
            setattr(seg, var, value)

    def __getattr__(self, var):
        """
        Return the value of the default segment in this group
        """
        if not self._segments:
            raise Exception("No segments have been added to this segment group")
        return getattr(self.default, var)


class NineCell(nineline.cells.NineCell):

    class Params(object):

        def __init__(self, params_dict):
            self.__dict__ = params_dict

    def __init__(self, **parameters):
        self._init_morphology()
        self._init_biophysics()
        # Setup variables used by pyNN
        self.source_section = self.default_group.default
        self.source = self.source_section(0.5)._ref_v
        # for recording
        self.recordable = {'spikes': None, 'v': self.source_section._ref_v}
        for seg_id, seg in self.segments.iteritems():
            self.recordable[self.seg_varname(seg_id) + '.v'] = seg._ref_v 
        self.spike_times = h.Vector(0)
        self.traces = {}
        self.gsyn_trace = {}
        self.recording_time = 0
        self.rec = h.NetCon(self.source, None, sec=self.source_section)

#         if parameters.has_key('parent') and parameters['parent'] is not None:
#             # A weak reference is used to avoid a circular reference that would prevent the garbage 
#             # collector from being called on the cell class    
#             self.parent = weakref.ref(parameters['parent'])

    def _init_morphology(self):
        """
        Reads morphology from a MorphML 2 file and creates the appropriate segments in neuron
        
        @param barebones_only [bool]: If set, extra helper fields will be deleted after the are \
                                      required, leaving the "barebones" pyNEURON structure for \
                                      each nrn.Section
        """
        if not len(self.morph_model.segments):
            raise Exception("The loaded morphology does not contain any segments")
        # Initialise all segments
        self.segments = {}
        # Create a group to hold all segments (this is the default group for components that don't 
        # specify a segment group). Create an object to provide 'attribute' route to update 
        # parameter of model via segment groups
        self.all_segs = SegmentGroup()
        self.root_segment = None
        for morphml_seg in self.morph_model.segments:
            if self.segments.has_key(morphml_seg.id):
                raise Exception ("Segment id '{}' conflicts with a previously defined member of " \
                                 "the cell object.".format(morphml_seg.id))
            seg = Segment(morphml_seg)
            self.segments[morphml_seg.id] = seg
            self.all_segs.append(seg)
            setattr(self, self.seg_varname(morphml_seg.id), seg)
            if not morphml_seg.parent:
                if self.root_segment:
                    raise Exception("Two segments ({0} and {1}) were declared without parents, " \
                                    "meaning the neuronal tree is disconnected"\
                                    .format(self.root_segment.id, seg.id))
                self.root_segment = seg
        if not self.root_segment:
            raise Exception("The neuronal tree does not have a root segment, meaning it is " \
                            "connected in a circle (I assume this is not intended)")
        # Connect the segments together
        for morphml_seg in self.morph_model.segments:
            if morphml_seg.parent:
                self.segments[morphml_seg.id]._connect(self.segments[morphml_seg.parent.id],
                                                       morphml_seg.parent.fractionAlong)
        # Work out the segment lengths properly accounting for the "fraction_along". This is 
        # performed via a tree traversal to ensure that the parents 'proximal' field has already 
        # been calculated beforehand
        segment_stack = [self.root_segment]
        while len(segment_stack):
            seg = segment_stack.pop()
            if seg._parent_seg:
                proximal = seg._parent_seg._proximal * (1 - seg._fraction_along) + \
                           seg._parent_seg._distal * seg._fraction_along
                seg._set_proximal(proximal)
            segment_stack += seg._children
        # Set up groups of segments for inserting mechanisms
        self.groups = {}
        self.default_group = None # Will be overwritten in first iteration of loop
        for morphml_group in self.morph_model.groups:
            group = SegmentGroup()
            if morphml_group.id == self.morph_model.default_group or not self.default_group:
                self.default_group = group
            self.groups[morphml_group.id] = group
            setattr(self, self.group_varname(morphml_group.id), group)
            for member_id in morphml_group.members:
                try:
                    group.append(self.segments[member_id],
                                 is_default=(member_id == morphml_group.default))
                except KeyError:
                    raise Exception("Member id {} (referenced in group '{}') was not found in " \
                                    "loaded segments".format(member_id, morphml_group.id))

    def _init_biophysics(self):
        """
        Loop through loaded currents and synapses, and insert them into the relevant sections.
        """
        for mech in sorted(self.memb_model.mechanisms, key=attrgetter('id')):
            if self.component_translations.has_key(mech.id):
                translations = dict([(key, val[0]) for key, val in
                                     self.component_translations[mech.id].iteritems()])
            else:
                translations = None
            for seg in self.get_group(mech.group_id):
                try:
                    seg.insert(mech.id, cell_id=self.memb_model.celltype_id,
                                                                        translations=translations)
                except ValueError as e:
                    raise Exception("Could not insert {mech_id} into section group {group_id} " \
                                    "({error})"
                                    .format(mech_id=mech.id, error=e, 
                                            group_id=mech.group_id if mech.group_id else 'all_segs'))
        #Loop through loaded membrane mechanisms and insert them into the relevant sections.
        for cm in self.memb_model.capacitances:
            for seg in self.get_group(cm.group_id):
                seg.cm = cm.value
        #Loop through loaded membrane mechanisms and insert them into the relevant sections.
        for reversal in self.memb_model.reversal_potentials:
            for seg in self.get_group(reversal.group_id):
                setattr(seg, 'e' + reversal.species, reversal.value)
        for ra in self.memb_model.axial_resistances:
            for seg in self.get_group(ra.group_id):
                seg.Ra = ra.value
        for syn in self.memb_model.synapses:
            hoc_name = self.memb_model.celltype_id + '_' + syn.id
            if hoc_name in dir(h):
                SynapseType = getattr(h, hoc_name)
            else:
                raise Exception("Did not find '{}' synapse type".format(hoc_name))
            for seg in self.get_group(syn.group_id):
                receptor = SynapseType(0.5, sec=seg)
                setattr(seg, syn.id, receptor)

    def __getattr__(self, var):
        """
        Any '.'s in the attribute var are treated as delimeters of a nested varspace lookup. This 
        is done to allow pyNN's population.tset method to set attributes of cell components.
        
        @param var [str]: var of the attribute or '.' delimeted string of segment, component and \
                          attribute vars
        """
        if '.' in var:
            components = var.split('.', 1)
            return getattr(getattr(self, components[0]), components[1])
        else:
            raise AttributeError("'{}'".format(var))

    def __setattr__(self, var, val):
        """
        Any '.'s in the attribute var are treated as delimeters of a nested varspace lookup.
         This is done to allow pyNN's population.tset method to set attributes of cell components.
        
        @param var [str]: var of the attribute or '.' delimeted string of segment, component and \
                          attribute vars
        @param val [*]: val of the attribute
        """
        if '.' in var:
            components = var.split('.', 1)
            setattr(getattr(self, components[0]), components[1], val)
        else:
            super(NineCell, self).__setattr__(var, val)

    def record(self, *args):
        # If one argument is provided assume that it is the pyNN version of this method 
        # (i.e. map to record_spikes)
        if len(args) == 1:
            assert(self.parent is not None)
            self.record_spikes(args[0])
        elif len(args) == 2:
            variable, output = args #@UnusedVariable
            if variable == 'spikes':
                self.record_spikes(1)
            elif variable == 'v':
                self.record_v(1)
            else:
                raise Exception('Unrecognised variable ''{}'' provided as first argument'.\
                                format(variable))
            raise Exception("Not sure how this is meant to work anymore")
#             pyNN.neuron.simulator.recorder_list.append(self.Recorder(self, variable, output))
        else:
            raise Exception ('Wrong number of arguments, expected either 2 or 3 got {}'.\
                             format(len(args) + 1))

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

    def memb_init(self):
        # Initialisation of member states goes here
        for seg in self.all_segs:
            seg.v = seg.v_init


    def set_parameters(self, param_dict):
        for name in self.parameter_names:
            setattr(self, name, param_dict[name])

    def get_threshold(self):
        return self.memb_model.action_potential_threshold.get('v', 0.0)
    
    def get_group(self, group_id):
        return self.groups[group_id] if group_id else self.all_segs    


class NineCellMetaClass(nineline.cells.NineCellMetaClass):
    """
    Metaclass for building NineMLNineCellType subclasses
    Called by nineml_celltype_from_model
    """

    loaded_celltypes = {}

    def __new__(cls, celltype_id, nineml_path, morph_id=None, build_mode='lazy',
                           silent=False, solver_name=None):
        celltype_name = celltype_id
        if morph_id:
            celltype_name += morph_id
        try:
            celltype = cls.loaded_celltypes[(celltype_name, nineml_path)]
        except KeyError:
            dct = {'memb_model': nineline.cells.readers.read_NCML(celltype_id, nineml_path),
                   'morph_model': nineline.cells.readers.read_MorphML(celltype_id, nineml_path, morph_id)}
            build_options = dct['memb_model'].build_options['nemo']['neuron']
            install_dir, dct['component_translations'] = \
                    build_celltype_files(celltype_id, nineml_path, build_mode=build_mode,
                                         method=build_options.method, 
                                         kinetics=build_options.kinetics,
                                         silent_build=silent)
            load_mechanisms(install_dir)
            dct['mech_path'] = install_dir
            celltype = super(NineCellMetaClass, cls).__new__(cls, celltype_name, (NineCell,), dct)
            # Save cell type in case it needs to be used again
            cls.loaded_celltypes[(celltype_name, nineml_path)] = celltype
        return celltype


if __name__ == "__main__":
    pass

