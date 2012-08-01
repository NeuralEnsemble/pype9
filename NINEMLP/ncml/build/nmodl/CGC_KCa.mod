

TITLE CGC_KCa


NEURON {
  RANGE KCa_m, comp0_e, comp0_gbar
  RANGE i_KCa
  RANGE ik
  USEION k READ ek WRITE ik
}


FUNCTION comp0_beta_c (v, cai) {
  comp0_beta_c  =  
  (comp0_Q10 * comp0_Abeta_c) / 
    (1.0 + cai / (comp0_Bbeta_c * exp(v / comp0_Kbeta_c)))
}


FUNCTION comp0_alpha_c (v, cai) {
  comp0_alpha_c  =  
  (comp0_Q10 * comp0_Aalpha_c) / 
    (1.0 + (comp0_Balpha_c * exp(v / comp0_Kalpha_c)) / cai)
}


PARAMETER {
  comp0_Abeta_c  =  1.5
  comp0_gbar  =  0.004
  comp0_Kalpha_c  =  -11.765
  comp0_Q10  =  1.0
  comp0_Kbeta_c  =  -11.765
  comp0_Balpha_c  =  0.0015
  comp0_e  =  -84.69
  comp0_Aalpha_c  =  2.5
  Vrest  =  -68.0
  fix_celsius  =  30.0
  comp0_Bbeta_c  =  0.00015
}


STATE {
  KCa_m
}


ASSIGNED {
  KCa_m_inf
  KCa_m_tau
  ica
  cai
  v
  ik
  ek
  i_KCa
}


PROCEDURE asgns () {
  KCa_m_tau  =  comp0_beta_c(v, cai)
  KCa_m_inf  =  comp0_alpha_c(v, cai)
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  i_KCa  =  (comp0_gbar * KCa_m) * (v - comp0_e)
  ik  =  i_KCa
}


DERIVATIVE states {
  asgns ()
  KCa_m'  =  (KCa_m_inf + -(KCa_m)) / KCa_m_tau
}


INITIAL {
  asgns ()
  KCa_m  =  
  (comp0_alpha_c(v, cai)) / 
    (comp0_alpha_c(v, cai) + comp0_beta_c(v, cai))
}


PROCEDURE print_state () {
  printf ("KCa_m = %g\n" ,  KCa_m)
}
