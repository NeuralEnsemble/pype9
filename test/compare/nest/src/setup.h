//
//  set_parameters_and_state.h
//
//  Created by Tom Close on 12/04/2016.
//  Copyright © 2016 Tom Close. All rights reserved.
//

#ifndef conditions_h
#define conditions_h

#include "mock_nest.h"

#define INJECTION_AMPLITUDE 20 // pA

inline void set_status(Dictionary& status) {
    status.insert(Name("C_m"), Token(1.0));
    status.insert(Name("a"), Token(0.2));
    status.insert(Name("alpha"), Token(0.04));
    status.insert(Name("b"), Token(0.025));
    status.insert(Name("beta"), Token(5.0));
    status.insert(Name("c"), Token(-75.0));
    status.insert(Name("d"), Token(0.2));
    status.insert(Name("theta"), Token(-50.0));
    status.insert(Name("zeta"), Token(140.0));
    status.insert(Name("U"), Token(-14.0));
    status.insert(Name("V"), Token(-65.0));
}

template <class NodeType> void set_ring_buffers(NodeType& node) {
    
    long_t buffer_length = NUM_SLICES * nest::Scheduler::min_delay;
    nest::RingBuffer& isyn = node.B_.Isyn_analog_port;
    
    for (long_t i = 0; i < buffer_length; ++i)
        if (i < buffer_length / 2)
            isyn.set_value(i, 0.0);
        else
            isyn.set_value(i, INJECTION_AMPLITUDE);
}

#endif /* status_h */
