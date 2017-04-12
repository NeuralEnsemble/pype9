============
Installation
============

There are two steps to installing Pype9, the first is installing one or both of
the simulator backends, Neuron_ and/or NEST_, and the second is installing
Pype9 and prerequisite Python packages.


.. note::

    Pype9 currently only works with Python 2.7. Python 3 support is
    planned for future versions.


Simulator Backends
------------------
Pype9 works with the following simulator backend versions

* Neuron_ >= 7.3
* NEST_ == 2.10.0

The easiest way to install them depends on your operating system. 

.. note::

    Pype9 v0.1.0 does not work with the latest NEST_ version, 2.12,
    as the build system was changed from autotools to cmake. A new release
    (0.1.1) will be made to add NEST_ 2.12 support.

on MacOS
^^^^^^^^
On macOS, NEST_ and Neuron_ can be installed via the Homebrew_ package manager.
Note that it tends not to be a good idea to use multiple package managers (e.g.
macports), so if you use a different package manager it may be better to
install `from Source Code`_. 


If you haven't already have configured a Python distribution on your system (or
don't mind reinstalling your existing packages), I would recommend installing
the standard Python distribution with Homebrew_ first

.. code-block:: bash

   brew install python
   
Neuron_ can be installed with Homebrew_ by

.. code-block:: bash

   brew install --with-mpi neuron
   
Note that ``--with-mpi`` is optional but will enable you to spread your
simulation over multiple compute cores/nodes of your computer.

Unfortunately, NEST_ 2.10, can no longer be installed via Homebrew_ as 2.12 is
the latest version. Therefore, you will need to install it `from Source Code`_.


on Ubuntu/Debian
^^^^^^^^^^^^^^^^
NEST and Neuron packages are available in the NeuroDebian_ repository, otherwise
please install from source (see `from Source Code`_).

on Windows
^^^^^^^^^^
Pype9 has not been tested on Windows (and NEST does not run on Windows), so
although Pype9/Neuron may run, it is recommended that you use the Docker
container to run simulations on Windows.

with Docker
^^^^^^^^^^^
There is a Docker_ image located at https://hub.docker.com/r/tclose/pype9/ that
you can pull to run the simulations within a Docker container. See the
instructions in the comments of the ``Dockerfile`` in the Pype9 repository for
instructions on how to do this.

from Source Code
^^^^^^^^^^^^^^^^
Instructions on how to install NEST from source can be found on official NEST
website, http://www.nest-simulator.org/installation/

Good instructions on how to install Neuron from source can be found in Andrew
Davisons notes here,
http://www.davison.webfactional.com/notes/installation-neuron-python/.

In the ``prereq`` folder there are also scripts for installing the Neuron and
NEST from source on a Ubuntu image, which may serve as a good reference.

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
downloading/cloning this repository and using *pip*

.. code-block:: bash

   cd <pype9-repo-dir>
   pip install -r requirements.txt .

If you cannot use *pip* you will need to manually install the *libninemlnrn*
shared library, which contains wrappers for GSL random distribution functions,
with

.. code-block:: bash

   cd <pype9-repo-dir>/pype9/neuron/cells/code_gen/libninemlnrn
   CC=<your-Neuron-c-compiler> ./manual_compile.sh

After that you just need to ensure the root of the Pype9 package is on your
Python path (i.e. either symlinked to the ``site-packages`` directory or on the
PYTHONPATH environment variable). 

.. _NineML: http://nineml.net
.. _NeuroDebian: http://neuro.debian.net
.. _Docker: https://www.docker.com
.. _Homebrew: https://brew.sh
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu
.. _Enthought: https://www.enthought.com