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
import numpy
from neuron import h, nrn, load_mechanisms
from nineline.cells.build.neuron import build_celltype_files
import nineline.cells
from .. import create_unit_conversions, convert_units

import logging

logger = logging.getLogger("NineLine")

_basic_SI_to_neuron_conversions = (('s', 'ms'),
                                   ('V', 'mV'),
                                   ('A', 'nA'),
                                   ('S', 'uS'),
                                   ('F', 'nF'),
                                   ('m', 'um'),
                                   ('Hz', 'Hz'),
                                   ('Ohm', 'MOhm'),
                                   ('M', 'mM'))

_compound_SI_to_neuron_conversions = (((('A', 1), ('m', -2)), (('mA', 1), ('cm', -2))),
                                    ((('F', 1), ('m', -2)), (('uF', 1), ('cm', -2))),
                                    ((('S', 1), ('m', -2)), (('S', 1), ('cm', -2))))


_basic_unit_dict, _compound_unit_dict = create_unit_conversions(_basic_SI_to_neuron_conversions,
                                                                _compound_SI_to_neuron_conversions)

_default_variable_translations = {'Voltage': 'init_v', 'Diameter': 'diam'} #FIXME: This is a little hackish


def convert_to_neuron_units(value, unit_str):
    return convert_units(value, unit_str, _basic_unit_dict, _compound_unit_dict)


class NineCell(nineline.cells.NineCell):

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
                super(NineCell.Segment.ComponentTranslator, self).__setattr__('_component', 
                                                                              component)
                ## The translation of the parameter names            
                super(NineCell.Segment.ComponentTranslator, self).__setattr__('_translations', 
                                                                              translations)
    
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
                    
            def __dir__(self):
                return (super(NineCell.Segment.ComponentTranslator, self).__dir__ + 
                        self._translations.keys())
    
        def __init__(self, nineml_model):
            """
            Initialises the Segment including its proximal and distal sections for connecting child 
            segments
            
            @param seg [common.ncml.MorphMLHandler.Segment]: Segment tuple loaded from MorphML \
                                                             (see common.ncml.MorphMLHandler)
            """
            nrn.Section.__init__(self) #@UndefinedVariable
            h.pt3dclear(sec=self)
            self.diam = float(nineml_model.distal.diameter)
            self._distal = numpy.array((nineml_model.distal.x, nineml_model.distal.y, 
                                        nineml_model.distal.z))
            h.pt3dadd(nineml_model.distal.x, nineml_model.distal.y, nineml_model.distal.z,
                      nineml_model.distal.diameter, sec=self)
            if nineml_model.proximal:
                self._set_proximal((nineml_model.proximal.x, nineml_model.proximal.y,
                                    nineml_model.proximal.z))
            # Set initialisation variables here    
            self.v_init = nineline.cells.DEFAULT_V_INIT
            # A list to store any gap junctions in
            self._gap_junctions = []
            # Local information, though not sure if I need this here
            self.name = nineml_model.name
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
                super(NineCell.Segment, self).__setattr__(var, val)
    
        def _set_proximal(self, proximal):
            """
            Sets the proximal position and calculates the length of the segment
            
            @param proximal [float(3)]: The 3D position of the start of the segment
            """
            self._proximal = numpy.asarray(proximal)
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
    
        def insert(self, component_name, biophysics_name=None, translations=None):
            """
            Inserts a mechanism using the in-built NEURON 'insert' method and then constructs a 
            'Component' class to point to the variable parameters of the component using meaningful 
            names
            
            @param component_name [str]: The name of the component to be inserted
            @param biophysics_name [str]: If the biophysics_name is provided, then it is used as a prefix to the \
                                  component (eg. if biophysics_name='Granule' and component_name='CaHVA', the \
                                  insert mechanism would be 'Granule_CaHVA'), in line with the naming \
                                  convention used for NCML mechanisms
            """
            # Prepend the biophysics_name to the component name if provided
            if biophysics_name:
                mech_name = biophysics_name + "_" + component_name
            else:
                mech_name = component_name
            # Insert the mechanism into the segment
            super(NineCell.Segment, self).insert(mech_name)
            # Map the component (always at position 0.5 as a segment only ever has one "NEURON segment") 
            # to an object in the Segment object. If translations are provided, wrap the component in
            # a Component translator that intercepts getters and setters and redirects them to the 
            # translated values.
            if translations:
                super(NineCell.Segment, self).__setattr__(component_name,
                                                 self.ComponentTranslator(getattr(self(0.5), mech_name),
                                                                          translations))
            else:
                super(NineCell.Segment, self).__setattr__(component_name, getattr(self(0.5), mech_name))

    class Parameter(object):
        
        def __init__(self, name, varname, components):
            self.name = name
            self.varname = varname
            self.components = components
            
        def set(self, value):
            for comp in self.components:
                setattr(comp, self.varname, value)
                
        def get(self):
            if self.components:
                value = getattr(self.components[0], self.varname) 
                for comp in self.components:
                    if value != getattr(comp, self.varname):
                        raise Exception("Found inconsistent values for parameter '{}' ({} and {})"
                                        "across mapped segments"
                                        .format(self.name, value, getattr(comp, self.varname)))
            else:
                raise Exception("Parameter '{}' does not map to any segments ".format(self.name))
            return value        
        
    class InitialState(object):
        
        def __init__(self, name, varname, components):
            self.name = name
            self.varname = varname
            self.components = components
            self.value = None
            
        def set(self, value):
            self.value = value
            
        def initialise_state(self):
            for comp in self.components:
                setattr(comp, self.varname, self.value)
            
        def get(self):
            if self.value is None:
                logger.warning("Tried to retrieve value of initial state '{}' before it was set"
                               .format(self.varname))
            return self.value
                
    def __init__(self, **parameters):
        self._construct_morphology(self.nineml_model.morphology)
        self._map_biophysics_to_morphology(self.nineml_model)
        # Setup variables required by pyNN
        try:
            self.source_section = self.segments['soma']
        except KeyError:
            logger.warning("'soma' section specified for {} cell class, randomly select"
                           .format(self.nineml_model.name))
            self.source_section = next(self.segments.itervalues())
        self.source = self.source_section(0.5)._ref_v
        # for recording
        self.recordable = {'spikes': None, 'v': self.source_section._ref_v}
        for seg_name, seg in self.segments.iteritems():
            self.recordable[seg_name + '.v'] = seg._ref_v 
        self.spike_times = h.Vector(0)
        self.traces = {}
        self.gsyn_trace = {}
        self.recording_time = 0
        self.rec = h.NetCon(self.source, None, sec=self.source_section)
        self._initialized = False
        # Set up references from parameter names to internal variables and set parameters
        self._link_parameters(self.nineml_model)
        self.set_parameters(parameters)
         
    def _construct_morphology(self, nineml_model):
        """
        Reads morphology from a MorphML 2 file and creates the appropriate segments in neuron
        
        @param barebones_only [bool]: If set, extra helper fields will be deleted after the are \
                                      required, leaving the "barebones" pyNEURON structure for \
                                      each nrn.Section
        """
        if not len(nineml_model.segments):
            raise Exception("The loaded morphology does not contain any segments")
        # Initialise all segments
        self.segments = {}
        self.root_segment = None
        for model in nineml_model.segments.values():
            seg = NineCell.Segment(model)
            self.segments[model.name] = seg
            #TODO This should really be part of the 9ML package
            if not model.parent:
                if self.root_segment:
                    raise Exception("Two segments ({0} and {1}) were declared without parents, " 
                                    "meaning the neuronal tree is disconnected"
                                    .format(self.root_segment.name, seg.name))
                self.root_segment = seg
        #TODO And this check too
        if not self.root_segment:
            raise Exception("The neuronal tree does not have a root segment, meaning it is " 
                            "connected in a circle (I assume this is not intended)")
        # Connect the segments together
        for model in nineml_model.segments.values():
            if model.parent:
                self.segments[model.name]._connect(self.segments[model.parent.segment_name],
                                                   model.parent.fraction_along)
        # Work out the segment lengths properly accounting for the "fraction_along". This is 
        # performed via a tree traversal to ensure that the parents 'proximal' field has already 
        # been calculated beforehand
        segment_stack = [self.root_segment]
        while len(segment_stack):
            seg = segment_stack.pop()
            if seg._parent_seg:
                proximal = (seg._parent_seg._proximal * (1 - seg._fraction_along) + 
                            seg._parent_seg._distal * seg._fraction_along)
                seg._set_proximal(proximal)
            segment_stack += seg._children
        # Set up segment classifications for inserting mechanisms
        self.classifications = {}
        for model in nineml_model.classifications.values():
            classification = {}
            for name, cls_model in model.classes.iteritems(): #@UnusedVariable
                seg_class = []
                for member in cls_model.members:
                    try:
                        seg_class.append(self.segments[member.segment_name])
                    except KeyError:
                        raise Exception("Member '{}' (referenced in group '{}') was not found in "
                                        "loaded segments".format(member, cls_model.name))
                classification[cls_model.name] = seg_class
            self.classifications[model.name] = classification
                
    def _map_biophysics_to_morphology(self, nineml_model):
        """
        Loop through loaded currents and synapses, and insert them into the relevant sections.
        """
        for mapping in nineml_model.mappings:
            for comp_name in mapping.components:
                component = nineml_model.biophysics.components[comp_name]
                if component.type == 'membrane-capacitance':
                    cm = convert_to_neuron_units(float(component.parameters['C_m'].value),
                                                 component.parameters['C_m'].unit)[0]
                    for seg_class in mapping.segments:
                        for seg in self.classifications[mapping.segments.classification][seg_class]:
                            seg.cm = cm
                elif component.type == 'defaults':
                    Ra = convert_to_neuron_units(float(component.parameters['Ra'].value),
                                                 component.parameters['Ra'].unit)[0]
                    for seg_class in mapping.segments:
                        for seg in self.classifications[mapping.segments.classification][seg_class]:
                            seg.Ra = Ra
                elif component.type == 'post-synaptic-conductance':
                    hoc_name = nineml_model.biophysics.name + '_' + comp_name
                    if hoc_name in dir(h):
                        SynapseType = getattr(h, hoc_name)
                    else:
                        raise Exception("Did not find '{}' synapse type".format(hoc_name))
                    for seg_class in mapping.segments:
                        for seg in self.classifications[mapping.segments.classification][seg_class]:
                            receptor = SynapseType(0.5, sec=seg)
                            setattr(seg, comp_name, receptor)
                else:
                    if self.component_translations.has_key(comp_name):
                        translations = dict([(key, val[0]) for key, val in
                                             self.component_translations[comp_name].iteritems()])
                    else:
                        translations = None
                    for seg_class in mapping.segments:
                        for seg in self.classifications[mapping.segments.classification][seg_class]:
                            try:
                                seg.insert(comp_name, 
                                           biophysics_name=nineml_model.biophysics.name,
                                           translations=translations)
                            except ValueError as e:
                                raise Exception("Could not insert {mech} into section group {clss} "
                                                "({error})".format(mech=comp_name, error=e, 
                                                                   clss=seg_class))

    def _link_parameters(self, nineml_model):
        self._parameters = {}
        self._initial_states = {}
        for p in nineml_model.parameters:
            if hasattr(self, p.name) and not self.param_links_tested:
                logger.warning("Naming conflict between parameter '{}' and class member of the same"
                               " name. Parameter can be set but will not be able to be retrieved "
                               "except indirectly through the 'segments' attribute. Please consider"
                               " selecting a different name if possible."
                               .format(p.name))
            try:
                varname = _default_variable_translations[p.reference]
            except KeyError:
                varname = p.reference
            components = []
            for seg_class in p.segments:
                segments = self.classifications[p.segments.classification][seg_class]
                if p.component:
                    class_components = [getattr(seg, p.component) for seg in segments]
                else:
                    class_components = segments
            components.extend(class_components)
            if p.type == 'initialState':
                self._initial_states[p.name] = self.InitialState(p.name, varname, components) 
            else:
                self._parameters[p.name] = self.Parameter(p.name, varname, components)
        self.__class__._param_links_tested = True
        
    def set_parameters(self, parameters):
        for name, value in parameters.iteritems():
            try:
                self._parameters[name].set(value)
            except KeyError:
                try:
                    initial_state = self._initial_states[name]
                except KeyError:
                    raise Exception("NineLine celltype '{}' does not have parameter '{}'"
                                    .format(type(self), name))
                    if not self._initialized:
                        initial_state.set(value)
                    else:
                        raise Exception("Attempted to set initial state '{}' after the cell has " 
                                        "been initialised".format(name))

    def get_threshold(self):
        return self.nineml_model.biophysics.components['__NO_COMPONENT__'].parameters['V_t'].value

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
        for state in self._initial_states.itervalues():
            state.initialize_state()
        self._initialized = True
            
    def __getattr__(self, varname):
        """
        To support the access to components on particular segments in PyNN the segment name can 
        be prepended enclosed in curly brackets (i.e. '{}').
         
        @param var [str]: var of the attribute, with optional segment segment name enclosed with {} and prepended
        """
        # Retrieving the _parameters attribute with __getattribute__ first avoids infinite recursive
        # loops of __getattr__.
        parameters = self.__getattribute__('_parameters')
        try:
            return parameters[varname].get()
        except KeyError:
            try:
                return self._initial_states[varname].get()
            except KeyError:
                if varname.startswith('{'):
                    seg_name, comp_name = varname[1:].split('}', 1)
                    return getattr(self.segments[seg_name], comp_name)
                else:
                    raise AttributeError(varname)

    def __setattr__(self, varname, val):
        """
        Any '.'s in the attribute var are treated as delimeters of a nested varspace lookup.
         This is done to allow pyNN's population.tset method to set attributes of cell components.
        
        @param var [str]: var of the attribute or '.' delimeted string of segment, component and \
                          attribute vars
        @param val [*]: val of the attribute
        """
        # Check to see if cell has the '_parameters' attribute, which is initialised last out of the
        # internal member variables, after which the cell is assumed to be initialised and only 
        # parameters can be set as attributes.
        try:
            parameters = self.__getattribute__('_parameters')
        except AttributeError:
            super(NineCell, self).__setattr__(varname, val)
            return
        if parameters.has_key(varname):
            parameters[varname].set(val)
        elif varname.startswith('{'):
            seg_name, comp_name = varname[1:].split('}', 1)
            setattr(self.segments[seg_name], comp_name, val)
        elif varname.endswith('_init'):
            dir(self)
        else:
            raise Exception("Cannot add new attribute '{}' to cell {} class".format(varname, 
                                                                                    type(self)))
        
    def __dir__(self):
        return dir(super(NineCell, self)) + self._parameters.keys()

class NineCellMetaClass(nineline.cells.NineCellMetaClass):
    """
    Metaclass for building NineMLNineCellType subclasses
    Called by nineml_celltype_from_model
    """

    loaded_celltypes = {}

    def __new__(cls, celltype_name, nineml_model, build_mode='lazy', silent=False, solver_name=None): #@UnusedVariable
        try:
            celltype = cls.loaded_celltypes[(nineml_model.name, nineml_model.url)]
        except KeyError:
            dct = {'nineml_model': nineml_model}
            build_options = nineml_model.biophysics.build_hints['nemo']['neuron']
            install_dir, dct['component_translations'] = \
                    build_celltype_files(nineml_model.biophysics.name, nineml_model.url, 
                                         build_mode=build_mode,
                                         method=build_options.method, 
                                         kinetics=build_options.kinetic_components,
                                         silent_build=silent)
            load_mechanisms(install_dir)
            dct['mech_path'] = install_dir
            dct['_param_links_tested'] = False
            celltype = super(NineCellMetaClass, cls).__new__(cls, celltype_name, nineml_model, 
                                                             (NineCell,), dct)
            # Save cell type in case it needs to be used again
            cls.loaded_celltypes[(celltype_name, nineml_model.url)] = celltype
        return celltype


if __name__ == "__main__":
    pass

