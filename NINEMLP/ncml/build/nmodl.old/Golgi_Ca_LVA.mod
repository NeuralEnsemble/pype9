TITLE Low threshold calcium current Cerebellum Golgi Cell Model
:
:   Ca++ current responsible for low threshold spikes (LTS)
:   RETICULAR THALAMUS
:   Differential equations
:
:   Model of Huguenard & McCormick, J Neurophysiol 68: 1373-1383, 1992.
:   The kinetics is described by standard equations (NOT GHK)
:   using a m2h format, according to the voltage-clamp data
:   (whole cell patch clamp) of Huguenard & Prince, J Neurosci.
:   12: 3804-3817, 1992.  The model was introduced in Destexhe et al.
:   J. Neurophysiology 72: 803-818, 1994.
:   See http://www.cnl.salk.edu/~alain , http://cns.fmed.ulaval.ca
:
:    - Kinetics adapted to fit the T-channel of reticular neuron
:    - Q10 changed to 5 and 3
:    - Time constant tau_h fitted from experimental data
:    - shift parameter for screening charge
:
:   ACTIVATION FUNCTIONS FROM EXPERIMENTS (NO CORRECTION)
:
:   Reversal potential taken from Nernst Equation
:
:   Written by Alain Destexhe, Salk Institute, Sept 18, 1992
:

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
        SUFFIX Golgi_Ca_LVA
        USEION ca2 READ ca2i, ca2o WRITE ica2 VALENCE 2
        RANGE g, gca2bar, m_inf, tau_m, h_inf, tau_h, shift
	RANGE ica2, m ,h, ca2rev
	RANGE phi_m, phi_h
	RANGE v0_m_inf,v0_h_inf,k_m_inf,k_h_inf,C_tau_m
	RANGE A_tau_m,v0_tau_m1,v0_tau_m2,k_tau_m1,k_tau_m2
	RANGE C_tau_h ,A_tau_h ,v0_tau_h1,v0_tau_h2,k_tau_h1 ,k_tau_h2

    }

UNITS {
        (molar) = (1/liter)
        (mV) =  (millivolt)
        (mA) =  (milliamp)
        (mM) =  (millimolar)

        FARADAY = (faraday) (coulomb)
        R = (k-mole) (joule/degC)
}

PARAMETER {
        v               (mV)
        celsius (degC)
        eca2 (mV)
	   gca2bar  = 2.5e-4 (mho/cm2)
        shift   = 2     (mV)            : screening charge for Ca_o = 2 mM
        ca2i  (mM)           : adjusted for eca=120 mV
        ca2o  (mM)
	
	v0_m_inf = -50 (mV)
	v0_h_inf = -78 (mV)
	k_m_inf = -7.4 (mV)
	k_h_inf = 5.0  (mv)
	
	C_tau_m = 3
	A_tau_m = 1.0
	v0_tau_m1 = -25 (mV)
	v0_tau_m2 = -100 (mV)
	k_tau_m1 = 10 (mV)
	k_tau_m2 = -15 (mV)
	
	C_tau_h = 85
	A_tau_h = 1.0
	v0_tau_h1 = -46 (mV)
	v0_tau_h2 = -405 (mV)
	k_tau_h1 = 4 (mV)
	k_tau_h2 = -50 (mV)
	
    }
    

STATE {
        m h
}

ASSIGNED {
        ica2     (mA/cm2)
        ca2rev   (mV)
	g        (mho/cm2) 
        m_inf
        tau_m   (ms)
        h_inf
        tau_h   (ms)
        phi_m
        phi_h
}

BREAKPOINT {
        SOLVE ca2state METHOD cnexp
        ca2rev = (1e3) * (R*(celsius+273.15))/(2*FARADAY) * log (ca2o/ca2i)
        g = gca2bar * m*m*h
        ica2 = gca2bar * m*m*h * (v-ca2rev)
}

DERIVATIVE ca2state {
        evaluate_fct(v)

        m' = (m_inf - m) / tau_m
        h' = (h_inf - h) / tau_h
}

UNITSOFF
INITIAL {
:
:   Activation functions and kinetics were obtained from
:   Huguenard & Prince, and were at 23-25 deg.
:   Transformation to 36 deg assuming Q10 of 5 and 3 for m and h
:   (as in Coulter et al., J Physiol 414: 587, 1989)
:

        evaluate_fct(v)
        m = m_inf
        h = h_inf
}

PROCEDURE evaluate_fct(v(mV)) { 
:
:   Time constants were obtained from J. Huguenard
:
        phi_m = 5.0 ^ ((celsius-24)/10)
        phi_h = 3.0 ^ ((celsius-24)/10)
	
	TABLE m_inf, tau_m, h_inf, tau_h
	DEPEND shift, phi_m, phi_h FROM -100 TO 30 WITH 13000 
        m_inf = 1.0 / ( 1 + exp((v + shift - v0_m_inf)/k_m_inf) )
        h_inf = 1.0 / ( 1 + exp((v + shift - v0_h_inf)/k_h_inf) )
	
        tau_m = ( C_tau_m + A_tau_m / ( exp((v+shift - v0_tau_m1)/ k_tau_m1) + exp((v+shift - v0_tau_m2)/k_tau_m2) ) ) / phi_m
        tau_h = ( C_tau_h + A_tau_h / ( exp((v+shift - v0_tau_h1)/k_tau_h1) + exp((v+shift - v0_tau_h2)/k_tau_h2) ) ) / phi_h
}
UNITSON