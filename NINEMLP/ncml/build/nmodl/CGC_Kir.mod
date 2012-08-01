

TITLE CGC_Kir


NEURON {
  RANGE Kir_m, comp24_vcbdur, comp24_vchdur, comp24_vcsteps, comp24_vcinc, comp24_vcbase, comp24_vchold, comp0_e, comp0_gbar
  RANGE i_Kir
  RANGE ik
  USEION k READ ek WRITE ik
}


FUNCTION comp0_beta_d (v) {
  comp0_beta_d  =  
  comp0_Q10 * comp0_Abeta_d * 
    exp((v + -(comp0_V0beta_d)) / comp0_Kbeta_d)
}


FUNCTION comp0_alpha_d (v) {
  comp0_alpha_d  =  
  comp0_Q10 * comp0_Aalpha_d * 
    exp((v + -(comp0_V0alpha_d)) / comp0_Kalpha_d)
}


PARAMETER {
  comp0_Abeta_d  =  0.16994
  comp0_gbar  =  0.0009
  comp0_Kalpha_d  =  -24.3902
  comp24_vchdur  =  30.0
  comp0_Q10  =  3.0
  comp24_vcsteps  =  8.0
  comp24_vchold  =  -71.0
  comp0_V0beta_d  =  -83.94
  comp0_Kbeta_d  =  35.714
  comp0_e  =  -84.69
  comp24_vcbase  =  -69.0
  comp0_Aalpha_d  =  0.13289
  Vrest  =  -68.0
  fix_celsius  =  30.0
  comp24_vcbdur  =  100.0
  comp24_vcinc  =  10.0
  comp0_V0alpha_d  =  -83.94
}


STATE {
  Kir_mC
  Kir_mO
  Kir_m
}


ASSIGNED {
  ica
  cai
  v
  ik
  ek
  i_Kir
}


PROCEDURE reactions () {
  Kir_m  =  Kir_mO
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  reactions ()
  i_Kir  =  (comp0_gbar * Kir_m) * (v - comp0_e)
  ik  =  i_Kir
}


DERIVATIVE states {
  LOCAL v27
  v27  =  Kir_mO 
Kir_mO'  =  -(Kir_mO * comp0_beta_d(v)) + (1 - v27) * (comp0_alpha_d(v))
}


INITIAL {
  Kir_m  =  (comp0_alpha_d(v)) / (comp0_alpha_d(v) + comp0_beta_d(v))
  Kir_mO  =  Kir_m
}


PROCEDURE print_state () {
  printf ("Kir_mO = %g\n" ,  Kir_mO)
}
