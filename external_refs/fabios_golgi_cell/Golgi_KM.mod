TITLE Cerebellum Golgi Cell Model

COMMENT
        K-slow channel
   
	Author: E.DAngelo, T.Nieus, A. Fontana
	Last revised: 8.5.2000
ENDCOMMENT

NEURON { 
	SUFFIX Golgi_KM 
	USEION k READ ek WRITE ik 
	RANGE gkbar, ik, g
	:RANGE Aalpha_n, Kalpha_n, V0alpha_n, alpha_n, beta_n 
	:RANGE Abeta_n, Kbeta_n, V0beta_n
	:RANGE V0_ninf, B_ninf
	RANGE n, n_inf, tau_n, tcorr
} 
 
UNITS { 
	(mA) = (milliamp) 
	(mV) = (millivolt) 
} 
 
PARAMETER { 
	Aalpha_n = 0.0033 (/ms)
	Kalpha_n = 40 (mV)
	V0alpha_n = -30 (mV)
	
	Abeta_n = 0.0033 (/ms)
	Kbeta_n = -20 (mV)
	V0beta_n = -30 (mV)
	
	V0_ninf = -35 (mV)
	B_ninf =  6 (mV)
	
	gkbar= 0.001 (mho/cm2)
	ek   (mV)
	celsius (degC) 
	Q10 = 3	(1) 
}

STATE { 
	n 
} 

ASSIGNED { 
	v (mV) 
	ik (mA/cm2) 
	n_inf 
	tau_n (ms) 
	g (mho/cm2) 
	alpha_n (/ms) 
	beta_n (/ms) 
	tcorr (1)
} 
 
INITIAL { 
	rate(v) 
	n = n_inf 
} 
 
BREAKPOINT { 
	SOLVE states METHOD derivimplicit 
	g = gkbar*n 
	ik = g*(v - ek) 
	alpha_n = alp_n(v) 
	beta_n = bet_n(v) 
} 
 
DERIVATIVE states { 
	rate(v) 
	n' =(n_inf - n)/tau_n 
} 
 
FUNCTION alp_n(v(mV))(/ms) { 
	alp_n = Aalpha_n*exp((v-V0alpha_n)/Kalpha_n) 
} 
 
FUNCTION bet_n(v(mV))(/ms) { 
	bet_n = Abeta_n*exp((v-V0beta_n)/Kbeta_n) 
} 

UNITSOFF

LOCAL delta
LOCAL q10
 
PROCEDURE rate(v (mV)) {LOCAL a_n, b_n, s_n  
	TABLE n_inf, tau_n 
	DEPEND Aalpha_n, Kalpha_n, V0alpha_n, 
	       Abeta_n, Kbeta_n, V0beta_n, V0_ninf, B_ninf, celsius FROM -100 TO 30 WITH 13000 
	a_n = alp_n(v)  
	b_n = bet_n(v)

	tcorr = Q10^((celsius - 22)/10)
	s_n = tcorr*(a_n + b_n) 
	tau_n = 1/s_n
 
:  n_inf = a_n/(a_n + b_n) 
	n_inf = 1/(1+exp(-(v-V0_ninf)/B_ninf))
} 

