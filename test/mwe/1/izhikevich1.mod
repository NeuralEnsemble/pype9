NEURON {
    POINT_PROCESS Izhikevich1
    RANGE a, b, c, d, u, uinit, vthresh
    NONSPECIFIC_CURRENT i
}

UNITS {
    (mV) = (millivolt)
    (nA) = (nanoamp)
    (nF) = (nanofarad)
}

INITIAL {
    u = uinit
    net_send(0, 1)
}

PARAMETER {
    e       = 0.02 (/ms)
    b       = 0.2  (/ms)
    c       = -65  (mV)   : reset potential after a spike
    d       = 2    (mV/ms)
    vthresh = 30   (mV)   : spike threshold
    Cm      = 0.001  (nF)
    uinit   = -14  (mV/ms)
}

ASSIGNED {
    v (mV)
    i (nA)
}

STATE { 
    u (mV/ms)
}

BREAKPOINT {
    SOLVE states METHOD cnexp  : derivimplicit
    i = -Cm * (0.04*v*v + 5*v + 140 - u)
    :printf("t=%f, v=%f u=%f, i=%f, dv=%f, du=%f\n", t, v, u, i, 0.04*v*v + 5*v + 140 - u, a*(b*v-u))
}

DERIVATIVE states {
    u' = e*(b*v - u) 
}

NET_RECEIVE (weight (mV)) {
    if (flag == 1) {
        WATCH (v > vthresh) 2
    } else if (flag == 2) {
        net_event(t)
        v = c
        u = u + d
    } else { : synaptic activation
        v = v + weight
    }
}
