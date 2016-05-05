//
//  set_parameters_and_state.h
//
//  Created by Tom Close on 12/04/2016.
//  Copyright © 2016 Tom Close. All rights reserved.
//

#ifndef setup_h
#define setup_h

#include "random.h"

#include "models/IzhikevichMaster.h"
#include "models/PyNNLeakyIntegrateAndFire.h"
#include "models/IafAlpha.h"
#include "models/IzhikevichBranch.h"

#define _Izhikevich_ 1
#define _PyNNLeakyIntegrateAndFire_ 2
#define _IafAlpha_ 3
#define _Poisson_ 4

//#define MASTER_CHOICE _PyNNLeakyIntegrateAndFire_
#define MASTER_CHOICE _IafAlpha_
//#define MASTER_CHOICE _Izhikevich_
//#define BRANCH_CHOICE _Izhikevich_

double dt = 0.25;

#if MASTER_CHOICE == _Izhikevich_

#define MASTER IzhikevichMaster
#define CURRENT_INJECTION
#define INJECTION_PORT Isyn_analog_port
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

#elif MASTER_CHOICE == _PyNNLeakyIntegrateAndFire_

#define MASTER PyNNLeakyIntegrateAndFire
#define CURRENT_INJECTION
#define INJECTION_PORT i_synaptic_analog_port
#define INJECTION_AMPLITUDE 500 // pA

inline void set_status(Dictionary& status) {
    status.insert(Name("v_reset"), Token(-70.0));
    status.insert(Name("refractory_period"), Token(2.0));
    status.insert(Name("Cm"), Token(250.0));
    status.insert(Name("g_leak"), Token(25.0));
    status.insert(Name("v_threshold"), Token(-55.0));
    status.insert(Name("e_leak"), Token(-70.0));
    status.insert(Name("v"), Token(-65.0));
    status.insert(Name("end_refractory"), Token(0.0));
}

#elif MASTER_CHOICE == _IafAlpha_

#define MASTER IafAlpha
#define INCOMING_SPIKES
#define INCOMING_SPIKE_PORT input_spike_event_port
#define INCOMING_SPIKE_WEIGHT 367.55
#define INCOMING_SPIKE_FREQUENCY 50

inline void set_status(Dictionary& status) {
    status.insert(Name("v_reset__cell"), Token(-70.0));
    status.insert(Name("refractory_period__cell"), Token(2.0));
    status.insert(Name("Cm__cell"), Token(250.0));
    status.insert(Name("g_leak__cell"), Token(25.0));
    status.insert(Name("v_threshold__cell"), Token(-55.0));
    status.insert(Name("e_leak__cell"), Token(-70.0));
    status.insert(Name("v__cell"), Token(-65.0));
    status.insert(Name("end_refractory__cell"), Token(0.0));
    status.insert(Name("tau__psr__syn"), Token(0.1));
    status.insert(Name("a__psr__syn"), Token(0.0));
    status.insert(Name("b__psr__syn"), Token(0.0));
}

#elif MASTER_CHOICE == _Poisson_

#define MASTER Poisson

inline void set_status(Dictionary& status) {
    status.insert(Name("per_time"), Token(100.0));
    status.insert(Name("t_next"), Token(0.0));
}


#endif

#ifdef BRANCH_CHOICE

#if BRANCH_CHOICE == _Izhikevich_

#define BRANCH IzhikevichBranch

#endif

#endif

template <class NodeType> void set_ring_buffers(NodeType& node) {

    unsigned int buffer_length = NUM_SLICES * nest::Scheduler::min_delay;
    double total_time = buffer_length * dt;

#ifdef INCOMING_SPIKES
    nest::ListRingBuffer& input = node.B_.INCOMING_SPIKE_PORT;

    double spike_period = 1000.0 / INCOMING_SPIKE_FREQUENCY;

    std::cout << "total time: " << total_time << std::endl;
    std::cout << "spike period: " << spike_period << std::endl;

    for (double t = 0.0; t < total_time; t += spike_period)
        if (t > total_time / 2.0)
            input.append_value((int)floor(t/dt), INCOMING_SPIKE_WEIGHT);
#endif

#ifdef CURRENT_INJECTION
    nest::RingBuffer& isyn = node.B_.INJECTION_PORT;

    for (long_t i = 0; i < buffer_length; ++i)
        if (i < buffer_length / 2)
            isyn.set_value(i, 0.0);
        else
            isyn.set_value(i, INJECTION_AMPLITUDE);
#endif
}

#endif /* setup_h */
