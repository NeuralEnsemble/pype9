======================
Command Line Interface
======================

The Pype9 command line tool will be installed along with the Python library
when it is installed with pip.

Help
----

The available pipelines can be listed with::

   $ pype help
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

   $ pype help plot
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
    
Runs a simulation described by an Experiment layer 9ML file
    
Positional arguments
^^^^^^^^^^^^^^^^^^^^
    model:
        Path to nineml model file which to simulate. It can be
        a relative path, absolute path, URL or if the path
        starts with '//' it will be interpretedas a
        ninemlcatalog path. For files with multiple
        components, the name of component to simulated must be
        appended after a #, e.g. //neuron/izhikevich#izhikevich
    {neuron,nest}:
        Which simulator backend to use
    time:
        Time to run the simulation for
    timestep:
        Timestep used to solve the differential equations
    
Optional arguments
^^^^^^^^^^^^^^^^^^

    -h, --help            show this help message and exit
    --prop PARAM VALUE UNITS
                        Set the property to the given value
    --init_regime INIT_REGIME
                        Initial regime for dynamics
    --init_value STATE-VARIABLE VALUE UNITS
                        Initial regime for dynamics
    --record PORT/STATE-VARIABLE FILENAME
                        Record the values from the send port or state variable
                        and the filename to save it into
    --play PORT FILENAME  Name of receive port and filename with signal to play
                        it into
    --seed SEED           Random seed used to create network and properties
    --build_mode BUILD_MODE
                        The strategy used to build and compile the model. Can
                        be one of '{}' (default lazy)


Plot
----

Convenient script for plotting the output of PyPe9 simulations (actually not
9ML specific as the signals are stored in Neo format)

Positional arguments
^^^^^^^^^^^^^^^^^^^^
  filename:
    Neo file outputted from a PyPe9 simulation

Optional arguments
^^^^^^^^^^^^^^^^^^
    -h, --help            show this help message and exit
    --save SAVE           Location to save the figure to
    --height HEIGHT       Height of the plot
    --width WIDTH         Width of the plot
    --hide                Whether to show the plot or not
    --resolution RESOLUTION
                        Resolution of the figure when it is saved


Convert
-------

usage: pype9 convert [-h] [--nineml_version NINEML_VERSION] in_file out_file

Converts a 9ML file from one supported format to another

Positional arguments
^^^^^^^^^^^^^^^^^^^^
    in_file:
        9ML file to be converted
    out_file:
        Converted filename

Optional arguments
^^^^^^^^^^^^^^^^^^
    -h, --help            show this help message and exit
    --nineml_version NINEML_VERSION
                        The version of nineml to output