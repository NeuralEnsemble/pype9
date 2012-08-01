

TITLE CGC_KV


NEURON {
  RANGE KV_m, comp32_vcbdur, comp32_vchdur, comp32_vcsteps, comp32_vcinc, comp32_vcbase, comp32_vchold, comp9_e, comp9_gbar
  RANGE i_KV
  RANGE ik
  USEION k READ ek WRITE ik
}


FUNCTION linoid (x, y) {
  LOCAL v37
  if 
    (fabs(x / y) < 1e-06) 
     {v37  =  y * (1.0 + -(x / y / 2.0))} 
    else {v37  =  x / (exp(x / y) + -1.0)} 
linoid  =  v37
}


FUNCTION comp9_beta_n (v) {
  comp9_beta_n  =  
  comp9_Q10 * comp9_Abeta_n * 
    exp((v + -(comp9_V0beta_n)) / comp9_Kbeta_n)
}


FUNCTION comp9_alpha_n (v) {
  comp9_alpha_n  =  
  comp9_Q10 * comp9_Aalpha_n * 
    linoid(v + -(comp9_V0alpha_n), comp9_Kalpha_n)
}


PARAMETER {
  comp9_V0alpha_n  =  -25.0
  comp32_vchdur  =  30.0
  comp32_vcinc  =  10.0
  comp32_vchold  =  -71.0
  comp9_Kalpha_n  =  -10.0
  comp9_Kbeta_n  =  -80.0
  comp9_gbar  =  0.003
  comp32_vcbase  =  -69.0
  comp9_V0beta_n  =  -35.0
  comp32_vcsteps  =  8.0
  Vrest  =  -68.0
  fix_celsius  =  30.0
  comp9_Q10  =  13.5137964673603
  comp9_Aalpha_n  =  -0.01
  comp32_vcbdur  =  100.0
  comp9_e  =  -84.69
  comp9_Abeta_n  =  0.125
}


STATE {
  KV_mC
  KV_mO
  KV_m
}


ASSIGNED {
  ica
  cai
  v
  ik
  ek
  i_KV
}


PROCEDURE reactions () {
  KV_m  =  KV_mO
}


BREAKPOINT {
  LOCAL v39
  SOLVE states METHOD derivimplicit
  reactions ()
  v39  =  KV_m 
i_KV  =  (comp9_gbar * v39 * v39 * v39 * v39) * (v - comp9_e)
  ik  =  i_KV
}


DERIVATIVE states {
  LOCAL v35
  v35  =  KV_mO 
KV_mO'  =  -(KV_mO * comp9_beta_n(v)) + (1 - v35) * (comp9_alpha_n(v))
}


INITIAL {
  KV_m  =  (comp9_alpha_n(v)) / (comp9_alpha_n(v) + comp9_beta_n(v))
  KV_mO  =  KV_m
}


PROCEDURE print_state () {
  printf ("KV_mO = %g\n" ,  KV_mO)
}
