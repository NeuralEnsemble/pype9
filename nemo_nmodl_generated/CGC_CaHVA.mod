

TITLE CGC_CaHVA


NEURON {
  RANGE comp210_vchold, comp210_vcbase, comp210_vcinc, comp210_vcsteps, comp210_vchdur, comp210_vcbdur, comp295_gbar, comp295_e, CaHVA_m, CaHVA_h
  RANGE i_CaHVA
  RANGE ica
  RANGE eca
  USEION ca READ eca WRITE ica
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


FUNCTION linoid (x, y) {
  LOCAL v4119
  if 
    (fabs(x / y) < 1e-06) 
     {v4119  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4119  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4119
}


FUNCTION comp295_alpha_s (v) {
  comp295_alpha_s  =  
  comp295_Q10 * comp295_Aalpha_s * 
    exp((v + -(comp295_V0alpha_s)) / comp295_Kalpha_s)
}


FUNCTION comp295_alpha_u (v) {
  comp295_alpha_u  =  
  comp295_Q10 * comp295_Aalpha_u * 
    exp((v + -(comp295_V0alpha_u)) / comp295_Kalpha_u)
}


FUNCTION comp295_beta_s (v) {
  comp295_beta_s  =  
  comp295_Q10 * comp295_Abeta_s * 
    exp((v + -(comp295_V0beta_s)) / comp295_Kbeta_s)
}


FUNCTION comp295_beta_u (v) {
  comp295_beta_u  =  
  comp295_Q10 * comp295_Abeta_u * 
    exp((v + -(comp295_V0beta_u)) / comp295_Kbeta_u)
}


PARAMETER {
  comp210_vcinc  =  10.0
  comp210_vcbdur  =  100.0
  comp295_e  =  129.33
  comp295_V0beta_s  =  -18.66
  comp295_V0beta_u  =  -48.0
  comp210_vchold  =  -71.0
  comp295_Kalpha_u  =  -18.183
  comp295_Kalpha_s  =  15.87301587302
  comp295_Kbeta_u  =  83.33
  comp295_Kbeta_s  =  -25.641
  comp295_V0alpha_s  =  -29.06
  comp295_V0alpha_u  =  -48.0
  comp295_gbar  =  0.00046
  comp295_Q10  =  3.0
  comp210_vcsteps  =  8.0
  comp295_Aalpha_u  =  0.0013
  comp295_Aalpha_s  =  0.04944
  comp210_vchdur  =  30.0
  fix_celsius  =  30.0
  comp210_vcbase  =  -69.0
  comp295_Abeta_u  =  0.0013
  comp295_Abeta_s  =  0.08298
}


STATE {
  CaHVA_mC
  CaHVA_mO
  CaHVA_hC
  CaHVA_hO
  CaHVA_m
  CaHVA_h
}


ASSIGNED {
  v
  ica
  eca
  i_CaHVA
}


PROCEDURE reactions () {
  CaHVA_m  =  CaHVA_mO
  CaHVA_h  =  CaHVA_hO
}


BREAKPOINT {
  LOCAL v4121
  SOLVE states METHOD derivimplicit
  reactions ()
  v4121  =  CaHVA_m 
i_CaHVA  =  (comp295_gbar * v4121 * v4121 * CaHVA_h) * (v - eca)
  ica  =  i_CaHVA
}


DERIVATIVE states {
  LOCAL v4114, v4117
  v4114  =  CaHVA_hO 
CaHVA_hO'  =  
    -(CaHVA_hO * comp295_beta_u(v)) + (1 - v4114) * (comp295_alpha_u(v))
  v4117  =  CaHVA_mO 
CaHVA_mO'  =  
    -(CaHVA_mO * comp295_beta_s(v)) + (1 - v4117) * (comp295_alpha_s(v))
}


INITIAL {
  CaHVA_m  =  
  (comp295_alpha_s(v)) / (comp295_alpha_s(v) + comp295_beta_s(v))
  CaHVA_mO  =  CaHVA_m
  CaHVA_h  =  
  (comp295_alpha_u(v)) / (comp295_alpha_u(v) + comp295_beta_u(v))
  CaHVA_hO  =  CaHVA_h
  eca  =  comp295_e
}


PROCEDURE print_state () {
  printf ("NMODL state: t = %g v = %g CaHVA_hO = %g\n" , t, v,  CaHVA_hO)
  printf ("NMODL state: t = %g v = %g CaHVA_mO = %g\n" , t, v,  CaHVA_mO)
  printf ("NMODL state: t = %g v = %g CaHVA_h = %g\n" , t, v,  CaHVA_h)
  printf ("NMODL state: t = %g v = %g CaHVA_m = %g\n" , t, v,  CaHVA_m)
}
