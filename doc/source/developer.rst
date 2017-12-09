=======================
Developer Documentation
=======================

Contributions to Pype9 are most welcome! To contribute simply fork
Pype9 on Github_ and create a pull request when you are ready to merge
your code.

Contributions are required to:
* Strictly adhere to Pep8_ (PyLint_ is useful for checking this)
* Not significantly decrease the `code coverage`_. Meaning that you
will probably need to add a unittest or two.


Additional Simulator Backends
-----------------------------

An area in which Pype9 can be extended is by adding support for
additional simulator backends (e.g. Brian2_, GeNN_), including any
that you may be developing.

One of the key benefits of clearly separating the model description
language (i.e. NineML_), and the associated `NineML Python library`_,
from simulator-specific code is that provides a clearly defined
interface for adding support for additional simulators. Therefore,
extending Pype9 is definitely not a requirement for adding NineML_
support for your simulator (and from a language perspective a diversity
of independent tools is desirable).  However, since Pype9 has already
implemented many of the menial tasks involved in working with NineML_
models, such as managing the build process and file IO, you may find it
convenient to extend Pype9's base classes.

In order to extend Pype9's base classes you will need to override the
following abstract methods.

Single Cell Simulations
~~~~~~~~~~~~~~~~~~~~~~~

CodeGenerator
^^^^^^^^^^^^^

* :meth:`pype9.simulate.common.code_gen.CodeGenerator.generate_source_files`
* configure_build_files
* compile_source_files
* clean_src_dir
* clean_compile_dir
* load_libraries

Cell
^^^^

* _get
* _set
* _set_regime
* record
* record_regime
* recording
* _regime_recording
* reset_recordings
* play
* connect

Network Simulations
~~~~~~~~~~~~~~~~~~~

At this stage Pype9's network simulations are handled by PyNN_ so it
is probably only practical to add support for simulators that are
supported by PyNN. Future versions of Pype9 will likely introduce
base classes for network objects, which can be extended though. 


Additional Pipelines
--------------------

Pype9 has been designed to be a general umbrella containing a wide range
of pipelines for manipulating and working with NineML_ models in
addition to running simulations.

Import Simulator-Specific Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

High on the list of useful additional pipelines are importer pipelines
that take models, or part thereof, written in simulator specific code
and translate them into NineML_.

For example, a prototype NMODL_ and Neuron_ "model view" importers
exists in the branch *neuron_import* at http://github.com/tclose/pype9.
It would be great to extend this to other popular simulators such as
NEST and Brian. 

Graphical User Interface
~~~~~~~~~~~~~~~~~~~~~~~~

Another key benefit of separating the model description from the
simulation code is that it greatly simplifies the creation of graphical
user interfaces with which to create models with. With the
`NineML Python Library`_ able to read JSON files, a promising approach
would be to create a javascript GUI that can read, modify and write
NineML_ files to JSON that could then be simulated with different
backends.


.. _NineML: http://nineml.net
.. _GitHub: https://github.com/NeuralEnsemble/pype9
.. _PyNN: http://neuralensemble.org/PyNN/
.. _GeNN: http://genn-team.github.io/genn/
.. _Brian2: https://brian2.readthedocs.io/en/stable/
.. _NEST: http://nest-simulator.org
.. _Neuron: http://neuron.yale.edu
.. _Pep8: https://www.python.org/dev/peps/pep-0008/
.. _PyLint: https://pypi.python.org/pypi/pylint
.. _`NineML Python library`: http://nineml-python.readthedocs.io/en/latest/
.. _`code coverage`: https://coveralls.io/github/NeuralEnsemble/pype9?branch=master
