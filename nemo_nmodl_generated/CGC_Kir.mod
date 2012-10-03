

TITLE CGC_Kir


NEURON {
  RANGE comp1566_vchold, comp1566_vcbase, comp1566_vcinc, comp1566_vcsteps, comp1566_vchdur, comp1566_vcbdur, comp1651_gbar, comp1651_e, Kir_m
  RANGE i_Kir
  RANGE ik
  RANGE ek
  USEION k READ ek WRITE ik
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


FUNCTION comp1651_beta_d (v) {
  comp1651_beta_d  =  
  comp1651_Q10 * comp1651_Abeta_d * 
    exp((v + -(comp1651_V0beta_d)) / comp1651_Kbeta_d)
}


FUNCTION comp1651_alpha_d (v) {
  comp1651_alpha_d  =  
  comp1651_Q10 * comp1651_Aalpha_d * 
    exp((v + -(comp1651_V0alpha_d)) / comp1651_Kalpha_d)
}


FUNCTION linoid (x, y) {
  LOCAL v4135
  if 
    (fabs(x / y) < 1e-06) 
     {v4135  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4135  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4135
}


PARAMETER {
  fix_celsius  =  30.0
  comp1651_Kalpha_d  =  -24.3902
  comp1566_vchold  =  -71.0
  comp1566_vcinc  =  10.0
  comp1651_gbar  =  0.0009
  comp1566_vcsteps  =  8.0
  comp1651_e  =  -84.69
  comp1566_vchdur  =  30.0
  comp1651_Q10  =  3.0
  comp1566_vcbdur  =  100.0
  comp1651_V0alpha_d  =  -83.94
  comp1566_vcbase  =  -69.0
  comp1651_Abeta_d  =  0.16994
  comp1651_Kbeta_d  =  35.714
  comp1651_Aalpha_d  =  0.13289
  comp1651_V0beta_d  =  -83.94
}


STATE {
  Kir_mC
  Kir_mO
  Kir_m
}


ASSIGNED {
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
  i_Kir  =  (comp1651_gbar * Kir_m) * (v - ek)
  ik  =  i_Kir
}


DERIVATIVE states {
  LOCAL v4133
  v4133  =  Kir_mO 
Kir_mO'  =  
    -(Kir_mO * comp1651_beta_d(v)) + (1 - v4133) * (comp1651_alpha_d(v))
}


INITIAL {
  Kir_m  =  
  (comp1651_alpha_d(v)) / (comp1651_alpha_d(v) + comp1651_beta_d(v))
  Kir_mO  =  Kir_m
  ek  =  comp1651_e
}


PROCEDURE print_state () {
  printf ("NMODL state: t = %g v = %g Kir_mO = %g\n" , t, v,  Kir_mO)
  printf ("NMODL state: t = %g v = %g Kir_m = %g\n" , t, v,  Kir_m)
}
