TITLE Cerebellum Golgi Cell Model

COMMENT
        Na resurgent channel
	  
	Author: T.Nieus
	Last revised: 30.6.2003 
	Critical value gNa
	Inserted a control in bet_s to avoid huge values of x1
			
ENDCOMMENT
 
NEURON { 
	SUFFIX Golgi_NaR
	USEION na READ ena WRITE ina 
	RANGE gnabar, ina, g
	RANGE Aalpha_s,Abeta_s,V0alpha_s,V0beta_s,Kalpha_s,Kbeta_s 
        RANGE Shiftalpha_s,Shiftbeta_s,tau_s,s_inf
	RANGE Aalpha_f,Abeta_f,V0alpha_f,V0beta_f,Kalpha_f, Kbeta_f
	RANGE f, tau_f,f_inf,s , tau_s,s_inf, tcorr
} 
 
UNITS {    
	(mA) = (milliamp) 
	(mV) = (millivolt) 
} 
 
PARAMETER { 
	
	: s-ALFA
	Aalpha_s = -0.00493 (/ms)
	V0alpha_s = -4.48754 (mV)
	Kalpha_s = -6.81881 (mV)
	Shiftalpha_s = 0.00008 (/ms)

	: s-BETA
	Abeta_s = 0.01558 (/ms)
	V0beta_s = 43.97494 (mV)
	Kbeta_s =  0.10818 (mV)
	Shiftbeta_s = 0.04752 (/ms)

	: f-ALFA
	Aalpha_f = 0.31836 (/ms)
	V0alpha_f = -80 (mV)
	Kalpha_f = -62.52621 (mV)

	: f-BETA
	Abeta_f = 0.01014 (/ms)
	V0beta_f = -83.3332 (mV)
	Kbeta_f = 16.05379 (mV)

	v (mV) 
	gnabar= 0.0017 (mho/cm2)
	ena  (mV) 
	celsius (degC) 
	Q10 = 3	(1)
} 

STATE { 
	s 
	f
} 

ASSIGNED { 
	ina (mA/cm2) 
	g (mho/cm2) 

	alpha_s (/ms)
	beta_s (/ms)
	s_inf
	tau_s (ms)
	
	alpha_f (/ms)
	beta_f (/ms)
	f_inf
	tau_f (ms)
	tcorr (1)
} 
 
INITIAL { 
	rate(v) 
	s = s_inf
	f = f_inf
} 
 
BREAKPOINT { 
	SOLVE states METHOD derivimplicit 
	g = gnabar*s*f
	ina = g*(v - ena)

	alpha_s = alp_s(v)
	beta_s = bet_s(v) 

	alpha_f = alp_f(v)
	beta_f = bet_f(v) 
} 
 
DERIVATIVE states { 
	rate(v) 
	s' = ( s_inf - s ) / tau_s 
	f' = ( f_inf - f ) / tau_f 
} 
 
PROCEDURE rate(v (mV)) { LOCAL a_s,b_s,a_f,b_f
	TABLE s_inf,tau_s,f_inf,tau_f DEPEND celsius FROM -100 TO 30 WITH 13000	

	a_s = alp_s(v)  
	b_s = bet_s(v) 
	s_inf = a_s / ( a_s + b_s ) 
	tau_s = 1 / ( a_s + b_s ) 

	a_f = alp_f(v)  
	b_f = bet_f(v) 
	f_inf = a_f / ( a_f + b_f ) 
	tau_f = 1 / ( a_f + b_f ) 
} 



FUNCTION alp_s(v (mV)) (/ms){
	tcorr = Q10^( ( celsius - 20 (degC) ) / 10 (degC) )
	alp_s = tcorr*(Shiftalpha_s+Aalpha_s*((v+V0alpha_s)/ 1 (mV) )/(exp((v+V0alpha_s)/Kalpha_s)-1))
}

FUNCTION bet_s(v (mV)) (/ms){ LOCAL x1
	tcorr = Q10^((celsius-20(degC))/10(degC))	

	x1=(v+V0beta_s)/Kbeta_s
	if (x1>200) {x1=200}
	bet_s =tcorr*(Shiftbeta_s+Abeta_s*((v+V0beta_s)/1 (mV) )/(exp(x1)-1))

}

FUNCTION alp_f(v (mV)) (/ms){
	tcorr = Q10^( ( celsius - 20 (degC) ) / 10 (degC) )
	alp_f =	tcorr * Aalpha_f * exp( ( v - V0alpha_f ) / Kalpha_f)
}

FUNCTION bet_f(v (mV)) (/ms){
	tcorr = Q10^( ( celsius - 20 (degC) ) / 10 (degC) )
	bet_f =	tcorr * Abeta_f * exp( ( v - V0beta_f ) / Kbeta_f )	
}

