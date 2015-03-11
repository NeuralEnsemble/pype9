import neuron
import pylab as plt
from neuron import h, nrn, load_mechanisms
from math import pi
from os import path


def _new_property(obj_hierarchy, attr_name):
    """
    Returns a new property, mapping attr_name to obj_hierarchy.attr_name.

    For example, suppose that an object of class A has an attribute b which
    itself has an attribute c which itself has an attribute d. Then placing
      e = _new_property('b.c', 'd')
    in the class definition of A makes A.e an alias for A.b.c.d
    """

    def set(self, value):  # @ReservedAssignment
        obj = reduce(getattr, [self] + obj_hierarchy.split('.'))
        setattr(obj, attr_name, value)

    def get(self):
        obj = reduce(getattr, [self] + obj_hierarchy.split('.'))
        return getattr(obj, attr_name)

    return property(fset=set, fget=get)


class IzhikevichPyNN(nrn.Section):  # @UndefinedVariable
    """docstring"""

    def __init__(self, a_=0.02, b=0.2):

        # initialise Section object with 'pas' mechanism
        nrn.Section.__init__(self)  # @UndefinedVariable
        self.seg = self(0.5)
        self.source_section = self
        self.L = 10
        self.seg.diam = 10 / pi
        self.c_m = 1.0

        # insert Izhikevich mechanism
        self.izh = h.Izhikevich(0.5, sec=self)
        self.source = self.izh
        self.a_ = a_
        self.b = b

    a_ = _new_property('izh', 'a')
    b = _new_property('izh', 'b')

# load_mechanisms('/Users/tclose/git/pyNN/src/neuron/nmodl')
# load_mechanisms('/Users/tclose/git/pype9/test/data/xml/9build/neuron/'
#                 'Izhikevich9ML/src')
load_mechanisms(path.join(path.dirname(__file__), '1'))
load_mechanisms(path.join(path.dirname(__file__), '2'))
sec = IzhikevichPyNN()
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
