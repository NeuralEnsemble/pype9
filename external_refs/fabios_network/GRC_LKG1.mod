TITLE Cerebellum Granule Cell Model

COMMENT
        Leakage
   
	Author: A. Fontana
	Last revised: 18.12.98
ENDCOMMENT
 
NEURON { 
	SUFFIX GRC_LKG1 
	NONSPECIFIC_CURRENT il
	RANGE el, gl,i
} 
 
UNITS { 
	(mA) = (milliamp) 
	(mV) = (millivolt) 
} 
 
PARAMETER { 
	v (mV) 
	gl = 5.68e-5 (mho/cm2)
	celsius = 30 (degC)
	el =  -16.5 (mV) : resting at -70 mV	:-11 resting at -68 mV
	: -58 : to make it 
} 

ASSIGNED { 
	il (mA/cm2) 
	i (mA/cm2) 
}
  
BREAKPOINT { 
	il = gl*(v - el) 
	i = il
} 
