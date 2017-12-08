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
``convert`` and ``plot`` pipelines but in order to run simulations with
Pype9 you will need to install at least one of the supported simulator
backends (see below).

Simulator Backends
------------------

Pype9 currently works with the following simulator backends

* Neuron_ >= 7.5
* NEST_ >= 2.14.0

There are various configurations in which to install them, with the
best choice dependent on your operating system/development
configuration and your own personal preference.


.. warning: Make sure that you use the same Python installation for
            the simulator backend Python bindings as you use for
            the Pype9 package.
 
Manual Installation from Source (Linux/MacOS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Detailed instructions on how to install NEST_ can be found on the
official `NEST docs`_.

Good instructions on how to install Neuron_ from source can be found in
`Andrew Davisons notes`_.

Homebrew/Linuxbrew (MacOS/Linux)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Homebrew_ is a package manager that was developed for MacOS, but which
has proven so successful that it has been ported to Linux (Linuxbrew)
to complement in-built package managers (Linuxbrew installs packages
to a users home directory).

The Pype9 command line interface (CLI), Neuron_ and NEST_ can all be
installed using Homebrew_ in one line with::

   $ brew install tclose/pype9/pype9

The following options can be provided to the formula

* with-python3 - Install Pype9, Neuron_ and NEST_ using Python 3
* with-mpi - Install Pype9, Neuron_ and NEST_ with MPI support

.. warning:: As of 2.14.0 NEST will need to be reinstalled using
            ``brew reinstall NEST --HEAD`` in order to include commit
            that installs the required C++ header files to the install
            prefix (instead of leaving them in the build directory,
            which is deleted after the build). In future versions of
            NEST this step will not be necessary.
 
Note that this Homebrew_ formula installs the Pype9 package and all its
Python dependencies in a virtual environment inside the Homebrew_
*Cellar*. Therefore, if you would like to access Pype9's Python API you
should only install the Neuron_ and NEST_ dependencies via Homebrew_
and Pype9 and its Python dependencies via Pip_::

   $ brew install --only-dependencies tclose/pype9/pype9
   $ pip install pype9

or for Python 3::

   $ brew install --only-dependencies tclose/pype9/pype9 --with-python3
   $ pip3 install pype9
   
Please see `the notes on how Homebrew handles Python`_, to ensure that
you use the same installation for Neuron_, NEST_ and Pype9, taking
special note of the sections on bottling if not passing options to the
build (i.e. ``--with-python3`` or ``--with-mpi``).

If you don't have a strong preference for which Python you use I
would recommend using a Homebrew_ Python installation (either 2 or 3,
but probably 3 is best since support for Python 2 ends in 2020) as the
system Python on MacOS has been slightly altered and can break some
packages.
          
.. note:: To set Hombrew's Python 2 to be the default Python used from
          your terminal add ``/opt/brew/opt/python/libexec/bin`` to
          your PATH variable.
          
Install scripts (Linux/MacOS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install Neuron_ and NEST_ from source you can use the scripts that
Pype9 uses to set up its automated testing environment, which can be
found in the ``install`` directory of the Pype9 repo. For example, to
install NEST_ 2.14.0 with Python 3 bindings to the prefix
``/opt/nest/2.14.0``::

    $ wget https://raw.githubusercontent.com/tclose/pype9/develop/install/nest.sh
    $ ./nest.sh 2.14.0 3 /opt/nest/2.14.0
    
or Neuron_ 7.5:: 

    $ wget https://raw.githubusercontent.com/tclose/pype9/develop/install/neuron.sh
    $ ./neuron.sh 7.5 3 /opt/neuron/7.5

These install scripts also work well within a virtualenv_, where they
will install NEST_ and Neuron_ to the virtualenv_ prefix by default.
This allows you to maintain different versions of Neuron_, NEST_ on
your system, which is useful when upgrading.

When installing to a virtualenv_, the Python version and install prefix
don't need to be supplied to the install scripts::

    $ wget https://raw.githubusercontent.com/tclose/pype9/develop/install/nest.sh
    $ wget https://raw.githubusercontent.com/tclose/pype9/develop/install/neuron.sh
    $ pip install virtualenvwrapper
    $ mkvirtualenv -p python3 pype9
    $ ./nest.sh 2.14.0
    $ ./neuron.sh 7.5

On Ubuntu, the installation requires the following packages

* build-essential
* autoconf
* automake
* libtool
* libreadline6-dev
* libncurses5-dev
* libgsl0-dev
* python-dev
* python3-dev
* openmpi-bin
* libopenmpi-dev
* inkscape
* libhdf5-serial-dev
* libyaml-dev

Similar packages can be found in other package managers on other
distributions/systems (e.g. Homebrew_).

Docker (Windows/Linux/MacOS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A complete installation of Neuron_, NEST_ and Pype9 (with MPI and
against Python 3) can be found on the Docker image,
https://hub.docker.com/r/tclose/pype9.

1. Install Docker (see https://docs.docker.com/engine/installation/)

2. Pull the Pype9 Docker image::

    $ docker pull tclose/pype9

3. Create a Docker container from the downloaded image::
 
    $ docker run -v `pwd`/<your-local-output-dir>:/home/docker/output \
        -t -i tclose/pype9 /bin/bash

This will create a folder called `<your-local-output-dir>` in the
directory you are running the docker container, which you can access
from your host computer (i.e. outside of the container) and view the
output figures from.

4. From inside the running container, you will be able to run pype9,
   e.g.::

    (pype9)docker@b3eca79b5209:~$ pype9 simulate \
        ~/catalog/neuron/HodgkinHuxley#PyNNHodgkinHuxleyProperties \
        nest 500.0 0.001 \
        --init_value v 65 mV \
        --init_value m 0.0 unitless \
        --init_value h 1.0 unitless \
        --init_value n 0.0 unitless \
        --record v ~/output/hh-v.neo.pkl

    (pype9)docker@b3eca79b5209:~$ pype9 plot ~/output/hh-v.neo.pkl \
        --save ~/output/hh-v.png

Supply the `--help` option to see a full list of options for each
example.

5. Edit the xml descriptions in the ~/catalog directory to alter the
simulated models as desired.


.. _NineML: http://nineml.net
.. _NeuroDebian: http://neuro.debian.net
.. _Pip: http://pip.pypa.io
.. _Docker: https://www.docker.com
.. _Homebrew: https://brew.sh
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu
.. _Enthought: https://www.enthought.com
.. _`Python Package Index (PyPI)`: http://pypi.org
.. _`the notes on how Homebrew handles Python`: https://docs.brew.sh/Homebrew-and-Python.html
.. _`Andrew Davisons notes`: http://www.davison.webfactional.com/notes/installation-neuron-python/
.. _`NEST docs`: http://www.nest-simulator.org/installation/
.. _virtualenv: https://virtualenv.pypa.io/en/stable/
