

TITLE CGC_KCa


NEURON {
  RANGE comp1216_vchold, comp1216_vcbase, comp1216_vcinc, comp1216_vcsteps, comp1216_vchdur, comp1216_vcbdur, comp1301_gbar, comp1301_e, KCa_m
  RANGE i_KCa
  RANGE ik
  RANGE ek
  RANGE cai
  USEION ca READ cai
  USEION k READ ek WRITE ik
}


FUNCTION comp1301_beta_c (v, cai) {
  comp1301_beta_c  =  
  (comp1301_Q10 * comp1301_Abeta_c) / 
    (1.0 + cai / (comp1301_Bbeta_c * exp(v / comp1301_Kbeta_c)))
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


FUNCTION comp1301_alpha_c (v, cai) {
  comp1301_alpha_c  =  
  (comp1301_Q10 * comp1301_Aalpha_c) / 
    (1.0 + (comp1301_Balpha_c * exp(v / comp1301_Kalpha_c)) / cai)
}


FUNCTION linoid (x, y) {
  LOCAL v4130
  if 
    (fabs(x / y) < 1e-06) 
     {v4130  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4130  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4130
}


PARAMETER {
  comp1216_vcbase  =  -69.0
  comp1216_vchold  =  -71.0
  fix_celsius  =  30.0
  comp1301_Abeta_c  =  1.5
  comp1301_Q10  =  1.0
  comp1216_vchdur  =  30.0
  comp1216_vcsteps  =  8.0
  comp1301_e  =  -84.69
  comp1216_vcbdur  =  100.0
  comp1301_Kbeta_c  =  -11.765
  comp1216_vcinc  =  10.0
  comp1301_Bbeta_c  =  0.00015
  comp1301_Aalpha_c  =  2.5
  comp1301_Kalpha_c  =  -11.765
  comp1301_gbar  =  0.003
  comp1301_Balpha_c  =  0.0015
}


STATE {
  KCa_mC
  KCa_mO
  KCa_m
}


ASSIGNED {
  comp1301_cai
  v
  cai
  ik
  ek
  i_KCa
}


PROCEDURE reactions () {
  KCa_m  =  KCa_mO
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  reactions ()
  i_KCa  =  (comp1301_gbar * KCa_m) * (v - ek)
  ik  =  i_KCa
}


DERIVATIVE states {
  LOCAL v4128
  comp1301_cai  =  cai
  v4128  =  KCa_mO 
KCa_mO'  =  
    -(KCa_mO * comp1301_beta_c(v, comp1301_cai)) + 
        (1 - v4128) * (comp1301_alpha_c(v, comp1301_cai))
}


INITIAL {
  comp1301_cai  =  cai
  KCa_m  =  
  (comp1301_alpha_c(v, comp1301_cai)) / 
    (comp1301_alpha_c(v, comp1301_cai) + 
        comp1301_beta_c(v, comp1301_cai))
  KCa_mO  =  KCa_m
  ek  =  comp1301_e
}


PROCEDURE print_state () {
  printf ("NMODL state: t = %g v = %g KCa_mO = %g\n" , t, v,  KCa_mO)
  printf ("NMODL state: t = %g v = %g KCa_m = %g\n" , t, v,  KCa_m)
}
