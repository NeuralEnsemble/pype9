TITLE Cerebellum Golgi Cell Model

COMMENT
        Na transient channel
	Gutfreund parametrization
   
	Author: E.DAngelo, T.Nieus, A. Fontana
	Last revised: 8.5.2000
ENDCOMMENT
 
NEURON { 
	SUFFIX Golgi_Na 
	USEION na READ ena WRITE ina 
	RANGE gnabar, ina, g
	RANGE alpha_m, beta_m, alpha_h, beta_h 
	RANGE Aalpha_m, Kalpha_m, V0alpha_m
	RANGE Abeta_m, Kbeta_m, V0beta_m

	RANGE Aalpha_h, Kalpha_h, V0alpha_h
	RANGE Abeta_h, Kbeta_h, V0beta_h

	RANGE m_inf, tau_m, h_inf, tau_h, m, h, tcorr
} 
 
UNITS { 
	(mA) = (milliamp) 
	(mV) = (millivolt) 
} 
 
PARAMETER { 

	Aalpha_m = 0.3 (/ms-mV)
	Kalpha_m = -10 (mV)
	V0alpha_m = -25 (mV)
	
	Abeta_m = 12 (/ms)
	Kbeta_m = -18.182 (mV)
	V0beta_m = -50 (mV)

	Aalpha_h  = 0.21 (/ms)
	Kalpha_h  = -3.333 (mV)
	V0alpha_h = -50 (mV)
 
	Abeta_h  = 3 (/ms)
	Kbeta_h  = -5 (mV)
	V0beta_h = -17 (mV)
	   
	v (mV) 
	gnabar	=  0.048 (mho/cm2)

	ena (mV) 
	celsius (degC)
	Q10 = 3 (1)
} 

STATE { 
	m 
	h 
} 

ASSIGNED { 
	ina (mA/cm2) 
	m_inf 
	h_inf 
	tau_m (ms) 
	tau_h (ms) 
	g (mho/cm2) 
	alpha_m (/ms)
	beta_m (/ms)
	alpha_h (/ms)
	beta_h (/ms)
	tcorr	(1)
} 
 
INITIAL { 
	rate(v) 
	m = m_inf 
	h = h_inf 
} 
 
BREAKPOINT { 
	SOLVE states METHOD derivimplicit 
	g = gnabar*m*m*m*h 
	ina = g*(v - ena)
	alpha_m = alp_m(v)
	beta_m = bet_m(v) 
	alpha_h = alp_h(v)
	beta_h = bet_h(v) 
} 
 
DERIVATIVE states { 
	rate(v) 
	m' =(m_inf - m)/tau_m 
	h' =(h_inf - h)/tau_h 
} 
 
FUNCTION alp_m(v(mV))(/ms) {
	tcorr = Q10^((celsius-20(degC))/10(degC)) 
	alp_m = tcorr*Aalpha_m*linoid(v-V0alpha_m,Kalpha_m) 
} 
 
FUNCTION bet_m(v(mV))(/ms) {
	tcorr = Q10^((celsius-20(degC))/10(degC)) 
	bet_m = tcorr*Abeta_m*exp((v-V0beta_m)/Kbeta_m) 
} 
 
FUNCTION alp_h(v(mV))(/ms) {
	tcorr = Q10^((celsius-20(degC))/10(degC)) 
	alp_h = tcorr*Aalpha_h*exp((v-V0alpha_h)/Kalpha_h) 
} 
 
FUNCTION bet_h(v(mV))(/ms) {
	tcorr = Q10^((celsius-20(degC))/10(degC)) 
	bet_h = tcorr*Abeta_h/(1+exp((v-V0beta_h)/Kbeta_h))
} 
 
PROCEDURE rate(v (mV)) {LOCAL a_m, b_m, a_h, b_h 
	TABLE m_inf, tau_m, h_inf, tau_h 
	DEPEND Aalpha_m, Kalpha_m, V0alpha_m, 
	       Abeta_m, Kbeta_m, V0beta_m,
               Aalpha_h, Kalpha_h, V0alpha_h,
               Abeta_h, Kbeta_h, V0beta_h, celsius FROM -100 TO 30 WITH 13000 
	a_m = alp_m(v)  
	b_m = bet_m(v) 
	a_h = alp_h(v)  
	b_h = bet_h(v) 
	m_inf = a_m/(a_m + b_m) 
	tau_m = 1/(a_m + b_m) 
	h_inf = a_h/(a_h + b_h) 
	tau_h = 1/(a_h + b_h) 
	:if (tau_h<0.1 (ms)) {tau_h=0.1 (ms)} : riga aggiunta il 10 giugno 2003
} 

FUNCTION linoid(x (mV),y (mV)) (mV) {
        if (fabs(x/y) < 1e-6) {
                linoid = y*(1 - x/y/2)
        }else{
                linoid = x/(1 - exp(x/y))
        }
}

