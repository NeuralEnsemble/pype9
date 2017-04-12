===============
Unsupported 9ML
===============

NineML_ aims to be a comprehensive description language for neural simulation. This
means that it allows the expression of some uncommon configurations that are
difficult to implement in Neuron_ and NEST_. Work is planned to make the Neuron_
and NEST_ pipelines in Pype9 fully support NineML_, however until then the following
restrictions apply to models that can be used with Pype9.

* synapses must be linear (to be relaxed in v0.2)
* synapses can only have one variable that varies over a projection (e.g.
  weight) (to be relaxed in v0.2)
* no analog connections between populations (i.e. gap junctions) (gap
  junctions to be implemented in v0.2)
* only one event send port per cell (current limitation of Neuron_/NEST_)
* names given to NineML_ elements are not escaped and therefore can clash with
  built-in keywords and some PyPe9 method names (e.g. 'lambda' is a reserved
  keyword in Python). Please avoid using names that clash with C++ or Python
  keywords (all 9ML names will be escaped in PyPe9 v0.2).

.. _NineML: http://nineml.net
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu