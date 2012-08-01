TITLE Binary potassium channel

COMMENT

NEURON implementation of a binary potassium conductance

gk = 0 for v < vth
gk = gbar for v > vth

Laboratory for Neuronal Circuit Dynamics
RIKEN Brain Science Institute, Wako City, Japan
http://www.neurodynamics.brain.riken.jp

Reference: Akemann and Knoepfel, J.Neurosci. 26 (2006) 4602
Date of Implementation: April 2005
Contact: akemann@brain.riken.jp

ENDCOMMENT


NEURON {
	SUFFIX Kbin
	USEION k READ ek WRITE ik
	RANGE gbar, gk, ik
	GLOBAL vth
}

UNITS {
	(mV) = (millivolt)
	(mA) = (milliamp)
	(nA) = (nanoamp)
	(pA) = (picoamp)
	(S)  = (siemens)
	(nS) = (nanosiemens)
	(pS) = (picosiemens)
	(um) = (micron)		
}

PARAMETER {
	v (mV)
	gbar = 16e-4	(mho/cm2)
	ek = -88 (mV)
	vth = -10 (mV)
}

ASSIGNED {
	ik (mA/cm2)
	gk (mho/cm2)
}

BREAKPOINT {
	gk = gbar * gatefkt(v)
	ik = gk * (v-ek)
}

FUNCTION gatefkt( v (mV) )  {
	if(v < vth) {
	gatefkt = 0
	} else {
	gatefkt = 1 }
}       
