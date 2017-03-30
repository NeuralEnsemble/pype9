============
Installation
============

Simulator Backends
------------------
Pype9 works with the following simulator backends

* Neuron >= 7.3
* NEST == 2.10.0 

on MacOS
^^^^^^^^
On macOS, NEST and Neuron can be installed via the Hombrew package manager (https://brew.sh).
*Before* installing them with *Homebrew* it is preferable (but not essential) to install the
Homebrew version of Python with::

   brew install python

NEST can be installed with::

   brew install --with-python nest
   
and Neuron can be installed with::


   brew install neuron
   
NB: If you have MPI installed and want to use it to spread your simulation over multiple compute
cores/nodes you should provide the `--with-mpi` option.
   
If you don't/can't use Hombrew then see the _`Source` section below. 


on Ubuntu/Debian
^^^^^^^^^^^^^^^^
NEST and Neuron packages are available in the NeuroDebian repository (http://neuro.debian.net),
otherwise please install from source (see _`Source`).

on Windows
^^^^^^^^^^
Pype9 has not been tested on Windows (and NEST does not run on Windows), so
although Pype9/Neuron may run, it is recommended that you use the Docker
container to run simulations on Windows.

with Docker
^^^^^^^^^^^
There is a Docker image located at https://hub.docker.com/r/tclose/pype9/
that you can pull to run the simulations within a Docker container. See the instructions
in the comments of the `Dockerfile` in the Pype9 repo for instructions on how to do this.

from Source Code
^^^^^^^^^^^^^^^^
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
this repository and using *pip*::

   cd <pype9-repo-dir>
   pip install -r requirements.txt .

If you cannot use *pip* you will need to manually install the *libninemlnrn*
shared library, which contains wrappers for GSL random distribution functions, with:: 

   cd <pype9-repo-dir>/pype9/neuron/cells/code_gen/libninemlnrn
   CC=<your-Neuron-c-compiler> ./manual_compile.sh

After that you just need to ensure the root of the Pype9 package is on your
PYTHONPATH environment variable. 