PyPe9
========

"PYthon PipelinEs for NineML (PyPe9)" is a collection of software pipelines
written in Python to read and simulate networks of detailed
neuronal models described in NineML in both Neuron and NEST simulators.

CAUTION!: PyPe9 is currently still under development and has not been officially released. Use at your own risk!

PyPe9 implements syntax that is planned for NineML v2. The closest matching specification can be found under the `refactor_v2` branch at https://github.com/tclose/nineml/, although it is currently lagging the lib9ML implementation as of 15/10/2015.

Author: Thomas G. Close (tclose@oist.jp)

Pre-requisites
---
 * Python 2.7
 * PyNEURON (see http://www.davison.webfactional.com/notes/installation-neuron-python/)
 * PyNEST (see http://www.nest-simulator.org/installation/)
 * PyNN (> v0.8, see http://neuralensemble.org/docs/PyNN/installation.html)
 * lib9ML (`bleeding_edge` branch at http://github.com/tclose/lib9ML)
 * diophantine (`master` branch at https://github.com/tclose/Diophantine)
 * NineMLCatalog (for unit-tests, `develop` branch at http://github.com/tclose/NineMLCatalog)
 
Installation
---

After installing PyNEURON, PyNEST and PyNN via their instructions clone the lib9ML, Diophantine, NineMLCatalog and PyPe9 repositories to somewhere sensible on your local computer (e.g. $HOME/git/nineml, $HOME/git/diophantine, $HOME/git/ninemlcatalog & $HOME/git/pype9). Then add the root directory of each repository to your PYTHONPATH environment variable (see https://docs.python.org/2/using/cmdline.html#envvar-PYTHONPATH).

Testing
---
PyPe9 is currently still under heavy development, however there are some unit-tests in the <pype9-home>/tests/unittests directory that should work. In particular try the `test_dynamics.py` unit tests to see if it has been installed properly.

Documentation
---
There is the skeleton documentation in the <pype9-home>/doc directory, which can be built with Sphynx. However, it still needs a lot of work at this stage.

