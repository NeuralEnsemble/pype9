if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
# from pype9.cells.neuron import CellMetaClass
from os import path
from utils import test_data_dir
import neuron
import pylab as plt
# from pyNN.neuron.cells import Izhikevich_ as IzhikevichPyNN

import collections
# MPI may not be required but NEURON sometimes needs to be initialised after
# MPI so I am doing it here just to be safe (and to save me headaches in the
# future)
from neuron import h, nrn, load_mechanisms
import os.path
from pype9.cells.code_gen.neuron import CodeGenerator
from math import pi


def _new_property(obj_hierarchy, attr_name):
    """
    Returns a new property, mapping attr_name to obj_hierarchy.attr_name.

    For example, suppose that an object of class A has an attribute b which
    itself has an attribute c which itself has an attribute d. Then placing
      e = _new_property('b.c', 'd')
    in the class definition of A makes A.e an alias for A.b.c.d
    """
    def set(self, value):
        obj = reduce(getattr, [self] + obj_hierarchy.split('.'))
        setattr(obj, attr_name, value)
    def get(self):
        obj = reduce(getattr, [self] + obj_hierarchy.split('.'))
        return getattr(obj, attr_name)
    return property(fset=set, fget=get)


class BaseSingleCompartmentNeuron(nrn.Section):
    """docstring"""

    def __init__(self, c_m, i_offset):

        # initialise Section object with 'pas' mechanism
        nrn.Section.__init__(self)
        self.seg = self(0.5)
        self.L = 100
        self.seg.diam = 1000/pi  # gives area = 1e-3 cm2

        self.source_section = self

        # insert current source
        self.stim = h.IClamp(0.5, sec=self)
        self.stim.delay = 0
        self.stim.dur = 1e12
        self.stim.amp = i_offset

        # for recording
        self.spike_times = h.Vector(0)
        self.traces = {}
        self.recording_time = 0

        self.v_init = None

    def area(self):
        """Membrane area in"""
        return pi*self.L*self.seg.diam

    c_m      = _new_property('seg', 'cm')
    i_offset = _new_property('stim', 'amp')

    def memb_init(self):
        assert self.v_init is not None, "cell is a %s" % self.__class__.__name__
        for seg in self:
            seg.v = self.v_init
        #self.seg.v = self.v_init

    def set_parameters(self, param_dict):
        for name in self.parameter_names:
            setattr(self, name, param_dict[name])


class IzhikevichPyNN(BaseSingleCompartmentNeuron):
    """docstring"""

    def __init__(self, a_=0.02, b=0.2, c=-65.0, d=2.0, i_offset=0.0):
        BaseSingleCompartmentNeuron.__init__(self, 1.0, i_offset)
        self.L = 10
        self.seg.diam = 10/pi
        self.c_m = 1.0

        # insert Izhikevich mechanism
        self.izh = h.Izhikevich(0.5, sec=self)
        self.source = self.izh
        self.rec = h.NetCon(self.seg._ref_v, None,
                            self.get_threshold(), 0.0, 0.0,
                            sec=self)
        self.excitatory = self.inhibitory = self.source

        self.parameter_names = ['a_', 'b', 'c', 'd', 'i_offset']
        self.set_parameters(locals())
        self.u_init = None

    a_ = _new_property('izh', 'a')
    b = _new_property('izh', 'b')
    c = _new_property('izh', 'c')
    d = _new_property('izh', 'd')
    ## using 'a_' because for some reason, cell.a gives the error "NameError: a, the mechanism does not exist at PySec_170bb70(0.5)"

    def record(self, active):
        if active:
            self.rec = h.NetCon(self.seg._ref_v, None,
                                self.get_threshold(), 0.0, 0.0,
                                sec=self)
            self.rec.record(self.spike_times)

    def get_threshold(self):
        return self.izh.vthresh

    def memb_init(self):
        assert self.v_init is not None, "cell is a %s" % self.__class__.__name__
        assert self.u_init is not None
        for seg in self:
            seg.v = self.v_init
            seg.u = self.u_init


class TestNeuronLoad(TestCase):

    izhikevich_file = path.join(test_data_dir, 'xml', 'Izhikevich2003.xml')
    izhikevich_name = 'Izhikevich9ML'

    def test_neuron_load(self):
#         Izhikevich9ML = CellMetaClass(self.izhikevich_file,
#                                       name=self.izhikevich_name,
#                                       build_mode='compile_only', verbose=True,
#                                       membrane_voltage='V',
#                                       membrane_capacitance='Cm')
        load_mechanisms('/Users/tclose/git/pyNN/src/neuron/nmodl')
#         (_, _, _, install_dir) = CodeGenerator().generate(
#             self.izhikevich_file, name=self.izhikevich_name,
#             build_mode='compile_only', verbose=True,
#             membrane_voltage='V', membrane_capacitance='Cm')
#         load_mechanisms('/Users/tclose/git/pype9/test/data/xml/9build/neuron/Izhikevich9ML/src')

#         nml = Izhikevich9ML()
        nml = collections.namedtuple('tmp', 'source_section')(h.Section())
        pnn = IzhikevichPyNN()
        # PyNN version
        for sec in (pnn, nml.source_section):
            # Specify current injection
            stim = h.IClamp(1.0, sec=sec)
            stim.delay = 1   # ms
            stim.dur = 100   # ms
            stim.amp = 0.2   # nA
            # Record Time from NEURON (neuron.h._ref_t)
            rec_t = neuron.h.Vector()
            rec_t.record(neuron.h._ref_t)
            # Record Voltage from the center of the soma
            rec_v = neuron.h.Vector()
            rec_v.record(sec(0.5)._ref_v)
            neuron.h.finitialize(-60)
            neuron.init()
            neuron.run(5)
            plt.plot(rec_t, rec_v)
        plt.show()


if __name__ == '__main__':
    t = TestNeuronLoad()
    t.test_neuron_load()
