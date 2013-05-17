"""

  This module contains extensions to the pyNN.connectors module

  @file ncml.py
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
import numpy
from pyNN.space import Space
from pyNN.connectors import MapConnector
from pyNN.parameters import LazyArray 


class CloneConnector(MapConnector):
    """
    Connects cells with the same connectivity pattern as a previous projection.
    """
    parameter_names = ('allow_self_connections',)

    def __init__(self, orig_proj, allow_self_connections=True, safe=True, callback=None):
        """
        Create a new CloneConnector.
        
        `orig_proj` -- the projection to clone the connectivity pattern from
        `allow_self_connections` -- if the connector is used to connect a
            Population to itself, this flag determines whether a neuron is
            allowed to connect to itself, or only to other neurons in the
            Population.
        `weights` -- may either be a float, a RandomDistribution object, a list/
                     1D array with at least as many items as connections to be
                     created. Units nA.
        `delays`  -- as `weights`. If `None`, all synaptic delays will be set
                     to the global minimum delay.
        `space` -- a `Space` object, needed if you wish to specify distance-
                   dependent weights or delays
        """
        MapConnector.__init__(self, safe, callback=callback)
        self.orig_proj = orig_proj
        self.allow_self_connections = allow_self_connections

    def connect(self, projection):
        conn_list = numpy.array([(self.orig_proj.pre.id_to_index(c.source),
                                  self.orig_proj.post.id_to_index(c.target))
                                 for c in self.orig_proj.connections])
        conn_matrix = numpy.zeros((projection.pre.size, projection.post.size))
        conn_matrix[conn_list[:,0], conn_list[:,1]] = True
        connection_map= LazyArray(conn_matrix)
        self._connect_with_map(connection_map)