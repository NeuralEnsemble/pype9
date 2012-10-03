

TITLE CGC_Na


NEURON {
  RANGE comp2817_vchold, comp2817_vcbase, comp2817_vcinc, comp2817_vcsteps, comp2817_vchdur, comp2817_vcbdur, comp2902_gbar, comp2902_e, Na_m, Na_h
  RANGE i_Na
  RANGE ina
  RANGE ena
  USEION na READ ena WRITE ina
}


FUNCTION linoid (x, y) {
  LOCAL v4156
  if 
    (fabs(x / y) < 1e-06) 
     {v4156  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4156  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4156
}


FUNCTION comp2902_beta_h (v) {
  comp2902_beta_h  =  
  (comp2902_Q10 * comp2902_Abeta_h) / 
    (1.0 + exp((v + -(comp2902_V0beta_h)) / comp2902_Kbeta_h))
}


FUNCTION comp2902_beta_m (v) {
  comp2902_beta_m  =  
  comp2902_Q10 * comp2902_Abeta_m * 
    exp((v + -(comp2902_V0beta_m)) / comp2902_Kbeta_m)
}


FUNCTION comp2902_alpha_h (v) {
  comp2902_alpha_h  =  
  comp2902_Q10 * comp2902_Aalpha_h * 
    exp((v + -(comp2902_V0alpha_h)) / comp2902_Kalpha_h)
}


FUNCTION comp2902_alpha_m (v) {
  comp2902_alpha_m  =  
  comp2902_Q10 * comp2902_Aalpha_m * 
    linoid(v + -(comp2902_V0alpha_m), comp2902_Kalpha_m)
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


PARAMETER {
  comp2902_V0alpha_m  =  -19.0
  comp2902_V0alpha_h  =  -44.0
  comp2817_vchold  =  -71.0
  comp2902_Abeta_m  =  12.0
  comp2902_Abeta_h  =  1.5
  comp2817_vcbdur  =  100.0
  comp2902_Kalpha_m  =  -10.0
  comp2902_Kalpha_h  =  -3.333
  comp2817_vcsteps  =  9.0
  comp2817_vchdur  =  30.0
  comp2902_Aalpha_h  =  0.105
  comp2902_Aalpha_m  =  -0.3
  comp2902_Q10  =  3.0
  fix_celsius  =  30.0
  comp2902_gbar  =  0.013
  comp2902_e  =  87.39
  comp2817_vcinc  =  10.0
  comp2902_Kbeta_h  =  -5.0
  comp2902_Kbeta_m  =  -18.182
  comp2902_V0beta_m  =  -44.0
  comp2902_V0beta_h  =  -11.0
  comp2817_vcbase  =  -60.0
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
  LOCAL v4158
  SOLVE states METHOD derivimplicit
  reactions ()
  v4158  =  Na_m 
i_Na  =  (comp2902_gbar * v4158 * v4158 * v4158 * Na_h) * (v - ena)
  ina  =  i_Na
}


DERIVATIVE states {
  LOCAL v4151, v4154
  v4151  =  Na_mO 
Na_mO'  =  
    -(Na_mO * comp2902_beta_m(v)) + (1 - v4151) * (comp2902_alpha_m(v))
  v4154  =  Na_hO 
Na_hO'  =  
    -(Na_hO * comp2902_beta_h(v)) + (1 - v4154) * (comp2902_alpha_h(v))
}


INITIAL {
  Na_h  =  
  (comp2902_alpha_h(v)) / (comp2902_alpha_h(v) + comp2902_beta_h(v))
  Na_hO  =  Na_h
  Na_m  =  
  (comp2902_alpha_m(v)) / (comp2902_alpha_m(v) + comp2902_beta_m(v))
  Na_mO  =  Na_m
  ena  =  comp2902_e
}


PROCEDURE print_state () {
  printf ("NMODL state: t = %g v = %g Na_hO = %g\n" , t, v,  Na_hO)
  printf ("NMODL state: t = %g v = %g Na_mO = %g\n" , t, v,  Na_mO)
  printf ("NMODL state: t = %g v = %g Na_h = %g\n" , t, v,  Na_h)
  printf ("NMODL state: t = %g v = %g Na_m = %g\n" , t, v,  Na_m)
}
