import neuron
import pylab as plt
from neuron import h, nrn, load_mechanisms
from math import pi
from os import path


def _new_property(obj_hierarchy, attr_name):
    def set(self, value):
        obj = reduce(getattr, [self] + obj_hierarchy.split('.'))
        setattr(obj, attr_name, value)

    def get(self):
        obj = reduce(getattr, [self] + obj_hierarchy.split('.'))
        return getattr(obj, attr_name)

    return property(fset=set, fget=get)


class Izhikevich(nrn.Section):
    """docstring"""

    def __init__(self):
        nrn.Section.__init__(self)
        self.seg = self(0.5)
        self.source_section = self
        self.L = 10
        self.seg.diam = 10 / pi
        self.c_m = 1.0
        self.izh = h.Izhikevich1(0.5, sec=self)
        self.source = self.izh

        # Comment out this line or replace with 'self.izh.b = 0.2' or replace
        # the property name with a name that isn't in the izhikevich class
        # like 'self.e = 0.02'
        self.a = 0.02
#         self.izh.a = 0.2
#         self.e = 0.02

        a = _new_property('izh', 'e')


load_mechanisms(path.join(path.dirname(__file__), '1'))

# Comment out this line and it works regardless
load_mechanisms(path.join(path.dirname(__file__), '2'))


sec = Izhikevich()
stim = h.IClamp(1.0, sec=sec)
stim.delay = 1
stim.dur = 100
stim.amp = 0.2
rec_t = neuron.h.Vector()
rec_t.record(neuron.h._ref_t)
rec_v = neuron.h.Vector()
rec_v.record(sec(0.5)._ref_v)
neuron.h.finitialize(-60)
neuron.init()
neuron.run(5)
plt.plot(rec_t, rec_v)
plt.show()
