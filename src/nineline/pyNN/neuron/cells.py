from __future__ import absolute_import 
try:
    from mpi4py import MPI # @UnresolvedImport @UnusedImport
except:
    pass
import nineline.pyNN.common
from neuron import h
from pyNN.common.control import build_state_queries
import pyNN.neuron.simulator as simulator
import pyNN.models
from nineline.cells.neuron import NineCellMetaClass, NineCell
import logging

logger = logging.getLogger("PyNN")

get_current_time, get_time_step, get_min_delay, \
        get_max_delay, num_processes, rank = build_state_queries(simulator)


class NinePyNNCell(pyNN.models.BaseCellType, NineCell, nineline.pyNN.common.cells.NinePyNNCell):   
    """
    Extends the vanilla NineCell to include all the PyNN requirements
    """
    
    def __init__(self, **parameters):
        NineCell.__init__(self, **parameters)
        # Setup variables used by pyNN
        try:
            self.source_section = self.segments['soma']
        except KeyError:
            print ("WARNING! No 'soma' section specified for {} cell class"
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
        for seg in self.segments.itervalues():
            seg.v = seg.v_init
            
    
    def __getattr__(self, var):
        """
        To support the access to components on particular segments in PyNN the segment name can 
        be prepended enclosed in curly brackets (i.e. '{}').
        
        @param var [str]: var of the attribute, with optional segment segment name enclosed with {} and prepended
        """
        if var.startswith('{'):
            seg_name, comp_name = var[1:].split('}', 1)
            return getattr(self.segments[seg_name], comp_name)
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
        if var.startswith('{'):
            seg_name, comp_name = var[1:].split('}', 1)
            setattr(self.segments[seg_name], comp_name, val)
        else:
            super(NineCell, self).__setattr__(var, val)


class NinePyNNCellMetaClass(nineline.pyNN.common.cells.NinePyNNCellMetaClass):
    
    loaded_celltypes = {}
    
    def __new__(cls, name, nineml_model, build_mode='lazy', silent=False, solver_name=None):
        try:
            celltype = cls.loaded_celltypes[(nineml_model.name, nineml_model.url)]
        except KeyError:
            model = NineCellMetaClass(name, nineml_model, build_mode=build_mode, silent=silent, 
                                      solver_name=solver_name)
            dct = {'model': model,
                   'recordable': model().recordable.keys()}
            celltype = super(NinePyNNCellMetaClass, cls).__new__(cls, name, (NinePyNNCell,), dct)
            # If the url where the celltype is defined is specified save the celltype to be retried later
            if nineml_model.url is not None: 
                cls.loaded_celltypes[(name, nineml_model.url)] = celltype
        return celltype
    