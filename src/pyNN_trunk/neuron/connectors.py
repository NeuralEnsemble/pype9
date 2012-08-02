"""
Connection method classes for the neuron module

:copyright: Copyright 2006-2011 by the PyNN team, see AUTHORS.
:license: CeCILL, see LICENSE for details.

$Id: connectors.py 1003 2011-10-31 13:42:54Z apdavison $
"""

from pyNN.neuron import simulator
from pyNN.connectors import AllToAllConnector, \
                            OneToOneConnector, \
                            FixedProbabilityConnector, \
                            DistanceDependentProbabilityConnector, \
                            FromListConnector, \
                            FromFileConnector, \
                            FixedNumberPreConnector, \
                            FixedNumberPostConnector, \
                            SmallWorldConnector, \
                            CSAConnector
