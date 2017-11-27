Pype9
=====

.. image:: https://travis-ci.org/NeuralEnsemble/pype9.svg?branch=master
    :target: https://travis-ci.org/NeuralEnsemble/pype9
.. image:: https://coveralls.io/repos/github/NeuralEnsemble/pype9/badge.svg?branch=master
    :target: https://coveralls.io/github/NeuralEnsemble/pype9?branch=master
.. image:: https://img.shields.io/pypi/pyversions/pype9.svg
    :target: https://pypi.python.org/pypi/pype9/
    :alt: Supported Python versions
.. image:: https://img.shields.io/pypi/v/pype9.svg
    :target: https://pypi.python.org/pypi/pype9/
    :alt: Latest Version    
.. image:: https://readthedocs.org/projects/pype9/badge/?version=latest
    :target: http://pype9.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status 

PYthon PipelinEs for 9ML (Pype9) is a collection of Python pipelines
for simulating networks of neuron models described in NineML_ with various
simulator backends.


Links
-----

* Documentation: http://pype9.readthedocs.org
* Mailing list: `NeuralEnsemble Google Group`_
* Issue tracker: https://github.com/NeuralEnsemble/pype9/issues


Supported Simulators
--------------------

Pype9 works with either or both of the following simulator backends

* Neuron_ >= 7.3
* NEST_ >= 2.12.0

Detailed instructions on how to install these simulators on different platforms
can be found in the `Installation documentation`_.


Unsupported NineML
------------------

NineML_ aims to be a comprehensive description language for neural simulation. This
means that it allows the expression of some uncommon configurations that are
difficult to implement in Neuron_ and NEST_. Work is planned to make the NEURON
and NEST pipelines in Pype9 support NineML_ fully, however until then the
following restrictions apply to models that can be used with Pype9.

* synapses must be linear
* synapses can only have one variable that varies over a projection (e.g.
  weight)
* no recurrent analog connections between populations (e.g. gap junctions)
* only one event send port per cell
* names given to NineML_ elements are not escaped and therefore can clash with
  built-in keywords and some PyPe9 method names (e.g. 'lambda' is a reserved
  keyword in Python). Please avoid using names that clash with C++ or Python
  keywords (NB: This will be fixed in future versions).


Examples
--------

Given a cell model described in NineML_ saved in
``my_hodgkin_huxley.xml``, the simulator pipeline can run from the command line:

.. code-block:: bash
   
   $ pype9 simulate my_hodgkin_huxley.xml#hh_props neuron 100.0 0.01 \
     --play isyn isyn.neo.pkl --record v v.neo.pkl --init_value v -65.0 mV
   
or in a Python script

.. code-block:: python

   from pype9.simulator.neuron import cell, Simulation
   from nineml import units as un
   
   HodgkinHuxley = cell.MetaClass('my_hodgkin_huxley.xml#hh_class')
   with Simulation(dt=0.01 * un.ms, seed=1234) as sim: 
      hh = HodgkinHuxley('my_hodgkin_huxley.xml#hh_props', v=-65.0 * un.mV)
      hh.record('v')
      sim.run(100.0 * un.ms)
   v = hh.recording('v')
   
Pype9 also supports network models described in NineML_ via integration with PyNN_

.. code-block:: bash
   
   $ pype9 simulate brunel.xml nest 1000.0 0.01 \
     --record Exc.spike_output Exc-nest.neo.pkl \
     --record Inh.spike_output Inh-nest.neo.pkl \
     --seed 12345
   
or

.. code-block:: python

   from pype9.simulator.neuron import Network, Simulation
   from nineml import units as un
   
   with Simulation(dt=0.01 * un.ms, seed=1234) as sim: 
      brunel_ai = Network('brunel.xml#AI')
      brunel_ai.component_array('Exc').record('spike_output')
      brunel_ai.component_array('Inh').record('spike_output')
      sim.run(1000.0 * un.ms)
   exc_spikes = brunel_ai.component_array('Exc').recording('spike_output')
   inh_spikes = brunel_ai.component_array('Inh').recording('spike_output')
   
See `Creating Simulations in Python`_ in the Pype9 docs for more examples and pipelines.

In addition to the ``simulate`` command there is also a ``plot`` command for
conveniently plotting the results of the simulation with Matplotlib_,
and a ``convert`` command to convert NineML_ files between different serialization
formats (XML, YAML, JSON and HDF5) and NineML_ versions (1.0 and 2.0dev). See the
documentation for details.


:copyright: Copyright 20012-2016 by the Pype9 team, see AUTHORS.
:license: MIT, see LICENSE for details.

.. _PyNN: http://neuralensemble.org/docs/PyNN/
.. _`NeuralEnsemble Google Group`: https://groups.google.com/forum/#!forum/neuralensemble
.. _Matplotlib: http://matplotlib.org
.. _`Creating Simulations in Python`: http://pype9.readthedocs.io/latest/scripting.html
.. _`Installation documentation`: http://pype9.readthedocs.io/en/latest/installation.html
.. _NineML: http://nineml.net
.. _NEST: https://nest-simulator.org
.. _Neuron: https://neuron.yale.edu.au
