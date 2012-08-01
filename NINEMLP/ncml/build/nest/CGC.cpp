#include "CGC.h"
#include "exceptions.h"
#include "network.h"
#include "dict.h"
#include "integerdatum.h"
#include "doubledatum.h"
#include "dictutils.h"
#include "numerics.h"
#include <limits>

#include "universal_data_logger_impl.h"

#include <iomanip>
#include <iostream>
#include <cstdio>
#include <cmath>

#include <gsl/gsl_errno.h>
#include <gsl/gsl_matrix.h>
#include <gsl/gsl_sf_exp.h>

namespace nest {




double comp2657_alpha_m (double v, void* pnode) {
  double rv3396 ;
  rv3396  =  comp2657_Q10 * comp2657_Aalpha_m * linoid(v + -(comp2657_V0alpha_m), comp2657_Kalpha_m);
  return rv3396;
}




double comp2270_beta_f (double v, void* pnode) {
  double rv3397 ;
  rv3397  =  comp2270_Q10 * comp2270_Abeta_f * exp((v + -(comp2270_V0beta_f)) / comp2270_Kbeta_f);
  return rv3397;
}




double comp2270_beta_s (double v, void* pnode) {
  double rv3398 ;
  rv3398  =  comp2270_Q10 * (comp2270_Shiftbeta_s + comp2270_Abeta_s * (v + comp2270_V0beta_s) / (exp((v + comp2270_V0beta_s) / comp2270_Kbeta_s) + -1.0));
  return rv3398;
}




double comp1911_beta_h (double v, void* pnode) {
  double rv3399 ;
  rv3399  =  (comp1911_Q10 * comp1911_Abeta_h) / (1.0 + exp((v + -(comp1911_V0beta_h)) / comp1911_Kbeta_h));
  return rv3399;
}




double comp1911_beta_m (double v, void* pnode) {
  double rv3400 ;
  rv3400  =  comp1911_Q10 * comp1911_Abeta_m * exp((v + -(comp1911_V0beta_m)) / comp1911_Kbeta_m);
  return rv3400;
}




double linoid (double x, double y, void* pnode) {
  double rv3401 ;
  double v3403 ;
  if (abs(x / y) < 1e-06) 
      {v3403  =  y * (1.0 + -(x / y / 2.0));} 
      else 
        {v3403  =  x / (exp(x / y) + -1.0);}; 
rv3401  =  v3403;
  return rv3401;
}




double comp1911_alpha_m (double v, void* pnode) {
  double rv3404 ;
  rv3404  =  comp1911_Q10 * comp1911_Aalpha_m * linoid(v + -(comp1911_V0alpha_m), comp1911_Kalpha_m);
  return rv3404;
}




double comp1911_alpha_h (double v, void* pnode) {
  double rv3405 ;
  rv3405  =  comp1911_Q10 * comp1911_Aalpha_h * exp((v + -(comp1911_V0alpha_h)) / comp1911_Kalpha_h);
  return rv3405;
}




double comp509_beta_b (double v, void* pnode) {
  double rv3406 ;
  rv3406  =  comp509_Q10 * comp509_Abeta_b * sigm(v + -(comp509_V0beta_b), comp509_Kbeta_b);
  return rv3406;
}




double comp509_beta_a (double v, void* pnode) {
  double rv3407 ;
  rv3407  =  comp509_Q10 * comp509_Abeta_a / exp((v + -(comp509_V0beta_a)) / comp509_Kbeta_a);
  return rv3407;
}




double sigm (double x, double y, void* pnode) {
  double rv3408 ;
  rv3408  =  1.0 / (exp(x / y) + 1.0);
  return rv3408;
}




double comp2270_alpha_f (double v, void* pnode) {
  double rv3409 ;
  rv3409  =  comp2270_Q10 * comp2270_Aalpha_f * exp((v + -(comp2270_V0alpha_f)) / comp2270_Kalpha_f);
  return rv3409;
}




double comp150_beta_s (double v, void* pnode) {
  double rv3410 ;
  rv3410  =  comp150_Q10 * comp150_Abeta_s * exp((v + -(comp150_V0beta_s)) / comp150_Kbeta_s);
  return rv3410;
}




double comp150_beta_u (double v, void* pnode) {
  double rv3411 ;
  rv3411  =  comp150_Q10 * comp150_Abeta_u * exp((v + -(comp150_V0beta_u)) / comp150_Kbeta_u);
  return rv3411;
}




double comp2270_alpha_s (double v, void* pnode) {
  double rv3412 ;
  rv3412  =  (comp2270_Q10 * (comp2270_Shiftalpha_s + comp2270_Aalpha_s * (v + comp2270_V0alpha_s))) / (exp((v + comp2270_V0alpha_s) / comp2270_Kalpha_s) + -1.0);
  return rv3412;
}




double comp924_alpha_c (double v, double cai, void* pnode) {
  double rv3413 ;
  rv3413  =  (comp924_Q10 * comp924_Aalpha_c) / (1.0 + (comp924_Balpha_c * exp(v / comp924_Kalpha_c)) / cai);
  return rv3413;
}




double comp150_alpha_u (double v, void* pnode) {
  double rv3414 ;
  rv3414  =  comp150_Q10 * comp150_Aalpha_u * exp((v + -(comp150_V0alpha_u)) / comp150_Kalpha_u);
  return rv3414;
}




double comp150_alpha_s (double v, void* pnode) {
  double rv3415 ;
  rv3415  =  comp150_Q10 * comp150_Aalpha_s * exp((v + -(comp150_V0alpha_s)) / comp150_Kalpha_s);
  return rv3415;
}




double comp509_alpha_b (double v, void* pnode) {
  double rv3416 ;
  rv3416  =  comp509_Q10 * comp509_Aalpha_b * sigm(v + -(comp509_V0alpha_b), comp509_Kalpha_b);
  return rv3416;
}




double comp509_alpha_a (double v, void* pnode) {
  double rv3417 ;
  rv3417  =  comp509_Q10 * comp509_Aalpha_a * sigm(v + -(comp509_V0alpha_a), comp509_Kalpha_a);
  return rv3417;
}




double comp1331_beta_n (double v, void* pnode) {
  double rv3418 ;
  rv3418  =  comp1331_Q10 * comp1331_Abeta_n * exp((v + -(comp1331_V0beta_n)) / comp1331_Kbeta_n);
  return rv3418;
}




double comp1086_beta_d (double v, void* pnode) {
  double rv3419 ;
  rv3419  =  comp1086_Q10 * comp1086_Abeta_d * exp((v + -(comp1086_V0beta_d)) / comp1086_Kbeta_d);
  return rv3419;
}




double comp1086_alpha_d (double v, void* pnode) {
  double rv3420 ;
  rv3420  =  comp1086_Q10 * comp1086_Aalpha_d * exp((v + -(comp1086_V0alpha_d)) / comp1086_Kalpha_d);
  return rv3420;
}




double comp1604_alpha_n (double v, void* pnode) {
  double rv3421 ;
  rv3421  =  comp1604_Q10 * comp1604_Aalpha_n * linoid(v + -(comp1604_V0alpha_n), comp1604_Kalpha_n);
  return rv3421;
}




double comp1604_beta_n (double v, void* pnode) {
  double rv3422 ;
  rv3422  =  comp1604_Q10 * comp1604_Abeta_n * exp((v + -(comp1604_V0beta_n)) / comp1604_Kbeta_n);
  return rv3422;
}




double comp924_beta_c (double v, double cai, void* pnode) {
  double rv3423 ;
  rv3423  =  (comp924_Q10 * comp924_Abeta_c) / (1.0 + cai / (comp924_Bbeta_c * exp(v / comp924_Kbeta_c)));
  return rv3423;
}




double comp2657_beta_m (double v, void* pnode) {
  double rv3424 ;
  rv3424  =  comp2657_Q10 * comp2657_Abeta_m * linoid(v + -(comp2657_V0beta_m), comp2657_Kbeta_m);
  return rv3424;
}




double comp1331_alpha_n (double v, void* pnode) {
  double rv3425 ;
  rv3425  =  comp1331_Q10 * comp1331_Aalpha_n * exp((v + -(comp1331_V0alpha_n)) / comp1331_Kalpha_n);
  return rv3425;
}




extern "C" int CGC_dynamics (double t, const double y[], double f[], void* pnode) {
  double v3434, v3435, v3436, v3437, v3426, v3427, v3428, v3429, v3430, v3431, v3432, v3433, comp2657_B_minf, comp2657_V0_minf, v, pNa_m_inf, comp1331_B_ninf, comp1331_V0_ninf, KM_m_inf, comp65_ca, cai, KCa_m_inf, KCa_m_tau, comp509_K_binf, comp509_V0_binf, comp509_b_inf, pNa_m_tau, comp509_K_ainf, comp509_V0_ainf, comp509_a_inf, KM_m_tau, comp509_tau_a, comp509_tau_b, KA_h_inf, KA_m_tau, KA_h_tau, KA_m_inf, Kir_mO, Kir_m, Na_mO, Na_m, Na_hO, Na_h, CaHVA_hO, CaHVA_h, CaHVA_mO, CaHVA_m, Nar_mO, Nar_m, Nar_hO, Nar_h, KV_mO, KV_m, KM_m, pNa_m, KCa_m, KA_m, KA_h, i_Na, i_Nar, i_pNa, ina, i_KM, i_KV, i_KA, i_KCa, i_Kir, ik, i_Lkg1, i_Lkg2, i, i_CaHVA, ica, comp2270_Aalpha_f, comp509_V0beta_b, comp509_V0beta_a, comp2657_Kbeta_m, comp1764_vcbase, comp1604_V0alpha_n, comp2845_vchold, comp2845_vcinc, comp1331_Kalpha_n, comp924_Bbeta_c, comp1246_vcbdur, comp150_Abeta_s, comp150_Q10, comp150_Abeta_u, comp2270_V0alpha_s, comp2270_V0alpha_f, comp1911_V0alpha_h, comp2845_vcsteps, comp839_vcinc, comp839_vchold, fix_celsius, comp1246_vcsteps, comp924_Q10, comp1331_Q10, comp924_e, comp1086_Q10, comp1086_gbar, comp150_V0alpha_u, comp150_V0alpha_s, comp1604_Abeta_n, comp1911_Kbeta_h, comp1519_vchold, comp839_vchdur, comp2572_vcbase, comp2572_vcinc, comp924_Abeta_c, comp2657_Kalpha_m, comp1519_vcsteps, comp1911_Kbeta_m, comp1764_vcbdur, comp150_gbar, comp1086_Kbeta_d, comp2270_Q10, comp424_vcbdur, comp1764_vcsteps, comp509_Aalpha_b, comp509_Aalpha_a, comp1086_Aalpha_d, comp1880_ggaba, comp2572_vcsteps, comp1911_Kalpha_m, comp1911_Kalpha_h, comp2657_V0beta_m, comp509_e, comp1086_V0beta_d, comp2270_Shiftbeta_s, comp1331_V0alpha_n, comp2270_Aalpha_s, comp1604_Aalpha_n, comp2270_gbar, comp150_V0beta_u, comp150_V0beta_s, comp65_cai0, comp2657_Q10, comp924_Balpha_c, comp1331_Aalpha_n, comp1519_vchdur, comp1604_V0beta_n, comp1604_Kalpha_n, comp2185_vchdur, comp2657_Abeta_m, comp1604_gbar, comp509_Abeta_a, comp509_Abeta_b, comp924_Kbeta_c, comp1086_Kalpha_d, comp1086_V0alpha_d, comp150_e, comp1331_e, comp1519_vcbase, comp150_Kalpha_s, comp150_Kalpha_u, comp1331_V0beta_n, comp1911_e, comp424_vcbase, comp2185_vcinc, comp424_vcsteps, comp509_V0alpha_a, comp509_V0alpha_b, comp2270_Kbeta_s, comp1764_vchold, comp1331_gbar, comp2270_Kbeta_f, comp1764_vcinc, comp424_vcinc, comp1246_vchdur, comp924_Aalpha_c, comp924_Kalpha_c, comp65_cao, comp2572_vcbdur, comp1911_gbar, comp65_beta, comp509_Kalpha_a, comp2185_vcbase, comp2845_vchdur, comp509_Kalpha_b, comp2572_vchold, comp2657_V0alpha_m, comp839_vcsteps, comp1519_vcbdur, comp1880_egaba, comp2270_Shiftalpha_s, comp2270_Abeta_f, comp1849_gbar, comp2185_vchold, comp2572_vchdur, comp2845_vcbdur, comp1911_Q10, comp2657_gbar, comp150_Aalpha_u, comp150_Aalpha_s, comp2657_e, comp150_Kbeta_u, comp1331_Kbeta_n, comp2185_vcsteps, comp509_Kbeta_b, comp509_Kbeta_a, comp1246_vcinc, comp424_vchold, comp2270_Kalpha_f, comp509_gbar, comp509_Q10, comp2270_Kalpha_s, comp839_vcbdur, comp1911_Abeta_h, comp1911_Abeta_m, comp150_Kbeta_s, comp1604_e, comp1086_Abeta_d, comp1246_vcbase, comp2270_V0beta_s, comp1086_e, comp2270_e, comp1911_V0beta_h, comp2270_V0beta_f, comp1911_V0beta_m, comp424_vchdur, comp1331_Abeta_n, comp924_gbar, comp1246_vchold, comp1604_Q10, comp839_vcbase, comp1911_Aalpha_h, comp1911_V0alpha_m, comp1849_e, comp1911_Aalpha_m, comp65_F, comp1519_vcinc, comp2270_Abeta_s, comp2845_vcbase, comp1604_Kbeta_n, comp1764_vchdur, comp2657_Aalpha_m, comp2185_vcbdur, comp65_d ;
  

  // S is shorthand for the type that describes the model state 
  typedef CGC::State_ S;
  

  // cast the node ptr to an object of the proper type
  assert(pnode);
  const  CGC & node =  *(reinterpret_cast< CGC *>(pnode));
  

  // y[] must be the state vector supplied by the integrator, 
  // not the state vector in the node, node.S_.y[]. 
  

  comp2270_Aalpha_f  =  node.P_.comp2270_Aalpha_f;
  comp509_V0beta_b  =  node.P_.comp509_V0beta_b;
  comp509_V0beta_a  =  node.P_.comp509_V0beta_a;
  comp2657_Kbeta_m  =  node.P_.comp2657_Kbeta_m;
  comp1764_vcbase  =  node.P_.comp1764_vcbase;
  comp1604_V0alpha_n  =  node.P_.comp1604_V0alpha_n;
  comp2845_vchold  =  node.P_.comp2845_vchold;
  comp2845_vcinc  =  node.P_.comp2845_vcinc;
  comp1331_Kalpha_n  =  node.P_.comp1331_Kalpha_n;
  comp924_Bbeta_c  =  node.P_.comp924_Bbeta_c;
  comp1246_vcbdur  =  node.P_.comp1246_vcbdur;
  comp150_Abeta_s  =  node.P_.comp150_Abeta_s;
  comp150_Q10  =  node.P_.comp150_Q10;
  comp150_Abeta_u  =  node.P_.comp150_Abeta_u;
  comp2270_V0alpha_s  =  node.P_.comp2270_V0alpha_s;
  comp2270_V0alpha_f  =  node.P_.comp2270_V0alpha_f;
  comp1911_V0alpha_h  =  node.P_.comp1911_V0alpha_h;
  comp509_K_binf  =  node.P_.comp509_K_binf;
  comp2845_vcsteps  =  node.P_.comp2845_vcsteps;
  comp839_vcinc  =  node.P_.comp839_vcinc;
  comp839_vchold  =  node.P_.comp839_vchold;
  fix_celsius  =  node.P_.fix_celsius;
  comp1246_vcsteps  =  node.P_.comp1246_vcsteps;
  comp924_Q10  =  node.P_.comp924_Q10;
  comp1331_Q10  =  node.P_.comp1331_Q10;
  comp924_e  =  node.P_.comp924_e;
  comp1086_Q10  =  node.P_.comp1086_Q10;
  comp1086_gbar  =  node.P_.comp1086_gbar;
  comp150_V0alpha_u  =  node.P_.comp150_V0alpha_u;
  comp150_V0alpha_s  =  node.P_.comp150_V0alpha_s;
  comp1604_Abeta_n  =  node.P_.comp1604_Abeta_n;
  comp1911_Kbeta_h  =  node.P_.comp1911_Kbeta_h;
  comp1519_vchold  =  node.P_.comp1519_vchold;
  comp839_vchdur  =  node.P_.comp839_vchdur;
  comp2572_vcbase  =  node.P_.comp2572_vcbase;
  comp2572_vcinc  =  node.P_.comp2572_vcinc;
  comp924_Abeta_c  =  node.P_.comp924_Abeta_c;
  comp2657_Kalpha_m  =  node.P_.comp2657_Kalpha_m;
  comp1519_vcsteps  =  node.P_.comp1519_vcsteps;
  comp1911_Kbeta_m  =  node.P_.comp1911_Kbeta_m;
  comp1764_vcbdur  =  node.P_.comp1764_vcbdur;
  comp150_gbar  =  node.P_.comp150_gbar;
  comp1086_Kbeta_d  =  node.P_.comp1086_Kbeta_d;
  comp509_K_ainf  =  node.P_.comp509_K_ainf;
  comp2270_Q10  =  node.P_.comp2270_Q10;
  comp424_vcbdur  =  node.P_.comp424_vcbdur;
  comp1764_vcsteps  =  node.P_.comp1764_vcsteps;
  comp509_Aalpha_b  =  node.P_.comp509_Aalpha_b;
  comp509_Aalpha_a  =  node.P_.comp509_Aalpha_a;
  comp1086_Aalpha_d  =  node.P_.comp1086_Aalpha_d;
  comp1880_ggaba  =  node.P_.comp1880_ggaba;
  comp2572_vcsteps  =  node.P_.comp2572_vcsteps;
  comp1911_Kalpha_m  =  node.P_.comp1911_Kalpha_m;
  comp1911_Kalpha_h  =  node.P_.comp1911_Kalpha_h;
  comp2657_V0beta_m  =  node.P_.comp2657_V0beta_m;
  comp509_e  =  node.P_.comp509_e;
  comp1086_V0beta_d  =  node.P_.comp1086_V0beta_d;
  comp2270_Shiftbeta_s  =  node.P_.comp2270_Shiftbeta_s;
  comp1331_V0alpha_n  =  node.P_.comp1331_V0alpha_n;
  comp2270_Aalpha_s  =  node.P_.comp2270_Aalpha_s;
  comp1604_Aalpha_n  =  node.P_.comp1604_Aalpha_n;
  comp2270_gbar  =  node.P_.comp2270_gbar;
  comp150_V0beta_u  =  node.P_.comp150_V0beta_u;
  comp150_V0beta_s  =  node.P_.comp150_V0beta_s;
  comp65_cai0  =  node.P_.comp65_cai0;
  comp2657_Q10  =  node.P_.comp2657_Q10;
  comp924_Balpha_c  =  node.P_.comp924_Balpha_c;
  comp1331_Aalpha_n  =  node.P_.comp1331_Aalpha_n;
  comp1519_vchdur  =  node.P_.comp1519_vchdur;
  comp1604_V0beta_n  =  node.P_.comp1604_V0beta_n;
  comp1604_Kalpha_n  =  node.P_.comp1604_Kalpha_n;
  comp2185_vchdur  =  node.P_.comp2185_vchdur;
  comp2657_Abeta_m  =  node.P_.comp2657_Abeta_m;
  comp2657_B_minf  =  node.P_.comp2657_B_minf;
  comp1604_gbar  =  node.P_.comp1604_gbar;
  comp509_Abeta_a  =  node.P_.comp509_Abeta_a;
  comp509_Abeta_b  =  node.P_.comp509_Abeta_b;
  comp924_Kbeta_c  =  node.P_.comp924_Kbeta_c;
  comp1086_Kalpha_d  =  node.P_.comp1086_Kalpha_d;
  comp1331_V0_ninf  =  node.P_.comp1331_V0_ninf;
  comp1086_V0alpha_d  =  node.P_.comp1086_V0alpha_d;
  comp150_e  =  node.P_.comp150_e;
  comp1331_e  =  node.P_.comp1331_e;
  comp1519_vcbase  =  node.P_.comp1519_vcbase;
  comp150_Kalpha_s  =  node.P_.comp150_Kalpha_s;
  comp150_Kalpha_u  =  node.P_.comp150_Kalpha_u;
  comp1331_V0beta_n  =  node.P_.comp1331_V0beta_n;
  comp1911_e  =  node.P_.comp1911_e;
  comp424_vcbase  =  node.P_.comp424_vcbase;
  comp2185_vcinc  =  node.P_.comp2185_vcinc;
  comp424_vcsteps  =  node.P_.comp424_vcsteps;
  comp509_V0alpha_a  =  node.P_.comp509_V0alpha_a;
  comp509_V0alpha_b  =  node.P_.comp509_V0alpha_b;
  comp2270_Kbeta_s  =  node.P_.comp2270_Kbeta_s;
  comp1764_vchold  =  node.P_.comp1764_vchold;
  comp1331_gbar  =  node.P_.comp1331_gbar;
  comp2270_Kbeta_f  =  node.P_.comp2270_Kbeta_f;
  comp1764_vcinc  =  node.P_.comp1764_vcinc;
  comp424_vcinc  =  node.P_.comp424_vcinc;
  comp1246_vchdur  =  node.P_.comp1246_vchdur;
  comp924_Aalpha_c  =  node.P_.comp924_Aalpha_c;
  comp924_Kalpha_c  =  node.P_.comp924_Kalpha_c;
  comp65_cao  =  node.P_.comp65_cao;
  comp2572_vcbdur  =  node.P_.comp2572_vcbdur;
  comp509_V0_binf  =  node.P_.comp509_V0_binf;
  comp1911_gbar  =  node.P_.comp1911_gbar;
  comp65_beta  =  node.P_.comp65_beta;
  comp509_Kalpha_a  =  node.P_.comp509_Kalpha_a;
  comp2185_vcbase  =  node.P_.comp2185_vcbase;
  comp2845_vchdur  =  node.P_.comp2845_vchdur;
  comp509_Kalpha_b  =  node.P_.comp509_Kalpha_b;
  comp2572_vchold  =  node.P_.comp2572_vchold;
  comp2657_V0alpha_m  =  node.P_.comp2657_V0alpha_m;
  comp839_vcsteps  =  node.P_.comp839_vcsteps;
  comp1519_vcbdur  =  node.P_.comp1519_vcbdur;
  comp1880_egaba  =  node.P_.comp1880_egaba;
  comp2270_Shiftalpha_s  =  node.P_.comp2270_Shiftalpha_s;
  comp2270_Abeta_f  =  node.P_.comp2270_Abeta_f;
  comp1849_gbar  =  node.P_.comp1849_gbar;
  comp2185_vchold  =  node.P_.comp2185_vchold;
  comp2657_V0_minf  =  node.P_.comp2657_V0_minf;
  comp2572_vchdur  =  node.P_.comp2572_vchdur;
  comp2845_vcbdur  =  node.P_.comp2845_vcbdur;
  comp1911_Q10  =  node.P_.comp1911_Q10;
  comp2657_gbar  =  node.P_.comp2657_gbar;
  comp150_Aalpha_u  =  node.P_.comp150_Aalpha_u;
  comp150_Aalpha_s  =  node.P_.comp150_Aalpha_s;
  comp2657_e  =  node.P_.comp2657_e;
  comp150_Kbeta_u  =  node.P_.comp150_Kbeta_u;
  comp1331_Kbeta_n  =  node.P_.comp1331_Kbeta_n;
  comp2185_vcsteps  =  node.P_.comp2185_vcsteps;
  comp509_Kbeta_b  =  node.P_.comp509_Kbeta_b;
  comp509_Kbeta_a  =  node.P_.comp509_Kbeta_a;
  comp1246_vcinc  =  node.P_.comp1246_vcinc;
  comp424_vchold  =  node.P_.comp424_vchold;
  comp509_V0_ainf  =  node.P_.comp509_V0_ainf;
  comp2270_Kalpha_f  =  node.P_.comp2270_Kalpha_f;
  comp509_gbar  =  node.P_.comp509_gbar;
  comp509_Q10  =  node.P_.comp509_Q10;
  comp2270_Kalpha_s  =  node.P_.comp2270_Kalpha_s;
  comp839_vcbdur  =  node.P_.comp839_vcbdur;
  comp1911_Abeta_h  =  node.P_.comp1911_Abeta_h;
  comp1911_Abeta_m  =  node.P_.comp1911_Abeta_m;
  comp150_Kbeta_s  =  node.P_.comp150_Kbeta_s;
  comp1604_e  =  node.P_.comp1604_e;
  comp1086_Abeta_d  =  node.P_.comp1086_Abeta_d;
  comp1246_vcbase  =  node.P_.comp1246_vcbase;
  comp1331_B_ninf  =  node.P_.comp1331_B_ninf;
  comp2270_V0beta_s  =  node.P_.comp2270_V0beta_s;
  comp1086_e  =  node.P_.comp1086_e;
  comp2270_e  =  node.P_.comp2270_e;
  comp1911_V0beta_h  =  node.P_.comp1911_V0beta_h;
  comp2270_V0beta_f  =  node.P_.comp2270_V0beta_f;
  comp1911_V0beta_m  =  node.P_.comp1911_V0beta_m;
  comp424_vchdur  =  node.P_.comp424_vchdur;
  comp1331_Abeta_n  =  node.P_.comp1331_Abeta_n;
  comp924_gbar  =  node.P_.comp924_gbar;
  comp1246_vchold  =  node.P_.comp1246_vchold;
  comp1604_Q10  =  node.P_.comp1604_Q10;
  comp839_vcbase  =  node.P_.comp839_vcbase;
  comp1911_Aalpha_h  =  node.P_.comp1911_Aalpha_h;
  comp1911_V0alpha_m  =  node.P_.comp1911_V0alpha_m;
  comp1849_e  =  node.P_.comp1849_e;
  comp1911_Aalpha_m  =  node.P_.comp1911_Aalpha_m;
  comp65_F  =  node.P_.comp65_F;
  comp1519_vcinc  =  node.P_.comp1519_vcinc;
  comp2270_Abeta_s  =  node.P_.comp2270_Abeta_s;
  comp2845_vcbase  =  node.P_.comp2845_vcbase;
  comp1604_Kbeta_n  =  node.P_.comp1604_Kbeta_n;
  comp1764_vchdur  =  node.P_.comp1764_vchdur;
  comp2657_Aalpha_m  =  node.P_.comp2657_Aalpha_m;
  comp2185_vcbdur  =  node.P_.comp2185_vcbdur;
  comp65_d  =  node.P_.comp65_d;
  v  =  y[0];
  KA_h  =  y[1];
  KA_m  =  y[2];
  KCa_m  =  y[3];
  pNa_m  =  y[4];
  KM_m  =  y[5];
  KV_mO  =  y[6];
  Nar_hO  =  y[7];
  Nar_mO  =  y[8];
  CaHVA_mO  =  y[9];
  CaHVA_hO  =  y[10];
  Na_hO  =  y[11];
  Na_mO  =  y[12];
  Kir_mO  =  y[13];
  comp65_ca  =  y[14];
  pNa_m_inf  =  1.0 / (1.0 + exp(-(v + -(comp2657_V0_minf)) / comp2657_B_minf));
  KM_m_inf  =  1.0 / (1.0 + exp(-(v + -(comp1331_V0_ninf)) / comp1331_B_ninf));
  cai  =  comp65_ca;
  KCa_m_inf  =  comp924_alpha_c(v, cai);
  KCa_m_tau  =  comp924_beta_c(v, cai);
  comp509_b_inf  =  1.0 / (1.0 + exp((v + -(comp509_V0_binf)) / comp509_K_binf));
  pNa_m_tau  =  5.0 / (comp2657_alpha_m(v) + comp2657_beta_m(v));
  comp509_a_inf  =  1.0 / (1.0 + exp((v + -(comp509_V0_ainf)) / comp509_K_ainf));
  KM_m_tau  =  1.0 / (comp1331_alpha_n(v) + comp1331_beta_n(v));
  comp509_tau_a  =  1.0 / (comp509_alpha_a(v) + comp509_beta_a(v));
  comp509_tau_b  =  1.0 / (comp509_alpha_b(v) + comp509_beta_b(v));
  KA_h_inf  =  comp509_b_inf;
  KA_m_tau  =  comp509_tau_a;
  KA_h_tau  =  comp509_tau_b;
  KA_m_inf  =  comp509_a_inf;
  Kir_m  =  Kir_mO;
  Na_m  =  Na_mO;
  Na_h  =  Na_hO;
  CaHVA_h  =  CaHVA_hO;
  CaHVA_m  =  CaHVA_mO;
  Nar_m  =  Nar_mO;
  Nar_h  =  Nar_hO;
  KV_m  =  KV_mO;
  // rate equation KA_h
  f[1]  =  (KA_h_inf + -(KA_h)) / KA_h_tau;
  // rate equation KA_m
  f[2]  =  (KA_m_inf + -(KA_m)) / KA_m_tau;
  // rate equation KCa_m
  f[3]  =  (KCa_m_inf + -(KCa_m)) / KCa_m_tau;
  // rate equation pNa_m
  f[4]  =  (pNa_m_inf + -(pNa_m)) / pNa_m_tau;
  // rate equation KM_m
  f[5]  =  (KM_m_inf + -(KM_m)) / KM_m_tau;
  // rate equation KV_mO
  v3426  =  KV_mO;; 
f[6]  =  -(KV_mO * comp1604_beta_n(v)) + (1 - v3426) * (comp1604_alpha_n(v));
  // rate equation Nar_hO
  v3427  =  Nar_hO;; 
f[7]  =  -(Nar_hO * comp2270_beta_f(v)) + (1 - v3427) * (comp2270_alpha_f(v));
  // rate equation Nar_mO
  v3428  =  Nar_mO;; 
f[8]  =  -(Nar_mO * comp2270_beta_s(v)) + (1 - v3428) * (comp2270_alpha_s(v));
  // rate equation CaHVA_mO
  v3429  =  CaHVA_mO;; 
f[9]  =  -(CaHVA_mO * comp150_beta_s(v)) + (1 - v3429) * (comp150_alpha_s(v));
  // rate equation CaHVA_hO
  v3430  =  CaHVA_hO;; 
f[10]  =  -(CaHVA_hO * comp150_beta_u(v)) + (1 - v3430) * (comp150_alpha_u(v));
  // rate equation Na_hO
  v3431  =  Na_hO;; 
f[11]  =  -(Na_hO * comp1911_beta_h(v)) + (1 - v3431) * (comp1911_alpha_h(v));
  // rate equation Na_mO
  v3432  =  Na_mO;; 
f[12]  =  -(Na_mO * comp1911_beta_m(v)) + (1 - v3432) * (comp1911_alpha_m(v));
  // rate equation Kir_mO
  v3433  =  Kir_mO;; 
f[13]  =  -(Kir_mO * comp1086_beta_d(v)) + (1 - v3433) * (comp1086_alpha_d(v));
  // rate equation comp65_ca
  f[14]  =  (-(ica)) / (2.0 * comp65_F * comp65_d) + -(comp65_beta * (cai + -(comp65_cai0)));
  v3434  =  Na_m;; 
i_Na  =  (comp1911_gbar * v3434 * v3434 * v3434 * Na_h) * (v - comp1911_e);
  i_Nar  =  (comp2270_gbar * Nar_m * Nar_h) * (v - comp2270_e);
  i_pNa  =  (comp2657_gbar * pNa_m) * (v - comp2657_e);
  ina  =  i_Na + i_Nar + i_pNa;
  i_KM  =  (comp1331_gbar * KM_m) * (v - comp1331_e);
  v3435  =  KV_m;; 
i_KV  =  (comp1604_gbar * v3435 * v3435 * v3435 * v3435) * (v - comp1604_e);
  v3436  =  KA_m;; 
i_KA  =  (comp509_gbar * v3436 * v3436 * v3436 * KA_h) * (v - comp509_e);
  i_KCa  =  (comp924_gbar * KCa_m) * (v - comp924_e);
  i_Kir  =  (comp1086_gbar * Kir_m) * (v - comp1086_e);
  ik  =  i_KM + i_KV + i_KA + i_KCa + i_Kir;
  i_Lkg1  =  comp1849_gbar * (v - comp1849_e);
  i_Lkg2  =  comp1880_ggaba * (v - comp1880_egaba);
  i  =  i_Lkg1 + i_Lkg2;
  v3437  =  CaHVA_m;; 
i_CaHVA  =  (comp150_gbar * v3437 * v3437 * CaHVA_h) * (v - comp150_e);
  ica  =  i_CaHVA;
  f[0]  =  0.0;
  

  return GSL_SUCCESS;
}


RecordablesMap<CGC> CGC::recordablesMap_;
template <> void RecordablesMap<CGC>::create()
{
  insert_("comp65_ca", &CGC::get_y_elem_<CGC::State_::COMP65_CA>);
  insert_("Kir_mO", &CGC::get_y_elem_<CGC::State_::KIR_MO>);
  insert_("Na_mO", &CGC::get_y_elem_<CGC::State_::NA_MO>);
  insert_("Na_hO", &CGC::get_y_elem_<CGC::State_::NA_HO>);
  insert_("CaHVA_hO", &CGC::get_y_elem_<CGC::State_::CAHVA_HO>);
  insert_("CaHVA_mO", &CGC::get_y_elem_<CGC::State_::CAHVA_MO>);
  insert_("Nar_mO", &CGC::get_y_elem_<CGC::State_::NAR_MO>);
  insert_("Nar_hO", &CGC::get_y_elem_<CGC::State_::NAR_HO>);
  insert_("KV_mO", &CGC::get_y_elem_<CGC::State_::KV_MO>);
  insert_("KM_m", &CGC::get_y_elem_<CGC::State_::KM_M>);
  insert_("pNa_m", &CGC::get_y_elem_<CGC::State_::PNA_M>);
  insert_("KCa_m", &CGC::get_y_elem_<CGC::State_::KCA_M>);
  insert_("KA_m", &CGC::get_y_elem_<CGC::State_::KA_M>);
  insert_("KA_h", &CGC::get_y_elem_<CGC::State_::KA_H>);
  insert_("v", &CGC::get_y_elem_<CGC::State_::V>);
  insert_(names::V_m, &CGC::get_y_elem_<CGC::State_::V>);
}




CGC::Parameters_::Parameters_ () :
  comp2270_Aalpha_f  (0.31836),
comp509_V0beta_b  (-49.9537),
comp509_V0beta_a  (-18.27914),
comp2657_Kbeta_m  (5.0),
comp1764_vcbase  (-69.0),
comp1604_V0alpha_n  (-25.0),
comp2845_vchold  (-71.0),
comp2845_vcinc  (10.0),
comp1331_Kalpha_n  (40.0),
comp924_Bbeta_c  (0.00015),
comp1246_vcbdur  (100.0),
comp150_Abeta_s  (0.08298),
comp150_Q10  (3.0),
comp150_Abeta_u  (0.0013),
comp2270_V0alpha_s  (-4.48754),
comp2270_V0alpha_f  (-80.0),
comp1911_V0alpha_h  (-44.0),
comp509_K_binf  (8.4),
comp2845_vcsteps  (9.0),
comp839_vcinc  (10.0),
comp839_vchold  (-71.0),
fix_celsius  (30.0),
comp1246_vcsteps  (8.0),
comp924_Q10  (1.0),
comp1331_Q10  (2.40822468528069),
comp924_e  (-84.69),
comp1086_Q10  (3.0),
comp1086_gbar  (0.0009),
comp150_V0alpha_u  (-48.0),
comp150_V0alpha_s  (-29.06),
comp1604_Abeta_n  (0.125),
comp1911_Kbeta_h  (-5.0),
comp1519_vchold  (-71.0),
comp839_vchdur  (30.0),
comp2572_vcbase  (-60.0),
comp2572_vcinc  (10.0),
comp924_Abeta_c  (1.5),
comp2657_Kalpha_m  (-5.0),
comp1519_vcsteps  (8.0),
comp1911_Kbeta_m  (-18.182),
comp1764_vcbdur  (100.0),
comp150_gbar  (0.00046),
comp1086_Kbeta_d  (35.714),
comp509_K_ainf  (-19.8),
comp2270_Q10  (3.0),
comp424_vcbdur  (100.0),
comp1764_vcsteps  (8.0),
comp509_Aalpha_b  (0.11042),
comp509_Aalpha_a  (4.88826),
comp1086_Aalpha_d  (0.13289),
comp1880_ggaba  (2.17e-05),
comp2572_vcsteps  (9.0),
comp1911_Kalpha_m  (-10.0),
comp1911_Kalpha_h  (-3.333),
comp2657_V0beta_m  (-42.0),
comp509_e  (-84.69),
comp1086_V0beta_d  (-83.94),
comp2270_Shiftbeta_s  (0.04752),
comp1331_V0alpha_n  (-30.0),
comp2270_Aalpha_s  (-0.00493),
comp1604_Aalpha_n  (-0.01),
comp2270_gbar  (0.0005),
comp150_V0beta_u  (-48.0),
comp150_V0beta_s  (-18.66),
comp65_cai0  (0.0001),
comp2657_Q10  (1.0),
comp924_Balpha_c  (0.0015),
comp1331_Aalpha_n  (0.0033),
comp1519_vchdur  (30.0),
comp1604_V0beta_n  (-35.0),
comp1604_Kalpha_n  (-10.0),
comp2185_vchdur  (30.0),
comp2657_Abeta_m  (0.062),
comp2657_B_minf  (5.0),
comp1604_gbar  (0.003),
comp509_Abeta_a  (0.99285),
comp509_Abeta_b  (0.10353),
comp924_Kbeta_c  (-11.765),
comp1086_Kalpha_d  (-24.3902),
comp1331_V0_ninf  (-30.0),
comp1086_V0alpha_d  (-83.94),
comp150_e  (129.33),
comp1331_e  (-84.69),
comp1519_vcbase  (-69.0),
comp150_Kalpha_s  (15.87301587302),
comp150_Kalpha_u  (-18.183),
comp1331_V0beta_n  (-30.0),
comp1911_e  (87.39),
comp424_vcbase  (-69.0),
comp2185_vcinc  (10.0),
comp424_vcsteps  (8.0),
comp509_V0alpha_a  (-9.17203),
comp509_V0alpha_b  (-111.33209),
comp2270_Kbeta_s  (0.10818),
comp1764_vchold  (-71.0),
comp1331_gbar  (0.00035),
comp2270_Kbeta_f  (16.05379),
comp1764_vcinc  (10.0),
comp424_vcinc  (10.0),
comp1246_vchdur  (30.0),
comp924_Aalpha_c  (2.5),
comp924_Kalpha_c  (-11.765),
comp65_cao  (2.0),
comp2572_vcbdur  (100.0),
comp509_V0_binf  (-78.8),
comp1911_gbar  (0.013),
comp65_beta  (1.5),
comp509_Kalpha_a  (-23.32708),
comp2185_vcbase  (-60.0),
comp2845_vchdur  (30.0),
comp509_Kalpha_b  (12.8433),
comp2572_vchold  (-71.0),
comp2657_V0alpha_m  (-42.0),
comp839_vcsteps  (8.0),
comp1519_vcbdur  (100.0),
comp1880_egaba  (-65.0),
comp2270_Shiftalpha_s  (8e-05),
comp2270_Abeta_f  (0.01014),
comp1849_gbar  (5.68e-05),
comp2185_vchold  (-71.0),
comp2657_V0_minf  (-42.0),
comp2572_vchdur  (30.0),
comp2845_vcbdur  (100.0),
comp1911_Q10  (3.0),
comp2657_gbar  (2e-05),
comp150_Aalpha_u  (0.0013),
comp150_Aalpha_s  (0.04944),
comp2657_e  (87.39),
comp150_Kbeta_u  (83.33),
comp1331_Kbeta_n  (-20.0),
comp2185_vcsteps  (9.0),
comp509_Kbeta_b  (-8.90123),
comp509_Kbeta_a  (19.47175),
comp1246_vcinc  (10.0),
comp424_vchold  (-71.0),
comp509_V0_ainf  (-46.7),
comp2270_Kalpha_f  (-62.52621),
comp509_gbar  (0.004),
comp509_Q10  (3.0),
comp2270_Kalpha_s  (-6.81881),
comp839_vcbdur  (100.0),
comp1911_Abeta_h  (1.5),
comp1911_Abeta_m  (12.0),
comp150_Kbeta_s  (-25.641),
comp1604_e  (-84.69),
comp1086_Abeta_d  (0.16994),
comp1246_vcbase  (-69.0),
comp1331_B_ninf  (6.0),
comp2270_V0beta_s  (43.97494),
comp1086_e  (-84.69),
comp2270_e  (87.39),
comp1911_V0beta_h  (-11.0),
comp2270_V0beta_f  (-83.3332),
comp1911_V0beta_m  (-44.0),
comp424_vchdur  (30.0),
comp1331_Abeta_n  (0.0033),
comp924_gbar  (0.004),
comp1246_vchold  (-71.0),
comp1604_Q10  (13.5137964673603),
comp839_vcbase  (-69.0),
comp1911_Aalpha_h  (0.105),
comp1911_V0alpha_m  (-19.0),
comp1849_e  (-58.0),
comp1911_Aalpha_m  (-0.3),
comp65_F  (96485.0),
comp1519_vcinc  (10.0),
comp2270_Abeta_s  (0.01558),
comp2845_vcbase  (-60.0),
comp1604_Kbeta_n  (-80.0),
comp1764_vchdur  (30.0),
comp2657_Aalpha_m  (-0.091),
comp2185_vcbdur  (100.0),
comp65_d  (0.2)
{}


CGC::State_::State_ (const Parameters_& p) : r_(0)
{
  double v3438, v3439, v3440, v3441, comp2657_B_minf, comp2657_V0_minf, v, pNa_m_inf, comp1331_B_ninf, comp1331_V0_ninf, KM_m_inf, comp65_ca, cai, KCa_m_inf, KCa_m_tau, comp509_K_binf, comp509_V0_binf, comp509_b_inf, pNa_m_tau, comp509_K_ainf, comp509_V0_ainf, comp509_a_inf, KM_m_tau, comp509_tau_a, comp509_tau_b, KA_h_inf, KA_m_tau, KA_h_tau, KA_m_inf, KV_m, KV_mO, Nar_h, Nar_hO, Nar_m, Nar_mO, CaHVA_m, CaHVA_mO, CaHVA_h, CaHVA_hO, Na_h, Na_hO, Na_m, Na_mO, Kir_m, Kir_mO, KCa_m, pNa_m, KM_m, KA_h, KA_m, i_Na, i_Nar, i_pNa, ina, i_KM, i_KV, i_KA, i_KCa, i_Kir, ik, i_Lkg1, i_Lkg2, i, i_CaHVA, ica, comp2270_Aalpha_f, comp509_V0beta_b, comp509_V0beta_a, comp2657_Kbeta_m, comp1764_vcbase, comp1604_V0alpha_n, comp2845_vchold, comp2845_vcinc, comp1331_Kalpha_n, comp924_Bbeta_c, comp1246_vcbdur, comp150_Abeta_s, comp150_Q10, comp150_Abeta_u, comp2270_V0alpha_s, comp2270_V0alpha_f, comp1911_V0alpha_h, comp2845_vcsteps, comp839_vcinc, comp839_vchold, fix_celsius, comp1246_vcsteps, comp924_Q10, comp1331_Q10, comp924_e, comp1086_Q10, comp1086_gbar, comp150_V0alpha_u, comp150_V0alpha_s, comp1604_Abeta_n, comp1911_Kbeta_h, comp1519_vchold, comp839_vchdur, comp2572_vcbase, comp2572_vcinc, comp924_Abeta_c, comp2657_Kalpha_m, comp1519_vcsteps, comp1911_Kbeta_m, comp1764_vcbdur, comp150_gbar, comp1086_Kbeta_d, comp2270_Q10, comp424_vcbdur, comp1764_vcsteps, comp509_Aalpha_b, comp509_Aalpha_a, comp1086_Aalpha_d, comp1880_ggaba, comp2572_vcsteps, comp1911_Kalpha_m, comp1911_Kalpha_h, comp2657_V0beta_m, comp509_e, comp1086_V0beta_d, comp2270_Shiftbeta_s, comp1331_V0alpha_n, comp2270_Aalpha_s, comp1604_Aalpha_n, comp2270_gbar, comp150_V0beta_u, comp150_V0beta_s, comp65_cai0, comp2657_Q10, comp924_Balpha_c, comp1331_Aalpha_n, comp1519_vchdur, comp1604_V0beta_n, comp1604_Kalpha_n, comp2185_vchdur, comp2657_Abeta_m, comp1604_gbar, comp509_Abeta_a, comp509_Abeta_b, comp924_Kbeta_c, comp1086_Kalpha_d, comp1086_V0alpha_d, comp150_e, comp1331_e, comp1519_vcbase, comp150_Kalpha_s, comp150_Kalpha_u, comp1331_V0beta_n, comp1911_e, comp424_vcbase, comp2185_vcinc, comp424_vcsteps, comp509_V0alpha_a, comp509_V0alpha_b, comp2270_Kbeta_s, comp1764_vchold, comp1331_gbar, comp2270_Kbeta_f, comp1764_vcinc, comp424_vcinc, comp1246_vchdur, comp924_Aalpha_c, comp924_Kalpha_c, comp65_cao, comp2572_vcbdur, comp1911_gbar, comp65_beta, comp509_Kalpha_a, comp2185_vcbase, comp2845_vchdur, comp509_Kalpha_b, comp2572_vchold, comp2657_V0alpha_m, comp839_vcsteps, comp1519_vcbdur, comp1880_egaba, comp2270_Shiftalpha_s, comp2270_Abeta_f, comp1849_gbar, comp2185_vchold, comp2572_vchdur, comp2845_vcbdur, comp1911_Q10, comp2657_gbar, comp150_Aalpha_u, comp150_Aalpha_s, comp2657_e, comp150_Kbeta_u, comp1331_Kbeta_n, comp2185_vcsteps, comp509_Kbeta_b, comp509_Kbeta_a, comp1246_vcinc, comp424_vchold, comp2270_Kalpha_f, comp509_gbar, comp509_Q10, comp2270_Kalpha_s, comp839_vcbdur, comp1911_Abeta_h, comp1911_Abeta_m, comp150_Kbeta_s, comp1604_e, comp1086_Abeta_d, comp1246_vcbase, comp2270_V0beta_s, comp1086_e, comp2270_e, comp1911_V0beta_h, comp2270_V0beta_f, comp1911_V0beta_m, comp424_vchdur, comp1331_Abeta_n, comp924_gbar, comp1246_vchold, comp1604_Q10, comp839_vcbase, comp1911_Aalpha_h, comp1911_V0alpha_m, comp1849_e, comp1911_Aalpha_m, comp65_F, comp1519_vcinc, comp2270_Abeta_s, comp2845_vcbase, comp1604_Kbeta_n, comp1764_vchdur, comp2657_Aalpha_m, comp2185_vcbdur, comp65_d ;
  comp2270_Aalpha_f  =  p.comp2270_Aalpha_f;
  comp509_V0beta_b  =  p.comp509_V0beta_b;
  comp509_V0beta_a  =  p.comp509_V0beta_a;
  comp2657_Kbeta_m  =  p.comp2657_Kbeta_m;
  comp1764_vcbase  =  p.comp1764_vcbase;
  comp1604_V0alpha_n  =  p.comp1604_V0alpha_n;
  comp2845_vchold  =  p.comp2845_vchold;
  comp2845_vcinc  =  p.comp2845_vcinc;
  comp1331_Kalpha_n  =  p.comp1331_Kalpha_n;
  comp924_Bbeta_c  =  p.comp924_Bbeta_c;
  comp1246_vcbdur  =  p.comp1246_vcbdur;
  comp150_Abeta_s  =  p.comp150_Abeta_s;
  comp150_Q10  =  p.comp150_Q10;
  comp150_Abeta_u  =  p.comp150_Abeta_u;
  comp2270_V0alpha_s  =  p.comp2270_V0alpha_s;
  comp2270_V0alpha_f  =  p.comp2270_V0alpha_f;
  comp1911_V0alpha_h  =  p.comp1911_V0alpha_h;
  comp509_K_binf  =  p.comp509_K_binf;
  comp2845_vcsteps  =  p.comp2845_vcsteps;
  comp839_vcinc  =  p.comp839_vcinc;
  comp839_vchold  =  p.comp839_vchold;
  fix_celsius  =  p.fix_celsius;
  comp1246_vcsteps  =  p.comp1246_vcsteps;
  comp924_Q10  =  p.comp924_Q10;
  comp1331_Q10  =  p.comp1331_Q10;
  comp924_e  =  p.comp924_e;
  comp1086_Q10  =  p.comp1086_Q10;
  comp1086_gbar  =  p.comp1086_gbar;
  comp150_V0alpha_u  =  p.comp150_V0alpha_u;
  comp150_V0alpha_s  =  p.comp150_V0alpha_s;
  comp1604_Abeta_n  =  p.comp1604_Abeta_n;
  comp1911_Kbeta_h  =  p.comp1911_Kbeta_h;
  comp1519_vchold  =  p.comp1519_vchold;
  comp839_vchdur  =  p.comp839_vchdur;
  comp2572_vcbase  =  p.comp2572_vcbase;
  comp2572_vcinc  =  p.comp2572_vcinc;
  comp924_Abeta_c  =  p.comp924_Abeta_c;
  comp2657_Kalpha_m  =  p.comp2657_Kalpha_m;
  comp1519_vcsteps  =  p.comp1519_vcsteps;
  comp1911_Kbeta_m  =  p.comp1911_Kbeta_m;
  comp1764_vcbdur  =  p.comp1764_vcbdur;
  comp150_gbar  =  p.comp150_gbar;
  comp1086_Kbeta_d  =  p.comp1086_Kbeta_d;
  comp509_K_ainf  =  p.comp509_K_ainf;
  comp2270_Q10  =  p.comp2270_Q10;
  comp424_vcbdur  =  p.comp424_vcbdur;
  comp1764_vcsteps  =  p.comp1764_vcsteps;
  comp509_Aalpha_b  =  p.comp509_Aalpha_b;
  comp509_Aalpha_a  =  p.comp509_Aalpha_a;
  comp1086_Aalpha_d  =  p.comp1086_Aalpha_d;
  comp1880_ggaba  =  p.comp1880_ggaba;
  comp2572_vcsteps  =  p.comp2572_vcsteps;
  comp1911_Kalpha_m  =  p.comp1911_Kalpha_m;
  comp1911_Kalpha_h  =  p.comp1911_Kalpha_h;
  comp2657_V0beta_m  =  p.comp2657_V0beta_m;
  comp509_e  =  p.comp509_e;
  comp1086_V0beta_d  =  p.comp1086_V0beta_d;
  comp2270_Shiftbeta_s  =  p.comp2270_Shiftbeta_s;
  comp1331_V0alpha_n  =  p.comp1331_V0alpha_n;
  comp2270_Aalpha_s  =  p.comp2270_Aalpha_s;
  comp1604_Aalpha_n  =  p.comp1604_Aalpha_n;
  comp2270_gbar  =  p.comp2270_gbar;
  comp150_V0beta_u  =  p.comp150_V0beta_u;
  comp150_V0beta_s  =  p.comp150_V0beta_s;
  comp65_cai0  =  p.comp65_cai0;
  comp2657_Q10  =  p.comp2657_Q10;
  comp924_Balpha_c  =  p.comp924_Balpha_c;
  comp1331_Aalpha_n  =  p.comp1331_Aalpha_n;
  comp1519_vchdur  =  p.comp1519_vchdur;
  comp1604_V0beta_n  =  p.comp1604_V0beta_n;
  comp1604_Kalpha_n  =  p.comp1604_Kalpha_n;
  comp2185_vchdur  =  p.comp2185_vchdur;
  comp2657_Abeta_m  =  p.comp2657_Abeta_m;
  comp2657_B_minf  =  p.comp2657_B_minf;
  comp1604_gbar  =  p.comp1604_gbar;
  comp509_Abeta_a  =  p.comp509_Abeta_a;
  comp509_Abeta_b  =  p.comp509_Abeta_b;
  comp924_Kbeta_c  =  p.comp924_Kbeta_c;
  comp1086_Kalpha_d  =  p.comp1086_Kalpha_d;
  comp1331_V0_ninf  =  p.comp1331_V0_ninf;
  comp1086_V0alpha_d  =  p.comp1086_V0alpha_d;
  comp150_e  =  p.comp150_e;
  comp1331_e  =  p.comp1331_e;
  comp1519_vcbase  =  p.comp1519_vcbase;
  comp150_Kalpha_s  =  p.comp150_Kalpha_s;
  comp150_Kalpha_u  =  p.comp150_Kalpha_u;
  comp1331_V0beta_n  =  p.comp1331_V0beta_n;
  comp1911_e  =  p.comp1911_e;
  comp424_vcbase  =  p.comp424_vcbase;
  comp2185_vcinc  =  p.comp2185_vcinc;
  comp424_vcsteps  =  p.comp424_vcsteps;
  comp509_V0alpha_a  =  p.comp509_V0alpha_a;
  comp509_V0alpha_b  =  p.comp509_V0alpha_b;
  comp2270_Kbeta_s  =  p.comp2270_Kbeta_s;
  comp1764_vchold  =  p.comp1764_vchold;
  comp1331_gbar  =  p.comp1331_gbar;
  comp2270_Kbeta_f  =  p.comp2270_Kbeta_f;
  comp1764_vcinc  =  p.comp1764_vcinc;
  comp424_vcinc  =  p.comp424_vcinc;
  comp1246_vchdur  =  p.comp1246_vchdur;
  comp924_Aalpha_c  =  p.comp924_Aalpha_c;
  comp924_Kalpha_c  =  p.comp924_Kalpha_c;
  comp65_cao  =  p.comp65_cao;
  comp2572_vcbdur  =  p.comp2572_vcbdur;
  comp509_V0_binf  =  p.comp509_V0_binf;
  comp1911_gbar  =  p.comp1911_gbar;
  comp65_beta  =  p.comp65_beta;
  comp509_Kalpha_a  =  p.comp509_Kalpha_a;
  comp2185_vcbase  =  p.comp2185_vcbase;
  comp2845_vchdur  =  p.comp2845_vchdur;
  comp509_Kalpha_b  =  p.comp509_Kalpha_b;
  comp2572_vchold  =  p.comp2572_vchold;
  comp2657_V0alpha_m  =  p.comp2657_V0alpha_m;
  comp839_vcsteps  =  p.comp839_vcsteps;
  comp1519_vcbdur  =  p.comp1519_vcbdur;
  comp1880_egaba  =  p.comp1880_egaba;
  comp2270_Shiftalpha_s  =  p.comp2270_Shiftalpha_s;
  comp2270_Abeta_f  =  p.comp2270_Abeta_f;
  comp1849_gbar  =  p.comp1849_gbar;
  comp2185_vchold  =  p.comp2185_vchold;
  comp2657_V0_minf  =  p.comp2657_V0_minf;
  comp2572_vchdur  =  p.comp2572_vchdur;
  comp2845_vcbdur  =  p.comp2845_vcbdur;
  comp1911_Q10  =  p.comp1911_Q10;
  comp2657_gbar  =  p.comp2657_gbar;
  comp150_Aalpha_u  =  p.comp150_Aalpha_u;
  comp150_Aalpha_s  =  p.comp150_Aalpha_s;
  comp2657_e  =  p.comp2657_e;
  comp150_Kbeta_u  =  p.comp150_Kbeta_u;
  comp1331_Kbeta_n  =  p.comp1331_Kbeta_n;
  comp2185_vcsteps  =  p.comp2185_vcsteps;
  comp509_Kbeta_b  =  p.comp509_Kbeta_b;
  comp509_Kbeta_a  =  p.comp509_Kbeta_a;
  comp1246_vcinc  =  p.comp1246_vcinc;
  comp424_vchold  =  p.comp424_vchold;
  comp509_V0_ainf  =  p.comp509_V0_ainf;
  comp2270_Kalpha_f  =  p.comp2270_Kalpha_f;
  comp509_gbar  =  p.comp509_gbar;
  comp509_Q10  =  p.comp509_Q10;
  comp2270_Kalpha_s  =  p.comp2270_Kalpha_s;
  comp839_vcbdur  =  p.comp839_vcbdur;
  comp1911_Abeta_h  =  p.comp1911_Abeta_h;
  comp1911_Abeta_m  =  p.comp1911_Abeta_m;
  comp150_Kbeta_s  =  p.comp150_Kbeta_s;
  comp1604_e  =  p.comp1604_e;
  comp1086_Abeta_d  =  p.comp1086_Abeta_d;
  comp1246_vcbase  =  p.comp1246_vcbase;
  comp1331_B_ninf  =  p.comp1331_B_ninf;
  comp2270_V0beta_s  =  p.comp2270_V0beta_s;
  comp1086_e  =  p.comp1086_e;
  comp2270_e  =  p.comp2270_e;
  comp1911_V0beta_h  =  p.comp1911_V0beta_h;
  comp2270_V0beta_f  =  p.comp2270_V0beta_f;
  comp1911_V0beta_m  =  p.comp1911_V0beta_m;
  comp424_vchdur  =  p.comp424_vchdur;
  comp1331_Abeta_n  =  p.comp1331_Abeta_n;
  comp924_gbar  =  p.comp924_gbar;
  comp1246_vchold  =  p.comp1246_vchold;
  comp1604_Q10  =  p.comp1604_Q10;
  comp839_vcbase  =  p.comp839_vcbase;
  comp1911_Aalpha_h  =  p.comp1911_Aalpha_h;
  comp1911_V0alpha_m  =  p.comp1911_V0alpha_m;
  comp1849_e  =  p.comp1849_e;
  comp1911_Aalpha_m  =  p.comp1911_Aalpha_m;
  comp65_F  =  p.comp65_F;
  comp1519_vcinc  =  p.comp1519_vcinc;
  comp2270_Abeta_s  =  p.comp2270_Abeta_s;
  comp2845_vcbase  =  p.comp2845_vcbase;
  comp1604_Kbeta_n  =  p.comp1604_Kbeta_n;
  comp1764_vchdur  =  p.comp1764_vchdur;
  comp2657_Aalpha_m  =  p.comp2657_Aalpha_m;
  comp2185_vcbdur  =  p.comp2185_vcbdur;
  comp65_d  =  p.comp65_d;
  v  =  -65.0;
  pNa_m_inf  =  1.0 / (1.0 + exp(-(v + -(comp2657_V0_minf)) / comp2657_B_minf));
  KM_m_inf  =  1.0 / (1.0 + exp(-(v + -(comp1331_V0_ninf)) / comp1331_B_ninf));
  comp65_ca  =  0.0001;
  cai  =  comp65_ca;
  KCa_m_inf  =  comp924_alpha_c(v, cai);
  KCa_m_tau  =  comp924_beta_c(v, cai);
  comp509_b_inf  =  1.0 / (1.0 + exp((v + -(comp509_V0_binf)) / comp509_K_binf));
  pNa_m_tau  =  5.0 / (comp2657_alpha_m(v) + comp2657_beta_m(v));
  comp509_a_inf  =  1.0 / (1.0 + exp((v + -(comp509_V0_ainf)) / comp509_K_ainf));
  KM_m_tau  =  1.0 / (comp1331_alpha_n(v) + comp1331_beta_n(v));
  comp509_tau_a  =  1.0 / (comp509_alpha_a(v) + comp509_beta_a(v));
  comp509_tau_b  =  1.0 / (comp509_alpha_b(v) + comp509_beta_b(v));
  KA_h_inf  =  comp509_b_inf;
  KA_m_tau  =  comp509_tau_a;
  KA_h_tau  =  comp509_tau_b;
  KA_m_inf  =  comp509_a_inf;
  KV_m  =  (comp1604_alpha_n(v)) / (comp1604_alpha_n(v) + comp1604_beta_n(v));
  KV_mO  =  KV_m;
  Nar_h  =  (comp2270_alpha_f(v)) / (comp2270_alpha_f(v) + comp2270_beta_f(v));
  Nar_hO  =  Nar_h;
  Nar_m  =  (comp2270_alpha_s(v)) / (comp2270_alpha_s(v) + comp2270_beta_s(v));
  Nar_mO  =  Nar_m;
  CaHVA_m  =  (comp150_alpha_s(v)) / (comp150_alpha_s(v) + comp150_beta_s(v));
  CaHVA_mO  =  CaHVA_m;
  CaHVA_h  =  (comp150_alpha_u(v)) / (comp150_alpha_u(v) + comp150_beta_u(v));
  CaHVA_hO  =  CaHVA_h;
  Na_h  =  (comp1911_alpha_h(v)) / (comp1911_alpha_h(v) + comp1911_beta_h(v));
  Na_hO  =  Na_h;
  Na_m  =  (comp1911_alpha_m(v)) / (comp1911_alpha_m(v) + comp1911_beta_m(v));
  Na_mO  =  Na_m;
  Kir_m  =  (comp1086_alpha_d(v)) / (comp1086_alpha_d(v) + comp1086_beta_d(v));
  Kir_mO  =  Kir_m;
  KCa_m  =  (comp924_alpha_c(v, cai)) / (comp924_alpha_c(v, cai) + comp924_beta_c(v, cai));
  pNa_m  =  (comp2657_alpha_m(v)) / (comp2657_alpha_m(v) + comp2657_beta_m(v));
  KM_m  =  (comp1331_alpha_n(v)) / (comp1331_alpha_n(v) + comp1331_beta_n(v));
  KA_h  =  (comp509_alpha_b(v)) / (comp509_alpha_b(v) + comp509_beta_b(v));
  KA_m  =  (comp509_alpha_a(v)) / (comp509_alpha_a(v) + comp509_beta_a(v));
  y_[6]  =  KV_mO;
  y_[7]  =  Nar_hO;
  y_[8]  =  Nar_mO;
  y_[9]  =  CaHVA_mO;
  y_[10]  =  CaHVA_hO;
  y_[11]  =  Na_hO;
  y_[12]  =  Na_mO;
  y_[13]  =  Kir_mO;
  y_[14]  =  comp65_ca;
  y_[3]  =  KCa_m;
  y_[4]  =  pNa_m;
  y_[5]  =  KM_m;
  y_[1]  =  KA_h;
  y_[2]  =  KA_m;
  v3438  =  Na_m;; 
i_Na  =  (comp1911_gbar * v3438 * v3438 * v3438 * Na_h) * (v - comp1911_e);
  i_Nar  =  (comp2270_gbar * Nar_m * Nar_h) * (v - comp2270_e);
  i_pNa  =  (comp2657_gbar * pNa_m) * (v - comp2657_e);
  ina  =  i_Na + i_Nar + i_pNa;
  i_KM  =  (comp1331_gbar * KM_m) * (v - comp1331_e);
  v3439  =  KV_m;; 
i_KV  =  (comp1604_gbar * v3439 * v3439 * v3439 * v3439) * (v - comp1604_e);
  v3440  =  KA_m;; 
i_KA  =  (comp509_gbar * v3440 * v3440 * v3440 * KA_h) * (v - comp509_e);
  i_KCa  =  (comp924_gbar * KCa_m) * (v - comp924_e);
  i_Kir  =  (comp1086_gbar * Kir_m) * (v - comp1086_e);
  ik  =  i_KM + i_KV + i_KA + i_KCa + i_Kir;
  i_Lkg1  =  comp1849_gbar * (v - comp1849_e);
  i_Lkg2  =  comp1880_ggaba * (v - comp1880_egaba);
  i  =  i_Lkg1 + i_Lkg2;
  v3441  =  CaHVA_m;; 
i_CaHVA  =  (comp150_gbar * v3441 * v3441 * CaHVA_h) * (v - comp150_e);
  ica  =  i_CaHVA;
  y_[0]  =  0.0;
}


CGC::State_::State_ (const State_& s) : r_(s.r_)
{
  for ( int i = 0 ; i < 15 ; ++i ) y_[i] = s.y_[i];
}


CGC::State_& CGC::State_::operator=(const State_& s)
{
     assert(this != &s);  
     for ( size_t i = 0 ; i < 15 ; ++i )
       y_[i] = s.y_[i];
     r_ = s.r_;
     return *this;
}




void CGC::Parameters_::get (DictionaryDatum &d) const
{
  def<double_t>(d, "comp2270_Aalpha_f", comp2270_Aalpha_f);
  def<double_t>(d, "comp509_V0beta_b", comp509_V0beta_b);
  def<double_t>(d, "comp509_V0beta_a", comp509_V0beta_a);
  def<double_t>(d, "comp2657_Kbeta_m", comp2657_Kbeta_m);
  def<double_t>(d, "comp1764_vcbase", comp1764_vcbase);
  def<double_t>(d, "comp1604_V0alpha_n", comp1604_V0alpha_n);
  def<double_t>(d, "comp2845_vchold", comp2845_vchold);
  def<double_t>(d, "comp2845_vcinc", comp2845_vcinc);
  def<double_t>(d, "comp1331_Kalpha_n", comp1331_Kalpha_n);
  def<double_t>(d, "comp924_Bbeta_c", comp924_Bbeta_c);
  def<double_t>(d, "comp1246_vcbdur", comp1246_vcbdur);
  def<double_t>(d, "comp150_Abeta_s", comp150_Abeta_s);
  def<double_t>(d, "comp150_Q10", comp150_Q10);
  def<double_t>(d, "comp150_Abeta_u", comp150_Abeta_u);
  def<double_t>(d, "comp2270_V0alpha_s", comp2270_V0alpha_s);
  def<double_t>(d, "comp2270_V0alpha_f", comp2270_V0alpha_f);
  def<double_t>(d, "comp1911_V0alpha_h", comp1911_V0alpha_h);
  def<double_t>(d, "comp509_K_binf", comp509_K_binf);
  def<double_t>(d, "comp2845_vcsteps", comp2845_vcsteps);
  def<double_t>(d, "comp839_vcinc", comp839_vcinc);
  def<double_t>(d, "comp839_vchold", comp839_vchold);
  def<double_t>(d, "fix_celsius", fix_celsius);
  def<double_t>(d, "comp1246_vcsteps", comp1246_vcsteps);
  def<double_t>(d, "comp924_Q10", comp924_Q10);
  def<double_t>(d, "comp1331_Q10", comp1331_Q10);
  def<double_t>(d, "comp924_e", comp924_e);
  def<double_t>(d, "comp1086_Q10", comp1086_Q10);
  def<double_t>(d, "comp1086_gbar", comp1086_gbar);
  def<double_t>(d, "comp150_V0alpha_u", comp150_V0alpha_u);
  def<double_t>(d, "comp150_V0alpha_s", comp150_V0alpha_s);
  def<double_t>(d, "comp1604_Abeta_n", comp1604_Abeta_n);
  def<double_t>(d, "comp1911_Kbeta_h", comp1911_Kbeta_h);
  def<double_t>(d, "comp1519_vchold", comp1519_vchold);
  def<double_t>(d, "comp839_vchdur", comp839_vchdur);
  def<double_t>(d, "comp2572_vcbase", comp2572_vcbase);
  def<double_t>(d, "comp2572_vcinc", comp2572_vcinc);
  def<double_t>(d, "comp924_Abeta_c", comp924_Abeta_c);
  def<double_t>(d, "comp2657_Kalpha_m", comp2657_Kalpha_m);
  def<double_t>(d, "comp1519_vcsteps", comp1519_vcsteps);
  def<double_t>(d, "comp1911_Kbeta_m", comp1911_Kbeta_m);
  def<double_t>(d, "comp1764_vcbdur", comp1764_vcbdur);
  def<double_t>(d, "comp150_gbar", comp150_gbar);
  def<double_t>(d, "comp1086_Kbeta_d", comp1086_Kbeta_d);
  def<double_t>(d, "comp509_K_ainf", comp509_K_ainf);
  def<double_t>(d, "comp2270_Q10", comp2270_Q10);
  def<double_t>(d, "comp424_vcbdur", comp424_vcbdur);
  def<double_t>(d, "comp1764_vcsteps", comp1764_vcsteps);
  def<double_t>(d, "comp509_Aalpha_b", comp509_Aalpha_b);
  def<double_t>(d, "comp509_Aalpha_a", comp509_Aalpha_a);
  def<double_t>(d, "comp1086_Aalpha_d", comp1086_Aalpha_d);
  def<double_t>(d, "comp1880_ggaba", comp1880_ggaba);
  def<double_t>(d, "comp2572_vcsteps", comp2572_vcsteps);
  def<double_t>(d, "comp1911_Kalpha_m", comp1911_Kalpha_m);
  def<double_t>(d, "comp1911_Kalpha_h", comp1911_Kalpha_h);
  def<double_t>(d, "comp2657_V0beta_m", comp2657_V0beta_m);
  def<double_t>(d, "comp509_e", comp509_e);
  def<double_t>(d, "comp1086_V0beta_d", comp1086_V0beta_d);
  def<double_t>(d, "comp2270_Shiftbeta_s", comp2270_Shiftbeta_s);
  def<double_t>(d, "comp1331_V0alpha_n", comp1331_V0alpha_n);
  def<double_t>(d, "comp2270_Aalpha_s", comp2270_Aalpha_s);
  def<double_t>(d, "comp1604_Aalpha_n", comp1604_Aalpha_n);
  def<double_t>(d, "comp2270_gbar", comp2270_gbar);
  def<double_t>(d, "comp150_V0beta_u", comp150_V0beta_u);
  def<double_t>(d, "comp150_V0beta_s", comp150_V0beta_s);
  def<double_t>(d, "comp65_cai0", comp65_cai0);
  def<double_t>(d, "comp2657_Q10", comp2657_Q10);
  def<double_t>(d, "comp924_Balpha_c", comp924_Balpha_c);
  def<double_t>(d, "comp1331_Aalpha_n", comp1331_Aalpha_n);
  def<double_t>(d, "comp1519_vchdur", comp1519_vchdur);
  def<double_t>(d, "comp1604_V0beta_n", comp1604_V0beta_n);
  def<double_t>(d, "comp1604_Kalpha_n", comp1604_Kalpha_n);
  def<double_t>(d, "comp2185_vchdur", comp2185_vchdur);
  def<double_t>(d, "comp2657_Abeta_m", comp2657_Abeta_m);
  def<double_t>(d, "comp2657_B_minf", comp2657_B_minf);
  def<double_t>(d, "comp1604_gbar", comp1604_gbar);
  def<double_t>(d, "comp509_Abeta_a", comp509_Abeta_a);
  def<double_t>(d, "comp509_Abeta_b", comp509_Abeta_b);
  def<double_t>(d, "comp924_Kbeta_c", comp924_Kbeta_c);
  def<double_t>(d, "comp1086_Kalpha_d", comp1086_Kalpha_d);
  def<double_t>(d, "comp1331_V0_ninf", comp1331_V0_ninf);
  def<double_t>(d, "comp1086_V0alpha_d", comp1086_V0alpha_d);
  def<double_t>(d, "comp150_e", comp150_e);
  def<double_t>(d, "comp1331_e", comp1331_e);
  def<double_t>(d, "comp1519_vcbase", comp1519_vcbase);
  def<double_t>(d, "comp150_Kalpha_s", comp150_Kalpha_s);
  def<double_t>(d, "comp150_Kalpha_u", comp150_Kalpha_u);
  def<double_t>(d, "comp1331_V0beta_n", comp1331_V0beta_n);
  def<double_t>(d, "comp1911_e", comp1911_e);
  def<double_t>(d, "comp424_vcbase", comp424_vcbase);
  def<double_t>(d, "comp2185_vcinc", comp2185_vcinc);
  def<double_t>(d, "comp424_vcsteps", comp424_vcsteps);
  def<double_t>(d, "comp509_V0alpha_a", comp509_V0alpha_a);
  def<double_t>(d, "comp509_V0alpha_b", comp509_V0alpha_b);
  def<double_t>(d, "comp2270_Kbeta_s", comp2270_Kbeta_s);
  def<double_t>(d, "comp1764_vchold", comp1764_vchold);
  def<double_t>(d, "comp1331_gbar", comp1331_gbar);
  def<double_t>(d, "comp2270_Kbeta_f", comp2270_Kbeta_f);
  def<double_t>(d, "comp1764_vcinc", comp1764_vcinc);
  def<double_t>(d, "comp424_vcinc", comp424_vcinc);
  def<double_t>(d, "comp1246_vchdur", comp1246_vchdur);
  def<double_t>(d, "comp924_Aalpha_c", comp924_Aalpha_c);
  def<double_t>(d, "comp924_Kalpha_c", comp924_Kalpha_c);
  def<double_t>(d, "comp65_cao", comp65_cao);
  def<double_t>(d, "comp2572_vcbdur", comp2572_vcbdur);
  def<double_t>(d, "comp509_V0_binf", comp509_V0_binf);
  def<double_t>(d, "comp1911_gbar", comp1911_gbar);
  def<double_t>(d, "comp65_beta", comp65_beta);
  def<double_t>(d, "comp509_Kalpha_a", comp509_Kalpha_a);
  def<double_t>(d, "comp2185_vcbase", comp2185_vcbase);
  def<double_t>(d, "comp2845_vchdur", comp2845_vchdur);
  def<double_t>(d, "comp509_Kalpha_b", comp509_Kalpha_b);
  def<double_t>(d, "comp2572_vchold", comp2572_vchold);
  def<double_t>(d, "comp2657_V0alpha_m", comp2657_V0alpha_m);
  def<double_t>(d, "comp839_vcsteps", comp839_vcsteps);
  def<double_t>(d, "comp1519_vcbdur", comp1519_vcbdur);
  def<double_t>(d, "comp1880_egaba", comp1880_egaba);
  def<double_t>(d, "comp2270_Shiftalpha_s", comp2270_Shiftalpha_s);
  def<double_t>(d, "comp2270_Abeta_f", comp2270_Abeta_f);
  def<double_t>(d, "comp1849_gbar", comp1849_gbar);
  def<double_t>(d, "comp2185_vchold", comp2185_vchold);
  def<double_t>(d, "comp2657_V0_minf", comp2657_V0_minf);
  def<double_t>(d, "comp2572_vchdur", comp2572_vchdur);
  def<double_t>(d, "comp2845_vcbdur", comp2845_vcbdur);
  def<double_t>(d, "comp1911_Q10", comp1911_Q10);
  def<double_t>(d, "comp2657_gbar", comp2657_gbar);
  def<double_t>(d, "comp150_Aalpha_u", comp150_Aalpha_u);
  def<double_t>(d, "comp150_Aalpha_s", comp150_Aalpha_s);
  def<double_t>(d, "comp2657_e", comp2657_e);
  def<double_t>(d, "comp150_Kbeta_u", comp150_Kbeta_u);
  def<double_t>(d, "comp1331_Kbeta_n", comp1331_Kbeta_n);
  def<double_t>(d, "comp2185_vcsteps", comp2185_vcsteps);
  def<double_t>(d, "comp509_Kbeta_b", comp509_Kbeta_b);
  def<double_t>(d, "comp509_Kbeta_a", comp509_Kbeta_a);
  def<double_t>(d, "comp1246_vcinc", comp1246_vcinc);
  def<double_t>(d, "comp424_vchold", comp424_vchold);
  def<double_t>(d, "comp509_V0_ainf", comp509_V0_ainf);
  def<double_t>(d, "comp2270_Kalpha_f", comp2270_Kalpha_f);
  def<double_t>(d, "comp509_gbar", comp509_gbar);
  def<double_t>(d, "comp509_Q10", comp509_Q10);
  def<double_t>(d, "comp2270_Kalpha_s", comp2270_Kalpha_s);
  def<double_t>(d, "comp839_vcbdur", comp839_vcbdur);
  def<double_t>(d, "comp1911_Abeta_h", comp1911_Abeta_h);
  def<double_t>(d, "comp1911_Abeta_m", comp1911_Abeta_m);
  def<double_t>(d, "comp150_Kbeta_s", comp150_Kbeta_s);
  def<double_t>(d, "comp1604_e", comp1604_e);
  def<double_t>(d, "comp1086_Abeta_d", comp1086_Abeta_d);
  def<double_t>(d, "comp1246_vcbase", comp1246_vcbase);
  def<double_t>(d, "comp1331_B_ninf", comp1331_B_ninf);
  def<double_t>(d, "comp2270_V0beta_s", comp2270_V0beta_s);
  def<double_t>(d, "comp1086_e", comp1086_e);
  def<double_t>(d, "comp2270_e", comp2270_e);
  def<double_t>(d, "comp1911_V0beta_h", comp1911_V0beta_h);
  def<double_t>(d, "comp2270_V0beta_f", comp2270_V0beta_f);
  def<double_t>(d, "comp1911_V0beta_m", comp1911_V0beta_m);
  def<double_t>(d, "comp424_vchdur", comp424_vchdur);
  def<double_t>(d, "comp1331_Abeta_n", comp1331_Abeta_n);
  def<double_t>(d, "comp924_gbar", comp924_gbar);
  def<double_t>(d, "comp1246_vchold", comp1246_vchold);
  def<double_t>(d, "comp1604_Q10", comp1604_Q10);
  def<double_t>(d, "comp839_vcbase", comp839_vcbase);
  def<double_t>(d, "comp1911_Aalpha_h", comp1911_Aalpha_h);
  def<double_t>(d, "comp1911_V0alpha_m", comp1911_V0alpha_m);
  def<double_t>(d, "comp1849_e", comp1849_e);
  def<double_t>(d, "comp1911_Aalpha_m", comp1911_Aalpha_m);
  def<double_t>(d, "comp65_F", comp65_F);
  def<double_t>(d, "comp1519_vcinc", comp1519_vcinc);
  def<double_t>(d, "comp2270_Abeta_s", comp2270_Abeta_s);
  def<double_t>(d, "comp2845_vcbase", comp2845_vcbase);
  def<double_t>(d, "comp1604_Kbeta_n", comp1604_Kbeta_n);
  def<double_t>(d, "comp1764_vchdur", comp1764_vchdur);
  def<double_t>(d, "comp2657_Aalpha_m", comp2657_Aalpha_m);
  def<double_t>(d, "comp2185_vcbdur", comp2185_vcbdur);
  def<double_t>(d, "comp65_d", comp65_d);
}


void CGC::Parameters_::set (const DictionaryDatum &d)
{
  updateValue<double_t>(d, "comp2270_Aalpha_f", comp2270_Aalpha_f);
  updateValue<double_t>(d, "comp509_V0beta_b", comp509_V0beta_b);
  updateValue<double_t>(d, "comp509_V0beta_a", comp509_V0beta_a);
  updateValue<double_t>(d, "comp2657_Kbeta_m", comp2657_Kbeta_m);
  updateValue<double_t>(d, "comp1764_vcbase", comp1764_vcbase);
  updateValue<double_t>(d, "comp1604_V0alpha_n", comp1604_V0alpha_n);
  updateValue<double_t>(d, "comp2845_vchold", comp2845_vchold);
  updateValue<double_t>(d, "comp2845_vcinc", comp2845_vcinc);
  updateValue<double_t>(d, "comp1331_Kalpha_n", comp1331_Kalpha_n);
  updateValue<double_t>(d, "comp924_Bbeta_c", comp924_Bbeta_c);
  updateValue<double_t>(d, "comp1246_vcbdur", comp1246_vcbdur);
  updateValue<double_t>(d, "comp150_Abeta_s", comp150_Abeta_s);
  updateValue<double_t>(d, "comp150_Q10", comp150_Q10);
  updateValue<double_t>(d, "comp150_Abeta_u", comp150_Abeta_u);
  updateValue<double_t>(d, "comp2270_V0alpha_s", comp2270_V0alpha_s);
  updateValue<double_t>(d, "comp2270_V0alpha_f", comp2270_V0alpha_f);
  updateValue<double_t>(d, "comp1911_V0alpha_h", comp1911_V0alpha_h);
  updateValue<double_t>(d, "comp509_K_binf", comp509_K_binf);
  updateValue<double_t>(d, "comp2845_vcsteps", comp2845_vcsteps);
  updateValue<double_t>(d, "comp839_vcinc", comp839_vcinc);
  updateValue<double_t>(d, "comp839_vchold", comp839_vchold);
  updateValue<double_t>(d, "fix_celsius", fix_celsius);
  updateValue<double_t>(d, "comp1246_vcsteps", comp1246_vcsteps);
  updateValue<double_t>(d, "comp924_Q10", comp924_Q10);
  updateValue<double_t>(d, "comp1331_Q10", comp1331_Q10);
  updateValue<double_t>(d, "comp924_e", comp924_e);
  updateValue<double_t>(d, "comp1086_Q10", comp1086_Q10);
  updateValue<double_t>(d, "comp1086_gbar", comp1086_gbar);
  updateValue<double_t>(d, "comp150_V0alpha_u", comp150_V0alpha_u);
  updateValue<double_t>(d, "comp150_V0alpha_s", comp150_V0alpha_s);
  updateValue<double_t>(d, "comp1604_Abeta_n", comp1604_Abeta_n);
  updateValue<double_t>(d, "comp1911_Kbeta_h", comp1911_Kbeta_h);
  updateValue<double_t>(d, "comp1519_vchold", comp1519_vchold);
  updateValue<double_t>(d, "comp839_vchdur", comp839_vchdur);
  updateValue<double_t>(d, "comp2572_vcbase", comp2572_vcbase);
  updateValue<double_t>(d, "comp2572_vcinc", comp2572_vcinc);
  updateValue<double_t>(d, "comp924_Abeta_c", comp924_Abeta_c);
  updateValue<double_t>(d, "comp2657_Kalpha_m", comp2657_Kalpha_m);
  updateValue<double_t>(d, "comp1519_vcsteps", comp1519_vcsteps);
  updateValue<double_t>(d, "comp1911_Kbeta_m", comp1911_Kbeta_m);
  updateValue<double_t>(d, "comp1764_vcbdur", comp1764_vcbdur);
  updateValue<double_t>(d, "comp150_gbar", comp150_gbar);
  updateValue<double_t>(d, "comp1086_Kbeta_d", comp1086_Kbeta_d);
  updateValue<double_t>(d, "comp509_K_ainf", comp509_K_ainf);
  updateValue<double_t>(d, "comp2270_Q10", comp2270_Q10);
  updateValue<double_t>(d, "comp424_vcbdur", comp424_vcbdur);
  updateValue<double_t>(d, "comp1764_vcsteps", comp1764_vcsteps);
  updateValue<double_t>(d, "comp509_Aalpha_b", comp509_Aalpha_b);
  updateValue<double_t>(d, "comp509_Aalpha_a", comp509_Aalpha_a);
  updateValue<double_t>(d, "comp1086_Aalpha_d", comp1086_Aalpha_d);
  updateValue<double_t>(d, "comp1880_ggaba", comp1880_ggaba);
  updateValue<double_t>(d, "comp2572_vcsteps", comp2572_vcsteps);
  updateValue<double_t>(d, "comp1911_Kalpha_m", comp1911_Kalpha_m);
  updateValue<double_t>(d, "comp1911_Kalpha_h", comp1911_Kalpha_h);
  updateValue<double_t>(d, "comp2657_V0beta_m", comp2657_V0beta_m);
  updateValue<double_t>(d, "comp509_e", comp509_e);
  updateValue<double_t>(d, "comp1086_V0beta_d", comp1086_V0beta_d);
  updateValue<double_t>(d, "comp2270_Shiftbeta_s", comp2270_Shiftbeta_s);
  updateValue<double_t>(d, "comp1331_V0alpha_n", comp1331_V0alpha_n);
  updateValue<double_t>(d, "comp2270_Aalpha_s", comp2270_Aalpha_s);
  updateValue<double_t>(d, "comp1604_Aalpha_n", comp1604_Aalpha_n);
  updateValue<double_t>(d, "comp2270_gbar", comp2270_gbar);
  updateValue<double_t>(d, "comp150_V0beta_u", comp150_V0beta_u);
  updateValue<double_t>(d, "comp150_V0beta_s", comp150_V0beta_s);
  updateValue<double_t>(d, "comp65_cai0", comp65_cai0);
  updateValue<double_t>(d, "comp2657_Q10", comp2657_Q10);
  updateValue<double_t>(d, "comp924_Balpha_c", comp924_Balpha_c);
  updateValue<double_t>(d, "comp1331_Aalpha_n", comp1331_Aalpha_n);
  updateValue<double_t>(d, "comp1519_vchdur", comp1519_vchdur);
  updateValue<double_t>(d, "comp1604_V0beta_n", comp1604_V0beta_n);
  updateValue<double_t>(d, "comp1604_Kalpha_n", comp1604_Kalpha_n);
  updateValue<double_t>(d, "comp2185_vchdur", comp2185_vchdur);
  updateValue<double_t>(d, "comp2657_Abeta_m", comp2657_Abeta_m);
  updateValue<double_t>(d, "comp2657_B_minf", comp2657_B_minf);
  updateValue<double_t>(d, "comp1604_gbar", comp1604_gbar);
  updateValue<double_t>(d, "comp509_Abeta_a", comp509_Abeta_a);
  updateValue<double_t>(d, "comp509_Abeta_b", comp509_Abeta_b);
  updateValue<double_t>(d, "comp924_Kbeta_c", comp924_Kbeta_c);
  updateValue<double_t>(d, "comp1086_Kalpha_d", comp1086_Kalpha_d);
  updateValue<double_t>(d, "comp1331_V0_ninf", comp1331_V0_ninf);
  updateValue<double_t>(d, "comp1086_V0alpha_d", comp1086_V0alpha_d);
  updateValue<double_t>(d, "comp150_e", comp150_e);
  updateValue<double_t>(d, "comp1331_e", comp1331_e);
  updateValue<double_t>(d, "comp1519_vcbase", comp1519_vcbase);
  updateValue<double_t>(d, "comp150_Kalpha_s", comp150_Kalpha_s);
  updateValue<double_t>(d, "comp150_Kalpha_u", comp150_Kalpha_u);
  updateValue<double_t>(d, "comp1331_V0beta_n", comp1331_V0beta_n);
  updateValue<double_t>(d, "comp1911_e", comp1911_e);
  updateValue<double_t>(d, "comp424_vcbase", comp424_vcbase);
  updateValue<double_t>(d, "comp2185_vcinc", comp2185_vcinc);
  updateValue<double_t>(d, "comp424_vcsteps", comp424_vcsteps);
  updateValue<double_t>(d, "comp509_V0alpha_a", comp509_V0alpha_a);
  updateValue<double_t>(d, "comp509_V0alpha_b", comp509_V0alpha_b);
  updateValue<double_t>(d, "comp2270_Kbeta_s", comp2270_Kbeta_s);
  updateValue<double_t>(d, "comp1764_vchold", comp1764_vchold);
  updateValue<double_t>(d, "comp1331_gbar", comp1331_gbar);
  updateValue<double_t>(d, "comp2270_Kbeta_f", comp2270_Kbeta_f);
  updateValue<double_t>(d, "comp1764_vcinc", comp1764_vcinc);
  updateValue<double_t>(d, "comp424_vcinc", comp424_vcinc);
  updateValue<double_t>(d, "comp1246_vchdur", comp1246_vchdur);
  updateValue<double_t>(d, "comp924_Aalpha_c", comp924_Aalpha_c);
  updateValue<double_t>(d, "comp924_Kalpha_c", comp924_Kalpha_c);
  updateValue<double_t>(d, "comp65_cao", comp65_cao);
  updateValue<double_t>(d, "comp2572_vcbdur", comp2572_vcbdur);
  updateValue<double_t>(d, "comp509_V0_binf", comp509_V0_binf);
  updateValue<double_t>(d, "comp1911_gbar", comp1911_gbar);
  updateValue<double_t>(d, "comp65_beta", comp65_beta);
  updateValue<double_t>(d, "comp509_Kalpha_a", comp509_Kalpha_a);
  updateValue<double_t>(d, "comp2185_vcbase", comp2185_vcbase);
  updateValue<double_t>(d, "comp2845_vchdur", comp2845_vchdur);
  updateValue<double_t>(d, "comp509_Kalpha_b", comp509_Kalpha_b);
  updateValue<double_t>(d, "comp2572_vchold", comp2572_vchold);
  updateValue<double_t>(d, "comp2657_V0alpha_m", comp2657_V0alpha_m);
  updateValue<double_t>(d, "comp839_vcsteps", comp839_vcsteps);
  updateValue<double_t>(d, "comp1519_vcbdur", comp1519_vcbdur);
  updateValue<double_t>(d, "comp1880_egaba", comp1880_egaba);
  updateValue<double_t>(d, "comp2270_Shiftalpha_s", comp2270_Shiftalpha_s);
  updateValue<double_t>(d, "comp2270_Abeta_f", comp2270_Abeta_f);
  updateValue<double_t>(d, "comp1849_gbar", comp1849_gbar);
  updateValue<double_t>(d, "comp2185_vchold", comp2185_vchold);
  updateValue<double_t>(d, "comp2657_V0_minf", comp2657_V0_minf);
  updateValue<double_t>(d, "comp2572_vchdur", comp2572_vchdur);
  updateValue<double_t>(d, "comp2845_vcbdur", comp2845_vcbdur);
  updateValue<double_t>(d, "comp1911_Q10", comp1911_Q10);
  updateValue<double_t>(d, "comp2657_gbar", comp2657_gbar);
  updateValue<double_t>(d, "comp150_Aalpha_u", comp150_Aalpha_u);
  updateValue<double_t>(d, "comp150_Aalpha_s", comp150_Aalpha_s);
  updateValue<double_t>(d, "comp2657_e", comp2657_e);
  updateValue<double_t>(d, "comp150_Kbeta_u", comp150_Kbeta_u);
  updateValue<double_t>(d, "comp1331_Kbeta_n", comp1331_Kbeta_n);
  updateValue<double_t>(d, "comp2185_vcsteps", comp2185_vcsteps);
  updateValue<double_t>(d, "comp509_Kbeta_b", comp509_Kbeta_b);
  updateValue<double_t>(d, "comp509_Kbeta_a", comp509_Kbeta_a);
  updateValue<double_t>(d, "comp1246_vcinc", comp1246_vcinc);
  updateValue<double_t>(d, "comp424_vchold", comp424_vchold);
  updateValue<double_t>(d, "comp509_V0_ainf", comp509_V0_ainf);
  updateValue<double_t>(d, "comp2270_Kalpha_f", comp2270_Kalpha_f);
  updateValue<double_t>(d, "comp509_gbar", comp509_gbar);
  updateValue<double_t>(d, "comp509_Q10", comp509_Q10);
  updateValue<double_t>(d, "comp2270_Kalpha_s", comp2270_Kalpha_s);
  updateValue<double_t>(d, "comp839_vcbdur", comp839_vcbdur);
  updateValue<double_t>(d, "comp1911_Abeta_h", comp1911_Abeta_h);
  updateValue<double_t>(d, "comp1911_Abeta_m", comp1911_Abeta_m);
  updateValue<double_t>(d, "comp150_Kbeta_s", comp150_Kbeta_s);
  updateValue<double_t>(d, "comp1604_e", comp1604_e);
  updateValue<double_t>(d, "comp1086_Abeta_d", comp1086_Abeta_d);
  updateValue<double_t>(d, "comp1246_vcbase", comp1246_vcbase);
  updateValue<double_t>(d, "comp1331_B_ninf", comp1331_B_ninf);
  updateValue<double_t>(d, "comp2270_V0beta_s", comp2270_V0beta_s);
  updateValue<double_t>(d, "comp1086_e", comp1086_e);
  updateValue<double_t>(d, "comp2270_e", comp2270_e);
  updateValue<double_t>(d, "comp1911_V0beta_h", comp1911_V0beta_h);
  updateValue<double_t>(d, "comp2270_V0beta_f", comp2270_V0beta_f);
  updateValue<double_t>(d, "comp1911_V0beta_m", comp1911_V0beta_m);
  updateValue<double_t>(d, "comp424_vchdur", comp424_vchdur);
  updateValue<double_t>(d, "comp1331_Abeta_n", comp1331_Abeta_n);
  updateValue<double_t>(d, "comp924_gbar", comp924_gbar);
  updateValue<double_t>(d, "comp1246_vchold", comp1246_vchold);
  updateValue<double_t>(d, "comp1604_Q10", comp1604_Q10);
  updateValue<double_t>(d, "comp839_vcbase", comp839_vcbase);
  updateValue<double_t>(d, "comp1911_Aalpha_h", comp1911_Aalpha_h);
  updateValue<double_t>(d, "comp1911_V0alpha_m", comp1911_V0alpha_m);
  updateValue<double_t>(d, "comp1849_e", comp1849_e);
  updateValue<double_t>(d, "comp1911_Aalpha_m", comp1911_Aalpha_m);
  updateValue<double_t>(d, "comp65_F", comp65_F);
  updateValue<double_t>(d, "comp1519_vcinc", comp1519_vcinc);
  updateValue<double_t>(d, "comp2270_Abeta_s", comp2270_Abeta_s);
  updateValue<double_t>(d, "comp2845_vcbase", comp2845_vcbase);
  updateValue<double_t>(d, "comp1604_Kbeta_n", comp1604_Kbeta_n);
  updateValue<double_t>(d, "comp1764_vchdur", comp1764_vchdur);
  updateValue<double_t>(d, "comp2657_Aalpha_m", comp2657_Aalpha_m);
  updateValue<double_t>(d, "comp2185_vcbdur", comp2185_vcbdur);
  updateValue<double_t>(d, "comp65_d", comp65_d);
}


void CGC::State_::get (DictionaryDatum &d) const
{
  def<double_t>(d, "comp65_ca", y_[14]);
  def<double_t>(d, "Kir_mO", y_[13]);
  def<double_t>(d, "Na_mO", y_[12]);
  def<double_t>(d, "Na_hO", y_[11]);
  def<double_t>(d, "CaHVA_hO", y_[10]);
  def<double_t>(d, "CaHVA_mO", y_[9]);
  def<double_t>(d, "Nar_mO", y_[8]);
  def<double_t>(d, "Nar_hO", y_[7]);
  def<double_t>(d, "KV_mO", y_[6]);
  def<double_t>(d, "KM_m", y_[5]);
  def<double_t>(d, "pNa_m", y_[4]);
  def<double_t>(d, "KCa_m", y_[3]);
  def<double_t>(d, "KA_m", y_[2]);
  def<double_t>(d, "KA_h", y_[1]);
  def<double_t>(d, "v", y_[0]);
}


void CGC::State_::set (const DictionaryDatum &d, const Parameters_&)
{
  updateValue<double_t>(d, "comp65_ca", y_[14]);
  updateValue<double_t>(d, "Kir_mO", y_[13]);
  updateValue<double_t>(d, "Na_mO", y_[12]);
  updateValue<double_t>(d, "Na_hO", y_[11]);
  updateValue<double_t>(d, "CaHVA_hO", y_[10]);
  updateValue<double_t>(d, "CaHVA_mO", y_[9]);
  updateValue<double_t>(d, "Nar_mO", y_[8]);
  updateValue<double_t>(d, "Nar_hO", y_[7]);
  updateValue<double_t>(d, "KV_mO", y_[6]);
  updateValue<double_t>(d, "KM_m", y_[5]);
  updateValue<double_t>(d, "pNa_m", y_[4]);
  updateValue<double_t>(d, "KCa_m", y_[3]);
  updateValue<double_t>(d, "KA_m", y_[2]);
  updateValue<double_t>(d, "KA_h", y_[1]);
  updateValue<double_t>(d, "v", y_[0]);
}




CGC::Buffers_::Buffers_(CGC& n)
    : logger_(n),
      s_(0),
      c_(0),
      e_(0)
{
    // Initialization of the remaining members is deferred to
    // init_buffers_().
}


CGC::Buffers_::Buffers_(const Buffers_&, CGC& n)
    : logger_(n),
      s_(0),
      c_(0),
      e_(0)
{
    // Initialization of the remaining members is deferred to
    // init_buffers_().
}


CGC::CGC()
    : Archiving_Node(), 
      P_(), 
      S_(P_),
      B_(*this)
{
    recordablesMap_.create();
}


CGC::CGC(const CGC& n)
    : Archiving_Node(n), 
      P_(n.P_), 
      S_(n.S_),
      B_(n.B_, *this)
{
}
CGC::~CGC()
{
    // GSL structs only allocated by init_nodes_(), so we need to protect destruction
    if ( B_.s_ ) gsl_odeiv_step_free(B_.s_);
    if ( B_.c_ ) gsl_odeiv_control_free(B_.c_);
    if ( B_.e_ ) gsl_odeiv_evolve_free(B_.e_);
}


  void CGC::init_node_(const Node& proto)
{
    const CGC& pr = downcast<CGC>(proto);
    P_ = pr.P_;
    S_ = pr.S_;
}


void CGC::init_state_(const Node& proto)
{
    const CGC& pr = downcast<CGC>(proto);
    S_ = pr.S_;
}


void ~A::init_buffers_()
{
      B_.currents_.clear();           
    Archiving_Node::clear_history();

    B_.logger_.reset();

    B_.step_ = Time::get_resolution().get_ms();
    B_.IntegrationStep_ = B_.step_;

    B_.I_stim_ = 0.0;

    static const gsl_odeiv_step_type* T1 = gsl_odeiv_step_rkf45;
  
    if ( B_.s_ == 0 )
      B_.s_ = gsl_odeiv_step_alloc (T1, 15);
    else 
      gsl_odeiv_step_reset(B_.s_);
    
    if ( B_.c_ == 0 )  
      B_.c_ = gsl_odeiv_control_y_new (1e-3, 0.0);
    else
      gsl_odeiv_control_init(B_.c_, 1e-3, 0.0, 1.0, 0.0);
    
    if ( B_.e_ == 0 )  
      B_.e_ = gsl_odeiv_evolve_alloc(15);
    else 
      gsl_odeiv_evolve_reset(B_.e_);
  
    B_.sys_.function  = CGC_dynamics; 
    B_.sys_.jacobian  = 0;
    B_.sys_.dimension = 15;
    B_.sys_.params    = reinterpret_cast<void*>(this);
}


void CGC::calibrate()
{
    B_.logger_.init();  
    V_.RefractoryCounts_ = 20;
    V_.U_old_ = S_.y_[0];
}


void CGC::update(Time const & origin, const long_t from, const long_t to)
{
  assert(to >= 0 && (delay) from < Scheduler::get_min_delay());
    assert(from < to);

    for ( long_t lag = from ; lag < to ; ++lag )
      {
    
	double tt = 0.0 ; //it's all relative!
	V_.U_old_ = S_.y_[0];

   
	// adaptive step integration
	while (tt < B_.step_)
	{
	  const int status = gsl_odeiv_evolve_apply(B_.e_, B_.c_, B_.s_, 
				 &B_.sys_,              // system of ODE
				 &tt,                   // from t...
				  B_.step_,             // ...to t=t+h
				 &B_.IntegrationStep_ , // integration window (written on!)
				  S_.y_);	        // neuron state

	  if ( status != GSL_SUCCESS )
	    throw GSLSolverFailure(get_name(), status);
	}
  	// sending spikes: crossing 0 mV, pseudo-refractoriness and local maximum...
	// refractory?
	if (S_.r_)
	  {
	    --S_.r_;
	  }
	else
	  {
           
	  }
    
	// set new input current
	B_.I_stim_ = B_.currents_.get_value(lag);

	// log state data
	B_.logger_.record_data(origin.get_steps() + lag);

      }
}




void CGC::handle(SpikeEvent & e)
  {
    int flag;
    assert(e.get_delay() > 0);
    flag = 0;


}




void CGC::handle(CurrentEvent& e)
  {
    assert(e.get_delay() > 0);

    const double_t c=e.get_current();
    const double_t w=e.get_weight();

    B_.currents_.add_value(e.get_rel_delivery_steps(network()->get_slice_origin()), 
			w *c);
  }

void CGC::handle(DataLoggingRequest& e)
  {
    B_.logger_.handle(e);
  }


}


