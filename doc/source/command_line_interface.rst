======================
Command Line Interface
======================

The Pype9 command line tool, ``pype9``, will be installed along with the Python library
when it is installed with pip.

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

Simulate
--------

.. argparse::
    :module: pype9.cmd.simulate
    :func: argparser
    :prog: pype9 simulate


Examples
^^^^^^^^
`todo`

Plot
----

.. argparse::
    :module: pype9.cmd.plot
    :func: argparser
    :prog: pype9 plot

Examples
^^^^^^^^

`todo`

Convert
-------

.. argparse::
    :module: pype9.cmd.convert
    :func: argparser
    :prog: pype9 convert


Examples
^^^^^^^^
 `todo`