==========
Public API
==========

The Pype9 public API consists of seven classes required to create simulations
of individual neurons or neural networks described in NineML_. All classes in
the public API have an abstract base class in the ``pype9.simulate.base``
module and matching derived simulator-specific classes in the
``pype9.simulate.neuron`` and ``pype9.simulate.nest`` modules.

As the simulator-specific classes have the same signatures as those in the base
module only the base module classes are described here.

Simulation
----------

.. autoclass:: pype9.simulate.base.simulation.Simulation
    :members: run


CellMetaClass
-------------

.. autoclass:: pype9.simulate.base.cells.CellMetaClass


Cell
----

.. autoclass:: pype9.simulate.base.cells.Cell
    :members: record, recording, record_regime, regime_epochs, play, connect


Network
-------

.. autoclass:: pype9.simulate.base.network.Network
    :members: component_array, connection_group, component_arrays, connection_groups


Component Array
---------------
 
.. autoclass:: pype9.simulate.base.network.ComponentArray
    :members: record, recording, play


Connection Group
----------------

.. autoclass:: pype9.simulate.base.network.ConnectionGroup


Selection
---------

.. autoclass:: pype9.simulate.base.network.Selection


.. _NineML: http://nineml.net
