
.. image:: logo_small.png
   :align: right
   :width: 200

Pype9
=====


"PYthon PipelinEs for 9ml (Pype9)" is a collection of Python pipelines
to simulate neuron, and neuron network, models described in NineML
(http://nineml.net), using either *Neuron* (http://neuron.yale.edu)
or *NEST* (http://nest-simulator.org) as simulator backends.

Pype9 can be used from the command line, via a number of convenient tools,
which allow experiments to be designed and simulated without needing to use a
programming language[&dagger;]_. Alternatively, the simulations can be created
by using the Pype9 Python API directly.

User guide
----------

.. toctree::
    :maxdepth: 2 

    installation
    command_line_interface
    python_api
    getting_help

.. [&dagger;]: However, desiging experiments with the CLI does require the
               knowledge of one of the supported markup languages (e.g. XML,
               JSON, YAML) and the `NineML specification`_.
.. _NineML: http://nineml.net
.. _`NineML specification`: http://nineml.net/specification/