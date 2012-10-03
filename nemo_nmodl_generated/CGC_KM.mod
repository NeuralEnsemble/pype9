

TITLE CGC_KM


NEURON {
  RANGE comp1913_vchold, comp1913_vcbase, comp1913_vcinc, comp1913_vcsteps, comp1913_vchdur, comp1913_vcbdur, comp1998_gbar, comp1998_e, KM_m
  RANGE i_KM
  RANGE ik
  RANGE ek
  USEION k READ ek WRITE ik
}


FUNCTION linoid (x, y) {
  LOCAL v4137
  if 
    (fabs(x / y) < 1e-06) 
     {v4137  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4137  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4137
}


FUNCTION comp1998_beta_n (v) {
  comp1998_beta_n  =  
  comp1998_Q10 * comp1998_Abeta_n * 
    exp((v + -(comp1998_V0beta_n)) / comp1998_Kbeta_n)
}


FUNCTION comp1998_alpha_n (v) {
  comp1998_alpha_n  =  
  comp1998_Q10 * comp1998_Aalpha_n * 
    exp((v + -(comp1998_V0alpha_n)) / comp1998_Kalpha_n)
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


PARAMETER {
  comp1998_Abeta_n  =  0.0033
  comp1998_Q10  =  2.40822468528069
  comp1998_B_ninf  =  6.0
  fix_celsius  =  30.0
  comp1913_vcbase  =  -69.0
  comp1998_gbar  =  0.00035
  comp1998_Kalpha_n  =  40.0
  comp1998_V0alpha_n  =  -30.0
  comp1913_vchdur  =  30.0
  comp1998_V0_ninf  =  -30.0
  comp1913_vcbdur  =  100.0
  comp1913_vcinc  =  10.0
  comp1998_V0beta_n  =  -30.0
  comp1998_e  =  -84.69
  comp1998_Kbeta_n  =  -20.0
  comp1998_Aalpha_n  =  0.0033
  comp1913_vcsteps  =  8.0
  comp1913_vchold  =  -71.0
}


STATE {
  KM_m
}


ASSIGNED {
  KM_m_inf
  KM_m_tau
  v
  ik
  ek
  i_KM
}


PROCEDURE asgns () {
  KM_m_tau  =  1.0 / (comp1998_alpha_n(v) + comp1998_beta_n(v))
  KM_m_inf  =  
  1.0 / (1.0 + exp(-(v + -(comp1998_V0_ninf)) / comp1998_B_ninf))
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  i_KM  =  (comp1998_gbar * KM_m) * (v - ek)
  ik  =  i_KM
}


DERIVATIVE states {
  asgns ()
  KM_m'  =  (KM_m_inf + -(KM_m)) / KM_m_tau
}


INITIAL {
  asgns ()
  KM_m  =  1.0 / (1.0 + exp(-(v + -(comp1998_V0_ninf)) / comp1998_B_ninf))
  ek  =  comp1998_e
}


PROCEDURE print_state () {
  printf ("NMODL state: t = %g v = %g KM_m = %g\n" , t, v,  KM_m)
}
