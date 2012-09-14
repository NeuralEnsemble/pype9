TITLE Cerebellum Golgi Cell Model

COMMENT
        KDr channel
	Gutfreund parametrization
   
	Author: A. Fontana
	Last revised: 12.12.98
ENDCOMMENT

NEURON { 
	SUFFIX Golgi_KV 
	USEION k READ ek WRITE ik 
	RANGE gkbar, ik, g
	:RANGE Aalpha_n, Kalpha_n, V0alpha_n, alpha_n, beta_n 
	:RANGE Abeta_n, Kbeta_n, V0beta_n
	RANGE n, n_inf, tau_n, tcorr
} 
 
UNITS { 
	(mA) = (milliamp) 
	(mV) = (millivolt) 
} 
 
PARAMETER { 
	
	Aalpha_n = -0.01 (/ms-mV)
	Kalpha_n = -10 (mV)
	V0alpha_n = -26 (mV)

	Abeta_n = 0.125 (/ms)
	Kbeta_n = -80 (mV)
	V0beta_n = -36 (mV)
	v (mV)  
	gkbar= 0.032 (mho/cm2)

	ek (mV) 
	celsius (degC)
	Q10 = 3 (1)
} 

STATE { 
	n 
} 

ASSIGNED { 
	ik (mA/cm2) 
	n_inf 
	tau_n (ms) 
	g (mho/cm2) 
	alpha_n (/ms) 
	beta_n (/ms)
	tcorr	(1) 
} 
 
INITIAL { 
	rate(v) 
	n = n_inf 
} 
 
BREAKPOINT { 
	SOLVE states METHOD derivimplicit 
	g = gkbar*n*n*n*n 
	ik = g*(v - ek) 
	alpha_n = alp_n(v) 
	beta_n = bet_n(v) 
} 
 
DERIVATIVE states { 
	rate(v) 
	n' =(n_inf - n)/tau_n 
} 
 
FUNCTION alp_n(v(mV))(/ms) {
	tcorr = Q10^((celsius-6.3(degC))/10(degC)) 
	alp_n = tcorr*Aalpha_n*linoid(v-V0alpha_n, Kalpha_n)
} 
 
FUNCTION bet_n(v(mV))(/ms) {
	tcorr = Q10^((celsius-6.3(degC))/10(degC)) 
	bet_n = tcorr*Abeta_n*exp((v-V0beta_n)/Kbeta_n) 
} 
 
PROCEDURE rate(v (mV)) {LOCAL a_n, b_n 
	TABLE n_inf, tau_n 
	DEPEND Aalpha_n, Kalpha_n, V0alpha_n, 
               Abeta_n, Kbeta_n, V0beta_n, celsius FROM -100 TO 30 WITH 13000 
	a_n = alp_n(v)  
	b_n = bet_n(v) 
	tau_n = 1/(a_n + b_n) 
	n_inf = a_n/(a_n + b_n) 
} 

FUNCTION linoid(x (mV),y (mV)) (mV) {
        if (fabs(x/y) < 1e-6) {
                linoid = y*(1 - x/y/2)
        }else{
                linoid = x/(exp(x/y) - 1)
        }
}
