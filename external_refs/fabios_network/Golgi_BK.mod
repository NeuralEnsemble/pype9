TITLE Cerebellum Golgi Cell Model

COMMENT
        KCa channel
   
	Author: E.DAngelo, T.Nieus, A. Fontana
	Last revised: 8.5.2000
ENDCOMMENT
 
NEURON { 
	SUFFIX Golgi_BK
	USEION k READ ek WRITE ik 
	USEION ca READ cai
	RANGE gkbar, ik, g
	RANGE Aalpha_c, Balpha_c, Kalpha_c, alpha_c, beta_c
	RANGE Abeta_c, Bbeta_c, Kbeta_c 
	RANGE c_inf, tau_c, c, tcorr
} 
 
UNITS { 
	(mA) = (milliamp) 
	(mV) = (millivolt) 
	(molar) = (1/liter)
	(mM) = (millimolar)
} 
 
PARAMETER { 
	Aalpha_c = 7 (/ms)
	Balpha_c = 1.5e-3 (mM)

	Kalpha_c =  -11.765 (mV)

	Abeta_c = 1 (/ms)
	Bbeta_c = 0.15e-3 (mM)

	Kbeta_c = -11.765 (mV)

	v (mV) 
	cai (mM)
	gkbar= 0.003 (mho/cm2) 
	ek (mV)
	celsius (degC) 
	Q10 = 3		(1)
} 

STATE { 
	c 
} 

ASSIGNED { 
	ik (mA/cm2) 
	ica (mA/cm2)

	c_inf 
	tau_c (ms) 
	g (mho/cm2) 
	alpha_c (/ms) 
	beta_c (/ms)
	tcorr (1)
} 
 
INITIAL { 
	rate(v) 
	c = c_inf 
} 
 
BREAKPOINT { 
	SOLVE states METHOD derivimplicit 
	g = gkbar*c 
	ik = g*(v - ek) 
	alpha_c = alp_c(v) 
	beta_c = bet_c(v) 
} 
 
DERIVATIVE states { 
	rate(v) 
	c' =(c_inf - c)/tau_c 
} 
 
FUNCTION alp_c(v(mV))(/ms) { 
	tcorr = Q10^((celsius-30(degC))/10(degC))
	alp_c = tcorr*Aalpha_c/(1+(Balpha_c*exp(v/Kalpha_c)/cai)) 
} 
 
FUNCTION bet_c(v(mV))(/ms) {
	tcorr = Q10^((celsius-30(degC))/10(degC))
	bet_c = tcorr*Abeta_c/(1+cai/(Bbeta_c*exp(v/Kbeta_c))) 
} 
 
PROCEDURE rate(v (mV)) {LOCAL a_c, b_c 
	a_c = alp_c(v)  
	b_c = bet_c(v) 
	tau_c = 1/(a_c + b_c) 
	c_inf = a_c/(a_c + b_c) 
}