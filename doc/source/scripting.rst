==============================
Creating Simulations in Python
==============================

Pype9's ``simulate`` package is organised into ``base``, ``neuron`` and
``nest`` sub-packages. The ``base`` contains abstract base classes
and code that is common to both ``neuron`` and ``nest``. ``neuron`` and
``nest`` can be imported independently of each other meaning that only the
simulator(s) you plan to use needs to be installed on your system.

The public API (i.e. key classes) is consistent between ``base``, ``neuron``
and ``nest`` so code designed to run on with one simulator backend can be
switched to the other by simply changing the sub-package the classes were
imported from. Therefore, while the remainder of this page describes classes
in the ``base`` sub-package they are interchangeable with the Neuron_ and NEST_
versions.

Simulation Control
------------------

Kernel parameters such as simulator time step, delay limits and
seeds for pseudo random number generators are set within an instance of the
:ref:`Simulation` class. Simulator objects (i.e. cells and connection
instances) can only be created within the context of an active :ref:`Simulation`
instance. A :ref:`Simulation` instance is typically activated by "entering"
its context via the ``with`` keyword e.g.:

.. code-block:: python

    with Simulation(dt=0.1 * un.ms, seed=12345) as sim:
        ...create models here...
        


Individual Cells
----------------

Network
-------

.. _9ML: http://nineml.net
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu