import future.utils
import warnings
import nest

if future.utils.PY3 and nest.version().split()[1] == '2.12.0':
    # Undo monkey patch of warning performed by pyNEST 2.12.0 as it
    # isn't compatible with Python 3
    warnings.showwarning = warnings._showwarning_orig

from .cells import Cell, CellMetaClass  # @IgnorePep8
from .code_gen import CodeGenerator  # @IgnorePep8
from .simulation import Simulation  # @IgnorePep8
from .network import (  # @IgnorePep8
    Network, ComponentArray, Selection, ConnectionGroup,
    PyNNCellWrapperMetaClass)
from .units import UnitHandler  # @IgnorePep8
