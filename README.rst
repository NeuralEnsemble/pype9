Pype9
*****

"PYthon PipelinEs for 9ml (Pype9)" is a collection of software Python pipelines to
simulate networks of neuron models described in NineML (http://nineml.net)
using either Neuron (http://neuron.yale.edu) or NEST (http://nest-simulator.org)
as simulator backends.

.. image:: https://travis-ci.org/CNS-OIST/PyPe9.svg?branch=master
    :target: https://travis-ci.org/CNS-OIST/PyPe9
.. image:: https://coveralls.io/repos/github/CNS-OIST/PyPe9/badge.svg?branch=master
    :target: https://coveralls.io/github/CNS-OIST/PyPe9?branch=master


Installation
============

Simulator Backends
------------------

Pype9 works with the following simulator backends

* Neuron >= 7.3
* NEST == 2.10.0 

MacOS
^^^^^
On macOS, NEST and Neuron can be installed via the Hombrew package manager (https://brew.sh).
*Before* installing them with Homebrew it is preferable (but not essential) to install the
Homebrew version of Python with::

   brew install python

NEST can be installed with::

   brew install --with-python nest
   
and Neuron can be installed with::


   brew install neuron
   
NB: If you have MPI installed and want to use it to spread your simulation over multiple compute
cores/nodes you should provide the '--with-mpi' option.
   
If you don't/can't use Hombrew then see the _`Source` section below. 


Ubuntu/Debian
^^^^^^^^^^^^^
NEST and Neuron packages are available in the NeuroDebian repository (http://neuro.debian.net),
otherwise please install from source (see _`Source`).

Docker
^^^^^^
Alternatively, there is a Docker image located at https://hub.docker.com/r/tclose/pype9/
that you can pull to run the simulations within a Docker container. See the instructions
in the comments of the `Dockerfile` in the Pype9 repo for instructions on how to do this.

Windows
^^^^^^^
Pype9 has not been tested on Windows (and NEST does not run on Windows), so
although Pype9/Neuron may run, it is recommended that you use the Docker
container to run simulations on Windows.

Source
^^^^^^
Instructions on how to install NEST from source can be found on official NEST
website, http://www.nest-simulator.org/installation/

Good instructions on how to install Neuron from source can be found in Andrew
Davisons notes here, http://www.davison.webfactional.com/notes/installation-neuron-python/.

In the `prereq` folder there are also scripts for installing the Neuron and NEST from
source on a Ubuntu image, which may serve as a good reference.

Python
------

Pype9 depends on the following Python packages

* PyNN == 0.8.2 (http://neuralensemble.org/docs/PyNN/installation.html)
* lib9ML (`develop` branch at http://github.com/tclose/lib9ML)
* Diophantine == 0.1 (http://github.com/tclose/Diophantine)
* NineMLCatalog (for unit-tests,`develop` branch at http://github.com/tclose/NineMLCatalog)
* Sympy == 0.7.6 or 1.0.1dev (there is a bug in 1.0)
* Neo == 0.4.1

These requirements and the Pype9 package itself can be installed *after* the
simulator backends are installed (see _`Simulator Backends`) by downloading/cloning
this repository and using pip::

   cd <pype9-repo-dir>
   pip install -r requirements.txt .

If you cannot use pip (or you have recompiled your Neuron installation with a different
C compiler) tyou will need to manually install the _libninemlnrn_ library, which
contains wrappers for GSL random distribution functions, with:: 

   cd <pype9-repo-dir>/pype9/neuron/cells/code_gen/libninemlnrn
   CC=<your-Neuron-c-compiler> ./manual_compile.sh

After that you just need to ensure the root of the Pype9 package is on your
PYTHONPATH environment variable. 

Documentation
=============
There is a brief  skeleton documentation in the <pype9-home>/doc directory, which
can be built with Sphinx.


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
