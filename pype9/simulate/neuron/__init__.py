from .cells import Cell, CellMetaClass
from .simulation import Simulation
from .network import Network
from .units import UnitHandler
# from .pynn_interface.network import Network  # @UnusedImport
# from .pynn_interface.population import Population  # @UnusedImport
# from .pynn_interface.projection import Projection  # @UnusedImport
# from .pynn_interface.synapses import StaticSynapse  # @UnusedImport
from nineml import units as un


# A matrix consisting of the default, units used in NEURON along the columns
# and the SI, unit powers they consist of as the rows. Used to work out the
# simplest combination of NEURON, units to represent an arbitary combination
# of SI, units with.
dimensions_matrix = [
     [ 0,  1,  0,  0,  0, -1,  0, -1, -1,  1,  1,  0,  0],  # mass @IgnorePep8
     [ 0,  2, -2,  0, -3, -4,  1, -4, -2,  3,  2,  0,  0],  # length @IgnorePep8
     [ 1, -3,  0,  0,  0,  4,  0,  3,  3, -3, -3,  0,  0],  # time @IgnorePep8
     [ 0, -1,  1,  1,  0,  2,  0,  2,  2, -2, -2,  0,  0],  # current @IgnorePep8
     [ 0,  0,  0,  0,  1,  0,  0,  0,  0,  0,  0,  0,  0],  # amount @IgnorePep8
     [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  0],  # temperature @IgnorePep8
     [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1]]  # luminous intensity @IgnorePep8
#   ms  mV mA/cm2 nA mM uF/cm2 um S/cm2 uS ohm*cm ohm C cd

# A collary to the dimensions matrix, calculate the 10 x power of the, units
# associated with each of the default NEURON, units. Once the minimum dimension
# projection is calculated from the dimensions_matrix, the correct scalar
# is the sum of the corresponding, units., units_power = [
#      -3,  -3,   1,   -9, -3,   2,   -3,   4,  -6,  -2,     6,    1,  1]  # @IgnorePep8
#    ms   mV  mA/cm2 nA  mM  uF/cm2 um  S/cm2 uS ohm*cm 10e6*ohm C   cd


default_units = [un.ms,
                 un.mV,
                 un.mA / un.cm ** 2,
                 un.nA,
                 un.mM,
                 un.uF / un.cm ** 2,
                 un.um,
                 un.S / un.cm ** 2,
                 un.uS,
                 un.ohm * un.cm,
                 un.Mohm,
                 un.C,
                 un.cd]
