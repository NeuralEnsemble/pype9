
Pype9
=====


"PYthon PipelinEs for 9ml (Pype9)" is a collection of Python pipelines to
simulate neuron, and neuron network, models described in NineML_ using either
Neuron_ or NEST_ as simulator backends.

Pype9 has a command line interface (CLI), which allows experiments to be
designed and simulated without any scripting*.  Alternatively, simulations
can be scripted using Pype9's Python API, or generated cell class can be
integrated with native simulations.

User/Developer guide
--------------------

.. toctree::
    :maxdepth: 2 

    installation
    cli
    scripting
    add_backends
    api
    getting_help

.. [*] Designing the 9ML models used by the CLI currently requires 
       knowledge of one of the model description formats supported by the
       `NineML Python Library`_ (e.g. XML, JSON or YAML) and the
       `NineML specification`_ although a graphical UI is planned.

.. _NineML: http://nineml.net
.. _`NineML Python Library`: http://nineml.readthedocs.io
.. _`NineML specification`: http://nineml.net/specification/
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu