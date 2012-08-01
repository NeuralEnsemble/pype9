TITLE Leak Current

COMMENT

NEURON implementation of a passive leak/shunt

Laboratory for Neuronal Circuit Dynamics
RIKEN Brain Science Institute, Wako City, Japan
http://www.neurodynamics.brain.riken.jp

Reference: Akemann and Knoepfel, J. Neurosci. 26 (2006) 4602
Date of Implementation: April 2005
Contact: akemann@brain.riken.jp

ENDCOMMENT

NEURON {
	SUFFIX leak
	NONSPECIFIC_CURRENT i
	RANGE i, e, gbar
}

UNITS {
	(mV) = (millivolt)
	(mA) = (milliamp)
	(nA) = (nanoamp)
	(pA) = (picoamp)
	(S)  = (siemens)
}

PARAMETER {
	gbar = 9e-5 (S/cm2)  
	e = -61 (mV)
}

ASSIGNED {
	i (mA/cm2)
	v (mV)
}

BREAKPOINT {
	i = gbar*(v - e)
}
