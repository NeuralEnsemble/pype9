"""
The collection of 9ML annotations used by PyPe9
"""

# The overall PyPe9 namespace
PYPE9_NS = 'http://pype9.org'

BUILD_TRANS = 'NeuronTranslations'

# Basic NEURON section quantities (L, cm, v, etc...)
MEMBRANE_VOLTAGE = 'MembraneVoltage'
MEMBRANE_CAPACITANCE = 'MembraneCapacitance'

# External current ports
EXTERNAL_CURRENTS = 'ExternalCurrents'
NO_TIME_DERIVS = 'StateVariablesThatHaveNoTimeDerivatives'
NUM_TIME_DERIVS = 'NumberOfTimeDerivatives'

# Transform information
TRANSFORM_SRC = 'TransformSource'
TRANSFORM_DEST = 'TransformDestination'

# Ion species information
ION_SPECIES = 'IonSpecies'
NONSPECIFIC_CURRENT = 'nonSpecific'
INTERNAL_CONCENTRATION = 'InternalConcentration'
EXTERNAL_CONCENTRATION = 'ExternalConcentration'

# NEURON NMODL type
MECH_TYPE = 'MechType'
FULL_CELL_MECH = 'FullCellMech'
SUB_COMPONENT_MECH = 'SubComponentMech'
ARTIFICIAL_CELL_MECH = 'ArtificialCellMech'

# Build properties
BUILD_PROPS = 'BuildProperties'

# Additional variables (temporary until 9MLv2)
ADDITIONAL_VARS = 'AdditionalVariables'
INITIAL_REGIME = 'InitialRegime'
