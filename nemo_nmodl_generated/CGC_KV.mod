

TITLE CGC_KV


NEURON {
  RANGE comp2288_vchold, comp2288_vcbase, comp2288_vcinc, comp2288_vcsteps, comp2288_vchdur, comp2288_vcbdur, comp2373_gbar, comp2373_e, KV_m
  RANGE i_KV
  RANGE ik
  RANGE ek
  USEION k READ ek WRITE ik
}


FUNCTION linoid (x, y) {
  LOCAL v4142
  if 
    (fabs(x / y) < 1e-06) 
     {v4142  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4142  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4142
}


FUNCTION comp2373_alpha_n (v) {
  comp2373_alpha_n  =  
  comp2373_Q10 * comp2373_Aalpha_n * 
    linoid(v + -(comp2373_V0alpha_n), comp2373_Kalpha_n)
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


FUNCTION comp2373_beta_n (v) {
  comp2373_beta_n  =  
  comp2373_Q10 * comp2373_Abeta_n * 
    exp((v + -(comp2373_V0beta_n)) / comp2373_Kbeta_n)
}


PARAMETER {
  comp2373_Kalpha_n  =  -10.0
  comp2373_Kbeta_n  =  -80.0
  comp2373_gbar  =  0.003
  comp2373_e  =  -84.69
  fix_celsius  =  30.0
  comp2373_Q10  =  13.5137964673603
  comp2288_vcsteps  =  8.0
  comp2373_Abeta_n  =  0.125
  comp2288_vchold  =  -71.0
  comp2288_vcbdur  =  100.0
  comp2288_vchdur  =  30.0
  comp2288_vcbase  =  -69.0
  comp2288_vcinc  =  10.0
  comp2373_V0beta_n  =  -35.0
  comp2373_V0alpha_n  =  -25.0
  comp2373_Aalpha_n  =  -0.01
}


STATE {
  KV_mC
  KV_mO
  KV_m
}


ASSIGNED {
  v
  ik
  ek
  i_KV
}


PROCEDURE reactions () {
  KV_m  =  KV_mO
}


BREAKPOINT {
  LOCAL v4144
  SOLVE states METHOD derivimplicit
  reactions ()
  v4144  =  KV_m 
i_KV  =  (comp2373_gbar * v4144 * v4144 * v4144 * v4144) * (v - ek)
  ik  =  i_KV
}


DERIVATIVE states {
  LOCAL v4140
  v4140  =  KV_mO 
KV_mO'  =  
    -(KV_mO * comp2373_beta_n(v)) + (1 - v4140) * (comp2373_alpha_n(v))
}


INITIAL {
  KV_m  =  
  (comp2373_alpha_n(v)) / (comp2373_alpha_n(v) + comp2373_beta_n(v))
  KV_mO  =  KV_m
  ek  =  comp2373_e
}


PROCEDURE print_state () {
  printf ("NMODL state: t = %g v = %g KV_mO = %g\n" , t, v,  KV_mO)
  printf ("NMODL state: t = %g v = %g KV_m = %g\n" , t, v,  KV_m)
}
