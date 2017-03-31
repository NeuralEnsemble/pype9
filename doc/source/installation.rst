============
Installation
============

There are two steps to installing Pype9, the first is installing or both
simulator backends, Neuron and/or NEST, and the second installing the Pype9
Python package and its prerequisites.

Simulator Backends
------------------
Pype9 works with the following simulator backends

* Neuron >= 7.3   (https://www.neuron.yale.edu/neuron/)
* NEST == 2.10.0  (http://www.nest-simulator.org)

The easiest way to install them depends on your operating system. 

on MacOS
^^^^^^^^
On macOS, NEST and Neuron can be installed via the Hombrew package manager
(https://brew.sh). Unless you have already have configured the system or 
alternative Python distribution (e.g. Enthought), it can be a good idea to
install the *Homebrew* Python version *before* installing the simulator
backends. To install the *Homebrew* Python::

   brew install python

NEST can be installed with::

   brew install --with-python nest
   
and Neuron can be installed with::

   brew install neuron
   
NB: If you have MPI installed and want to use it to spread your simulation over
multiple compute cores/nodes you should provide the `--with-mpi` option.
   
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

Python Packages
---------------

Pype9 depends on the following Python packages

* nineml == 0.2.0 (currently github.com/tclose/lib9ML@develop)
* sympy == 0.7.6
* Jinja2 >= 2.6
* docutils >= 0.10
* mock > 1.0
* numpy >= 1.5
* quantities >= 0.11.1
* lazyarray >= 0.2.6
* neo == 0.4.1
* mpi4py >= 1.3.1
* pyNN == 0.8.2
* diophantine >= 0.1
* matplotlib

These requirements and the Pype9 package itself can be installed *after* the
simulator backends are installed (see _`Simulator Backends`) by
downloading/cloning this repository and using *pip*::

   cd <pype9-repo-dir>
   pip install -r requirements.txt .

If you cannot use *pip* you will need to manually install the *libninemlnrn*
shared library, which contains wrappers for GSL random distribution functions, with:: 

   cd <pype9-repo-dir>/pype9/neuron/cells/code_gen/libninemlnrn
   CC=<your-Neuron-c-compiler> ./manual_compile.sh

After that you just need to ensure the root of the Pype9 package is on your
Python path (i.e. either symlinked to the ``site-packages`` directory or on the
PYTHONPATH environment variable). 