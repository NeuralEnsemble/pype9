

TITLE CGC_Nar


NEURON {
  RANGE Nar_h, Nar_m, comp44_vcbdur, comp44_vchdur, comp44_vcsteps, comp44_vcinc, comp44_vcbase, comp44_vchold, comp0_e, comp0_gbar
  RANGE i_Nar
  RANGE ina
  USEION na READ ena WRITE ina
}


FUNCTION comp0_beta_s (v) {
  comp0_beta_s  =  
  comp0_Q10 * 
    (comp0_Shiftbeta_s + 
        comp0_Abeta_s * 
          (v + comp0_V0beta_s) / 
            (exp((v + comp0_V0beta_s) / comp0_Kbeta_s) + -1.0))
}


FUNCTION comp0_alpha_s (v) {
  comp0_alpha_s  =  
  (comp0_Q10 * 
        (comp0_Shiftalpha_s + comp0_Aalpha_s * (v + comp0_V0alpha_s))) 
    / 
    (exp((v + comp0_V0alpha_s) / comp0_Kalpha_s) + -1.0)
}


FUNCTION comp0_beta_f (v) {
  comp0_beta_f  =  
  comp0_Q10 * comp0_Abeta_f * 
    exp((v + -(comp0_V0beta_f)) / comp0_Kbeta_f)
}


FUNCTION comp0_alpha_f (v) {
  comp0_alpha_f  =  
  comp0_Q10 * comp0_Aalpha_f * 
    exp((v + -(comp0_V0alpha_f)) / comp0_Kalpha_f)
}


PARAMETER {
  comp0_Abeta_s  =  0.01558
  comp0_Abeta_f  =  0.01014
  comp0_Kalpha_s  =  -6.81881
  comp0_gbar  =  0.0005
  comp0_Kalpha_f  =  -62.52621
  comp44_vcbdur  =  100.0
  comp0_Q10  =  3.0
  comp0_Shiftalpha_s  =  8e-05
  comp0_V0beta_s  =  43.97494
  comp0_V0beta_f  =  -83.3332
  comp0_Kbeta_s  =  0.10818
  comp0_Kbeta_f  =  16.05379
  comp0_e  =  87.39
  comp44_vcsteps  =  9.0
  comp44_vchdur  =  30.0
  comp44_vcinc  =  10.0
  comp0_Aalpha_s  =  -0.00493
  comp0_Aalpha_f  =  0.31836
  Vrest  =  -68.0
  comp44_vchold  =  -71.0
  fix_celsius  =  30.0
  comp0_V0alpha_s  =  -4.48754
  comp44_vcbase  =  -60.0
  comp0_V0alpha_f  =  -80.0
  comp0_Shiftbeta_s  =  0.04752
}


STATE {
  Nar_hC
  Nar_hO
  Nar_mC
  Nar_mO
  Nar_h
  Nar_m
}


ASSIGNED {
  ica
  cai
  v
  ina
  ena
  i_Nar
}


PROCEDURE reactions () {
  Nar_h  =  Nar_hO
  Nar_m  =  Nar_mO
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  reactions ()
  i_Nar  =  (comp0_gbar * Nar_m * Nar_h) * (v - comp0_e)
  ina  =  i_Nar
}


DERIVATIVE states {
  LOCAL v47, v50
  v47  =  Nar_mO 
Nar_mO'  =  -(Nar_mO * comp0_beta_s(v)) + (1 - v47) * (comp0_alpha_s(v))
  v50  =  Nar_hO 
Nar_hO'  =  -(Nar_hO * comp0_beta_f(v)) + (1 - v50) * (comp0_alpha_f(v))
}


INITIAL {
  Nar_h  =  (comp0_alpha_f(v)) / (comp0_alpha_f(v) + comp0_beta_f(v))
  Nar_hO  =  Nar_h
  Nar_m  =  (comp0_alpha_s(v)) / (comp0_alpha_s(v) + comp0_beta_s(v))
  Nar_mO  =  Nar_m
}


PROCEDURE print_state () {
  printf ("Nar_hO = %g\n" ,  Nar_hO)
  printf ("Nar_mO = %g\n" ,  Nar_mO)
}
