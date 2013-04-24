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
from pyNN.connectors import Connector, ProbabilisticConnector


class CloneConnector(Connector):
    """
    Connects cells with the same connectivity pattern as a previous projection.
    """
    parameter_names = ('allow_self_connections',)

    def __init__(self, orig_proj, allow_self_connections=True, weights=0.0, delays=None,
                 space=Space(), safe=True, verbose=False):
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
        Connector.__init__(self, weights, delays, space, safe, verbose)
        self.orig_proj = orig_proj
        self.allow_self_connections = allow_self_connections

    def connect(self, projection):
        connector = ProbabilisticConnector(projection, self.weights, self.delays,
                                           self.allow_self_connections, self.space, safe=self.safe)
        self.progressbar(len(projection.pre))
        conn_list = numpy.array([(self.orig_proj.pre.id_to_index(c.source),
                                  self.orig_proj.post.id_to_index(c.target))
                                 for c in self.orig_proj.connections])
        # Borrowed this part of the algorithm from the pyNN.connectors.FromListConnector
        conn_list = conn_list[numpy.argsort(conn_list[:, 0])]
        self.sources = numpy.unique(conn_list[:, 0]).astype(numpy.int)
        self.candidates = projection.post.local_cells
        left = numpy.searchsorted(conn_list[:, 0], self.sources, 'left')
        right = numpy.searchsorted(conn_list[:, 0], self.sources, 'right')
        for count, (src, l, r) in enumerate(zip(self.sources, left, right)):
            targets = conn_list[l:r, 1]
            # Use Probabilistic connector to enable the weight and delay expressions to be set by 
            # the distance and/or probabilistic connectors 
            connector._probabilistic_connect(projection.pre[src], targets)
            self.progression(count, projection._simulator.state.mpi_rank)
