TITLE Internal accumulation of calcium in the Purkinje cell body near to the membrane

COMMENT

Modified from Khaliq et al., J.Neurosci. 23(2003)4899 

Laboratory for Neuronal Circuit Dynamics
RIKEN Brain Science Institute, Wako City, Japan
http://www.neurodynamics.brain.riken.jp

Reference: Akemann and Knoepfel, J.Neurosci. 26 (2006) 4602
Date of Implementation: May 2005
Contact: akemann@brain.riken.jp

ENDCOMMENT

NEURON {
	SUFFIX Caint
	USEION ca READ ica WRITE cai
	RANGE ca
	GLOBAL depth, beta
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
	F = 9.6485e4 (coulombs)
}

PARAMETER {
	celsius (degC)
	
	depth = 0.1 (um)
	beta = 1 (1/ms)
}

ASSIGNED {
	ica (mA/cm2)
	cai (mM)
	qt
}

STATE {
	ca (mM)
}

INITIAL {
	qt = q10^((celsius-22 (degC))/10 (degC))
	ca = 1e-4 (mM)
}

BREAKPOINT {
	SOLVE state METHOD cnexp
	if ( ca < 1e-4 (mM) ) { ca = 1e-4 (mM) }
	assigncai()
}

DERIVATIVE state {
	ca' = (-ica)/(2*(1e-4)*F*depth) - qt * beta * ca
}

PROCEDURE assigncai() {
	cai = ca
}