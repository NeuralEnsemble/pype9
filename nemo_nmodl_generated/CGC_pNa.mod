

TITLE CGC_pNa


NEURON {
  RANGE comp3795_vchold, comp3795_vcbase, comp3795_vcinc, comp3795_vcsteps, comp3795_vchdur, comp3795_vcbdur, comp3880_gbar, comp3880_e, pNa_m
  RANGE i_pNa
  RANGE ina
  RANGE ena
  USEION na READ ena WRITE ina
}


FUNCTION comp3880_alpha_m (v) {
  comp3880_alpha_m  =  
  comp3880_Q10 * comp3880_Aalpha_m * 
    linoid(v + -(comp3880_V0alpha_m), comp3880_Kalpha_m)
}


FUNCTION linoid (x, y) {
  LOCAL v4168
  if 
    (fabs(x / y) < 1e-06) 
     {v4168  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4168  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4168
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


FUNCTION comp3880_beta_m (v) {
  comp3880_beta_m  =  
  comp3880_Q10 * comp3880_Abeta_m * 
    linoid(v + -(comp3880_V0beta_m), comp3880_Kbeta_m)
}


PARAMETER {
  comp3880_Q10  =  1.0
  comp3880_B_minf  =  5.0
  comp3795_vchold  =  -71.0
  comp3880_Kalpha_m  =  -5.0
  comp3795_vcbase  =  -60.0
  comp3880_Abeta_m  =  0.062
  comp3880_gbar  =  2e-05
  fix_celsius  =  30.0
  comp3880_V0alpha_m  =  -42.0
  comp3880_V0_minf  =  -42.0
  comp3880_V0beta_m  =  -42.0
  comp3795_vchdur  =  30.0
  comp3880_e  =  87.39
  comp3795_vcsteps  =  9.0
  comp3795_vcbdur  =  100.0
  comp3795_vcinc  =  10.0
  comp3880_Aalpha_m  =  -0.091
  comp3880_Kbeta_m  =  5.0
}


STATE {
  pNa_m
}


ASSIGNED {
  pNa_m_tau
  pNa_m_inf
  v
  ina
  ena
  i_pNa
}


PROCEDURE asgns () {
  pNa_m_inf  =  
  1.0 / (1.0 + exp(-(v + -(comp3880_V0_minf)) / comp3880_B_minf))
  pNa_m_tau  =  5.0 / (comp3880_alpha_m(v) + comp3880_beta_m(v))
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  i_pNa  =  (comp3880_gbar * pNa_m) * (v - ena)
  ina  =  i_pNa
}


DERIVATIVE states {
  asgns ()
  pNa_m'  =  (pNa_m_inf + -(pNa_m)) / pNa_m_tau
}


INITIAL {
  asgns ()
  pNa_m  =  
  1.0 / (1.0 + exp(-(v + -(comp3880_V0_minf)) / comp3880_B_minf))
  ena  =  comp3880_e
}


PROCEDURE print_state () {
  printf ("NMODL state: t = %g v = %g pNa_m = %g\n" , t, v,  pNa_m)
}
