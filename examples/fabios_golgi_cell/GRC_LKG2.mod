TITLE Cerebellum Granule Cell Model

COMMENT
        Gaba A leakage
   
	Author: A. Fontana
	Last revised: 18.2.99
ENDCOMMENT
 
NEURON { 
	SUFFIX GRC_LKG2 
	NONSPECIFIC_CURRENT il
	RANGE egaba, ggaba , i
} 
 
UNITS { 
	(mA) = (milliamp) 
	(mV) = (millivolt) 
} 
 
PARAMETER { 
	v (mV) 
	ggaba = 3e-5 (mho/cm2)  : 2.17e-5 
	celsius = 30 (degC)
	egaba = -65 (mV)
} 

ASSIGNED { 
	il (mA/cm2) 
	i (mA/cm2) 
}

BREAKPOINT { 
	il = ggaba*(v - egaba) 
	i =il
} 
