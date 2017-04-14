======================
Command Line Interface
======================

The Pype9 command line interface will be installed on your system path when
Pype9 is installed with Pip_ (see :ref:`Installation`), otherwise it can be
found in the ``bin`` directory of the repository.

In a similar style to many popular command line tools (e.g. Git_, Pip_,
Homebrew_, etc..) there is a single command, ``pype9``, which is used to switch
between different pipelines, i.e.::

    $ pype9 <cmd> <options> <args>
 
There are currently four pipeline switches:

* simulate
* plot
* convert
* help

Simulate
--------

.. argparse::
    :module: pype9.cmd.simulate
    :func: argparser
    :prog: pype9 simulate


.. note::

    To simulate network simulations on Neuron_ over multiple cores you need to
    use the MPI_ command ``mpirun -n <ncores> pype9 simulate <options>``
    and have installed Neuron_ with the ``--with-mpi`` option
    (see :ref:`Installation`)

Plot
----

.. argparse::
    :module: pype9.cmd.plot
    :func: argparser
    :prog: pype9 plot

Convert
-------

.. argparse::
    :module: pype9.cmd.convert
    :func: argparser
    :prog: pype9 convert
 
 
Help
----

.. argparse::
    :module: pype9.cmd.help
    :func: argparser
    :prog: pype9 help

Examples
^^^^^^^^

The available pipelines can be listed with::

   $ pype9 help
   usage: pype9 <cmd> <args>

   available commands:
       convert
           Converts a 9ML file from one supported format to another
       help
           Prints help information associated with a PyPe9 command
       plot
           Convenient script for plotting the output of PyPe9 simulations (actually not
           9ML specific as the signals are stored in Neo format)
       simulate
           Runs a simulation described by an Experiment layer 9ML file

More detailed help messages for each available pipeline can be viewed by
supplying its name to the help::

   $ pype9 help plot
   usage: pype9 plot [-h] [--save SAVE] [--dims WIDTH HEIGHT] [--hide]
                  [--resolution RESOLUTION]
                  filename

   Convenient script for plotting the output of PyPe9 simulations (actually not
   9ML specific as the signals are stored in Neo format)
   
   positional arguments:
     filename              Neo file outputted from a PyPe9 simulation
   
   optional arguments:
     -h, --help            show this help message and exit
     --save SAVE           Location to save the figure to
     --dims WIDTH HEIGHT   Dimensions of the plot
     --hide                Whether to show the plot or not
     --resolution RESOLUTION
                           Resolution of the figure when it is saved
 
 
.. _Homebrew: http://brew.sh
.. _Git: http://git-scm.com/
.. _Pip: http://pip.pypa.io
.. _MPI: https//wikipedia.org/MPI
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu
.. _Neo: https://pythonhosted.org/neo/
.. _Matplotlib: http://matplotlib.org/
.. _YAML: http://www.yaml.org
.. _JSON: www.json.org/
.. _XML: https://www.w3.org/XML/