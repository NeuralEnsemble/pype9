

TITLE CGC_KA


NEURON {
  RANGE comp685_vchold, comp685_vcbase, comp685_vcinc, comp685_vcsteps, comp685_vchdur, comp685_vcbdur, comp770_gbar, comp770_e, KA_m, KA_h
  RANGE i_KA
  RANGE ik
  RANGE ek
  USEION k READ ek WRITE ik
}


FUNCTION comp770_beta_b (v) {
  comp770_beta_b  =  
  comp770_Q10 * comp770_Abeta_b * 
    sigm(v + -(comp770_V0beta_b), comp770_Kbeta_b)
}


FUNCTION comp770_beta_a (v) {
  comp770_beta_a  =  
  comp770_Q10 * 
    comp770_Abeta_a / exp((v + -(comp770_V0beta_a)) / comp770_Kbeta_a)
}


FUNCTION linoid (x, y) {
  LOCAL v4123
  if 
    (fabs(x / y) < 1e-06) 
     {v4123  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4123  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4123
}


FUNCTION comp770_alpha_a (v) {
  comp770_alpha_a  =  
  comp770_Q10 * comp770_Aalpha_a * 
    sigm(v + -(comp770_V0alpha_a), comp770_Kalpha_a)
}


FUNCTION comp770_alpha_b (v) {
  comp770_alpha_b  =  
  comp770_Q10 * comp770_Aalpha_b * 
    sigm(v + -(comp770_V0alpha_b), comp770_Kalpha_b)
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


PARAMETER {
  fix_celsius  =  30.0
  comp685_vchdur  =  30.0
  comp770_Aalpha_a  =  4.88826
  comp770_Aalpha_b  =  0.11042
  comp770_gbar  =  0.004
  comp770_Abeta_a  =  0.99285
  comp770_Abeta_b  =  0.10353
  comp770_V0alpha_b  =  -111.33209
  comp770_V0alpha_a  =  -9.17203
  comp685_vcbdur  =  100.0
  comp770_V0_binf  =  -78.8
  comp770_Kalpha_b  =  12.8433
  comp770_Kalpha_a  =  -23.32708
  comp685_vcsteps  =  8.0
  comp770_K_binf  =  8.4
  comp770_V0_ainf  =  -46.7
  comp770_Kbeta_a  =  19.47175
  comp770_Kbeta_b  =  -8.90123
  comp685_vchold  =  -71.0
  comp770_e  =  -84.69
  comp770_K_ainf  =  -19.8
  comp770_V0beta_a  =  -18.27914
  comp770_V0beta_b  =  -49.9537
  comp685_vcbase  =  -69.0
  comp770_Q10  =  3.0
  comp685_vcinc  =  10.0
}


STATE {
  KA_h
  KA_m
}


ASSIGNED {
  KA_m_tau
  KA_m_inf
  KA_h_inf
  comp770_b_inf
  comp770_tau_b
  comp770_tau_a
  KA_h_tau
  comp770_a_inf
  v
  ik
  ek
  i_KA
}


PROCEDURE asgns () {
  comp770_a_inf  =  
  1.0 / (1.0 + exp((v + -(comp770_V0_ainf)) / comp770_K_ainf))
  comp770_tau_a  =  1.0 / (comp770_alpha_a(v) + comp770_beta_a(v))
  comp770_tau_b  =  1.0 / (comp770_alpha_b(v) + comp770_beta_b(v))
  comp770_b_inf  =  
  1.0 / (1.0 + exp((v + -(comp770_V0_binf)) / comp770_K_binf))
  KA_h_tau  =  comp770_tau_b
  KA_h_inf  =  comp770_b_inf
  KA_m_inf  =  comp770_a_inf
  KA_m_tau  =  comp770_tau_a
}


BREAKPOINT {
  LOCAL v4125
  SOLVE states METHOD derivimplicit
  v4125  =  KA_m 
i_KA  =  (comp770_gbar * v4125 * v4125 * v4125 * KA_h) * (v - ek)
  ik  =  i_KA
}


DERIVATIVE states {
  asgns ()
  KA_m'  =  (KA_m_inf + -(KA_m)) / KA_m_tau
  KA_h'  =  (KA_h_inf + -(KA_h)) / KA_h_tau
}


INITIAL {
  asgns ()
  KA_h  =  1.0 / (1.0 + exp((v + -(comp770_V0_binf)) / comp770_K_binf))
  KA_m  =  1.0 / (1.0 + exp((v + -(comp770_V0_ainf)) / comp770_K_ainf))
  ek  =  comp770_e
}


PROCEDURE print_state () {
  printf ("NMODL state: t = %g v = %g KA_h = %g\n" , t, v,  KA_h)
  printf ("NMODL state: t = %g v = %g KA_m = %g\n" , t, v,  KA_m)
}
