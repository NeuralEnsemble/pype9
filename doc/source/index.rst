
.. image:: logo_small.png
   :align: right

Pype9
=====


"PYthon PipelinEs for 9ml (Pype9)" is a collection of Python pipelines to
simulate neuron, and neuron network, models described in NineML_ using either
Neuron_ or NEST_ as simulator backends.

Pype9 has a command line interface (CLI), which allows experiments to be
designed and simulated without programming*.  Alternatively, simulations
can be scripted using Pype9's Python API

User guide
----------

.. toctree::
    :maxdepth: 2 

    installation
    command_line_interface
    python_api
    getting_help

.. [*] Designing the 9ML models used by the CLI currently requires 
       knowledge of one of the formats supported by the
       `NineML Python Library`_ (e.g.XML, JSON, YAML) and the
       `NineML specification`_, although a graphical UI is planned for the
       future.
.. _NineML: http://nineml.net
.. _`NineML Python Library`: http://nineml.readthedocs.io
.. _`NineML specification`: http://nineml.net/specification/
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu