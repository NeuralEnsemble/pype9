

TITLE CGC_KA


NEURON {
  RANGE KA_h, KA_m, comp46_vcbdur, comp46_vchdur, comp46_vcsteps, comp46_vcinc, comp46_vcbase, comp46_vchold, comp5_e, comp5_gbar
  RANGE i_KA
  RANGE ik
  USEION k READ ek WRITE ik
}


FUNCTION comp5_beta_b (v) {
  comp5_beta_b  =  
  comp5_Q10 * comp5_Abeta_b * sigm(v + -(comp5_V0beta_b), comp5_Kbeta_b)
}


FUNCTION comp5_beta_a (v) {
  comp5_beta_a  =  
  comp5_Q10 * 
    comp5_Abeta_a / exp((v + -(comp5_V0beta_a)) / comp5_Kbeta_a)
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


FUNCTION comp5_alpha_b (v) {
  comp5_alpha_b  =  
  comp5_Q10 * comp5_Aalpha_b * 
    sigm(v + -(comp5_V0alpha_b), comp5_Kalpha_b)
}


FUNCTION comp5_alpha_a (v) {
  comp5_alpha_a  =  
  comp5_Q10 * comp5_Aalpha_a * 
    sigm(v + -(comp5_V0alpha_a), comp5_Kalpha_a)
}


PARAMETER {
  comp46_vcinc  =  10.0
  comp5_Kalpha_b  =  12.8433
  comp5_Kalpha_a  =  -23.32708
  comp5_V0alpha_b  =  -111.33209
  comp5_V0alpha_a  =  -9.17203
  comp46_vchdur  =  30.0
  comp5_e  =  -84.69
  comp5_V0_ainf  =  -46.7
  comp5_V0beta_b  =  -49.9537
  comp5_V0beta_a  =  -18.27914
  comp5_K_binf  =  8.4
  comp5_Abeta_b  =  0.10353
  comp5_Abeta_a  =  0.99285
  comp46_vchold  =  -71.0
  comp5_Aalpha_b  =  0.11042
  comp5_Aalpha_a  =  4.88826
  comp46_vcbase  =  -69.0
  comp5_Q10  =  3.0
  comp5_V0_binf  =  -78.8
  Vrest  =  -68.0
  fix_celsius  =  30.0
  comp5_Kbeta_b  =  -8.90123
  comp5_Kbeta_a  =  19.47175
  comp46_vcsteps  =  8.0
  comp46_vcbdur  =  100.0
  comp5_K_ainf  =  -19.8
  comp5_gbar  =  0.004
}


STATE {
  KA_h
  KA_m
}


ASSIGNED {
  KA_h_tau
  comp5_b_inf
  KA_m_inf
  comp5_tau_b
  comp5_tau_a
  KA_m_tau
  KA_h_inf
  comp5_a_inf
  ica
  cai
  v
  ik
  ek
  i_KA
}


PROCEDURE asgns () {
  comp5_a_inf  =  1.0 / (1.0 + exp((v + -(comp5_V0_ainf)) / comp5_K_ainf))
  comp5_tau_a  =  1.0 / (comp5_alpha_a(v) + comp5_beta_a(v))
  comp5_tau_b  =  1.0 / (comp5_alpha_b(v) + comp5_beta_b(v))
  comp5_b_inf  =  1.0 / (1.0 + exp((v + -(comp5_V0_binf)) / comp5_K_binf))
  KA_h_inf  =  comp5_b_inf
  KA_m_tau  =  comp5_tau_a
  KA_m_inf  =  comp5_a_inf
  KA_h_tau  =  comp5_tau_b
}


BREAKPOINT {
  LOCAL v48
  SOLVE states METHOD derivimplicit
  v48  =  KA_m 
i_KA  =  (comp5_gbar * v48 * v48 * v48 * KA_h) * (v - comp5_e)
  ik  =  i_KA
}


DERIVATIVE states {
  asgns ()
  KA_m'  =  (KA_m_inf + -(KA_m)) / KA_m_tau
  KA_h'  =  (KA_h_inf + -(KA_h)) / KA_h_tau
}


INITIAL {
  asgns ()
  KA_h  =  (comp5_alpha_b(v)) / (comp5_alpha_b(v) + comp5_beta_b(v))
  KA_m  =  (comp5_alpha_a(v)) / (comp5_alpha_a(v) + comp5_beta_a(v))
}


PROCEDURE print_state () {
  printf ("KA_h = %g\n" ,  KA_h)
  printf ("KA_m = %g\n" ,  KA_m)
}
