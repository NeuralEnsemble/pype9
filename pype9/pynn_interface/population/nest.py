"""

  This package mirrors the one in pyNN

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import sys
# Remove any system arguments that may conflict with
if '--debug' in sys.argv:
    raise Exception("'--debug' argument passed to script conflicts with an "
                    "argument to nest, causing the import to stop at the "
                    "NEST prompt")
import pyNN.nest.standardmodels
from pyNN.common.control import build_state_queries
import pyNN.nest.simulator as simulator
from ..cell_wrappers.nest import PyNNCellWrapperMetaClass
from .base import Population as BasePopulation

(get_current_time, get_time_step,
 get_min_delay, get_max_delay,
 num_processes, rank) = build_state_queries(simulator)

RELATIVE_BREP_BUILD_DIR = './build'


class Population(BasePopulation, pyNN.nest.Population):

    _pyNN_standard_celltypes = dict([(cellname,
                                      getattr(pyNN.nest.standardmodels.cells,
                                              cellname))
                                     for cellname in
                                             pyNN.nest.list_standard_models()])
    _Pype9CellMetaClass = PyNNCellWrapperMetaClass

    @classmethod
    def _translate_variable(cls, variable):
        # FIXME: This is a bit of a hack until I coordinate with Ivan about the
        # naming of variables in NEST
        if variable.startswith('{'):
            variable = variable[variable.find('}') + 1:]
        if variable == 'v':
            variable = 'V_m'
        return variable

    def record(self, variable, to_file=None):
        variable = self._translate_variable(variable)
        super(Population, self).record(variable, to_file)

    def _get_cell_initial_value(self, id, variable):  # @ReservedAssignment
        """Get the initial value of a state variable of the cell."""
        return super(Population, self)._get_cell_initial_value(
            id, self._translate_variable(variable))

    def initialize(self, **initial_values):
        """
        Set initial values of state variables, e.g. the membrane potential.

        Values passed to initialize() may be:
            (1) single numeric values (all neurons set to the same value)
            (2) RandomDistribution objects
            (3) lists/arrays of numbers of the same size as the population
            (4) mapping functions, where a mapping function accepts a single
                argument (the cell index) and returns a single number.

        Values should be expressed in the standard PyNN units (i.e. millivolts,
        nanoamps, milliseconds, microsiemens, nanofarads, event per second).

        Examples::

            p.initialize(v=-70.0)
            p.initialize(v=rand_distr, gsyn_exc=0.0)
            p.initialize(v=lambda i: -65 + i/10.0)
        """
        translated_initial_values = {}
        for name, value in initial_values.iteritems():
            translated_name = self.celltype.translations[
                name]['reverse_transform']
            translated_initial_values[translated_name] = value
        super(Population, self).initialize(**translated_initial_values)
