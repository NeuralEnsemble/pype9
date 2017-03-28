===============
Getting started
===============


Reading model descriptions from XML files
=========================================

NineML XML files can contain abstraction layer models, user layer models (with links to abstraction layer models
defined elsewhere) or both.

To read a file containing only abstraction layer elements:

.. code-block:: python

   >>> import nineml
   >>> items = nineml.read("BrunelIaF.xml")
   >>> items
   {'BrunelIaF': <dynamics.ComponentClass BrunelIaF>,
    'current': Dimension(name='current', i=1),
    'resistance': Dimension(name='resistance', i=-2, m=1, t=-3, l=2),
    'time': Dimension(name='time', t=1),
    'voltage': Dimension(name='voltage', i=-1, m=1, t=-3, l=2)}
