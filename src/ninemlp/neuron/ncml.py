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
import ninemlp.common.ncml
from ninemlp.utilities.nmodl import build as build_nnodl
from ninemlp import BUILD_MODE
from backports import any
from pyNN.common.control import build_state_queries
import pyNN.neuron.simulator

get_current_time, get_time_step, get_min_delay, get_max_delay, num_processes, rank = build_state_queries(pyNN.neuron.simulator)

RELATIVE_NMODL_DIR = 'build/nmodl'

## Used to store the directories from which NMODL objects have been loaded to avoid loading them twice
loaded_mech_paths = []

class Segment(nrn.Section): #@UndefinedVariable
    """
    Wraps the basic NEURON section to allow non-NEURON attributes to be added to the segment.
    Additional functionality could be added as needed
    """
    def __init__(self):
        nrn.Section.__init__(self) #@UndefinedVariable   

class NCMLCell(ninemlp.common.ncml.BaseNCMLCell):

    def __init__(self):
        self._init_morphology()
        self._init_biophysics()
        # for recording
        self.spike_times = h.Vector(0)
        self.traces = {}
        self.gsyn_trace = {}
        self.recording_time = 0

    def _init_morphology(self):
        """ Reads morphology from a NeuroML2 file and creates the appropriate segments in neuron"""
        self.segments = {}
        for seg in self.morphml_model.segments:
            sec = Segment()
            self.segments[seg.id] = sec
            setattr(self, seg.id, sec)
            h.pt3dclear(sec=sec)
            if seg.proximal:
                h.pt3dadd(seg.proximal.x, seg.proximal.y, seg.proximal.z, seg.proximal.diam,
                                                                                            sec=sec)
            h.pt3dadd(seg.distal.x, seg.distal.y, seg.distal.z, seg.distal.diam, sec=sec)
        for seg in self.morphml_model.segments:
            if seg.parent:
                self.segments[seg.id].connect(self.segments[seg.parent.id],
                                                                 seg.parent.fractionAlong, 0)
        self.groups = {}
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
            for sec in self.get_group(curr.group_id):
                sec.insert('pas')
                for seg in sec:
                    seg.pas.g = curr.cond_density.neuron()
        for curr in self.ncml_model.currents:
            for sec in self.get_group(curr.group_id):
                sec.insert(curr.id)
        #Loop through loaded membrane mechanisms and insert them into the relevant sections.
        for cm in self.ncml_model.capacitances:
            for sec in self.get_group(cm.group_id):
                sec.cm = cm.value.neuron()
        #Loop through loaded membrane mechanisms and insert them into the relevant sections.
        for reversal in self.ncml_model.reversal_potentials:
            for sec in self.get_group(reversal.group_id):
                setattr(sec, 'e' + reversal.species, reversal.value.neuron())
        for ra in self.ncml_model.axial_resistances:
            for sec in self.get_group(ra.group_id):
                sec.Ra = ra.value.neuron()
        for syn in self.ncml_model.synapses:
            if syn.type in dir(h):
                SynapseType = getattr(h, syn.type)
            else:
                try:
                    SynapseType = eval(syn.type) #FIXME (TGC): I don't think that this will ever work.
                except:
                    raise Exception ("Could not find synapse '%s' in loaded or built in synapses." % syn.id)
            for sec in self.get_group(syn.group_id):
                receptor = SynapseType(0.5, sec=sec)
                setattr(sec, syn.id, receptor)
                for param in syn.params:
                    setattr(receptor, param.name, param.value.neuron())
        for syn in self.ncml_model.gap_junctions:
            try:
                GapJunction = eval(syn.type)
            except:
                raise Exception ("Could not find synapse '%s' in loaded or built-in synapses." % syn.id)
            for sec in self.get_group(syn.group_id):
                receptor = SynapseType(0.5, sec=sec)
                setattr(sec, syn.id, receptor)
                for param in syn.params:
                    setattr(receptor, param.name, param.value.neuron())

    def memb_init(self):
        # Initialisation of member states goes here
#        for sec in self.segments:
#            sec.v = self.v_init
        pass

    def get_group(self, group_id):
        if not group_id:
            group = self.segments.values()
        else:
            group = self.groups[group_id]
        return group


    def record(self, active):
        if active:
            self.rec = h.NetCon(self.source, None, sec=self.source_section)
            self.rec.record(self.spike_times)
        else:
            self.spike_times = h.Vector(0)

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

    def set_parameters(self, param_dict):
        for name in self.parameter_names:
            setattr(self, name, param_dict[name])

    def get_threshold(self):
        return self.ncml_model.action_potential_threshold.get('v', 0.0)


class NCMLMetaClass(ninemlp.common.ncml.BaseNCMLMetaClass):
    """
    Metaclass for building NineMLCellType subclasses
    Called by nineml_celltype_from_model
    """
    def __new__(cls, name, bases, dct):
        #The __init__ function for the created class  
        def __init__(self, parameters={}):
            pyNN.models.BaseCellType.__init__(self, parameters)
            NCMLCell.__init__(self)
            self.source = self.soma(0.5)._ref_v
            self.source_section = self.soma
        dct['__init__'] = __init__
        cell_type = super(NCMLMetaClass, cls).__new__(cls, name, bases, dct)
        cell_type.model = cell_type
        return cell_type


def load_cell_type(name, path_to_xml_file, build_mode=BUILD_MODE):
    dct = {}
    dct['ncml_model'] = ninemlp.common.ncml.read_NCML(name, path_to_xml_file)
    dct['morphml_model'] = ninemlp.common.ncml.read_MorphML(name, path_to_xml_file)
    mech_path = str(os.path.join(os.path.dirname(path_to_xml_file), RELATIVE_NMODL_DIR))
    if mech_path not in loaded_mech_paths:
        build_nnodl(mech_path, build_mode=build_mode)
        load_mechanisms(mech_path)
        loaded_mech_paths.append(mech_path)
    return NCMLMetaClass(str(name), (pyNN.models.BaseCellType, NCMLCell), dct)


if __name__ == "__main__":
    import pprint
    Purkinje = load_cell_type("Purkinje",
                               "/home/tclose/cerebellar/xml/cerebellum/cells/Purkinje.xml")
    purkinje = Purkinje({})
    pprint.pprint(purkinje)
