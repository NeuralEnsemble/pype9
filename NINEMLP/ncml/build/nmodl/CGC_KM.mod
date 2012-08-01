

TITLE CGC_KM


NEURON {
  RANGE KM_m, comp24_vcbdur, comp24_vchdur, comp24_vcsteps, comp24_vcinc, comp24_vcbase, comp24_vchold, comp0_e, comp0_gbar
  RANGE i_KM
  RANGE ik
  USEION k READ ek WRITE ik
}


FUNCTION comp0_beta_n (v) {
  comp0_beta_n  =  
  comp0_Q10 * comp0_Abeta_n * 
    exp((v + -(comp0_V0beta_n)) / comp0_Kbeta_n)
}


FUNCTION comp0_alpha_n (v) {
  comp0_alpha_n  =  
  comp0_Q10 * comp0_Aalpha_n * 
    exp((v + -(comp0_V0alpha_n)) / comp0_Kalpha_n)
}


PARAMETER {
  comp0_Abeta_n  =  0.0033
  comp0_V0_ninf  =  -30.0
  comp0_Kalpha_n  =  40.0
  comp0_gbar  =  0.00035
  comp24_vchdur  =  30.0
  comp0_Q10  =  2.40822468528069
  comp24_vcsteps  =  8.0
  comp0_V0beta_n  =  -30.0
  comp24_vchold  =  -71.0
  comp0_Kbeta_n  =  -20.0
  comp0_e  =  -84.69
  comp0_B_ninf  =  6.0
  comp24_vcbase  =  -69.0
  comp0_Aalpha_n  =  0.0033
  Vrest  =  -68.0
  fix_celsius  =  30.0
  comp24_vcbdur  =  100.0
  comp24_vcinc  =  10.0
  comp0_V0alpha_n  =  -30.0
}


STATE {
  KM_m
}


ASSIGNED {
  KM_m_inf
  KM_m_tau
  ica
  cai
  v
  ik
  ek
  i_KM
}


PROCEDURE asgns () {
  KM_m_tau  =  1.0 / (comp0_alpha_n(v) + comp0_beta_n(v))
  KM_m_inf  =  1.0 / (1.0 + exp(-(v + -(comp0_V0_ninf)) / comp0_B_ninf))
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  i_KM  =  (comp0_gbar * KM_m) * (v - comp0_e)
  ik  =  i_KM
}


DERIVATIVE states {
  asgns ()
  KM_m'  =  (KM_m_inf + -(KM_m)) / KM_m_tau
}


INITIAL {
  asgns ()
  KM_m  =  (comp0_alpha_n(v)) / (comp0_alpha_n(v) + comp0_beta_n(v))
}


PROCEDURE print_state () {
  printf ("KM_m = %g\n" ,  KM_m)
}
