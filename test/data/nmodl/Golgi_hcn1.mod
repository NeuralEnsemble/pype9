TITLE Cerebellum Golgi Cell HCN1 Model

COMMENT

Author:Sergio Solinas, Lia Forti, Egidio DAngelo
Data from: Santoro et al. J Neurosci. 2000
Last revised: May 2007

Published in:
             Sergio M. Solinas, Lia Forti, Elisabetta Cesana, 
             Jonathan Mapelli, Erik De Schutter and Egidio D`Angelo (2008)
             Computational reconstruction of pacemaking and intrinsic 
             electroresponsiveness in cerebellar golgi cells
             Frontiers in Cellular Neuroscience 2:2
ENDCOMMENT

NEURON {
        SUFFIX Golgi_hcn1
	NONSPECIFIC_CURRENT ih
	RANGE o_fast_inf, o_slow_inf, tau_f, tau_s, Erev
	RANGE gbar,r,g
}       
        
UNITS {
        (mA) = (milliamp)
	(mV) = (millivolt)
	(S)  = (siemens)        
}


PARAMETER {
	celsius  (degC)
	gbar = 5e-5   (S/cm2)
        Erev = -20 (mV)
	q_10 = 3

	Ehalf = -72.49 (mV)
	c = 0.11305	(/mV)
	
	rA = 0.002096 (/mV)
        rB = 0.97596  (1)
        tCf = 0.01371 (1)
        tDf = -3.368  (mV)
	tEf = 2.302585092 (/mV)
	tCs = 0.01451 (1)
        tDs = -4.056  (mV)
	tEs = 2.302585092 (/mV)
}

ASSIGNED {
	ih		(mA/cm2)
        v               (mV)
	g		(S/cm2)
	o_fast_inf
        o_slow_inf
        tau_f           (ms)
	tau_s           (ms)       
}



STATE {	o_fast o_slow }


BREAKPOINT {
	SOLVE state METHOD cnexp
	g = gbar * (o_fast + o_slow)
        ih = g * (v - Erev)
}

DERIVATIVE state {	
	rate(v)
	o_fast' = (o_fast_inf - o_fast) / tau_f
	o_slow' = (o_slow_inf - o_slow) / tau_s
}

LOCAL q

INITIAL {
	q = q_10^((celsius -33(degC)) / 10(degC))
	rate(v)
	o_fast = o_fast_inf
	o_slow = o_slow_inf

}

FUNCTION r(potential (mV))  { 	:fraction of fast component in double exponential
	UNITSOFF
	r =  rA * potential + rB
        UNITSON
}

FUNCTION tau(potential (mV),t1,t2,t3) (ms) { 
	UNITSOFF
        tau = exp(((t1 * potential) - t2)*t3)
	UNITSON
}

FUNCTION o_inf(potential (mV), Ehalf, c)  { 
	UNITSOFF
        o_inf = 1 / (1 + exp((potential - Ehalf) * c))
        UNITSON
}

FUNCTION q10(celsius (deg))  {
	UNITSOFF
        q10 = exp(1.0986 * ((celsius - 33) / 10))
        UNITSON
}

PROCEDURE rate(v (mV)) { 
	TABLE o_fast_inf, o_slow_inf, tau_f, tau_s
	DEPEND celsius FROM -100 TO 30 WITH 13000

	: r(v) is the fraction of fast component in double exponential
	o_fast_inf = r(v) * o_inf(v,Ehalf,c)
	o_slow_inf = (1 - r(v)) * o_inf(v,Ehalf,c)
			
	tau_f =  tau(v,tCf,tDf,tEf) 
	tau_s =  tau(v,tCs,tDs,tEs) 
}
