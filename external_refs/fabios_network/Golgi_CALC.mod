TITLE Cerebellum Golgi Cell Model

COMMENT
        Calcium first order kinetics
   
	Author: A. Fontana
	Revised: 12.12.98
ENDCOMMENT

NEURON {
        SUFFIX Golgi_CALC
        USEION ca READ ica, cao WRITE cai
        RANGE d, beta, cai0, ca_pump_i
}

UNITS {
        (mV)    = (millivolt)
        (mA)    = (milliamp)
	(um)    = (micron)
	(molar) = (1/liter)
        (mM)    = (millimolar)
   	F      = (faraday) (coulomb)
}

PARAMETER {
        ica             (mA/cm2)
        celsius    (degC)
        d = .2          (um)
        cao = 2.        (mM)         
        cai0 = 1e-4     (mM)         
        beta = 1.3        (/ms)
}

ASSIGNED {
	ca_pump_i	(mA)
}
STATE {
	cai (mM)
}

INITIAL {
        cai = cai0 
}

BREAKPOINT {
       SOLVE conc METHOD derivimplicit
}

DERIVATIVE conc {    
	:  outward ionic current with valence 2+
	ca_pump_i = 2*beta*(cai-cai0)
	:  total outward Ca current
	cai' =  -ica/(2*F*d)*(1e4) - beta*(cai-cai0)
}


