import os.path
from quantities import Quantity
from pype9.utils import pq29_quantity
import numpy

units = []
for sim in ('neuron', 'nest'):
    with open(os.path.join(os.getcwd(), 'data', sim + '-units.txt')) as fin, \
            open(os.path.join(os.getcwd(), 'data',
                              sim + '-dimension_power.txt'), 'w') as fdim, \
            open(os.path.join(os.getcwd(), 'data',
                              sim + '-unit_power.txt'), 'w') as funit:
        for line in fin:
            units = pq29_quantity(Quantity(1.0, line)).units
            fdim.write(' '.join(str(d) for d in units.dimension._dims) + '\n')
            funit.write(str(units.power) + '\n')
