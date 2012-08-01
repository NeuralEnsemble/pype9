

TITLE CGC


NEURON {
  RANGE pNa_m, Nar_h, Nar_m, Na_h, Na_m, KV_m, KM_m, Kir_m, KCa_m, KA_h
  RANGE KA_m, CaHVA_h, CaHVA_m, comp315_vcbdur, comp315_vchdur, comp315_vcsteps, comp315_vcinc, comp315_vcbase, comp315_vchold, comp293_e
  RANGE comp293_gbar, comp292_vcbdur, comp292_vchdur, comp292_vcsteps, comp292_vcinc, comp292_vcbase, comp292_vchold, comp248_e, comp248_gbar, comp247_vcbdur
  RANGE comp247_vchdur, comp247_vcsteps, comp247_vcinc, comp247_vcbase, comp247_vchold, comp204_e, comp204_gbar, comp201_egaba, comp201_ggaba, comp198_e
  RANGE comp198_gbar, comp197_vcbdur, comp197_vchdur, comp197_vcsteps, comp197_vcinc, comp197_vcbase, comp197_vchold, comp174_e, comp174_gbar, comp173_vcbdur
  RANGE comp173_vchdur, comp173_vcsteps, comp173_vcinc, comp173_vcbase, comp173_vchold, comp149_e, comp149_gbar, comp148_vcbdur, comp148_vchdur, comp148_vcsteps
  RANGE comp148_vcinc, comp148_vcbase, comp148_vchold, comp124_e, comp124_gbar, comp100_e, comp100_gbar, comp59_e, comp59_gbar, comp15_e_Kv4
  RANGE comp15_gbar, comp14_ca
  RANGE i_KV, i_pNa, i_KM, i_KA, i_Kir, i_Nar, i_KCa, i_CaHVA, i_Na, i_Lkg2, i_Lkg1
  RANGE e
  NONSPECIFIC_CURRENT i
  RANGE ina
  USEION na READ ena WRITE ina
  RANGE ica
  USEION ca READ eca,ica WRITE ica,cai
  RANGE ik
  USEION k READ ek WRITE ik
  RANGE ica, cai
}


FUNCTION comp149_alpha_n (v) {
  comp149_alpha_n  =  
  comp149_Q10 * comp149_Aalpha_n * 
    exp((v + -(comp149_V0alpha_n)) / comp149_Kalpha_n)
}


FUNCTION comp124_beta_d (v) {
  comp124_beta_d  =  
  comp124_Q10 * comp124_Abeta_d * 
    exp((v + -(comp124_V0beta_d)) / comp124_Kbeta_d)
}


FUNCTION linoid (x, y) {
  LOCAL v341
  if 
    (fabs(x / y) < 1e-06) 
     {v341  =  y * (1.0 + -(x / y / 2.0))} 
    else {v341  =  x / (exp(x / y) + -1.0)} 
linoid  =  v341
}


FUNCTION comp15_beta_u (v) {
  comp15_beta_u  =  
  comp15_Q10 * comp15_Abeta_u * 
    exp((v + -(comp15_V0beta_u)) / comp15_Kbeta_u)
}


FUNCTION comp15_beta_s (v) {
  comp15_beta_s  =  
  comp15_Q10 * comp15_Abeta_s * 
    exp((v + -(comp15_V0beta_s)) / comp15_Kbeta_s)
}


FUNCTION comp293_alpha_m (v) {
  comp293_alpha_m  =  
  comp293_Q10 * comp293_Aalpha_m * 
    linoid(v + -(comp293_V0alpha_m), comp293_Kalpha_m)
}


FUNCTION comp204_beta_m (v) {
  comp204_beta_m  =  
  comp204_Q10 * comp204_Abeta_m * 
    exp((v + -(comp204_V0beta_m)) / comp204_Kbeta_m)
}


FUNCTION comp204_beta_h (v) {
  comp204_beta_h  =  
  (comp204_Q10 * comp204_Abeta_h) / 
    (1.0 + exp((v + -(comp204_V0beta_h)) / comp204_Kbeta_h))
}


FUNCTION comp59_beta_b (v) {
  comp59_beta_b  =  
  comp59_Q10 * comp59_Abeta_b * 
    sigm(v + -(comp59_V0beta_b), comp59_Kbeta_b)
}


FUNCTION comp59_beta_a (v) {
  comp59_beta_a  =  
  comp59_Q10 * 
    comp59_Abeta_a / exp((v + -(comp59_V0beta_a)) / comp59_Kbeta_a)
}


FUNCTION comp100_beta_c (v, cai) {
  comp100_beta_c  =  
  (comp100_Q10 * comp100_Abeta_c) / 
    (1.0 + cai / (comp100_Bbeta_c * exp(v / comp100_Kbeta_c)))
}


FUNCTION comp248_beta_s (v) {
  comp248_beta_s  =  
  comp248_Q10 * 
    (comp248_Shiftbeta_s + 
        comp248_Abeta_s * 
          (v + comp248_V0beta_s) / 
            (exp((v + comp248_V0beta_s) / comp248_Kbeta_s) + -1.0))
}


FUNCTION comp174_beta_n (v) {
  comp174_beta_n  =  
  comp174_Q10 * comp174_Abeta_n * 
    exp((v + -(comp174_V0beta_n)) / comp174_Kbeta_n)
}


FUNCTION comp248_beta_f (v) {
  comp248_beta_f  =  
  comp248_Q10 * comp248_Abeta_f * 
    exp((v + -(comp248_V0beta_f)) / comp248_Kbeta_f)
}


FUNCTION comp293_beta_m (v) {
  comp293_beta_m  =  
  comp293_Q10 * comp293_Abeta_m * 
    linoid(v + -(comp293_V0beta_m), comp293_Kbeta_m)
}


FUNCTION comp174_alpha_n (v) {
  comp174_alpha_n  =  
  comp174_Q10 * comp174_Aalpha_n * 
    linoid(v + -(comp174_V0alpha_n), comp174_Kalpha_n)
}


FUNCTION comp124_alpha_d (v) {
  comp124_alpha_d  =  
  comp124_Q10 * comp124_Aalpha_d * 
    exp((v + -(comp124_V0alpha_d)) / comp124_Kalpha_d)
}


FUNCTION comp248_alpha_s (v) {
  comp248_alpha_s  =  
  (comp248_Q10 * 
        (comp248_Shiftalpha_s + 
            comp248_Aalpha_s * (v + comp248_V0alpha_s))) 
    / 
    (exp((v + comp248_V0alpha_s) / comp248_Kalpha_s) + -1.0)
}


FUNCTION comp149_beta_n (v) {
  comp149_beta_n  =  
  comp149_Q10 * comp149_Abeta_n * 
    exp((v + -(comp149_V0beta_n)) / comp149_Kbeta_n)
}


FUNCTION comp248_alpha_f (v) {
  comp248_alpha_f  =  
  comp248_Q10 * comp248_Aalpha_f * 
    exp((v + -(comp248_V0alpha_f)) / comp248_Kalpha_f)
}


FUNCTION comp204_alpha_m (v) {
  comp204_alpha_m  =  
  comp204_Q10 * comp204_Aalpha_m * 
    linoid(v + -(comp204_V0alpha_m), comp204_Kalpha_m)
}


FUNCTION comp204_alpha_h (v) {
  comp204_alpha_h  =  
  comp204_Q10 * comp204_Aalpha_h * 
    exp((v + -(comp204_V0alpha_h)) / comp204_Kalpha_h)
}


FUNCTION comp100_alpha_c (v, cai) {
  comp100_alpha_c  =  
  (comp100_Q10 * comp100_Aalpha_c) / 
    (1.0 + (comp100_Balpha_c * exp(v / comp100_Kalpha_c)) / cai)
}


FUNCTION comp15_alpha_u (v) {
  comp15_alpha_u  =  
  comp15_Q10 * comp15_Aalpha_u * 
    exp((v + -(comp15_V0alpha_u)) / comp15_Kalpha_u)
}


FUNCTION comp15_alpha_s (v) {
  comp15_alpha_s  =  
  comp15_Q10 * comp15_Aalpha_s * 
    exp((v + -(comp15_V0alpha_s)) / comp15_Kalpha_s)
}


FUNCTION comp59_alpha_b (v) {
  comp59_alpha_b  =  
  comp59_Q10 * comp59_Aalpha_b * 
    sigm(v + -(comp59_V0alpha_b), comp59_Kalpha_b)
}


FUNCTION comp59_alpha_a (v) {
  comp59_alpha_a  =  
  comp59_Q10 * comp59_Aalpha_a * 
    sigm(v + -(comp59_V0alpha_a), comp59_Kalpha_a)
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


PARAMETER {
  comp15_V0beta_s  =  18.66
  comp149_e  =  84.69
  comp248_gbar  =  0.0005
  comp124_Q10  =  3.0
  comp248_Kalpha_f  =  62.52621
  comp124_Abeta_d  =  0.16994
  comp204_Q10  =  3.0
  comp248_Abeta_s  =  0.01558
  comp173_vcbase  =  69.0
  comp14_F  =  96485.0
  comp247_vcbase  =  60.0
  comp293_Kbeta_m  =  5.0
  comp149_Aalpha_n  =  0.0033
  comp197_vcbdur  =  100.0
  comp248_Abeta_f  =  0.01014
  comp100_e  =  84.69
  comp292_vcbase  =  60.0
  comp149_Q10  =  2.40822468528069
  comp292_vcsteps  =  9.0
  comp204_Abeta_m  =  12.0
  comp204_Abeta_h  =  1.5
  comp248_e  =  87.39
  comp293_V0alpha_m  =  42.0
  comp15_gbar  =  0.56
  comp148_vchold  =  71.0
  comp197_vcsteps  =  8.0
  comp59_Kalpha_b  =  12.8433
  comp59_Kalpha_a  =  23.32708
  comp204_Aalpha_m  =  0.3
  comp204_Aalpha_h  =  0.105
  comp248_V0beta_s  =  43.97494
  comp100_Q10  =  1.0
  comp124_gbar  =  0.0009
  comp315_vcbdur  =  100.0
  comp100_Abeta_c  =  1.5
  comp124_Kalpha_d  =  24.3902
  comp248_V0beta_f  =  83.3332
  comp15_Aalpha_u  =  0.0013
  comp15_Aalpha_s  =  0.04944
  comp59_V0_ainf  =  46.7
  comp59_e  =  84.69
  comp59_Q10  =  3.0
  comp248_Shiftbeta_s  =  0.04752
  comp174_Kbeta_n  =  80.0
  comp293_V0_minf  =  42.0
  comp14_beta  =  1.5
  comp100_gbar  =  0.004
  comp15_Abeta_u  =  0.0013
  comp15_Abeta_s  =  0.08298
  comp148_vcbase  =  69.0
  comp59_Abeta_b  =  0.10353
  comp293_e  =  87.39
  comp59_Abeta_a  =  0.99285
  comp173_vcbdur  =  100.0
  comp173_vcsteps  =  8.0
  comp247_vcbdur  =  100.0
  comp59_V0beta_b  =  49.9537
  comp293_Kalpha_m  =  5.0
  comp59_V0beta_a  =  18.27914
  comp59_K_ainf  =  19.8
  comp292_vcbdur  =  100.0
  comp201_egaba  =  65.0
  comp14_cao  =  2.0
  comp248_V0alpha_s  =  4.48754
  comp174_e  =  84.69
  comp197_vchdur  =  30.0
  comp292_vcinc  =  10.0
  comp100_Kalpha_c  =  11.765
  comp124_Kbeta_d  =  35.714
  comp248_Kbeta_s  =  0.10818
  comp124_V0beta_d  =  83.94
  comp248_Aalpha_s  =  0.00493
  comp174_Kalpha_n  =  10.0
  comp248_V0alpha_f  =  80.0
  comp149_Abeta_n  =  0.0033
  comp124_e  =  84.69
  comp248_Shiftalpha_s  =  8e-05
  comp197_vcinc  =  10.0
  comp315_vcinc  =  10.0
  comp248_Kbeta_f  =  16.05379
  comp204_V0alpha_m  =  19.0
  comp248_Aalpha_f  =  0.31836
  comp149_gbar  =  0.00035
  comp204_Kbeta_m  =  18.182
  comp204_V0alpha_h  =  44.0
  comp247_vcsteps  =  9.0
  comp149_V0_ninf  =  30.0
  comp204_Kbeta_h  =  5.0
  comp59_gbar  =  0.004
  comp248_Q10  =  3.0
  comp293_V0beta_m  =  42.0
  comp315_vchdur  =  30.0
  comp149_B_ninf  =  6.0
  comp149_Kalpha_n  =  40.0
  comp197_vchold  =  71.0
  comp204_gbar  =  0.013
  comp174_V0alpha_n  =  25.0
  comp59_Aalpha_b  =  0.11042
  comp59_Aalpha_a  =  4.88826
  comp148_vcbdur  =  100.0
  comp293_Abeta_m  =  0.062
  comp59_V0_binf  =  78.8
  comp100_Kbeta_c  =  11.765
  comp174_V0beta_n  =  35.0
  comp173_vchdur  =  30.0
  comp204_Kalpha_m  =  10.0
  comp247_vchdur  =  30.0
  comp315_vcsteps  =  9.0
  comp124_Aalpha_d  =  0.13289
  comp124_V0alpha_d  =  83.94
  comp204_Kalpha_h  =  3.333
  comp15_Kbeta_u  =  83.33
  comp15_Kbeta_s  =  25.641
  comp292_vchdur  =  30.0
  fix_celsius  =  30.0
  comp59_Kbeta_b  =  8.90123
  comp59_Kbeta_a  =  19.47175
  comp100_Balpha_c  =  0.0015
  comp15_Q10  =  3.0
  comp315_vchold  =  71.0
  comp59_K_binf  =  8.4
  comp197_vcbase  =  69.0
  comp15_Kalpha_u  =  18.183
  comp15_Kalpha_s  =  15.87301587302
  comp173_vcinc  =  10.0
  comp149_V0beta_n  =  30.0
  comp174_Q10  =  13.5137964673603
  comp198_e  =  58.0
  comp293_Aalpha_m  =  0.091
  comp15_e_Kv4  =  129.33
  comp198_gbar  =  5.68e-05
  comp14_cai0  =  0.0001
  comp15_V0alpha_u  =  48.0
  comp173_vchold  =  71.0
  comp15_V0alpha_s  =  29.06
  comp59_V0alpha_b  =  111.33209
  comp247_vcinc  =  10.0
  comp59_V0alpha_a  =  9.17203
  comp247_vchold  =  71.0
  comp149_Kbeta_n  =  20.0
  comp149_V0alpha_n  =  30.0
  comp174_Abeta_n  =  0.125
  comp100_Aalpha_c  =  2.5
  comp292_vchold  =  71.0
  comp204_V0beta_m  =  44.0
  comp293_gbar  =  2e-05
  comp174_Aalpha_n  =  0.01
  comp148_vcsteps  =  8.0
  comp204_V0beta_h  =  11.0
  comp174_gbar  =  0.003
  comp201_ggaba  =  2.17e-05
  comp315_vcbase  =  60.0
  comp148_vcinc  =  10.0
  comp14_d  =  0.2
  comp204_e  =  87.39
  comp293_B_minf  =  5.0
  comp148_vchdur  =  30.0
  comp100_Bbeta_c  =  0.00015
  comp248_Kalpha_s  =  6.81881
  comp15_V0beta_u  =  48.0
  comp293_Q10  =  1.0
}


STATE {
  comp14_ca
  Nar_hC
  Nar_hO
  Nar_mC
  Nar_mO
  KV_mC
  KV_mO
  KCa_m
  KA_h
  KA_m
  Na_hC
  Na_hO
  Na_mC
  Na_mO
  KM_m
  Kir_mC
  Kir_mO
  pNa_m
  CaHVA_hC
  CaHVA_hO
  CaHVA_mC
  CaHVA_mO
  Nar_h
  Nar_m
  KV_m
  Na_h
  Na_m
  Kir_m
  CaHVA_h
  CaHVA_m
}


ASSIGNED {
  KM_m_inf
  KA_h_tau
  KA_m_inf
  comp59_b_inf
  KM_m_tau
  KA_m_tau
  comp59_tau_b
  comp59_tau_a
  pNa_m_inf
  KCa_m_inf
  pNa_m_tau
  KA_h_inf
  comp59_a_inf
  KCa_m_tau
  ica
  cai
  v
  i
  ina
  ik
  e
  ena
  eca
  ek
  i_KV
  i_pNa
  i_KM
  i_KA
  i_Kir
  i_Nar
  i_KCa
  i_CaHVA
  i_Na
  i_Lkg2
  i_Lkg1
}


PROCEDURE asgns () {
  KCa_m_tau  =  comp100_beta_c(v, cai)
  comp59_a_inf  =  
  1.0 / (1.0 + exp((v + -(comp59_V0_ainf)) / comp59_K_ainf))
  pNa_m_tau  =  5.0 / (comp293_alpha_m(v) + comp293_beta_m(v))
  KCa_m_inf  =  comp100_alpha_c(v, cai)
  pNa_m_inf  =  
  1.0 / (1.0 + exp(-(v + -(comp293_V0_minf)) / comp293_B_minf))
  comp59_tau_a  =  1.0 / (comp59_alpha_a(v) + comp59_beta_a(v))
  comp59_tau_b  =  1.0 / (comp59_alpha_b(v) + comp59_beta_b(v))
  KM_m_tau  =  1.0 / (comp149_alpha_n(v) + comp149_beta_n(v))
  comp59_b_inf  =  
  1.0 / (1.0 + exp((v + -(comp59_V0_binf)) / comp59_K_binf))
  KM_m_inf  =  
  1.0 / (1.0 + exp(-(v + -(comp149_V0_ninf)) / comp149_B_ninf))
  KA_h_inf  =  comp59_b_inf
  KA_m_tau  =  comp59_tau_a
  KA_m_inf  =  comp59_a_inf
  KA_h_tau  =  comp59_tau_b
}


PROCEDURE reactions () {
  Nar_h  =  Nar_hO
  Nar_m  =  Nar_mO
  KV_m  =  KV_mO
  Na_h  =  Na_hO
  Na_m  =  Na_mO
  Kir_m  =  Kir_mO
  CaHVA_h  =  CaHVA_hO
  CaHVA_m  =  CaHVA_mO
}


PROCEDURE pools () {
  cai = comp14_ca
}


BREAKPOINT {
  LOCAL v349, v347, v345, v343
  SOLVE states METHOD derivimplicit
  reactions ()
  pools ()
  i_Lkg2  =  comp201_ggaba * (v - comp201_egaba)
  i_Lkg1  =  comp198_gbar * (v - comp198_e)
  i  =  i_Lkg2 + i_Lkg1
  v349  =  KV_m 
i_KV  =  (comp174_gbar * v349 * v349 * v349 * v349) * (v - comp174_e)
  i_KM  =  (comp149_gbar * KM_m) * (v - comp149_e)
  v347  =  KA_m 
i_KA  =  (comp59_gbar * v347 * v347 * v347 * KA_h) * (v - comp59_e)
  i_Kir  =  (comp124_gbar * Kir_m) * (v - comp124_e)
  i_KCa  =  (comp100_gbar * KCa_m) * (v - comp100_e)
  ik  =  i_KV + i_KM + i_KA + i_Kir + i_KCa
  i_pNa  =  (comp293_gbar * pNa_m) * (v - comp293_e)
  i_Nar  =  (comp248_gbar * Nar_m * Nar_h) * (v - comp248_e)
  v345  =  Na_m 
i_Na  =  (comp204_gbar * v345 * v345 * v345 * Na_h) * (v - comp204_e)
  ina  =  i_pNa + i_Nar + i_Na
  v343  =  CaHVA_m 
i_CaHVA  =  (comp15_gbar * v343 * v343 * CaHVA_h) * (v - comp15_e_Kv4)
  ica  =  i_CaHVA
}


DERIVATIVE states {
  LOCAL v318, v321, v324, v327, v330, v333, v336, v339
  asgns ()
  KA_m'  =  (KA_m_inf + -(KA_m)) / KA_m_tau
  KA_h'  =  (KA_h_inf + -(KA_h)) / KA_h_tau
  pNa_m'  =  (pNa_m_inf + -(pNa_m)) / pNa_m_tau
  KM_m'  =  (KM_m_inf + -(KM_m)) / KM_m_tau
  KCa_m'  =  (KCa_m_inf + -(KCa_m)) / KCa_m_tau
  v318  =  CaHVA_mO 
CaHVA_mO'  =  
    -(CaHVA_mO * comp15_beta_s(v)) + (1 - v318) * (comp15_alpha_s(v))
  v321  =  CaHVA_hO 
CaHVA_hO'  =  
    -(CaHVA_hO * comp15_beta_u(v)) + (1 - v321) * (comp15_alpha_u(v))
  v324  =  Kir_mO 
Kir_mO'  =  
    -(Kir_mO * comp124_beta_d(v)) + (1 - v324) * (comp124_alpha_d(v))
  v327  =  Na_mO 
Na_mO'  =  
    -(Na_mO * comp204_beta_m(v)) + (1 - v327) * (comp204_alpha_m(v))
  v330  =  Na_hO 
Na_hO'  =  
    -(Na_hO * comp204_beta_h(v)) + (1 - v330) * (comp204_alpha_h(v))
  v333  =  KV_mO 
KV_mO'  =  
    -(KV_mO * comp174_beta_n(v)) + (1 - v333) * (comp174_alpha_n(v))
  v336  =  Nar_mO 
Nar_mO'  =  
    -(Nar_mO * comp248_beta_s(v)) + (1 - v336) * (comp248_alpha_s(v))
  v339  =  Nar_hO 
Nar_hO'  =  
    -(Nar_hO * comp248_beta_f(v)) + (1 - v339) * (comp248_alpha_f(v))
  comp14_ca'  =  
  (-(ica)) / (2.0 * comp14_F * comp14_d) + 
    -(comp14_beta * (cai + -(comp14_cai0)))
}


INITIAL {
  asgns ()
  comp14_ca  =  0.0001
  Nar_h  =  
  (comp248_alpha_f(v)) / (comp248_alpha_f(v) + comp248_beta_f(v))
  Nar_hO  =  Nar_h
  Nar_m  =  
  (comp248_alpha_s(v)) / (comp248_alpha_s(v) + comp248_beta_s(v))
  Nar_mO  =  Nar_m
  KV_m  =  (comp174_alpha_n(v)) / (comp174_alpha_n(v) + comp174_beta_n(v))
  KV_mO  =  KV_m
  Na_h  =  (comp204_alpha_h(v)) / (comp204_alpha_h(v) + comp204_beta_h(v))
  Na_hO  =  Na_h
  Na_m  =  (comp204_alpha_m(v)) / (comp204_alpha_m(v) + comp204_beta_m(v))
  Na_mO  =  Na_m
  Kir_m  =  
  (comp124_alpha_d(v)) / (comp124_alpha_d(v) + comp124_beta_d(v))
  Kir_mO  =  Kir_m
  CaHVA_h  =  (comp15_alpha_u(v)) / (comp15_alpha_u(v) + comp15_beta_u(v))
  CaHVA_hO  =  CaHVA_h
  CaHVA_m  =  (comp15_alpha_s(v)) / (comp15_alpha_s(v) + comp15_beta_s(v))
  CaHVA_mO  =  CaHVA_m
  KCa_m  =  
  (comp100_alpha_c(v, cai)) / 
    (comp100_alpha_c(v, cai) + comp100_beta_c(v, cai))
  KM_m  =  (comp149_alpha_n(v)) / (comp149_alpha_n(v) + comp149_beta_n(v))
  pNa_m  =  
  (comp293_alpha_m(v)) / (comp293_alpha_m(v) + comp293_beta_m(v))
  KA_h  =  (comp59_alpha_b(v)) / (comp59_alpha_b(v) + comp59_beta_b(v))
  KA_m  =  (comp59_alpha_a(v)) / (comp59_alpha_a(v) + comp59_beta_a(v))
}


PROCEDURE print_state () {
  printf ("CaHVA_hO = %g\n" ,  CaHVA_hO)
  printf ("CaHVA_mO = %g\n" ,  CaHVA_mO)
  printf ("KA_h = %g\n" ,  KA_h)
  printf ("KA_m = %g\n" ,  KA_m)
  printf ("KCa_m = %g\n" ,  KCa_m)
  printf ("KM_m = %g\n" ,  KM_m)
  printf ("KV_mO = %g\n" ,  KV_mO)
  printf ("Kir_mO = %g\n" ,  Kir_mO)
  printf ("Na_hO = %g\n" ,  Na_hO)
  printf ("Na_mO = %g\n" ,  Na_mO)
  printf ("Nar_hO = %g\n" ,  Nar_hO)
  printf ("Nar_mO = %g\n" ,  Nar_mO)
  printf ("comp14_ca = %g\n" ,  comp14_ca)
  printf ("pNa_m = %g\n" ,  pNa_m)
}
