PyPe9
=====

"PYthon PipelinEs for 9ml (PyPe9)" is a collection of software pipelines
written in Python to read and simulate networks of neuron models
described in NineML (http://nineml.net) in both Neuron and NEST simulators.

PyPe9 is still under major development so please submit bug reports to the
GitHub issue tracker (http://github.com/CNS-OIST/PyPe9/issues).

Prerequisites
-------------
* Python >= 2.7.11
* PyNEURON >= 7.3 (see
  http://www.davison.webfactional.com/notes/installation-neuron-python/)
* PyNEST 2.10.0 (see http://www.nest-simulator.org/installation/)
* PyNN 0.8.1 (see http://neuralensemble.org/docs/PyNN/installation.html)
* lib9ML (`develop` branch at http://github.com/tclose/lib9ML)
* Diophantine 0.1 (`master` branch http://github.com/tclose/Diophantine)
* NineMLCatalog (for unit-tests,`develop` branch at
  http://github.com/tclose/NineMLCatalog)

NB: PyPe9 may work with earlier versions of the packages listed but it 
    has not been tested.
 
Installation
------------

After installing PyNEURON, PyNEST and PyNN via the linked instructions clone the 
lib9ML, Diophantine, NineMLCatalog and PyPe9 repositories to somewhere sensible
on your local computer (e.g. $HOME/git/nineml, $HOME/git/diophantine,
$HOME/git/ninemlcatalog & $HOME/git/pype9). Then add the python package root
in each directory the python path of your python distribution for each repo (e.g.
$HOME/git/nineml/nineml, $HOME/git/diophantine/diophantine,
$HOME/git/ninemlcatalog/python/ninemlcatalog.py and $HOME/git/pype9/pype9),
which can be done by adding the containing directory to the PYTHONPATH
environment variable (see https://docs.python.org/2/using/cmdline.html#envvar-PYTHONPATH).

Finally, there is a shared library containing wrappers for GSL random distribution
functions to allow them to be called from the generated NEURON NMODL mechanisms, which
needs to be built. 

cd <pype9-install-dir>/pype9/neuron/cells/code_gen/libninemlnrn
make

Then add the following line (substituting DYLD_LIBRARY_PATH for LD_LIBRARY_PATH on OSX) to
your ~/.bashrc (~/.bash_profile or ~/.profile, etc)

export LD_LIBRARY_PATH=<pype9-install-dir>/pype9/neuron/cells/code_gen/libninemlnrn:$LD_LIBRARY_PATH

Alternatively, there is a Docker image located at https://hub.docker.com/r/tclose/pype9/
that you can pull to run the simulations within a Docker container. See the instructions
in the comments of the Dockerfile in the PyPe9 repo for instructions on how to do this.


Testing
-------
There are unit-tests in the <pype9-home>/tests/unittests directory to run
common neuron models (_see_ test_dynamics.py) as well as the random balanced
network (_see_ test_network.py) published in
Brunel N, Dynamics of Sparsely Connected Networks of Excitatory and Inhibitory
Spiking Neurons, _Journal of Computational Neuroscience_ 8, 183–208 (2000).

Note that the Neuron (NMODL/Hoc) import functionality is still experimental and
requires proper unit-tests to be written.

Documentation
-------------
There is the skeleton documentation in the <pype9-home>/doc directory, which
can be built with Sphynx. However, it still needs a lot of work at this stage.

Known Limitations
-----------------

9ML aims to be a comprehensive description language for neural simulation. This
means that it allows the expression of some uncommon configurations that are
difficult to implement in NEURON and NEST. Work is planned to make the NEURON
and NEST pipelines in Pype9 support 9ML fully, however until then the following
restrictions apply to models that can be used with PyPe9.

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
  
:copyright: Copyright 20012-2016 by the PyPe9 team, see AUTHORS.
:license: MIT, see LICENSE for details.  
  
.. image:: https://travis-ci.org/CNS-OIST/PyPe9.svg?branch=master
    :target: https://travis-ci.org/CNS-OIST/PyPe9
.. image:: https://coveralls.io/repos/github/CNS-OIST/PyPe9/badge.svg?branch=master
    :target: https://coveralls.io/github/CNS-OIST/PyPe9?branch=master
