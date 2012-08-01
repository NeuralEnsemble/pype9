TITLE Voltage-gated potassium channel from Kv4 subunits

COMMENT

NEURON implementation of a potassium channel from Kv4 subunits
Kinetical Scheme: Hodgkin-Huxley m^4*h

Kinetic data taken from: Sacco and Tempia, J.Physiol. 543 (2002) 505

ACTIVATION:
The rate constants of activation (alphan) and deactivation (betan) were approximated by:

alphan = can * exp(-(v+cvan)/ckan)
betan = cbn * exp(-(v+cvbn)/ckbn)

Parameters can, cvan, ckan, cbn, cvbn, ckbn
are defined in the CONSTANT block.

INACTIVATION:
The model includes only the fast component of inactivation
The rate constants of inactivation (alphah) and de-inactivation (betah) were approximated by:

alphah = cah / (1+exp(-(v+cvah)/ckah))
betah = cbh / (1+exp(-(v+cvbh)/ckbh))

Parameters cah, cvah, ckah, cbh, cvbh, ckbh
are defined in the CONSTANT block.

Laboratory for Neuronal Circuit Dynamics
RIKEN Brain Science Institute, Wako City, Japan
http://www.neurodynamics.brain.riken.jp

Reference: Akemann and Knoepfel, J.Neurosci. 26 (2006) 4602
Date of Implementation: April 2005
Contact: akemann@brain.riken.jp

ENDCOMMENT


NEURON {
	SUFFIX Kv4
	USEION k READ ek WRITE ik
	RANGE gk, gbar, ik
	GLOBAL ninf, taun, hinf, tauh
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
	(molar) = (1/liter)
	(mM) = (millimolar)		
}

CONSTANT {
	q10 = 3

	can = 0.15743 (1/ms)
	cvan = 57 (mV)
	ckan = -32.19976 (mV)
	cbn = 0.15743 (1/ms)
	cvbn = 57 (mV)
	ckbn = 37.51346 (mV)

	cah = 0.01342 (1/ms)
	cvah = 60 (mV)
	ckah = -7.86476 (mV)
	cbh = 0.04477 (1/ms)
	cvbh = 54 (mV)
	ckbh = 11.3615 (mV)
}

PARAMETER {
	v (mV)
	celsius (degC)
	
	gbar = 0.0039 (mho/cm2)   <0,1e9>
}

ASSIGNED {
	ik (mA/cm2) 
	ek (mV)
	gk (mho/cm2)
	qt

	ninf
	taun (ms)
	alphan (1/ms)
	betan (1/ms)

	hinf
	tauh (ms)
	alphah (1/ms)
	betah (1/ms)        
}

STATE { n h }

INITIAL {
	qt = q10^((celsius-22 (degC))/10 (degC))
	rates(v)
	n = ninf
	h = hinf
}

BREAKPOINT {
	SOLVE states METHOD cnexp
      gk = gbar * n^4 * h 
	ik = gk * (v - ek)
}

DERIVATIVE states {
	rates(v)
	n' = (ninf-n)/taun
	h' = (hinf-h)/tauh 
}

PROCEDURE rates(v (mV)) {
	alphan = alphanfkt(v)
	betan = betanfkt(v)
	ninf = alphan / (alphan+betan) 
	taun = 1 / (qt*(alphan + betan))
	alphah = alphahfkt(v)
	betah = betahfkt(v)
	hinf = alphah / (alphah + betah)
	tauh = 1 / (qt*(alphah + betah))       
}

FUNCTION alphanfkt(v (mV)) (1/ms) {
	alphanfkt = can * exp(-(v+cvan)/ckan) 
}

FUNCTION betanfkt(v (mV)) (1/ms) {
	betanfkt = cbn * exp(-(v+cvbn)/ckbn)
}

FUNCTION alphahfkt(v (mV))  (1/ms) {
	alphahfkt = cah / (1+exp(-(v+cvah)/ckah))
}

FUNCTION betahfkt(v (mV))  (1/ms)  {
	betahfkt = cbh / (1+exp(-(v+cvbh)/ckbh))
}
