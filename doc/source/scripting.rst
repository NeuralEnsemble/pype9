==============================
Creating Simulations in Python
==============================

Pype9 is loosely organised into sub-packages corresponding to
each pipeline (e.g. ``simulate``, ``plot``, etc...). The ``simulate``
package contains the sub-packages, ``neuron`` and ``nest``, which provide the
simulator-specific calls to their respective backends.

All classes required to design and run simulations in these packages derive
from corresponding classes in the ``base`` package, which defines a consistent
:ref:`API` across all backends. Therefore, code designed to run on with one
backend can be switched to another by simply changing the package the
simulator-specific classes are imported from (like PyNN_).

.. note::
    The ``neuron`` and ``nest`` packages can be imported separately. Therefore,
    only the simulator you plan to use needs to be available on your system.


Simulation Control
------------------

Simulation parameters such as time step, delay limits and
seeds for pseudo random number generators are set within an instance of the
:ref:`Simulation` class. Simulator objects (e.g. cells and connections)
can only be instantiated within the context of an active
:ref:`Simulation` instance, and there can only be one active :ref:`Simulation`
instance at any time.

A :ref:`Simulation` is activated with the ``with`` keyword 

.. code-block:: python

    with Simulation(dt=0.1 * un.ms, seed=12345) as sim:
        ...define simulation here...

The simulation is advanced using the ``run`` method of the :ref:`Simulation`
instance

.. code-block:: python

   with Simulation(dt=0.1 * un.ms, seed=12345) as sim:
        ...define simulation here...
        sim.run(100.0 * un.ms)
        
this can be done in stages if states or parameters need to be updated
mid-simulation 

.. code-block:: python

   with Simulation(dt=0.1 * un.ms, seed=12345) as sim:
        ...define simulation here...
        sim.run(50.0 * un.ms)
        ...update parameters/states...
        sim.run(50.0 * un.ms)

After the simulation context exits all objects in the simulator backend 
are destroyed (unless an exception is thrown) and only recordings can be
reliably accessed from the "dead" Pype9 objects.


Cell Simulations
----------------

NineML_ Dynamics classes can be translated into simulator cell objects using
the :ref:`CellMetaClass` class. A metaclass_ is class of classes, i.e. one
whose instantiation is itself a class, such as the ``type`` class.
:ref:`CellMetaClass` instantiations derive from the :ref:`Cell` class
and can be used to represent different classes of neural models, such as
Izhikevich or Hodgkin-Huxley for example. From these :ref:`Cell` classes as
many cell instances (with their corresponding simulator objects) can be created
as required e.g:

.. code-block:: python

    Izhikevich = CellMetaClass('./izhikevich.xml#Izhikevich')
    izhi1 = Izhikevich(a=1, b=2, c=3, d=4, v=-65 * un.mV, u=14 * un.mV / un.ms)
    izhi2 = Izhikevich(a=4, b=3, c=2, d=1, v=-70 * un.mV, u=50 * un.mV / un.ms)
    izhi3 = Izhikevich('./izhikevich.xml#IzhikevichBurster')
    
If the specified Dynamics class has not been built before the :ref:`CellMetaClass`
will automatically generate the required source code for the model, compile it,
and load it into the simulator namespace. This can happen either inside or
outside of an active :ref:`Simulation` instance. However, the cells objects
themselves must be instantiated within a :ref:`Simulation` instance.

.. code-block:: python

    Izhikevich = CellMetaClass('./izhikevich.xml#Izhikevich')
    with Simulation(dt=0.1 * un.ms) as sim:
        izhi = Izhikevich(a=1, b=2, c=3, d=4, v=-65 * un.mV,
                          u=14 * un.mV / un.ms)
        sim.run(1000.0 * un.ms)
        
The data can be recorded from every send port and state variable in the NineML_
Dynamics class using the ``record`` method of the :ref:`Cell` class. The
recorded data can then be accessed with the ``recording`` method.

.. code-block:: python

    Izhikevich = CellMetaClass('./izhikevich.xml#Izhikevich',
                               build_dir='.9build')
    with Simulation(dt=0.1 * un.ms) as sim:
        izhi = Izhikevich(a=1, b=2, c=3, d=4, v=-65 * un.mV,
                          u=14 * un.mV / un.ms)
        izhi.record('v')
        sim.run(1000.0 * un.ms)
    v = izhi.recording('v')

Data in Neo_ format can be "played" into receive ports of the :ref:`Cell`

.. code-block:: python

    i_syn = neo.PickleIO('./data/my_recording.neo.pkl').read()
    Izhikevich = CellMetaClass('./izhikevich.xml#Izhikevich')
    with Simulation(dt=0.1 * un.ms) as sim:
        izhi = Izhikevich(a=1, b=2, c=3, d=4, v=-65 * un.mV,
                          u=14 * un.mV / un.ms)
        izhi.play('i_syn', i_syn)
        sim.run(1000.0 * un.ms)
   
States and parameters can be accessed and set using the attributes of the
:ref:`Cell` objects 

.. code-block:: python

    Izhikevich = CellMetaClass('./izhikevich.xml#Izhikevich',
                               build_dir='.9build')
    with Simulation(dt=0.1 * un.ms) as sim:
        izhi = Izhikevich(a=1, b=2, c=3, d=4)
        sim.run(500.0 * un.ms)
        izhi.v = 20 * un.mV
        sim.run(500.0 * un.ms)

Event ports can be connected between individual cells

.. code-block:: python

    Poisson = CellMetaClass('./poisson.xml#Poisson')
    LIFAlphSyn = CellMetaClass('./liaf_alpha_syn.xml#LIFAlphaSyn')
    with Simulation(dt=0.1 * un.ms) as sim:
        poisson = Poisson(rate=10 * un.Hz, t_next=0.5 * un.ms)
        lif = LIFAlphaSyn('./liaf_alpha_syn.xml#LIFAlphaSynProps')
        lif.connect(poisson, 'spike_out', 'spike_in')
        sim.run(1000.0 * un.ms)


Network Simulations
-------------------

.. code-block:: python

    with Simulation(dt=0.1 * un.ms) as sim:
        network = Network('./brunel/AI.xml#AI')
        network.component_array('Exc').record('spike_out')
        sim.run(1000.0 * un.ms)
    spikes = network.component_array('Exc').recording('spike_out')



.. _NineML: http://nineml.net
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu
.. _PyNN: http://neuralensemble.org/docs/PyNN/
.. _Neo: https://pythonhosted.org/neo/
.. _metaclass: https://en.wikipedia.org/wiki/Metaclass#Python_example