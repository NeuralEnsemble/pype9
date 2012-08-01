

TITLE CGC_pNa


NEURON {
  RANGE pNa_m, comp31_vcbdur, comp31_vchdur, comp31_vcsteps, comp31_vcinc, comp31_vcbase, comp31_vchold, comp9_e, comp9_gbar
  RANGE i_pNa
  RANGE ina
  USEION na READ ena WRITE ina
}


FUNCTION linoid (x, y) {
  LOCAL v33
  if 
    (fabs(x / y) < 1e-06) 
     {v33  =  y * (1.0 + -(x / y / 2.0))} 
    else {v33  =  x / (exp(x / y) + -1.0)} 
linoid  =  v33
}


FUNCTION comp9_beta_m (v) {
  comp9_beta_m  =  
  comp9_Q10 * comp9_Abeta_m * 
    linoid(v + -(comp9_V0beta_m), comp9_Kbeta_m)
}


FUNCTION comp9_alpha_m (v) {
  comp9_alpha_m  =  
  comp9_Q10 * comp9_Aalpha_m * 
    linoid(v + -(comp9_V0alpha_m), comp9_Kalpha_m)
}


PARAMETER {
  comp9_V0alpha_m  =  -42.0
  comp31_vchdur  =  30.0
  comp9_Kalpha_m  =  -5.0
  comp9_Kbeta_m  =  5.0
  comp9_gbar  =  2e-05
  comp31_vchold  =  -71.0
  comp31_vcinc  =  10.0
  comp9_V0beta_m  =  -42.0
  comp9_V0_minf  =  -42.0
  comp31_vcbase  =  -60.0
  Vrest  =  -68.0
  fix_celsius  =  30.0
  comp9_Q10  =  1.0
  comp9_Aalpha_m  =  -0.091
  comp9_B_minf  =  5.0
  comp9_e  =  87.39
  comp31_vcsteps  =  9.0
  comp9_Abeta_m  =  0.062
  comp31_vcbdur  =  100.0
}


STATE {
  pNa_m
}


ASSIGNED {
  pNa_m_inf
  pNa_m_tau
  ica
  cai
  v
  ina
  ena
  i_pNa
}


PROCEDURE asgns () {
  pNa_m_tau  =  5.0 / (comp9_alpha_m(v) + comp9_beta_m(v))
  pNa_m_inf  =  1.0 / (1.0 + exp(-(v + -(comp9_V0_minf)) / comp9_B_minf))
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  i_pNa  =  (comp9_gbar * pNa_m) * (v - comp9_e)
  ina  =  i_pNa
}


DERIVATIVE states {
  asgns ()
  pNa_m'  =  (pNa_m_inf + -(pNa_m)) / pNa_m_tau
}


INITIAL {
  asgns ()
  pNa_m  =  (comp9_alpha_m(v)) / (comp9_alpha_m(v) + comp9_beta_m(v))
}


PROCEDURE print_state () {
  printf ("pNa_m = %g\n" ,  pNa_m)
}
