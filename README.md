PyPe9
========

"PYthon PipelinEs for 9ml (PyPe9)" is a collection of software pipelines
written in Python to read and simulate networks of neuronal models
described in NineML (http://nineml.net) in both Neuron and NEST simulators.

PyPe9 is still under development so please submit bug reports to the GitHub
issue tracker (http://github.com/CNS-OIST/PyPe9/issues).

Author: Tom G. Close (tom.close@monash.edu)

Pre-requisites
---
 * Python 2.7
 * PyNEURON (see http://www.davison.webfactional.com/notes/installation-neuron-python/)
 * PyNEST (see http://www.nest-simulator.org/installation/)
 * PyNN v0.8 (see http://neuralensemble.org/docs/PyNN/installation.html)
 * lib9ML (`bleeding_edge` branch at http://github.com/tclose/lib9ML)
 * Diophantine (`master` branch at https://github.com/tclose/Diophantine)
 * NineMLCatalog (for unit-tests, `develop` branch at http://github.com/tclose/NineMLCatalog)
 
Installation
---

After installing PyNEURON, PyNEST and PyNN via their instructions clone the 
lib9ML, Diophantine, NineMLCatalog and PyPe9 repositories to somewhere sensible
on your local computer (e.g. $HOME/git/nineml, $HOME/git/diophantine,
$HOME/git/ninemlcatalog & $HOME/git/pype9). Then add the root directory of 
each repository to your PYTHONPATH environment variable
(see https://docs.python.org/2/using/cmdline.html#envvar-PYTHONPATH).

Testing
---
There are unit-tests in the <pype9-home>/tests/unittests directory to run
common neuron models (_see_ test_dynamics.py) as well as the random balanced
network (_see_ test_network.py) published in
Brunel N, Dynamics of Sparsely Connected Networks of Excitatory and Inhibitory Spiking Neurons, _Journal of Computational Neuroscience_ 8, 183–208 (2000).

Note that the Neuron (NMODL/Hoc) import functionality is still experimental and
requires proper unit-tests to be written.

Documentation
---
There is the skeleton documentation in the <pype9-home>/doc directory, which
can be built with Sphynx. However, it still needs a lot of work at this stage.

Known Limitations
---

9ML aims to be a comprehensive description language for neural simulation. This
means that it allows the expression of some uncommon configurations, which are
difficult to implement in NEURON and NEST. Work is planned to make the NEURON
and NEST pipelines in Pype9 support 9ML fully, however until then the following
restrictions apply to network models

* synapses must be linear (to be relaxed in v0.2)
* synapses can only have one variable that varies over a projection
  (e.g. weight) (to be relaxed in v0.2)
* no analog connections between populations (i.e. gap junctions)
  (gap junctions to be implemented in v0.2)
* only one event send port per cell (current limitation of NEURON/NEST)
