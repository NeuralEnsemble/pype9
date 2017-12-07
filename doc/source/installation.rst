============
Installation
============

Pype9 itself is a pure Python application and can be installed from the
`Python Package Index (PyPI)`_ with Pip_::

    $ pip install pype9

If you would like to use the *plot* command you will also need
to install matplotlib, which can be done separately or by specifying
the 'plot' extra::

    $ pip install pype9[plot]

With just the Python packages installed you will be able to use the
`convert` and `plot` pipelines but in order to run simulations with
Pype9 you will need to install at least one of the supported simulator
backends (see below).

Simulator Backends
------------------

Pype9 currently works with the following simulator backends

* Neuron_ >= 7.5
* NEST_ >= 2.14.0

There are various configurations in which to install them, with the
best choice dependent on your operating system/development
configuration and your own personal preference

.. warning: Make sure that you use the same Python installation for
            the simulator backend Python bindings as you use for
            the Pype9 package.

Homebrew/Linuxbrew (MacOS/Linux)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Homebrew_ is a package manager that was developed for MacOS to make up
for the fact that MacOS doesn't have an integrated package manager like
Linux systems, but which has proven so successful that it has been
ported to Linux (Linuxbrew).

The Pype9 command line interface (CLI), Neuron_ and NEST_ can all be
installed using Homebrew_ in one line with::

   $ brew install tclose/pype9/pype9

The following options can be provided to the formula

* with-python3 - Install Pype9, Neuron_ and NEST_ using Python 3
* with-mpi - Install Pype9, Neuron_ and NEST_ with MPI support

.. warning:: As of 2.14.0 NEST will need to be reinstalled using
            `brew reinstall NEST --HEAD` in order to include commit
            that installs the required C++ header files to the install
            prefix (instead of leaving them in the build directory,
            which is deleted after the build). In future versions of
            NEST this step will not be necessary.
 
Note that this formula installs the Pype9 and all its Python
dependencies in a virtual environment inside the Homebrew_ "cellar".
Therefore, if you would like to access Pype9's Python API you should
just install the Neuron_ and NEST_ dependencies via Homebrew_ and Pype9
and its Python dependencies via Pip_::

   $ brew install --only-dependencies tclose/pype9/pype9
   $ pip install pype9

or for Python 3::

   $ brew install --only-dependencies tclose/pype9/pype9 --with-python3
   $ pip3 install pype9
   
Please see [Python notes](https://docs.brew.sh/Homebrew-and-Python.html)
for Homebrew_ for it handles Python, taking special note of the sections
on bottling if not using MPI or Python 3. If you don't have a strong
preference or an existing Python installation with the scientific stack
installed (e.g. Enthought) I would recommend using a Homebrew_ Python
installation (either 2 or 3, but probably 3 is best since support for
Python 2 ends in 2020) for your scientific computing.
          
.. note:: To set Hombrew_'s Python 2 to be the default Python used from
          your terminal add `/opt/brew/opt/python/libexec/bin` to your
          PATH variable.
          
From Source (Linux/MacOS)
~~~~~~~~~~~~~~~~~~~~~~~~~

Instructions on how to install NEST from source can be found on official
NEST website, http://www.nest-simulator.org/installation/

Good instructions on how to install Neuron from source can be found in
Andrew Davisons notes here,
http://www.davison.webfactional.com/notes/installation-neuron-python/.

Alternatively, you can use the installation scripts 



On macOS, NEST_ and Neuron_ can be installed via the Homebrew_ package
manager.

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

Docker (Windows/Linux/MacOS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

There is a Docker_ image located at https://hub.docker.com/r/tclose/pype9/ that
you can pull to run the simulations within a Docker container. See the
instructions in the comments of the ``Dockerfile`` in the Pype9 repository for
instructions on how to do this.

from Source Code
^^^^^^^^^^^^^^^^

In the ``prereq`` folder there are also scripts for installing the Neuron and
NEST from source on a Ubuntu image, which may serve as a good reference.


Python packages
---------------
 

 
.. _NineML: http://nineml.net
.. _NeuroDebian: http://neuro.debian.net
.. _Pip: http://pip.pypa.io
.. _Docker: https://www.docker.com
.. _Homebrew: https://brew.sh
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu
.. _Enthought: https://www.enthought.com
.. _`Python Package Index (PyPI)`: http://pypi.org

