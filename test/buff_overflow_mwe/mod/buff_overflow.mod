TITLE Spiking node generated from 9ML using PyPe9 version 0.1 at 'Tue 31 Oct 17 05:11:29PM'

NEURON {
    POINT_PROCESS BuffOverflow
    NONSPECIFIC_CURRENT i___pype9
    : T
    RANGE regime_
    

    :StateVariables:
    RANGE refractory_end__cell
    RANGE a__psr__Excitation
    RANGE b__psr__Excitation
    RANGE a__psr__Inhibition
    RANGE b__psr__Inhibition
    RANGE a__psr__External
    RANGE b__psr__External
    RANGE v
    RANGE v_clamp___pype9

    :Parameters
    RANGE refractory_period__cell
    RANGE tau__cell
    RANGE R__cell
    RANGE v_reset__cell
    RANGE v_threshold__cell
    RANGE tau__psr__Excitation
    RANGE weight__pls__Excitation
    RANGE tau__psr__Inhibition
    RANGE weight__pls__Inhibition
    RANGE tau__psr__External
    RANGE weight__pls__External
    RANGE cm___pype9

    : Analog receive ports

    :Aliases
    RANGE i_synaptic__psr__Excitation
    RANGE fixed_weight__pls__Excitation
    RANGE weight__psr__Excitation
    RANGE i_synaptic__psr__Inhibition
    RANGE fixed_weight__pls__Inhibition
    RANGE weight__psr__Inhibition
    RANGE i_synaptic__psr__External
    RANGE fixed_weight__pls__External
    RANGE weight__psr__External
    RANGE i_synaptic__cell
    RANGE i___pype9

    :Connection Parameters

}

UNITS {
    : Define symbols for base units
    (mV) = (millivolt)
    (nA) = (nanoamp)
    (nF) = (nanofarad)
    (uF) = (microfarad)
    (S)  = (siemens)
    (uS) = (microsiemens)
    (mM) = (milli/liter)
    (um) = (micrometer)
}

CONSTANT {
    : IDs for regimes, events and conditions 

    : Transition flags
    INIT = -1    
    ON_EVENT = 0

    : Regime ids
    SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY = 0
    SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD = 1

    : Event port ids
    INPUT_SPIKE__PSR__EXCITATION = 0
    INPUT_SPIKE__PSR__INHIBITION = 1
    INPUT_SPIKE__PSR__EXTERNAL = 2

}

INITIAL {

    : Initialise the NET_RECEIVE block by sending appropriate flag to itself
    net_send(0, INIT)
}

PARAMETER {
    : True parameters
    refractory_period__cell = 0 (ms)
    tau__cell = 0 (ms)
    R__cell = 0 (1/uS)
    v_reset__cell = 0 (mV)
    v_threshold__cell = 0 (mV)
    tau__psr__Excitation = 0 (ms)
    weight__pls__Excitation = 0 (nA)
    tau__psr__Inhibition = 0 (ms)
    weight__pls__Inhibition = 0 (nA)
    tau__psr__External = 0 (ms)
    weight__pls__External = 0 (nA)
    cm___pype9 = 0 (nF)

    : Constants
    g_clamp___pype9 = 100000000.0 (uS)

    : Units for connection properties
 

    : Unit correction for 't' used in printf in order to get modlunit to work.
    PER_MS = 1 (/ms)
}


ASSIGNED {
    : Internal flags
    regime_
    found_transition_
    
    : Analog receive ports

    : Aliases
    i_synaptic__psr__Excitation (nA)
    fixed_weight__pls__Excitation (nA)
    weight__psr__Excitation (nA)
    i_synaptic__psr__Inhibition (nA)
    fixed_weight__pls__Inhibition (nA)
    weight__psr__Inhibition (nA)
    i_synaptic__psr__External (nA)
    fixed_weight__pls__External (nA)
    weight__psr__External (nA)
    i_synaptic__cell (nA)
    i___pype9 (nA)

    : State variables without explicit derivatives
    refractory_end__cell (ms)
    v (mV)
    v_clamp___pype9 (mV)

    :Connection Parameters
}

STATE {
    a__psr__Excitation (nA)
    b__psr__Excitation (nA)
    a__psr__Inhibition (nA)
    b__psr__Inhibition (nA)
    a__psr__External (nA)
    b__psr__External (nA)
}


BREAKPOINT {
    SOLVE states METHOD derivimplicit
    i_synaptic__psr__Excitation = a__psr__Excitation
    i_synaptic__psr__Inhibition = a__psr__Inhibition
    i_synaptic__psr__External = a__psr__External
    i_synaptic__cell = i_synaptic__psr__Excitation + i_synaptic__psr__External + i_synaptic__psr__Inhibition
    if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY) {
        i___pype9 = g_clamp___pype9*(v - v_clamp___pype9)
    } else {
        i___pype9 = -cm___pype9*(R__cell*i_synaptic__cell - v)/tau__cell
    }
}


DERIVATIVE states {
    a__psr__Excitation' = deriv_a__psr__Excitation(a__psr__Excitation, b__psr__Excitation)
    b__psr__Excitation' = deriv_b__psr__Excitation(b__psr__Excitation)
    a__psr__Inhibition' = deriv_a__psr__Inhibition(a__psr__Inhibition, b__psr__Inhibition)
    b__psr__Inhibition' = deriv_b__psr__Inhibition(b__psr__Inhibition)
    a__psr__External' = deriv_a__psr__External(a__psr__External, b__psr__External)
    b__psr__External' = deriv_b__psr__External(b__psr__External)
}

FUNCTION deriv_a__psr__Excitation(a__psr__Excitation (nA), b__psr__Excitation (nA)    ) (nA/ms) {
    if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY) {
        deriv_a__psr__Excitation = (-a__psr__Excitation + b__psr__Excitation)/tau__psr__Excitation
    
    } else if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD) {
        deriv_a__psr__Excitation = (-a__psr__Excitation + b__psr__Excitation)/tau__psr__Excitation
    }
}
FUNCTION deriv_b__psr__Excitation(b__psr__Excitation (nA)    ) (nA/ms) {
    if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY) {
        deriv_b__psr__Excitation = -b__psr__Excitation/tau__psr__Excitation
    
    } else if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD) {
        deriv_b__psr__Excitation = -b__psr__Excitation/tau__psr__Excitation
    }
}
FUNCTION deriv_a__psr__Inhibition(a__psr__Inhibition (nA), b__psr__Inhibition (nA)    ) (nA/ms) {
    if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY) {
        deriv_a__psr__Inhibition = (-a__psr__Inhibition + b__psr__Inhibition)/tau__psr__Inhibition
    
    } else if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD) {
        deriv_a__psr__Inhibition = (-a__psr__Inhibition + b__psr__Inhibition)/tau__psr__Inhibition
    }
}
FUNCTION deriv_b__psr__Inhibition(b__psr__Inhibition (nA)    ) (nA/ms) {
    if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY) {
        deriv_b__psr__Inhibition = -b__psr__Inhibition/tau__psr__Inhibition
    
    } else if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD) {
        deriv_b__psr__Inhibition = -b__psr__Inhibition/tau__psr__Inhibition
    }
}
FUNCTION deriv_a__psr__External(a__psr__External (nA), b__psr__External (nA)    ) (nA/ms) {
    if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY) {
        deriv_a__psr__External = (-a__psr__External + b__psr__External)/tau__psr__External
    
    } else if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD) {
        deriv_a__psr__External = (-a__psr__External + b__psr__External)/tau__psr__External
    }
}
FUNCTION deriv_b__psr__External(b__psr__External (nA)    ) (nA/ms) {
    if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY) {
        deriv_b__psr__External = -b__psr__External/tau__psr__External
    
    } else if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD) {
        deriv_b__psr__External = -b__psr__External/tau__psr__External
    }
}

NET_RECEIVE(connection_weight_, channel) {
    INITIAL {
      : stop channel being set to 0 by default
    }
    found_transition_ = -1
    if (flag == INIT) {
        : Set up required watch statements
        WATCH (t > refractory_end__cell) 1  : Watch trigger of on-condition and send appropriate flag
        WATCH (v > v_threshold__cell) 2  : Watch trigger of on-condition and send appropriate flag
    } else if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY) {
        if (flag == ON_EVENT && channel == INPUT_SPIKE__PSR__EXCITATION) {
                  
            : Required aliases
            fixed_weight__pls__Excitation = weight__pls__Excitation
            weight__psr__Excitation = fixed_weight__pls__Excitation

            : State assignments
            b__psr__Excitation = b__psr__Excitation + weight__psr__Excitation
            v_clamp___pype9 = v

            : Output events
        
            : Regime transition
            if (found_transition_ == -1) {
                found_transition_ = flag
            } else {
                printf("WARNING!! Found multiple transitions %f and %f at time %f", found_transition_, flag, t * PER_MS)
            }
            regime_ = SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY

        }
        if (flag == ON_EVENT && channel == INPUT_SPIKE__PSR__INHIBITION) {
                  
            : Required aliases
            fixed_weight__pls__Inhibition = weight__pls__Inhibition
            weight__psr__Inhibition = fixed_weight__pls__Inhibition

            : State assignments
            b__psr__Inhibition = b__psr__Inhibition + weight__psr__Inhibition
            v_clamp___pype9 = v

            : Output events
        
            : Regime transition
            if (found_transition_ == -1) {
                found_transition_ = flag
            } else {
                printf("WARNING!! Found multiple transitions %f and %f at time %f", found_transition_, flag, t * PER_MS)
            }
            regime_ = SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY

        }
        if (flag == ON_EVENT && channel == INPUT_SPIKE__PSR__EXTERNAL) {
                  
            : Required aliases
            fixed_weight__pls__External = weight__pls__External
            weight__psr__External = fixed_weight__pls__External

            : State assignments
            b__psr__External = b__psr__External + weight__psr__External
            v_clamp___pype9 = v

            : Output events
        
            : Regime transition
            if (found_transition_ == -1) {
                found_transition_ = flag
            } else {
                printf("WARNING!! Found multiple transitions %f and %f at time %f", found_transition_, flag, t * PER_MS)
            }
            regime_ = SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY

        }
        if (flag == 1) {  : Condition 't > refractory_end__cell'
                  
            : Required aliases

            : State assignments

            : Output events
        
            : Regime transition
            if (found_transition_ == -1) {
                found_transition_ = flag
            } else {
                printf("WARNING!! Found multiple transitions %f and %f at time %f", found_transition_, flag, t * PER_MS)
            }
            regime_ = SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD

        }
    } else if (regime_ == SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD) {
        if (flag == ON_EVENT && channel == INPUT_SPIKE__PSR__EXCITATION) {
                  
            : Required aliases
            fixed_weight__pls__Excitation = weight__pls__Excitation
            weight__psr__Excitation = fixed_weight__pls__Excitation

            : State assignments
            b__psr__Excitation = b__psr__Excitation + weight__psr__Excitation

            : Output events
        
            : Regime transition
            if (found_transition_ == -1) {
                found_transition_ = flag
            } else {
                printf("WARNING!! Found multiple transitions %f and %f at time %f", found_transition_, flag, t * PER_MS)
            }
            regime_ = SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD

        }
        if (flag == ON_EVENT && channel == INPUT_SPIKE__PSR__INHIBITION) {
                  
            : Required aliases
            fixed_weight__pls__Inhibition = weight__pls__Inhibition
            weight__psr__Inhibition = fixed_weight__pls__Inhibition

            : State assignments
            b__psr__Inhibition = b__psr__Inhibition + weight__psr__Inhibition

            : Output events
        
            : Regime transition
            if (found_transition_ == -1) {
                found_transition_ = flag
            } else {
                printf("WARNING!! Found multiple transitions %f and %f at time %f", found_transition_, flag, t * PER_MS)
            }
            regime_ = SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD

        }
        if (flag == ON_EVENT && channel == INPUT_SPIKE__PSR__EXTERNAL) {
                  
            : Required aliases
            fixed_weight__pls__External = weight__pls__External
            weight__psr__External = fixed_weight__pls__External

            : State assignments
            b__psr__External = b__psr__External + weight__psr__External

            : Output events
        
            : Regime transition
            if (found_transition_ == -1) {
                found_transition_ = flag
            } else {
                printf("WARNING!! Found multiple transitions %f and %f at time %f", found_transition_, flag, t * PER_MS)
            }
            regime_ = SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___SUBTHRESHOLD

        }
        if (flag == 2) {  : Condition 'v > v_threshold__cell'
                  
            : Required aliases

            : State assignments
            refractory_end__cell = refractory_period__cell + t
            v = v_reset__cell
            v_clamp___pype9 = v_reset__cell

            : Output events
            net_event(t)  : FIXME: Need to specify which output port this is
        
            : Regime transition
            if (found_transition_ == -1) {
                found_transition_ = flag
            } else {
                printf("WARNING!! Found multiple transitions %f and %f at time %f", found_transition_, flag, t * PER_MS)
            }
            regime_ = SOLE_____SOLE___SOLE_____SOLE___SOLE_____SOLE___REFRACTORY

        }
    } else {
        printf("ERROR! Unrecognised regime %f", regime_)
    }
}

          
