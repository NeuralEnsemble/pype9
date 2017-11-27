============
Installation
============

There two stages to installing Pype9: installing one or more of the simulator
backends and installing the Pype9 package itself.

Simulator Backends
------------------

Pype9 works with the following simulator backend versions

* Neuron_ >= 7.3
* NEST_ >= 2.12.0

There are a few methods to install them, the  depends on your operating system. 

.. warning: Make sure that you use the same Python version when installing
            the simulator backend that you use to install the Pype9 package.

on MacOS
^^^^^^^^
On macOS, NEST_ and Neuron_ can be installed via the Homebrew_ package manager.

If you haven't already have configured a Python distribution on your system,
I would recommend installing the standard Python distribution with Homebrew_
first. Pype9 is compatible with both Python 2 (2.7) and Python 3 (>3.4), so
which one you choose is up to you.

.. code-block:: bash

   brew install python3
   
Neuron_ can be installed with Homebrew_ by

.. code-block:: bash

   brew install --with-mpi neuron
   
.. note:
    The flag ``--with-mpi`` is note required but will enable you to spread your
    simulation over multiple compute cores/nodes of your computer.

   
NEST_ can be installed with Homebrew_ by

.. code-block:: bash

   brew install nest
   
.. warning:
    NEST currently doesn't install the source headers alongside the libraries
    and Homebrew throws away the build directory after it is built, which means
    that Pype9 is not able to find the appropriate headers to build custom
    modules against. However, the currently open PR,
    https://github.com/nest/nest-simulator/pull/844 should fix this.
 

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


Python packages
---------------
 
Pype9 can be installed from the `Python Package Index (PyPI)`_ with *pip*::

    $ pip install pype9

However, if you would like to use the *plot* command you will also need to 
install matplotlib, which can be done by providing the *plot* option::

    $ pip install pype9[plot]

.. note: In order to run simulations in pype9 you will need to install one of
         the supported simulator backends (see below).

 
.. _NineML: http://nineml.net
.. _NeuroDebian: http://neuro.debian.net
.. _Pip: http://pip.pypa.io
.. _Docker: https://www.docker.com
.. _Homebrew: https://brew.sh
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu
.. _Enthought: https://www.enthought.com
.. _`Python Package Index (PyPI)`: http://pypi.org

