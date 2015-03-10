from __future__ import absolute_import
from datetime import datetime
# MPI may not be required but NEURON sometimes needs to be initialised after
# MPI so I am doing it here just to be safe (and to save me headaches in the
# future)
try:
    from mpi4py import MPI  # @UnusedImport @IgnorePep8 This is imported before NEURON to avoid a bug in NEURON
except ImportError:
    pass
from neuron import h, nrn, load_mechanisms
import neo
import quantities as pq
import os.path
from pype9.cells.code_gen.neuron import CodeGenerator
from pype9.cells.tree import (
    in_units, AxialResistanceModel, MembraneCapacitanceModel,
    IonConcentrationModel)
from pyNN.neuron.cells import VectorSpikeSource
from . import base
from .base import simulation_controller


NeuronSection = type(h.Section())


class MultiCompCell(base.Cell):

    def __init__(self, model=None, **parameters):
        super(base.Cell, self).__init__(model=model)
        # Construct all the NEURON structures
        self._construct()
        # Setup variables required by pyNN
        self.source = self.source_section(0.5)._ref_v
        self.parameters = parameters

        # for recording Once NEST supports sections, it might be an idea to
        # drop this in favour of a more explicit scheme
        self.recordable = {'spikes': None, 'v': self.source_section._ref_v}
        for seg_name, seg in self.segments.iteritems():
            self.recordable['{' + seg_name + '}v'] = seg._ref_v
        self.spike_times = h.Vector(0)
        self.traces = {}
        self.gsyn_trace = {}
        self.recording_time = 0
        self.rec = h.NetCon(self.source, None, sec=self.source_section)
        # Set up references from parameter names to internal variables and set
        # parameters
        self._link_parameters()
        self.set_properties(parameters)

    def _construct(self):
        """
        Reads morphology from a MorphML 2 file and creates the appropriate
        segments in neuron

        @param barebones_only [bool]: If set, extra helper fields will be
                                      deleted after the are required, leaving
                                      the "barebones" pyNEURON structure for
                                      each nrn.Section
        """
        # Initialise all segments
        self.segments = {}
        self.source_section = None
        # Get the set of all component names
        comp_names = reduce(set.union, [set(c.name
                                            for c in m.components)
                                        for m in self._model.segments])
        # Create a empty list for each comp name to contain the segments in it
        self._comp_segments = dict((name, []) for name in comp_names)
        for seg_model in self._model.segments:
            seg = Compartment(seg_model)
            self.segments[seg_model.name] = seg
            if not seg_model.parent:
                assert self.source_section is None
                self.source_section = seg
            # Insert mechanisms and set electrical properties
            required_props = ['Ra', 'cm']
            for comp in seg_model.distributed_components:
                self._comp_segments[comp.name].append(seg)
                if isinstance(comp, AxialResistanceModel):
                    seg.Ra = in_units(comp.value, 'ohm.cm')
                    required_props.remove('Ra')
                elif isinstance(comp, MembraneCapacitanceModel):
                    seg.cm = in_units(comp.value, 'uF/cm^2')
                    required_props.remove('cm')
                else:
                    if comp.name in self.component_translations:
                        translations = dict(
                            [(key, val[0]) for key, val in
                             self.component_translations[comp].iteritems()])
                    else:
                        translations = None
                    seg.insert_distributed(comp, translations=translations)
            for comp in seg_model.discrete_components:
                seg.insert_discrete(comp)
            if required_props:
                raise Exception("The following required properties were not "
                                "set for segment '{}': '{}'"
                                .format(seg_model.name,
                                        "', '".join(required_props)))
        # Connect the segments together
        for seg_model in self._model.segments:
            if seg_model.parent:
                self.segments[seg_model.name]._connect(
                    self.segments[seg_model.parent.name])
        # Set global variables (if there are multiple components of the same
        # class these variables will be set multiple times but that shouldn't
        # hurt
        for comp in self._model.components.itervalues():
            for param, val in comp.global_parameters.iteritems():
                h('{}_{} = {}'.format(param, comp.class_name, val))

    def get_threshold(self):
        return in_units(self._model.spike_threshold, 'mV')

    def memb_init(self):
        if 'initial_v' in self.parameters:
            for seg in self.segments.itervalues():
                seg.v = self.parameters['initial_v']
        for param in self._parameters.itervalues():
            if isinstance(param, self.InitialState):
                param.initialize_state()
# 
#     def _link_parameters(self):
#         self._parameters = {}
#         # FIXME: this assumes the source is a 9ml model
#         for p in self._model._source.parameters:
#             if hasattr(self, p.name) and not self.param_links_tested:
#                 logger.warning("Naming conflict between parameter '{}' and "
#                                "class member of the same name. Parameter can "
#                                "be set but will not be able to be retrieved "
#                                "except indirectly through the 'segments' "
#                                "attribute. Please consider selecting a "
#                                "different name if possible.".format(p.name))
#             try:
#                 varname = basic_nineml_translations[p.reference]
#             except KeyError:
#                 varname = p.reference
#             components = []
#             for seg_class in p.segments:
#                 segments = self.classifications[p.segments.
#                                                 classification][seg_class]
#                 if p.component:
#                     class_components = [getattr(seg, p.component)
#                                         for seg in segments]
#                 else:
#                     class_components = segments
#             components.extend(class_components)
#             ParamClass = (self.InitialState if p.type == 'initialState'
#                           else self.Parameter)
#             self._parameters[p.name] = ParamClass(p.name, varname, components)
#         self.__class__._param_links_tested = True

    def set_properties(self, parameters):
        for name, value in parameters.iteritems():
            try:
                self._parameters[name].set(value)
            except KeyError:
                raise Exception("NineLine celltype '{}' does not have "
                                "parameter '{}'".format(type(self), name))

    def __getattr__(self, varname):
        """
        To support the access to components on particular segments in PyNN the
        segment name can be prepended enclosed in curly brackets (i.e. '{}').

        @param var [str]: var of the attribute, with optional segment segment
                          name enclosed with {} and prepended
        """
        # Retrieving the _parameters attribute with __getattribute__ first
        # avoids infinite recursive loops of __getattr__ if the cell hasn't
        # been initialised yet.
        parameters = self.__getattribute__('prototype')
        try:
            return parameters[varname].get()
        except KeyError:
            if varname.startswith('{'):
                seg_name, comp_name = varname[1:].split('}', 1)
                return getattr(self.segments[seg_name], comp_name)
            else:
                raise AttributeError(varname)

    def __setattr__(self, varname, val):
        """
        Any '.'s in the attribute var are treated as delimeters of a nested
        varspace lookup. This is done to allow pyNN's population.tset method to
        set attributes of cell components.

        @param var [str]: var of the attribute or '.' delimeted string of
                          segment, component and attribute vars
        @param val [*]: val of the attribute
        """
        # Check to see if cell has the '_parameters' attribute, which is
        # initialised last out of the internal member variables, after which
        # the cell is assumed to be initialised and only parameters can be set
        # as attributes.
        try:
            parameters = self.__getattribute__('_parameters')
        except AttributeError:
            super(MultiCompCell, self).__setattr__(varname, val)
            return
        # If the varname is a parameter
        if varname in parameters:
            parameters[varname].set(val)
        # Any attribute that ends with '_init' is assumed to be an initial
        # state (this is how PyNN sets neuron initial states)
        elif varname.endswith('_init'):
            try:
                parameter = parameters[varname[:-5]]
            except KeyError:
                raise Exception("Cell does not have initial state '{}' (as "
                                "specified by attempting to set '{}' on the "
                                "cell)".format(varname[:-5], varname))
            if not isinstance(parameter, self.InitialState):
                raise Exception("Parameter '{}' is not an initial state (as "
                                "specified by attempting to set '{}' on the "
                                "cell)" .format(varname[:-5], varname))
            parameter.set(val)
        # Component parameters can also be directly accessed (without the need
        # to specify them explicitly as a parameter) by placing the segment
        # name in brackets beforehand, then using a '.' to separate the
        # component name from the parameter name if required, i.e.
        #
        # {segment}component.parameter for a parameter of a component
        #
        # or
        #
        # {segment}parameter for a parameter of the segment directly
        #
        elif varname.startswith('{'):
            seg_name, comp_name = varname[1:].split('}', 1)
            setattr(self.segments[seg_name], comp_name, val)
        else:
            # TODO: Need to work out if I want this to throw an error or not.
            super(MultiCompCell, self).__setattr__(varname, val)
#             raise Exception("Cannot add new attribute '{}' to cell {} class"
#                               .format(varname, type(self)))

#     def __getattr__(self, varname):
#         """
#         First test to see if varname is a segment name and if so return the
#         segment else fall back to
# 
#         @param var [str]: var of the attribute, with optional segment segment
#                           name enclosed with {} and prepended
#         """
#         if '.' in varname:
#             parts = varname.split('.')
#             if len(parts) == 2:
#                 comp_name, var = parts
#                 # TODO: Just looking at the first segment is a dirty hack,
#                 #       should have a separate component object that is stored
#                 #       at cell level with a value and a list of segments to
#                 #       set
#                 val = getattr(self._comp_segments[comp_name][0], var)
#                 assert all([getattr(seg, var) == val
#                             for seg in self._comp_segments[comp_name]]), \
#                        "Accessing value of component when values have been " \
#                        "set independently"
#                 return val
#             elif len(parts) == 3:
#                 seg, comp_name, var = parts
#                 return getattr(getattr(self.segments[seg], comp_name), var)
#             else:
#                 raise AttributeError('Invalid number of components ({})'
#                                      .format(len(parts)))
#         else:
#             try:
#                 return self.segments[varname]
#             except KeyError:
#                 super(MultiCompCellStandAlone, self).__getattribute__(varname)
# 
#     def __setattr__(self, varname, value):
#         """
#         First test to see if varname is a segment name and if so return the
#         segment else fall back to
# 
#         @param var [str]: var of the attribute, with optional segment segment
#                           name enclosed with {} and prepended
#         """
#         # Although '.'s will only part of the varname if setattr is called
#         # explicitly. This allows a variables to be accessed at either the
#         # segment specific level or the component level.
#         if '.' in varname:
#             parts = varname.split('.')
#             if len(parts) == 2:
#                 comp_name, var = parts
#                 try:
#                     for seg in self._comp_segments[comp_name]:
#                         setattr(getattr(seg, comp_name), var, value)
#                 except KeyError:
#                     raise AttributeError("Cell derived from model '{}' does "
#                                          "not have component '{}'."
#                                          .format(self._model.name,
#                                                  comp_name))
#             elif len(parts) == 3:
#                 segment, comp_name, var = parts
#                 setattr(getattr(segment, comp_name), var, value)
#             else:
#                 raise AttributeError("Invalid number of components ({}), "
#                                      "can be either 2 (segment group or "
#                                      "name, variable) or 3 (segment group "
#                                      "or name, component, variable)"
#                                      .format(len(parts)))
#         else:
#             super(MultiCompCellStandAlone, self).__setattr__(varname, value)

    def __dir__(self):
        return dir(super(MultiCompCell, self)) + self._parameters.keys()

    def record(self, variable, segname=None, component=None):
        self._initialise_local_recording()
        if segname is None:
            seg = self.source_section
        else:
            try:
                seg = self.segments[segname]
            except KeyError:
                raise Exception("Did not find segment '{}' in cell morphology"
                                .format(segname))
        key = (variable, segname, component)
        if variable == 'spikes':
            self._recorders[key] = recorder = h.NetCon(seg._ref_v, None,
                                                       self.get_threshold(),
                                                       0.0, 1.0,
                                                       sec=seg)
            self._recordings[key] = recording = h.Vector()
            recorder.record(recording)
        else:
            container = getattr(seg, component) if component else seg
            pointer = getattr(container, '_ref_' + variable)
            self._recordings[key] = recording = h.Vector()
            recording.record(pointer)
#             if not self._recordings.has_key('time'):
#                 self._recordings['time'] = time_recording = h.Vector()
#                 time_recording.record(h._ref_t)

    def get_recording(self, variables=None, segnames=None, components=None,
                      in_block=False):
        """
        Gets a recording or recordings of previously recorded variable

        `variables`  -- the name of the variable or a list of names of
                        variables to return [str | list(str)]
        `segnames`   -- the segment name the variable is located or a list of
                        segment names (in which case length must match number
                        of variables) [str | list(str)]. "None" variables will
                        be translated to the 'source_section' segment
        `components` -- the component name the variable is part of or a list
                        of components names (in which case length must match
                        number of variables) [str | list(str)]. "None"
                        variables will be translated as segment variables
                        (i.e. no component)
        `in_block`   -- returns a neo.Block object instead of a neo.SpikeTrain
                        neo.AnalogSignal object (or list of for multiple
                        variable names)
        """
        return_single = False
        if variables is None:
            if segnames is None:
                raise Exception("As no variables were provided all recordings "
                                "will be returned, soit doesn't make sense to "
                                "provide segnames")
            if components is None:
                raise Exception("As no variables were provided all recordings "
                                "will be returned, so it doesn't make sense to"
                                " provide components")
            variables, segnames, components = zip(*self._recordings.keys())
        else:
            if isinstance(variables, basestring):
                variables = [variables]
                return_single = True
            if isinstance(segnames, basestring) or segnames is None:
                segnames = [segnames] * len(variables)
            if isinstance(components, basestring) or components is None:
                components = [components] * len(segnames)
        if in_block:
            segment = neo.Segment(rec_datetime=datetime.now())
        else:
            recordings = []
        for key in zip(variables, segnames, components):
            if key[0] == 'spikes':
                spike_train = neo.SpikeTrain(self._recordings[key],
                                             t_start=0.0 * pq.ms,
                                             t_stop=h.t * pq.ms, units='ms')
                if in_block:
                    segment.spiketrains.append(spike_train)
                else:
                    recordings.append(spike_train)
            else:
                if key[0] == 'v':
                    units = 'mV'
                else:
                    units = 'nA'
                analog_signal = neo.AnalogSignal(self._recordings[key],
                                                 sampling_period=h.dt * pq.ms,
                                                 t_start=0.0 * pq.ms,
                                                 name='.'.join(
                                                     [x for x in key
                                                      if x is not None]),
                                                 units=units)
                if in_block:
                    segment.analogsignals.append(analog_signal)
                else:
                    recordings.append(analog_signal)
        if in_block:
            data = neo.Block(description="Recording from NineLine stand-alone "
                                         "cell")
            data.segments = [segment]
            return data
        elif return_single:
            return recordings[0]
        else:
            return recordings

    def reset_recordings(self):
        """
        Resets the recordings for the cell and the NEURON simulator (assumes
        that only one cell is instantiated)
        """
        for rec in self._recordings.itervalues():
            rec.resize(0)

    def clear_recorders(self):
        """
        Clears all recorders and recordings
        """
        self._recorders = {}
        self._recordings = {}

    def _initialise_local_recording(self):
        if not hasattr(self, '_recorders'):
            self._recorders = {}
            self._recordings = {}
            simulation_controller.register_cell(self)


class MultiCompCellMetaClass(base.CellMetaClass):

    """
    Metaclass for building NineMLCellType subclasses Called by
    nineml_celltype_from_model
    """

    _built_types = {}
    CodeGenerator = CodeGenerator
    BaseCellClass = MultiCompCell

    @classmethod
    def load_model(cls, name, install_dir):  # @UnusedVariable @NoSelf
        load_mechanisms(os.path.dirname(install_dir))


class Compartment(NeuronSection):
    """
    Wraps the basic NEURON section to allow non-NEURON attributes to be
    added to the segment. Additional functionality could be added as needed
    """

    def __init__(self, model):
        """
        Initialises the Compartment including its proximal and distal sections
        for connecting child segments

        """
        nrn.Section.__init__(self)  # @UndefinedVariable
        h.pt3dclear(sec=self)
        self.diam = float(model.diameter)
        # Save the proximal and distal points for possible future reference
        self.distal = model.distal
        self.proximal = model.proximal
        # Set proximal and distal points in NEURON
        h.pt3dadd(model.distal[0], model.distal[1],
                  model.distal[2], model.diameter,
                  sec=self)
        h.pt3dadd(model.proximal[0], model.proximal[1],
                  model.proximal[2], model.diameter,
                  sec=self)
        # A list to store any gap junctions in
        self._gap_junctions = []
        self._syn_input = []
        # Local information, though not sure if I need this here
        self.name = model.name
        self._parent_seg = None
        if 'proximal_offset' in model.get_content():
            self._proximal_offset = model.get_content()['proximal_offset']
        else:
            self._proximal_offset = None
        self._children = []

    def __getattr__(self, var):
        """
        Any '.'s in the attribute var are treated as delimeters of a nested
        varspace lookup. This is done to allow pyNN's population.tset
        method to set attributes of cell components.

        @param var [str]: var of the attribute or '.' delimeted string of
                          segment, component and attribute vars
        """
        if '.' in var:
            components = var.split('.', 1)
            return getattr(getattr(self, components[0]), components[1])
        else:
            return getattr(self(0.5), var)

    def __setattr__(self, var, val):
        """
        Any '.'s in the attribute var are treated as delimeters of a nested
        varspace lookup. This is done to allow pyNN's population.tset
        method to set attributes of cell components.

        @param var [str]: var of the attribute or '.' delimeted string of
                          segment, component and attribute vars
        @param val [*]: val of the attribute
        """
        if '.' in var:
            components = var.split('.', 1)
            setattr(getattr(self, components[0]), components[1], val)
        else:
            super(Compartment, self).__setattr__(var, val)

    def _connect(self, parent_seg):
        """
        Connects the segment with its parent, setting its proximal position
        and calculating its length if it needs to.

        @param parent_seg [Compartment]: The parent segment to connect to
        """
        # Connect the segments in NEURON using h.Section's built-in method.
        self.connect(parent_seg, 1.0, 0)
        # Store the segment's parent just in case
        self._parent_seg = parent_seg
        parent_seg._children.append(self)

    def insert_distributed(self, component, translations=None):
        """
        Inserts a mechanism using the in-built NEURON 'insert' method and
        then constructs a 'Component' class to point to the variable
        parameters of the component using meaningful names

        `component` -- The component to be inserted
                      [pype9.BiophysicsModel]
        """
        # Insert the mechanism into the segment
        super(Compartment, self).insert(component.class_name)
        # Map the component (always at position 0.5 as a segment only ever
        # has one "NEURON segment") to an object in the Compartment object. If
        # translations are provided, wrap the component in a Component
        # translator that intercepts getters and setters and redirects them
        # to the translated values.
        if translations:
            super(Compartment, self).__setattr__(
                component.name, self.ComponentTranslator(
                    getattr(self(0.5), component.class_name),
                    translations))
        else:
            super(Compartment, self).__setattr__(
                component.name, getattr(self(0.5), component.class_name))
        if isinstance(component, IonConcentrationModel):
            setattr(self, component.param_name,
                    component.parameters[component.param_name])
        else:
            inserted_comp = getattr(self, component.class_name)
            for param, val in component.iterate_parameters(self):
                setattr(inserted_comp, param, val)

    def insert_discrete(self, component):
        """
        Inserts discrete (point-process) objects like synapses and current
        clamps
        """
        try:
            HocClass = getattr(h, component.class_name)
        except AttributeError:
            raise Exception("Did not find '{}' point-process type"
                            .format(component.class_name))
        discrete_comp = HocClass(0.5, sec=self)
        for param, val in component.iterate_parameters(self):
            setattr(discrete_comp, param, val)
        try:
            getattr(self, component.name).append(discrete_comp)
            # TypeError if the component.class_name == component.name and
            # has already inserted a mechanism of the same name and
            # AttributeError otherwise
        except (AttributeError, TypeError):
            comp_list = [discrete_comp]
            setattr(self, component.name, comp_list)

    def inject_current(self, current):
        """
        Injects current into the segment

        `current` -- a vector containing the current [neo.AnalogSignal]
        """
        self.iclamp = h.IClamp(0.5, sec=self)
        self.iclamp.delay = 0.0
        self.iclamp.dur = 1e12
        self.iclamp.amp = 0.0
        self.iclamp_amps = h.Vector(pq.Quantity(current, 'nA'))
        self.iclamp_times = h.Vector(pq.Quantity(current.times, 'ms'))
        self.iclamp_amps.play(self.iclamp._ref_amp, self.iclamp_times)

    def voltage_clamp(self, voltages, series_resistance=1e-3):
        """
        Clamps the voltage of a segment

        `voltage` -- a vector containing the voltages to clamp the segment
                     to [neo.AnalogSignal]
        """
        self.seclamp = h.SEClamp(0.5, sec=self)
        self.seclamp.rs = series_resistance
        self.seclamp.dur1 = 1e12
        self.seclamp_amps = h.Vector(pq.Quantity(voltages, 'mV'))
        self.seclamp_times = h.Vector(pq.Quantity(voltages.times, 'ms'))
        self.seclamp_amps.play(self.seclamp._ref_amp, self.seclamp_times)

    def synaptic_stimulation(self, spike_train, synapse_name, index=0):
        synapse = getattr(self, synapse_name)[index]
        vecstim = VectorSpikeSource(spike_train)
        netcon = h.NetCon(vecstim, synapse, sec=self)
        self._syn_input.append((vecstim, netcon))


class ComponentTranslator(object):

    """
    Acts as a proxy for the true component that was inserted using
    NEURON's in built 'insert' method. Used as a way to avoid the
    unique-identifier prefix that is prepended to NeMo parameters,
    while allowing the cellname prefix to be dropped from the
    component, thus providing a cleaner interface
    """

    def __init__(self, component, translations):
        # The true component object that was created by the pyNEURON
        # 'insert' method
        super(ComponentTranslator, self).__setattr__('_component',
                                                     component)
        # The translation of the parameter names
        super(Compartment.ComponentTranslator,
              self).__setattr__('_translations', translations)

    def __setattr__(self, var, value):
        try:
            setattr(self._component, self._translations[var], value)
        except KeyError as e:
            raise AttributeError("Component does not have translation"
                                 " for parameter {}".format(e))

    def __getattr__(self, var):
        try:
            return getattr(self._component, self._translations[var])
        except KeyError as e:
            raise AttributeError("Component does not have translation"
                                 "for parameter {}".format(e))

    def __dir__(self):
        return (super(Compartment.ComponentTranslator,
                      self).__dir__ + self._translations.keys())
