

TITLE CGC_CaHVA


NEURON {
  RANGE CaHVA_h, CaHVA_m, comp44_vcbdur, comp44_vchdur, comp44_vcsteps, comp44_vcinc, comp44_vcbase, comp44_vchold, comp0_e, comp0_gbar
  RANGE i_CaHVA
  RANGE ica
  USEION ca READ eca WRITE ica
}


FUNCTION comp0_beta_u (v) {
  comp0_beta_u  =  
  comp0_Q10 * comp0_Abeta_u * 
    exp((v + -(comp0_V0beta_u)) / comp0_Kbeta_u)
}


FUNCTION comp0_beta_s (v) {
  comp0_beta_s  =  
  comp0_Q10 * comp0_Abeta_s * 
    exp((v + -(comp0_V0beta_s)) / comp0_Kbeta_s)
}


FUNCTION comp0_alpha_u (v) {
  comp0_alpha_u  =  
  comp0_Q10 * comp0_Aalpha_u * 
    exp((v + -(comp0_V0alpha_u)) / comp0_Kalpha_u)
}


FUNCTION comp0_alpha_s (v) {
  comp0_alpha_s  =  
  comp0_Q10 * comp0_Aalpha_s * 
    exp((v + -(comp0_V0alpha_s)) / comp0_Kalpha_s)
}


PARAMETER {
  comp0_Abeta_u  =  0.0013
  comp0_Abeta_s  =  0.08298
  comp0_Kalpha_u  =  -18.183
  comp0_Kalpha_s  =  15.87301587302
  comp0_gbar  =  0.00046
  comp44_vcbdur  =  100.0
  comp0_Q10  =  3.0
  comp0_V0beta_u  =  -48.0
  comp0_V0beta_s  =  -18.66
  comp0_Kbeta_u  =  83.33
  comp0_Kbeta_s  =  -25.641
  comp0_e  =  129.33
  comp44_vcsteps  =  8.0
  comp44_vchdur  =  30.0
  comp0_Aalpha_u  =  0.0013
  comp44_vcinc  =  10.0
  comp0_Aalpha_s  =  0.04944
  comp44_vchold  =  -71.0
  fix_celsius  =  30.0
  comp0_V0alpha_u  =  -48.0
  comp0_V0alpha_s  =  -29.06
  comp44_vcbase  =  -69.0
}


STATE {
  CaHVA_hC
  CaHVA_hO
  CaHVA_mC
  CaHVA_mO
  CaHVA_h
  CaHVA_m
}


ASSIGNED {
  v
  ica
  eca
  i_CaHVA
}


PROCEDURE reactions () {
  CaHVA_h  =  CaHVA_hO
  CaHVA_m  =  CaHVA_mO
}


BREAKPOINT {
  LOCAL v52
  SOLVE states METHOD derivimplicit
  reactions ()
  v52  =  CaHVA_m 
i_CaHVA  =  (comp0_gbar * v52 * v52 * CaHVA_h) * (v - comp0_e)
  ica  =  i_CaHVA
}


DERIVATIVE states {
  LOCAL v47, v50
  v47  =  CaHVA_mO 
CaHVA_mO'  =  
    -(CaHVA_mO * comp0_beta_s(v)) + (1 - v47) * (comp0_alpha_s(v))
  v50  =  CaHVA_hO 
CaHVA_hO'  =  
    -(CaHVA_hO * comp0_beta_u(v)) + (1 - v50) * (comp0_alpha_u(v))
}


INITIAL {
  CaHVA_h  =  (comp0_alpha_u(v)) / (comp0_alpha_u(v) + comp0_beta_u(v))
  CaHVA_hO  =  CaHVA_h
  CaHVA_m  =  (comp0_alpha_s(v)) / (comp0_alpha_s(v) + comp0_beta_s(v))
  CaHVA_mO  =  CaHVA_m
}


PROCEDURE print_state () {
  printf ("CaHVA_hO = %g\n" ,  CaHVA_hO)
  printf ("CaHVA_mO = %g\n" ,  CaHVA_mO)
}
