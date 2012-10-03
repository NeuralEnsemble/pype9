

TITLE CGC_NaR


NEURON {
  RANGE comp3292_vchold, comp3292_vcbase, comp3292_vcinc, comp3292_vcsteps, comp3292_vchdur, comp3292_vcbdur, comp3377_gbar, comp3377_e, NaR_m, NaR_h
  RANGE i_NaR
  RANGE ina
  RANGE ena
  USEION na READ ena WRITE ina
}


FUNCTION comp3377_beta_s (v) {
  comp3377_beta_s  =  
  comp3377_Q10 * 
    (comp3377_Shiftbeta_s + 
        comp3377_Abeta_s * 
          (v + comp3377_V0beta_s) / 
            (exp((v + comp3377_V0beta_s) / comp3377_Kbeta_s) + -1.0))
}


FUNCTION comp3377_beta_f (v) {
  comp3377_beta_f  =  
  comp3377_Q10 * comp3377_Abeta_f * 
    exp((v + -(comp3377_V0beta_f)) / comp3377_Kbeta_f)
}


FUNCTION linoid (x, y) {
  LOCAL v4166
  if 
    (fabs(x / y) < 1e-06) 
     {v4166  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4166  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4166
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


FUNCTION comp3377_alpha_f (v) {
  comp3377_alpha_f  =  
  comp3377_Q10 * comp3377_Aalpha_f * 
    exp((v + -(comp3377_V0alpha_f)) / comp3377_Kalpha_f)
}


FUNCTION comp3377_alpha_s (v) {
  comp3377_alpha_s  =  
  comp3377_Q10 * 
    (comp3377_Shiftalpha_s + 
        comp3377_Aalpha_s * 
          (v + comp3377_V0alpha_s) / 
            (exp((v + comp3377_V0alpha_s) / comp3377_Kalpha_s) + -1.0))
}


PARAMETER {
  comp3377_V0alpha_s  =  -4.48754
  comp3377_V0alpha_f  =  -80.0
  comp3377_gbar  =  0.0005
  comp3377_e  =  87.39
  comp3292_vchdur  =  30.0
  comp3292_vcbdur  =  100.0
  comp3292_vchold  =  -71.0
  comp3377_Q10  =  3.0
  comp3377_Kalpha_f  =  -62.52621
  comp3377_Kalpha_s  =  -6.81881
  comp3377_Shiftalpha_s  =  8e-05
  comp3377_Aalpha_f  =  0.31836
  comp3377_Aalpha_s  =  -0.00493
  comp3292_vcbase  =  -60.0
  comp3377_V0beta_s  =  43.97494
  comp3377_V0beta_f  =  -83.3332
  comp3377_Abeta_f  =  0.01014
  comp3377_Abeta_s  =  0.01558
  comp3292_vcsteps  =  9.0
  fix_celsius  =  30.0
  comp3377_Kbeta_s  =  0.10818
  comp3377_Kbeta_f  =  16.05379
  comp3292_vcinc  =  10.0
  comp3377_Shiftbeta_s  =  0.04752
}


STATE {
  NaR_hC
  NaR_hO
  NaR_mC
  NaR_mO
  NaR_h
  NaR_m
}


ASSIGNED {
  v
  ina
  ena
  i_NaR
}


PROCEDURE reactions () {
  NaR_h  =  NaR_hO
  NaR_m  =  NaR_mO
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  reactions ()
  i_NaR  =  (comp3377_gbar * NaR_m * NaR_h) * (v - ena)
  ina  =  i_NaR
}


DERIVATIVE states {
  LOCAL v4161, v4164
  v4161  =  NaR_mO 
NaR_mO'  =  
    -(NaR_mO * comp3377_beta_s(v)) + (1 - v4161) * (comp3377_alpha_s(v))
  v4164  =  NaR_hO 
NaR_hO'  =  
    -(NaR_hO * comp3377_beta_f(v)) + (1 - v4164) * (comp3377_alpha_f(v))
}


INITIAL {
  NaR_h  =  
  (comp3377_alpha_f(v)) / (comp3377_alpha_f(v) + comp3377_beta_f(v))
  NaR_hO  =  NaR_h
  NaR_m  =  
  (comp3377_alpha_s(v)) / (comp3377_alpha_s(v) + comp3377_beta_s(v))
  NaR_mO  =  NaR_m
  ena  =  comp3377_e
}


PROCEDURE print_state () {
  printf ("NMODL state: t = %g v = %g NaR_hO = %g\n" , t, v,  NaR_hO)
  printf ("NMODL state: t = %g v = %g NaR_mO = %g\n" , t, v,  NaR_mO)
  printf ("NMODL state: t = %g v = %g NaR_h = %g\n" , t, v,  NaR_h)
  printf ("NMODL state: t = %g v = %g NaR_m = %g\n" , t, v,  NaR_m)
}
