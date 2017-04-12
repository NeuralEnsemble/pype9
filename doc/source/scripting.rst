==============================
Creating Simulations in Python
==============================

The Pype9 package is organised into sub-packages corresponding to the pipelines
it (e.g. ``simulate``, ``plot``, etc...). The ``simulate`` package contains the
sub-packages, ``neuron`` and ``nest``, which provide the simulator-specific
calls to their respective backends.

 
All classes required to design and run simulations in these packages derive from
corresponding classes in the ``base`` package, which defines a consistent
:ref:`Public API` across all backends. Therefore, code designed to run on with
one backend can be switched to another by simply changing the package the
simulator-specific classes are imported from (like PyNN_).

.. note::
    The ``neuron`` and ``nest`` packages can be imported separately. Therefore,
    only the simulator you plan to use needs to be available on your system.


Simulation Control
------------------

Simulation parameters such as time step, delay limits and seeds for pseudo
random number generators are set within an instance of the :ref:`Simulation`
class. Simulator objects (e.g. cells and connections) can only be instantiated
within the context of an active :ref:`Simulation` instance, and there can only
be one active :ref:`Simulation` instance at any time.

A :ref:`Simulation` is activated with the ``with`` keyword 

.. code-block:: python

    with Simulation(dt=0.1 * un.ms, seed=12345) as sim:
        # Design simulation here

The simulation is advanced using the ``run`` method of the :ref:`Simulation`
instance

.. code-block:: python

   with Simulation(dt=0.1 * un.ms, seed=12345) as sim:
        # Create simulator objects here
        sim.run(100.0 * un.ms)
        
this can be done in stages if states or parameters need to be updated
mid-simulation 

.. code-block:: python

   with Simulation(dt=0.1 * un.ms, seed=12345) as sim:
        # Create simulator objects here
        sim.run(50.0 * un.ms)
        # Update simulator object parameters/state-variables
        sim.run(50.0 * un.ms)

After the simulation context exits all objects in the simulator backend are
destroyed (unless an exception is thrown) and only recordings can be reliably
accessed from the "dead" Pype9 objects.


Cell Simulations
----------------

NineML_ Dynamics classes can be translated into simulator cell objects using the
:ref:`CellMetaClass` class. A metaclass_ is class of classes, i.e. one whose
instantiation is itself a class, such as the ``type`` class.
:ref:`CellMetaClass` instantiations derive from the :ref:`Cell` class and can
be used to represent different classes of neural models, such as Izhikevich or
Hodgkin-Huxley for example. From these :ref:`Cell` classes as many cell
instances (with their corresponding simulator objects) can be created as
required e.g:

.. code-block:: python

    # Create Izhikevich cell class by instantiating the CellMetaClass with a
    # ninml.Dynamics Izhikevich model
    Izhikevich = CellMetaClass('./izhikevich.xml#Izhikevich')
    # Parameters and states of the cell class must be provided when the cells
    # are instantiated.
    # either as keyword args
    izhi1 = Izhikevich(a=1, b=2, c=3, d=4, v=-65 * un.mV, u=14 * un.mV / un.ms)
    # or from a nineml.DynamicsProperties object
    izhi3 = Izhikevich('./izhikevich.xml#IzhikevichBurster')
    
If the specified Dynamics class has not been built before the
:ref:`CellMetaClass` will automatically generate the required source code for
the model, compile it, and load it into the simulator namespace. This can
happen either inside or outside of an active :ref:`Simulation` instance.
However, the cells objects themselves must be instantiated within a
:ref:`Simulation` instance.

.. code-block:: python

    # The cell class can be created outside the simulation context
    Izhikevich = CellMetaClass('./izhikevich.xml#Izhikevich')
    with Simulation(dt=0.1 * un.ms) as sim:
        # The cell object must be instantiated within the simulation context
        izhi = Izhikevich(a=1, b=2, c=3, d=4, v=-65 * un.mV,
                          u=14 * un.mV / un.ms)
        sim.run(1000.0 * un.ms)
        
The data can be recorded from every send port and state variable in the NineML_
Dynamics class using the ``record`` method of the :ref:`Cell` class. The
recorded data can then be accessed with the ``recording`` method. The
recordings will be Neo_ format.

.. code-block:: python

    Izhikevich = CellMetaClass('./izhikevich.xml#Izhikevich',
                               build_dir='.9build')
    with Simulation(dt=0.1 * un.ms) as sim:
        izhi = Izhikevich(a=1, b=2, c=3, d=4, v=-65 * un.mV,
                          u=14 * un.mV / un.ms)
        # Specify the variables to record
        izhi.record('v')
        sim.run(1000.0 * un.ms)
    # Retrieve the recording
    v = izhi.recording('v')

Data in Neo_ format can be "played" into receive ports of the :ref:`Cell`

.. code-block:: python

    neo_data = neo.PickleIO('./data/my_recording.neo.pkl').read()
    Izhikevich = CellMetaClass('./izhikevich.xml#Izhikevich')
    with Simulation(dt=0.1 * un.ms) as sim:
        izhi = Izhikevich(a=1, b=2, c=3, d=4, v=-65 * un.mV,
                          u=14 * un.mV / un.ms)
        # Play analog signal (must be of current dimension) into 'i_syn'
        # analog-receive port.
        izhi.play('i_syn', neo_data.analogsignals[0])
        sim.run(1000.0 * un.ms)
   
States and parameters can be accessed and set using the attributes of the
:ref:`Cell` objects 

.. code-block:: python

    Izhikevich = CellMetaClass('./izhikevich.xml#Izhikevich',
                               build_dir='.9build')
    with Simulation(dt=0.1 * un.ms) as sim:
        izhi = Izhikevich(a=1, b=2, c=3, d=4)
        sim.run(500.0 * un.ms)
        # Update the membrane voltage after 500 ms to 20 mV
        izhi.v = 20 * un.mV
        sim.run(500.0 * un.ms)

Event ports can be connected between individual cells

.. code-block:: python

    Poisson = CellMetaClass('./poisson.xml#Poisson')
    LIFAlphSyn = CellMetaClass('./liaf_alpha_syn.xml#LIFAlphaSyn')
    with Simulation(dt=0.1 * un.ms) as sim:
        poisson = Poisson(rate=10 * un.Hz, t_next=0.5 * un.ms)
        lif = LIFAlphaSyn('./liaf_alpha_syn.xml#LIFAlphaSynProps')
        # Connect 'spike_out' event-send port of the poisson cell to
        # the 'spike_in' event-receive port on the leaky-integrate-and-fire
        # cell 
        lif.connect(poisson, 'spike_out', 'spike_in')
        sim.run(1000.0 * un.ms)


Network Simulations
-------------------

Network simulations are specified in much the same way as `Cell Simulations`_,
with the exception that there is no metaclass for Networks (Network metaclasses
will be added  when the "Structure Layer" is introduced in NineML_ v2).
Therefore, :ref:`Network` objects need to be instantiated within the simulation
context.

.. code-block:: python

    with Simulation(dt=0.1 * un.ms) as sim:
        # Network objects need to be instantiated within the simulation context
        network = Network('./brunel/AI.xml#AI')
        sim.run(1000.0 * un.ms)
        
During construction of the network, the NineML_ Populations and Projections are
flattened into :ref:`Component Array` and :ref:`Connection Group` objects such
that the synapse dynamics in the projection are included in the dynamics of the
:ref:`Component Array` and each port connection is converted into a separate
:ref:`Connection Group` of static connections.

To record data, the relevant component array needs to be accessed using the
``component_array`` or ``component_arrays`` accessors of the network class.
Then as in the `Cell Simulations`_ case the ``record`` method is used to
specify which variables to record and the ``recording`` method is used to
access the recording after the simulation.

.. code-block:: python

    with Simulation(dt=0.1 * un.ms) as sim:
        network = Network('./brunel/AI.xml#AI')
        # 'spike_out' is explicitly connected in the connection so it is
        # mapped to the global namespace of the flattened cell + synapses model
        network.component_array('Exc').record('spike_out')
        # State-variables of the cell dynamics are suffixed with '__cell'
        network.component_array('Inh').record('v__cell')
        # State-variables of synapses, in this case synapses from the 
        # 'Inhibition' projection, are prefixed with '__<projection-name>'
        network.component_array('Exc').record('a__Inhibition')
        sim.run(1000.0 * un.ms)
    exc_spikes = network.component_array('Exc').recording('spike_out')
    inh_v = network.component_array('Inh').recording('v__cell')
    exc_inh_a = network.component_array('Exc').recording('a__Inhibition')
    

.. note::

    During the cell and synapse flattening process the names of state variables
    and unconnected ports will be suffixed with ``__cell`` if they belong to the
    population dynamics or ``__<my-projection>`` if they belong to the synapse
    of the a projection

Network models are simulated via integration with PyNN_ and therefore will run
on multiple processes using `Open MPI`_ (and `Open MP_` for NEST_) if the
calling Python script is run with ``mpirun``/``mpiexec``. 

 
.. _`Open MPI`: http://openmpi.org
.. _`Open MP`: http://openmp.org
.. _NineML: http://nineml.net
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu
.. _PyNN: http://neuralensemble.org/docs/PyNN/
.. _Neo: https://pythonhosted.org/neo/
.. _metaclass: https://en.wikipedia.org/wiki/Metaclass#Python_example