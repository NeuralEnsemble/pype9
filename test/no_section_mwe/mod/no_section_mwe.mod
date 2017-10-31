NEURON {
    POINT_PROCESS NoSectionMWE
    NONSPECIFIC_CURRENT i_int

    RANGE a
    RANGE tau
    RANGE tau2
    RANGE R
    RANGE cm_int
    RANGE i_int
}


PARAMETER {
    tau = 0
    tau2 = 0
    R = 0
    cm_int = 0
}


ASSIGNED {
    i_int
    v
}

STATE {
    a
}


BREAKPOINT {
    SOLVE states METHOD derivimplicit
    i_int = -cm_int*(R*a - v)/tau
}


DERIVATIVE states {
    a' = (-a)/tau2

}


NET_RECEIVE(connection_weight_, channel) {
    
}

          
