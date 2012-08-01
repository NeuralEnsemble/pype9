

TITLE CGC_Na


NEURON {
  RANGE Na_h, Na_m, comp52_vcbdur, comp52_vchdur, comp52_vcsteps, comp52_vcinc, comp52_vcbase, comp52_vchold, comp9_e, comp9_gbar
  RANGE i_Na
  RANGE ina
  USEION na READ ena WRITE ina
}


FUNCTION linoid (x, y) {
  LOCAL v60
  if 
    (fabs(x / y) < 1e-06) 
     {v60  =  y * (1.0 + -(x / y / 2.0))} 
    else {v60  =  x / (exp(x / y) + -1.0)} 
linoid  =  v60
}


FUNCTION comp9_beta_m (v) {
  comp9_beta_m  =  
  comp9_Q10 * comp9_Abeta_m * 
    exp((v + -(comp9_V0beta_m)) / comp9_Kbeta_m)
}


FUNCTION comp9_beta_h (v) {
  comp9_beta_h  =  
  (comp9_Q10 * comp9_Abeta_h) / 
    (1.0 + exp((v + -(comp9_V0beta_h)) / comp9_Kbeta_h))
}


FUNCTION comp9_alpha_m (v) {
  comp9_alpha_m  =  
  comp9_Q10 * comp9_Aalpha_m * 
    linoid(v + -(comp9_V0alpha_m), comp9_Kalpha_m)
}


FUNCTION comp9_alpha_h (v) {
  comp9_alpha_h  =  
  comp9_Q10 * comp9_Aalpha_h * 
    exp((v + -(comp9_V0alpha_h)) / comp9_Kalpha_h)
}


PARAMETER {
  comp9_V0alpha_m  =  -19.0
  comp52_vcbdur  =  100.0
  comp9_V0alpha_h  =  -44.0
  comp9_Kalpha_m  =  -10.0
  comp9_Kbeta_m  =  -18.182
  comp9_Kalpha_h  =  -3.333
  comp9_gbar  =  0.013
  comp9_Kbeta_h  =  -5.0
  comp52_vchdur  =  30.0
  comp9_V0beta_m  =  -44.0
  comp9_V0beta_h  =  -11.0
  comp52_vchold  =  -71.0
  Vrest  =  -68.0
  fix_celsius  =  30.0
  comp9_Q10  =  3.0
  comp52_vcsteps  =  9.0
  comp9_Aalpha_m  =  -0.3
  comp9_Aalpha_h  =  0.105
  comp52_vcbase  =  -60.0
  comp9_e  =  87.39
  comp9_Abeta_m  =  12.0
  comp52_vcinc  =  10.0
  comp9_Abeta_h  =  1.5
}


STATE {
  Na_hC
  Na_hO
  Na_mC
  Na_mO
  Na_h
  Na_m
}


ASSIGNED {
  ica
  cai
  v
  ina
  ena
  i_Na
}


PROCEDURE reactions () {
  Na_h  =  Na_hO
  Na_m  =  Na_mO
}


BREAKPOINT {
  LOCAL v62
  SOLVE states METHOD derivimplicit
  reactions ()
  v62  =  Na_m 
i_Na  =  (comp9_gbar * v62 * v62 * v62 * Na_h) * (v - comp9_e)
  ina  =  i_Na
}


DERIVATIVE states {
  LOCAL v55, v58
  v55  =  Na_mO 
Na_mO'  =  -(Na_mO * comp9_beta_m(v)) + (1 - v55) * (comp9_alpha_m(v))
  v58  =  Na_hO 
Na_hO'  =  -(Na_hO * comp9_beta_h(v)) + (1 - v58) * (comp9_alpha_h(v))
}


INITIAL {
  Na_h  =  (comp9_alpha_h(v)) / (comp9_alpha_h(v) + comp9_beta_h(v))
  Na_hO  =  Na_h
  Na_m  =  (comp9_alpha_m(v)) / (comp9_alpha_m(v) + comp9_beta_m(v))
  Na_mO  =  Na_m
}


PROCEDURE print_state () {
  printf ("Na_hO = %g\n" ,  Na_hO)
  printf ("Na_mO = %g\n" ,  Na_mO)
}
