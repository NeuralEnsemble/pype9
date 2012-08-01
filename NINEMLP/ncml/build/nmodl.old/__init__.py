"""

  This package contains code to import the appropriate mechanisms into NEURON and python

  
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

from cell._base.NEURON import nrn

# Only handles simple case at this stage, should be extended to include different simulators, compilations
nrn.nrn_load_dll("mech/x86_64/.libs/libnrnmech.so.0")
