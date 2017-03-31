Pype9
*****

.. image:: https://travis-ci.org/NeuralEnsemble/Pype9.svg?branch=master
    :target: https://travis-ci.org/NeuralEnsemble/Pype9
.. image:: https://coveralls.io/repos/github/NeuralEnsemble/Pype9/badge.svg?branch=master
    :target: https://coveralls.io/github/NeuralEnsemble/Pype9?branch=master
.. image:: https://readthedocs.org/projects/pype9/badge/?version=latest
    :target: http://pype9.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status 

Overview
========

"PYthon PipelinEs for 9ml (Pype9)" is a collection of software Python pipelines
to simulate networks of neuron models described in NineML (http://nineml.net)
using either Neuron or NEST simulator backends.



Documentation
=============
Pype9 documentation can be viewed at http://pype9.readthedocs.io (or the
the reST source files in <pype9-repo-dir>/doc/sources).


Installation
============

Pype9 works with either or both of the following simulator backends

* Neuron >= 7.3   (https://www.neuron.yale.edu/neuron/)
* NEST == 2.10.0  (http://www.nest-simulator.org)

Detailed instructions on how to install these simulators can be found at
http://pype9.readthedocs.io/en/latest/installation.html

*Before* installing the Pype9 package, the simulator(s) you plan to use should
be installed, and command line tools ``nrnivmodl`` for Neuron and ``nest-config``
for NEST should be accessible on your system path
(https://en.wikipedia.org/wiki/PATH_(variable)). Then the Pype9 and its
prerequisite Python packages can be installed with::

   cd <pype9-repo-dir>
   pip install -r requirements.txt .


Unsupported 9ML
===============

9ML aims to be a comprehensive description language for neural simulation. This
means that it allows the expression of some uncommon configurations that are
difficult to implement in NEURON and NEST. Work is planned to make the NEURON
and NEST pipelines in Pype9 support 9ML fully, however until then the following
restrictions apply to models that can be used with Pype9.

* synapses must be linear (to be relaxed in v0.2)
* synapses can only have one variable that varies over a projection
  (e.g. weight) (to be relaxed in v0.2)
* no analog connections between populations (i.e. gap junctions)
  (gap junctions to be implemented in v0.2)
* only one event send port per cell (current limitation of NEURON/NEST)
* names given to 9ML elements are not escaped and therefore can clash with
  built-in keywords and some PyPe9 method names (e.g. 'lambda' is a reserved
  keyword in Python). Please avoid using names that clash with C++ or Python
  keywords (all 9ML names will be escaped in PyPe9 v0.2).


Reporting Issues
================

Please submit bug reports and feature requests to the GitHub issue tracker
(http://github.com/CNS-OIST/PyPe9/issues).

:copyright: Copyright 20012-2016 by the Pype9 team, see AUTHORS.
:license: MIT, see LICENSE for details.
