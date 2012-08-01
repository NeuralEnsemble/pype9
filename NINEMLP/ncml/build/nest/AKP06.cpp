#include "AKP06.h"
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

#include <gsl/gsl_multimin.h>
namespace nest {




double comp91_Kv4_bhf (double v, void* pnode) {
  double rv309 ;
  double v312, v311, v310 ;
  v312  =  0.04477; v311  =  11.3615; v310  =  54.0;; 
rv309  =  v312 / (1.0 + exp(-((v + v310) / v311)));
  return rv309;
}




double comp141_Ih_tau (double v, void* pnode) {
  double rv313 ;
  double v319, v318, v317, v316, v315 ;
  v318  =  190.0; v317  =  720.0; v316  =  81.5; v315  =  11.9;; 
v319  =  (v + v316) / v315;; 
  rv313  =  v318 + v317 * exp(-(v319 * v319));
  return rv313;
}




double comp47_gate_flip_Kv3 (double v, double m, void* pnode) {
  double rv320 ;
  double v324, v323, v322, v321 ;
  double comp47_Kv3_bmf, comp47_Kv3_amf ;
  const  AKP06 & node =  *(reinterpret_cast< AKP06 *>(pnode));
  comp47_Kv3_bmf = node.P_.comp47_Kv3_bmf;
  comp47_Kv3_amf = node.P_.comp47_Kv3_amf;
  v324  =  comp47:Kv3_amf(v); 
  v323  =  v324 + comp47:Kv3_bmf(v); 
    v322  =  1.0 / v323; v321  =  v324 / v323;; 
rv320  =  (v321 + -(m)) / v322;
  return rv320;
}




double comp172_CaP_inf (double v, void* pnode) {
  double rv325 ;
  double v327, v326 ;
  v327  =  19.0; v326  =  5.5;; 
rv325  =  1.0 / (1.0 + exp(-((v + v327) / v326)));
  return rv325;
}




double comp47_Kv3_amf (double v, void* pnode) {
  double rv328 ;
  double v331, v330, v329 ;
  v331  =  0.22; v330  =  16.0; v329  =  -26.5;; 
rv328  =  v331 * exp(-(v + v330) / v329);
  return rv328;
}




double comp19_Kv1_amf (double v, void* pnode) {
  double rv332 ;
  double v335, v334, v333 ;
  v335  =  0.12889; v334  =  -33.90877; v333  =  45.0;; 
rv332  =  v335 * exp(-((v + v333) / v334));
  return rv332;
}




double comp172_CaP_tau (double v, void* pnode) {
  double rv336 ;
  double v339, v340 ;
  if (v > -50.0) 
      {v340  =  exp(-((v + 41.9) / 27.8));; 
          v339  =  1000.0 * (0.000191 + 0.00376 * v340 * v340);} 
      else 
        {v339  =  1000.0 * (0.00026367 + 0.1278 * exp(0.10327 * v));}; 
rv336  =  v339;
  return rv336;
}




double ghk (double v, double celsius, double ci, double co, void* pnode) {
  double rv341 ;
  double v347, v346, v344, v343 ;
  v344  =  96485.0; v343  =  8.3145;; 
v346  =  (0.002 * v344 * v) / (v343 * (273.19 + celsius));; 
  if (abs(1.0 + -(exp(-(v346)))) < 1e-06) 
          {v347  =  ((1e-06 * 2.0 * v344) * (ci + -(co * exp(-(v346))))) * (1.0 + v346 / 2.0);} 
          else 
            {v347  =  ((1e-06 * 2.0 * v346 * v344) * (ci + -(co * exp(-(v346))))) / (1.0 + -(exp(-(v346))));}; 
    rv341  =  v347;
  return rv341;
}




double comp193_CaBK_minf (double v, void* pnode) {
  double rv348 ;
  double v350, v349 ;
  v350  =  28.9; v349  =  6.2;; 
rv348  =  1.0 / (1.0 + exp(-((v + 5.0 + v350) / v349)));
  return rv348;
}




double comp47_Kv3_bmf (double v, void* pnode) {
  double rv351 ;
  double v354, v353, v352 ;
  v354  =  0.22; v353  =  16.0; v352  =  26.5;; 
rv351  =  v354 * exp(-(v + v353) / v352);
  return rv351;
}




double comp193_CaBK_hinf (double v, void* pnode) {
  double rv355 ;
  double v358, v357, v356 ;
  v358  =  0.085; v357  =  32.0; v356  =  -5.8;; 
rv355  =  v358 + (1.0 + -(v358)) / (1.0 + exp(-((v + 5.0 + v357) / v356)));
  return rv355;
}




double comp19_Kv1_bmf (double v, void* pnode) {
  double rv359 ;
  double v362, v361, v360 ;
  v362  =  0.12889; v361  =  12.42101; v360  =  45.0;; 
rv359  =  v362 * exp(-((v + v360) / v361));
  return rv359;
}




double comp91_Kv4_amf (double v, void* pnode) {
  double rv363 ;
  double v366, v365, v364 ;
  v366  =  0.15743; v365  =  -32.19976; v364  =  57.0;; 
rv363  =  v366 * exp(-((v + v364) / v365));
  return rv363;
}




double comp193_CaBK_zinf (double cai, void* pnode) {
  double rv367 ;
  double v368 ;
  v368  =  0.001;; rv367  =  1.0 / (1.0 + v368 / cai);
  return rv367;
}




double comp91_Kv4_bmf (double v, void* pnode) {
  double rv369 ;
  double v372, v371, v370 ;
  v372  =  0.15743; v371  =  37.51346; v370  =  57.0;; 
rv369  =  v372 * exp(-((v + v370) / v371));
  return rv369;
}




double comp193_CaBK_mtau (double v, void* pnode) {
  double rv373 ;
  double v378, v377, v376, v375, v374 ;
  v378  =  0.000505; 
  v377  =  86.4; v376  =  -10.1; v375  =  -33.3; v374  =  10.0;; 
rv373  =  v378 + 1.0 / (exp(-((v + 5.0 + v377) / v376)) + exp(-((v + 5.0 + v375) / v374)));
  return rv373;
}




double comp141_Ih_inf (double v, void* pnode) {
  double rv379 ;
  double v381, v380 ;
  v381  =  90.1; v380  =  -9.9;; 
rv379  =  1.0 / (1.0 + exp(-((v + v381) / v380)));
  return rv379;
}




double comp91_Kv4_ahf (double v, void* pnode) {
  double rv382 ;
  double v385, v384, v383 ;
  v385  =  0.01342; v384  =  -7.86476; v383  =  60.0;; 
rv382  =  v385 / (1.0 + exp(-((v + v383) / v384)));
  return rv382;
}




double comp193_CaBK_htau (double v, void* pnode) {
  double rv386 ;
  double v391, v390, v389, v388, v387 ;
  v391  =  0.0019; 
  v390  =  48.5; v389  =  -5.2; v388  =  -54.2; v387  =  12.9;; 
rv386  =  v391 + 1.0 / (exp(-((v + v390) / v389)) + exp(-((v + v388) / v387)));
  return rv386;
}




extern "C" int AKP06_dynamics (double t, const double y[], double f[], void* pnode) {
  double v408, v409, v410, v411, v398, v399, v400, v401, v404, v403, v405, v406, v407, v394, v393, v397, v396, temp_adj, v, CaBK_m_tau, Na_Na_x4, Na_Na_delta, Na_b0O, comp172_cao, comp18_ca, comp18_cac, cai, celsius, comp172_pcabar_CaP, comp172_pca_CaP, Na_Na_Ooff, Na_bin, Na_Na_x6, Na_Na_zeta, Na_bip, Narsg_Na_x2, Narsg_Na_beta, Narsg_b01, Narsg_b02, Narsg_b03, Narsg_b04, Na_b1n, Narsg_Na_Coff, Narsg_bi1, Narsg_Na_btfac, Narsg_bi2, Narsg_bi3, Narsg_bi4, Narsg_bi5, Narsg_b11, Narsg_b12, Narsg_b13, Narsg_b14, Narsg_Na_x4, Narsg_Na_delta, Narsg_b0O, CaBK_m_inf, Na_Na_x1, Na_Na_alpha, Na_f01, Na_f02, Na_f03, Na_f04, Na_Na_Con, Na_fi1, Na_Na_alfac, Na_fi2, Na_fi3, Na_fi4, Na_fi5, CaBK_h_tau, Na_f11, Na_f12, Na_f13, Na_f14, Narsg_Na_Ooff, Narsg_bin, CaP_m_tau, Narsg_Na_x6, Narsg_Na_zeta, Narsg_bip, Ih_m_tau, Narsg_b1n, Na_Na_x3, Na_Na_gamma, Na_f0O, Kv3_mO, Kv3_m, comp47_zn, comp47_e0, comp47_nc, comp47_switch_Kv3, comp47_i_gate_Kv3, comp193_CaBK_ztau, comp193_CaBK_alpha, Na_Na_Oon, Na_fin, Na_Na_x5, Na_Na_epsilon, Na_fip, Narsg_Na_x1, Narsg_Na_alpha, Narsg_f01, Narsg_f02, Narsg_f03, Narsg_f04, Na_f1n, Narsg_Na_Con, Narsg_fi1, Narsg_Na_alfac, Narsg_fi2, Narsg_fi3, Narsg_fi4, Narsg_fi5, Narsg_f11, Narsg_f12, Narsg_f13, Narsg_f14, CaBK_h_inf, comp193_CaBK_beta, Narsg_Na_x3, Narsg_Na_gamma, Narsg_f0O, CaP_m_inf, Ih_m_inf, Narsg_Na_Oon, Narsg_fin, Narsg_Na_x5, Narsg_Na_epsilon, Narsg_fip, Narsg_f1n, Na_Na_x2, Na_Na_beta, Na_b01, Na_b02, Na_b03, Na_b04, Na_Na_Coff, Na_bi1, Na_Na_btfac, Na_bi2, Na_bi3, Na_bi4, Na_bi5, Na_b11, Na_b12, Na_b13, Na_b14, comp193_CaBK_zO, comp193_CaBK_z, Kv1_mO, Kv1_m, Kv4_hO, Kv4_h, Kv4_mO, Kv4_m, Narsg_Na_zO, Narsg_Na_z, Na_Na_zO, Na_Na_z, CaP_m, Ih_m, CaBK_h, CaBK_m, Narsg_Na_zC5, Narsg_Na_zI5, Narsg_Na_zC4, Narsg_Na_zI4, Narsg_Na_zC3, Narsg_Na_zI3, Narsg_Na_zC2, Narsg_Na_zI2, Narsg_Na_zC1, Narsg_Na_zI1, Narsg_Na_zI6, Na_Na_zC5, Na_Na_zI5, Na_Na_zC4, Na_Na_zI4, Na_Na_zC3, Na_Na_zI3, Na_Na_zC2, Na_Na_zI2, Na_Na_zC1, Na_Na_zI1, Na_Na_zI6, i_Kv4, i_Kv3, i_Kv1, i_CaBK, ik, i_CaP, ica, i_comp75, i_Leak, i_Ih, i, i_Narsg, i_Na, ina, Narsg_gbar, comp18_ca_depth, comp47_gbar_Kv3, comp169_e_Leak, comp141_gbar_Ih, comp19_gbar_Kv1, comp17_C_m, Narsg_Na_gbar, comp18_F, Na_e, comp91_e_Kv4, Na_Na_gbar, Narsg_e, comp141_e_Ih, comp193_e_CaBK, comp18_ca0, Vrest, comp47_gunit, comp19_e_Kv1, comp169_gbar_Leak, comp47_e_Kv3, Na_gbar, comp91_gbar_Kv4, comp193_gbar_CaBK, comp18_ca_beta ;
  

  // S is shorthand for the type that describes the model state 
  typedef AKP06::State_ S;
  

  // cast the node ptr to an object of the proper type
  assert(pnode);
  const  AKP06 & node =  *(reinterpret_cast< AKP06 *>(pnode));
  

  // y[] must be the state vector supplied by the integrator, 
  // not the state vector in the node, node.S_.y[]. 
  

  Narsg_gbar  =  node.P_.Narsg_gbar;
  Na_Na_Ooff  =  node.P_.Na_Na_Ooff;
  comp47_e0  =  node.P_.comp47_e0;
  Na_Na_alpha  =  node.P_.Na_Na_alpha;
  comp18_ca_depth  =  node.P_.comp18_ca_depth;
  Narsg_Na_delta  =  node.P_.Narsg_Na_delta;
  Narsg_Na_epsilon  =  node.P_.Narsg_Na_epsilon;
  Narsg_Na_x6  =  node.P_.Narsg_Na_x6;
  Narsg_Na_x5  =  node.P_.Narsg_Na_x5;
  Narsg_Na_x4  =  node.P_.Narsg_Na_x4;
  comp47_gbar_Kv3  =  node.P_.comp47_gbar_Kv3;
  Narsg_Na_x3  =  node.P_.Narsg_Na_x3;
  Narsg_Na_x2  =  node.P_.Narsg_Na_x2;
  Narsg_Na_alfac  =  node.P_.Narsg_Na_alfac;
  Narsg_Na_x1  =  node.P_.Narsg_Na_x1;
  Narsg_Na_beta  =  node.P_.Narsg_Na_beta;
  Narsg_Na_Oon  =  node.P_.Narsg_Na_Oon;
  celsius  =  node.P_.celsius;
  Na_Na_x6  =  node.P_.Na_Na_x6;
  comp172_cao  =  node.P_.comp172_cao;
  Na_Na_x5  =  node.P_.Na_Na_x5;
  Na_Na_x4  =  node.P_.Na_Na_x4;
  Narsg_Na_Coff  =  node.P_.Narsg_Na_Coff;
  Na_Na_x3  =  node.P_.Na_Na_x3;
  Na_Na_x2  =  node.P_.Na_Na_x2;
  Na_Na_x1  =  node.P_.Na_Na_x1;
  comp169_e_Leak  =  node.P_.comp169_e_Leak;
  Na_Na_beta  =  node.P_.Na_Na_beta;
  Narsg_Na_alpha  =  node.P_.Narsg_Na_alpha;
  Na_Na_epsilon  =  node.P_.Na_Na_epsilon;
  Na_Na_Coff  =  node.P_.Na_Na_Coff;
  Na_Na_btfac  =  node.P_.Na_Na_btfac;
  comp141_gbar_Ih  =  node.P_.comp141_gbar_Ih;
  Narsg_Na_Con  =  node.P_.Narsg_Na_Con;
  comp47_nc  =  node.P_.comp47_nc;
  comp19_gbar_Kv1  =  node.P_.comp19_gbar_Kv1;
  Narsg_Na_btfac  =  node.P_.Narsg_Na_btfac;
  Narsg_Na_zeta  =  node.P_.Narsg_Na_zeta;
  Na_Na_Oon  =  node.P_.Na_Na_Oon;
  comp17_C_m  =  node.P_.comp17_C_m;
  temp_adj  =  node.P_.temp_adj;
  Narsg_Na_gbar  =  node.P_.Narsg_Na_gbar;
  comp18_F  =  node.P_.comp18_F;
  Na_Na_zeta  =  node.P_.Na_Na_zeta;
  Na_e  =  node.P_.Na_e;
  Na_Na_gamma  =  node.P_.Na_Na_gamma;
  comp91_e_Kv4  =  node.P_.comp91_e_Kv4;
  Na_Na_gbar  =  node.P_.Na_Na_gbar;
  Narsg_e  =  node.P_.Narsg_e;
  comp47_zn  =  node.P_.comp47_zn;
  comp141_e_Ih  =  node.P_.comp141_e_Ih;
  comp172_pcabar_CaP  =  node.P_.comp172_pcabar_CaP;
  comp193_e_CaBK  =  node.P_.comp193_e_CaBK;
  comp18_ca0  =  node.P_.comp18_ca0;
  Vrest  =  node.P_.Vrest;
  comp47_switch_Kv3  =  node.P_.comp47_switch_Kv3;
  comp47_gunit  =  node.P_.comp47_gunit;
  Na_Na_Con  =  node.P_.Na_Na_Con;
  comp19_e_Kv1  =  node.P_.comp19_e_Kv1;
  comp169_gbar_Leak  =  node.P_.comp169_gbar_Leak;
  Narsg_Na_gamma  =  node.P_.Narsg_Na_gamma;
  comp47_e_Kv3  =  node.P_.comp47_e_Kv3;
  Na_gbar  =  node.P_.Na_gbar;
  comp91_gbar_Kv4  =  node.P_.comp91_gbar_Kv4;
  Na_Na_delta  =  node.P_.Na_Na_delta;
  Narsg_Na_Ooff  =  node.P_.Narsg_Na_Ooff;
  Na_Na_alfac  =  node.P_.Na_Na_alfac;
  comp193_CaBK_ztau  =  node.P_.comp193_CaBK_ztau;
  comp193_gbar_CaBK  =  node.P_.comp193_gbar_CaBK;
  comp18_ca_beta  =  node.P_.comp18_ca_beta;
  v  =  y[0];
  Na_Na_zO  =  y[1];
  Na_Na_zI6  =  y[2];
  Na_Na_zI1  =  y[3];
  Na_Na_zC1  =  y[4];
  Na_Na_zI2  =  y[5];
  Na_Na_zC2  =  y[6];
  Na_Na_zI3  =  y[7];
  Na_Na_zC3  =  y[8];
  Na_Na_zI4  =  y[9];
  Na_Na_zC4  =  y[10];
  Na_Na_zI5  =  y[11];
  Na_Na_zC5  =  y[12];
  Narsg_Na_zO  =  y[13];
  Narsg_Na_zI6  =  y[14];
  Narsg_Na_zI1  =  y[15];
  Narsg_Na_zC1  =  y[16];
  Narsg_Na_zI2  =  y[17];
  Narsg_Na_zC2  =  y[18];
  Narsg_Na_zI3  =  y[19];
  Narsg_Na_zC3  =  y[20];
  Narsg_Na_zI4  =  y[21];
  Narsg_Na_zC4  =  y[22];
  Narsg_Na_zI5  =  y[23];
  Narsg_Na_zC5  =  y[24];
  CaBK_m  =  y[25];
  CaBK_h  =  y[26];
  Ih_m  =  y[27];
  CaP_m  =  y[28];
  Kv4_mO  =  y[29];
  Kv4_hO  =  y[30];
  comp18_ca  =  y[31];
  Kv1_mO  =  y[32];
  comp193_CaBK_zO  =  y[33];
  Kv3_mO  =  y[34];
  CaBK_m_tau  =  comp193_CaBK_mtau(v) / temp_adj;
  Na_b0O  =  Na_Na_delta * exp(v / Na_Na_x4) * temp_adj;
  if (comp18_ca < 0.0001) {v397  =  0.0001;} else {v397  =  comp18_ca;}; 
v396  =  v397;; comp18_cac  =  v396;
  cai  =  comp18_cac;
  comp172_pca_CaP  =  comp172_pcabar_CaP * ghk(v, celsius, cai, comp172_cao);
  Na_bin  =  Na_Na_Ooff * temp_adj;
  Na_bip  =  Na_Na_zeta * exp(v / Na_Na_x6) * temp_adj;
  Narsg_b01  =  Narsg_Na_beta * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b02  =  2.0 * Narsg_Na_beta * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b03  =  3.0 * Narsg_Na_beta * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b04  =  4.0 * Narsg_Na_beta * exp(v / Narsg_Na_x2) * temp_adj;
  Na_b1n  =  Na_Na_delta * exp(v / Na_Na_x4) * temp_adj;
  Narsg_bi1  =  Narsg_Na_Coff * temp_adj;
  Narsg_bi2  =  Narsg_Na_Coff * Narsg_Na_btfac * temp_adj;
  Narsg_bi3  =  Narsg_Na_Coff * Narsg_Na_btfac * Narsg_Na_btfac * temp_adj;
  Narsg_bi4  =  Narsg_Na_Coff * Narsg_Na_btfac * Narsg_Na_btfac * Narsg_Na_btfac * temp_adj;
  Narsg_bi5  =  Narsg_Na_Coff * Narsg_Na_btfac * Narsg_Na_btfac * Narsg_Na_btfac * Narsg_Na_btfac * temp_adj;
  Narsg_b11  =  Narsg_Na_beta * Narsg_Na_btfac * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b12  =  2.0 * Narsg_Na_beta * Narsg_Na_btfac * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b13  =  3.0 * Narsg_Na_beta * Narsg_Na_btfac * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b14  =  4.0 * Narsg_Na_beta * Narsg_Na_btfac * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b0O  =  Narsg_Na_delta * exp(v / Narsg_Na_x4) * temp_adj;
  CaBK_m_inf  =  comp193_CaBK_minf(v) / temp_adj;
  Na_f01  =  4.0 * Na_Na_alpha * exp(v / Na_Na_x1) * temp_adj;
  Na_f02  =  3.0 * Na_Na_alpha * exp(v / Na_Na_x1) * temp_adj;
  Na_f03  =  2.0 * Na_Na_alpha * exp(v / Na_Na_x1) * temp_adj;
  Na_f04  =  Na_Na_alpha * exp(v / Na_Na_x1) * temp_adj;
  Na_fi1  =  Na_Na_Con * temp_adj;
  Na_fi2  =  Na_Na_Con * Na_Na_alfac * temp_adj;
  Na_fi3  =  Na_Na_Con * Na_Na_alfac * Na_Na_alfac * temp_adj;
  Na_fi4  =  Na_Na_Con * Na_Na_alfac * Na_Na_alfac * Na_Na_alfac * temp_adj;
  Na_fi5  =  Na_Na_Con * Na_Na_alfac * Na_Na_alfac * Na_Na_alfac * Na_Na_alfac * temp_adj;
  CaBK_h_tau  =  comp193_CaBK_htau(v) / temp_adj;
  Na_f11  =  4.0 * Na_Na_alpha * Na_Na_alfac * exp(v / Na_Na_x1) * temp_adj;
  Na_f12  =  3.0 * Na_Na_alpha * Na_Na_alfac * exp(v / Na_Na_x1) * temp_adj;
  Na_f13  =  2.0 * Na_Na_alpha * Na_Na_alfac * exp(v / Na_Na_x1) * temp_adj;
  Na_f14  =  Na_Na_alpha * Na_Na_alfac * exp(v / Na_Na_x1) * temp_adj;
  Narsg_bin  =  Narsg_Na_Ooff * temp_adj;
  CaP_m_tau  =  comp172_CaP_tau(v) / temp_adj;
  Narsg_bip  =  Narsg_Na_zeta * exp(v / Narsg_Na_x6) * temp_adj;
  Ih_m_tau  =  comp141_Ih_tau(v) / temp_adj;
  Narsg_b1n  =  Narsg_Na_delta * exp(v / Narsg_Na_x4) * temp_adj;
  Na_f0O  =  Na_Na_gamma * exp(v / Na_Na_x3) * temp_adj;
  Kv3_m  =  Kv3_mO;
  if (comp47_switch_Kv3 > 0.0) 
      {v394  =  comp47_nc * 1000000.0 * comp47_e0 * 4.0 * comp47_zn * comp47_gate_flip_Kv3(v, Kv3_m);} 
      else 
        {v394  =  0.0;}; 
v393  =  v394;; comp47_i_gate_Kv3  =  v393;
  comp193_CaBK_alpha  =  comp193_CaBK_zinf(cai) / comp193_CaBK_ztau;
  Na_fin  =  Na_Na_Oon * temp_adj;
  Na_fip  =  Na_Na_epsilon * exp(v / Na_Na_x5) * temp_adj;
  Narsg_f01  =  4.0 * Narsg_Na_alpha * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f02  =  3.0 * Narsg_Na_alpha * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f03  =  2.0 * Narsg_Na_alpha * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f04  =  Narsg_Na_alpha * exp(v / Narsg_Na_x1) * temp_adj;
  Na_f1n  =  Na_Na_gamma * exp(v / Na_Na_x3) * temp_adj;
  Narsg_fi1  =  Narsg_Na_Con * temp_adj;
  Narsg_fi2  =  Narsg_Na_Con * Narsg_Na_alfac * temp_adj;
  Narsg_fi3  =  Narsg_Na_Con * Narsg_Na_alfac * Narsg_Na_alfac * temp_adj;
  Narsg_fi4  =  Narsg_Na_Con * Narsg_Na_alfac * Narsg_Na_alfac * Narsg_Na_alfac * temp_adj;
  Narsg_fi5  =  Narsg_Na_Con * Narsg_Na_alfac * Narsg_Na_alfac * Narsg_Na_alfac * Narsg_Na_alfac * temp_adj;
  Narsg_f11  =  4.0 * Narsg_Na_alpha * Narsg_Na_alfac * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f12  =  3.0 * Narsg_Na_alpha * Narsg_Na_alfac * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f13  =  2.0 * Narsg_Na_alpha * Narsg_Na_alfac * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f14  =  Narsg_Na_alpha * Narsg_Na_alfac * exp(v / Narsg_Na_x1) * temp_adj;
  CaBK_h_inf  =  comp193_CaBK_hinf(v) / temp_adj;
  comp193_CaBK_beta  =  (1.0 + -(comp193_CaBK_zinf(cai))) / comp193_CaBK_ztau;
  Narsg_f0O  =  Narsg_Na_gamma * exp(v / Narsg_Na_x3) * temp_adj;
  CaP_m_inf  =  comp172_CaP_inf(v);
  Ih_m_inf  =  comp141_Ih_inf(v);
  Narsg_fin  =  Narsg_Na_Oon * temp_adj;
  Narsg_fip  =  Narsg_Na_epsilon * exp(v / Narsg_Na_x5) * temp_adj;
  Narsg_f1n  =  Narsg_Na_gamma * exp(v / Narsg_Na_x3) * temp_adj;
  Na_b01  =  Na_Na_beta * exp(v / Na_Na_x2) * temp_adj;
  Na_b02  =  2.0 * Na_Na_beta * exp(v / Na_Na_x2) * temp_adj;
  Na_b03  =  3.0 * Na_Na_beta * exp(v / Na_Na_x2) * temp_adj;
  Na_b04  =  4.0 * Na_Na_beta * exp(v / Na_Na_x2) * temp_adj;
  Na_bi1  =  Na_Na_Coff * temp_adj;
  Na_bi2  =  Na_Na_Coff * Na_Na_btfac * temp_adj;
  Na_bi3  =  Na_Na_Coff * Na_Na_btfac * Na_Na_btfac * temp_adj;
  Na_bi4  =  Na_Na_Coff * Na_Na_btfac * Na_Na_btfac * Na_Na_btfac * temp_adj;
  Na_bi5  =  Na_Na_Coff * Na_Na_btfac * Na_Na_btfac * Na_Na_btfac * Na_Na_btfac * temp_adj;
  Na_b11  =  Na_Na_beta * Na_Na_btfac * exp(v / Na_Na_x2) * temp_adj;
  Na_b12  =  2.0 * Na_Na_beta * Na_Na_btfac * exp(v / Na_Na_x2) * temp_adj;
  Na_b13  =  3.0 * Na_Na_beta * Na_Na_btfac * exp(v / Na_Na_x2) * temp_adj;
  Na_b14  =  4.0 * Na_Na_beta * Na_Na_btfac * exp(v / Na_Na_x2) * temp_adj;
  comp193_CaBK_z  =  comp193_CaBK_zO;
  Kv1_m  =  Kv1_mO;
  Kv4_h  =  Kv4_hO;
  Kv4_m  =  Kv4_mO;
  Narsg_Na_z  =  Narsg_Na_zO;
  Na_Na_z  =  Na_Na_zO;
  // rate equation Na_Na_zO
  v398  =  Na_Na_zI6 + Na_Na_zI5 + Na_Na_zI4 + Na_Na_zI3 + Na_Na_zI2 + Na_Na_zI1 + Na_Na_zO + Na_Na_zC5 + Na_Na_zC4 + Na_Na_zC3 + Na_Na_zC2 + Na_Na_zC1;; 
f[1]  =  -(Na_Na_zO * Na_fin + Na_Na_zO * Na_fip + Na_Na_zO * Na_b0O) + Na_Na_zI6 * Na_bin + (1 - v398) * Na_bip + Na_Na_zC5 * Na_f0O;
  // rate equation Na_Na_zI6
  f[2]  =  -(Na_Na_zI6 * Na_b1n + Na_Na_zI6 * Na_bin) + Na_Na_zI5 * Na_f1n + Na_Na_zO * Na_fin;
  // rate equation Na_Na_zI1
  f[3]  =  -(Na_Na_zI1 * Na_bi1 + Na_Na_zI1 * Na_f11) + Na_Na_zC1 * Na_fi1 + Na_Na_zI2 * Na_b11;
  // rate equation Na_Na_zC1
  f[4]  =  -(Na_Na_zC1 * Na_fi1 + Na_Na_zC1 * Na_f01) + Na_Na_zI1 * Na_bi1 + Na_Na_zC2 * Na_b01;
  // rate equation Na_Na_zI2
  f[5]  =  -(Na_Na_zI2 * Na_bi2 + Na_Na_zI2 * Na_f12 + Na_Na_zI2 * Na_b11) + Na_Na_zC2 * Na_fi2 + Na_Na_zI3 * Na_b12 + Na_Na_zI1 * Na_f11;
  // rate equation Na_Na_zC2
  f[6]  =  -(Na_Na_zC2 * Na_fi2 + Na_Na_zC2 * Na_f02 + Na_Na_zC2 * Na_b01) + Na_Na_zI2 * Na_bi2 + Na_Na_zC3 * Na_b02 + Na_Na_zC1 * Na_f01;
  // rate equation Na_Na_zI3
  f[7]  =  -(Na_Na_zI3 * Na_bi3 + Na_Na_zI3 * Na_f13 + Na_Na_zI3 * Na_b12) + Na_Na_zC3 * Na_fi3 + Na_Na_zI4 * Na_b13 + Na_Na_zI2 * Na_f12;
  // rate equation Na_Na_zC3
  f[8]  =  -(Na_Na_zC3 * Na_fi3 + Na_Na_zC3 * Na_f03 + Na_Na_zC3 * Na_b02) + Na_Na_zI3 * Na_bi3 + Na_Na_zC4 * Na_b03 + Na_Na_zC2 * Na_f02;
  // rate equation Na_Na_zI4
  f[9]  =  -(Na_Na_zI4 * Na_bi4 + Na_Na_zI4 * Na_f14 + Na_Na_zI4 * Na_b13) + Na_Na_zC4 * Na_fi4 + Na_Na_zI5 * Na_b14 + Na_Na_zI3 * Na_f13;
  // rate equation Na_Na_zC4
  f[10]  =  -(Na_Na_zC4 * Na_fi4 + Na_Na_zC4 * Na_f04 + Na_Na_zC4 * Na_b03) + Na_Na_zI4 * Na_bi4 + Na_Na_zC5 * Na_b04 + Na_Na_zC3 * Na_f03;
  // rate equation Na_Na_zI5
  f[11]  =  -(Na_Na_zI5 * Na_bi5 + Na_Na_zI5 * Na_f1n + Na_Na_zI5 * Na_b14) + Na_Na_zC5 * Na_fi5 + Na_Na_zI6 * Na_b1n + Na_Na_zI4 * Na_f14;
  // rate equation Na_Na_zC5
  f[12]  =  -(Na_Na_zC5 * Na_fi5 + Na_Na_zC5 * Na_f0O + Na_Na_zC5 * Na_b04) + Na_Na_zI5 * Na_bi5 + Na_Na_zO * Na_b0O + Na_Na_zC4 * Na_f04;
  // rate equation Narsg_Na_zO
  v399  =  Narsg_Na_zI6 + Narsg_Na_zI5 + Narsg_Na_zI4 + Narsg_Na_zI3 + Narsg_Na_zI2 + Narsg_Na_zI1 + Narsg_Na_zO + Narsg_Na_zC5 + Narsg_Na_zC4 + Narsg_Na_zC3 + Narsg_Na_zC2 + Narsg_Na_zC1;; 
f[13]  =  -(Narsg_Na_zO * Narsg_fin + Narsg_Na_zO * Narsg_fip + Narsg_Na_zO * Narsg_b0O) + Narsg_Na_zI6 * Narsg_bin + (1 - v399) * Narsg_bip + Narsg_Na_zC5 * Narsg_f0O;
  // rate equation Narsg_Na_zI6
  f[14]  =  -(Narsg_Na_zI6 * Narsg_b1n + Narsg_Na_zI6 * Narsg_bin) + Narsg_Na_zI5 * Narsg_f1n + Narsg_Na_zO * Narsg_fin;
  // rate equation Narsg_Na_zI1
  f[15]  =  -(Narsg_Na_zI1 * Narsg_bi1 + Narsg_Na_zI1 * Narsg_f11) + Narsg_Na_zC1 * Narsg_fi1 + Narsg_Na_zI2 * Narsg_b11;
  // rate equation Narsg_Na_zC1
  f[16]  =  -(Narsg_Na_zC1 * Narsg_fi1 + Narsg_Na_zC1 * Narsg_f01) + Narsg_Na_zI1 * Narsg_bi1 + Narsg_Na_zC2 * Narsg_b01;
  // rate equation Narsg_Na_zI2
  f[17]  =  -(Narsg_Na_zI2 * Narsg_bi2 + Narsg_Na_zI2 * Narsg_f12 + Narsg_Na_zI2 * Narsg_b11) + Narsg_Na_zC2 * Narsg_fi2 + Narsg_Na_zI3 * Narsg_b12 + Narsg_Na_zI1 * Narsg_f11;
  // rate equation Narsg_Na_zC2
  f[18]  =  -(Narsg_Na_zC2 * Narsg_fi2 + Narsg_Na_zC2 * Narsg_f02 + Narsg_Na_zC2 * Narsg_b01) + Narsg_Na_zI2 * Narsg_bi2 + Narsg_Na_zC3 * Narsg_b02 + Narsg_Na_zC1 * Narsg_f01;
  // rate equation Narsg_Na_zI3
  f[19]  =  -(Narsg_Na_zI3 * Narsg_bi3 + Narsg_Na_zI3 * Narsg_f13 + Narsg_Na_zI3 * Narsg_b12) + Narsg_Na_zC3 * Narsg_fi3 + Narsg_Na_zI4 * Narsg_b13 + Narsg_Na_zI2 * Narsg_f12;
  // rate equation Narsg_Na_zC3
  f[20]  =  -(Narsg_Na_zC3 * Narsg_fi3 + Narsg_Na_zC3 * Narsg_f03 + Narsg_Na_zC3 * Narsg_b02) + Narsg_Na_zI3 * Narsg_bi3 + Narsg_Na_zC4 * Narsg_b03 + Narsg_Na_zC2 * Narsg_f02;
  // rate equation Narsg_Na_zI4
  f[21]  =  -(Narsg_Na_zI4 * Narsg_bi4 + Narsg_Na_zI4 * Narsg_f14 + Narsg_Na_zI4 * Narsg_b13) + Narsg_Na_zC4 * Narsg_fi4 + Narsg_Na_zI5 * Narsg_b14 + Narsg_Na_zI3 * Narsg_f13;
  // rate equation Narsg_Na_zC4
  f[22]  =  -(Narsg_Na_zC4 * Narsg_fi4 + Narsg_Na_zC4 * Narsg_f04 + Narsg_Na_zC4 * Narsg_b03) + Narsg_Na_zI4 * Narsg_bi4 + Narsg_Na_zC5 * Narsg_b04 + Narsg_Na_zC3 * Narsg_f03;
  // rate equation Narsg_Na_zI5
  f[23]  =  -(Narsg_Na_zI5 * Narsg_bi5 + Narsg_Na_zI5 * Narsg_f1n + Narsg_Na_zI5 * Narsg_b14) + Narsg_Na_zC5 * Narsg_fi5 + Narsg_Na_zI6 * Narsg_b1n + Narsg_Na_zI4 * Narsg_f14;
  // rate equation Narsg_Na_zC5
  f[24]  =  -(Narsg_Na_zC5 * Narsg_fi5 + Narsg_Na_zC5 * Narsg_f0O + Narsg_Na_zC5 * Narsg_b04) + Narsg_Na_zI5 * Narsg_bi5 + Narsg_Na_zO * Narsg_b0O + Narsg_Na_zC4 * Narsg_f04;
  // rate equation CaBK_m
  f[25]  =  (CaBK_m_inf + -(CaBK_m)) / CaBK_m_tau;
  // rate equation CaBK_h
  f[26]  =  (CaBK_h_inf + -(CaBK_h)) / CaBK_h_tau;
  // rate equation Ih_m
  f[27]  =  (Ih_m_inf + -(Ih_m)) / Ih_m_tau;
  // rate equation CaP_m
  f[28]  =  (CaP_m_inf + -(CaP_m)) / CaP_m_tau;
  // rate equation Kv4_mO
  v400  =  Kv4_mO;; 
f[29]  =  -(Kv4_mO * temp_adj * comp91_Kv4_bmf(v)) + (1 - v400) * (temp_adj * comp91_Kv4_amf(v));
  // rate equation Kv4_hO
  v401  =  Kv4_hO;; 
f[30]  =  -(Kv4_hO * temp_adj * comp91_Kv4_bhf(v)) + (1 - v401) * (temp_adj * comp91_Kv4_ahf(v));
  // rate equation comp18_ca
  if (comp18_ca < 0.0001) {v404  =  0.0001;} else {v404  =  comp18_ca;}; 
v403  =  v404;; 
  f[31]  =  (-(ica)) / (2.0 * comp18_ca0 * comp18_F * comp18_ca_depth) + -(v403 * comp18_ca_beta);
  // rate equation Kv1_mO
  v405  =  Kv1_mO;; 
f[32]  =  -(Kv1_mO * temp_adj * comp19_Kv1_bmf(v)) + (1 - v405) * (temp_adj * comp19_Kv1_amf(v));
  // rate equation comp193_CaBK_zO
  v406  =  comp193_CaBK_zO;; 
f[33]  =  -(comp193_CaBK_zO * comp193_CaBK_alpha) + (1 - v406) * comp193_CaBK_beta;
  // rate equation Kv3_mO
  v407  =  Kv3_mO;; 
f[34]  =  -(Kv3_mO * temp_adj * comp47_Kv3_bmf(v)) + (1 - v407) * (temp_adj * comp47_Kv3_amf(v));
  v408  =  Kv4_m;; 
i_Kv4  =  (comp91_gbar_Kv4 * v408 * v408 * v408 * v408 * Kv4_h) * (v - comp91_e_Kv4);
  v409  =  Kv3_m;; 
i_Kv3  =  (comp47_gbar_Kv3 * v409 * v409 * v409 * v409) * (v - comp47_e_Kv3);
  v410  =  Kv1_m;; 
i_Kv1  =  (comp19_gbar_Kv1 * v410 * v410 * v410 * v410) * (v - comp19_e_Kv1);
  v411  =  comp193_CaBK_z;; 
i_CaBK  =  (comp193_gbar_CaBK * v411 * v411 * CaBK_m * CaBK_h) * (v - comp193_e_CaBK);
  ik  =  i_Kv4 + i_Kv3 + i_Kv1 + i_CaBK;
  i_CaP  =  comp172_pca_CaP * CaP_m;
  ica  =  i_CaP;
  i_comp75  =  comp47_i_gate_Kv3;
  i_Leak  =  comp169_gbar_Leak * (v - comp169_e_Leak);
  i_Ih  =  (comp141_gbar_Ih * Ih_m) * (v - comp141_e_Ih);
  i  =  i_comp75 + i_Leak + i_Ih;
  i_Narsg  =  (Narsg_gbar * Narsg_Na_z) * (v - Narsg_e);
  i_Na  =  (Na_gbar * Na_Na_z) * (v - Na_e);
  ina  =  i_Narsg + i_Na;
  f[0]  =  -((-node.B_.I_stim_) + ica + i + ik + ina) / comp17_C_m;
  

  return GSL_SUCCESS;
}


RecordablesMap<AKP06> AKP06::recordablesMap_;
template <> void RecordablesMap<AKP06>::create()
{
  insert_("Kv3_mO", &AKP06::get_y_elem_<AKP06::State_::KV3_MO>);
  insert_("comp193_CaBK_zO", &AKP06::get_y_elem_<AKP06::State_::COMP193_CABK_ZO>);
  insert_("Kv1_mO", &AKP06::get_y_elem_<AKP06::State_::KV1_MO>);
  insert_("comp18_ca", &AKP06::get_y_elem_<AKP06::State_::COMP18_CA>);
  insert_("Kv4_hO", &AKP06::get_y_elem_<AKP06::State_::KV4_HO>);
  insert_("Kv4_mO", &AKP06::get_y_elem_<AKP06::State_::KV4_MO>);
  insert_("CaP_m", &AKP06::get_y_elem_<AKP06::State_::CAP_M>);
  insert_("Ih_m", &AKP06::get_y_elem_<AKP06::State_::IH_M>);
  insert_("CaBK_h", &AKP06::get_y_elem_<AKP06::State_::CABK_H>);
  insert_("CaBK_m", &AKP06::get_y_elem_<AKP06::State_::CABK_M>);
  insert_("Narsg_Na_zC5", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZC5>);
  insert_("Narsg_Na_zI5", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZI5>);
  insert_("Narsg_Na_zC4", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZC4>);
  insert_("Narsg_Na_zI4", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZI4>);
  insert_("Narsg_Na_zC3", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZC3>);
  insert_("Narsg_Na_zI3", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZI3>);
  insert_("Narsg_Na_zC2", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZC2>);
  insert_("Narsg_Na_zI2", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZI2>);
  insert_("Narsg_Na_zC1", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZC1>);
  insert_("Narsg_Na_zI1", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZI1>);
  insert_("Narsg_Na_zI6", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZI6>);
  insert_("Narsg_Na_zO", &AKP06::get_y_elem_<AKP06::State_::NARSG_NA_ZO>);
  insert_("Na_Na_zC5", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZC5>);
  insert_("Na_Na_zI5", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZI5>);
  insert_("Na_Na_zC4", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZC4>);
  insert_("Na_Na_zI4", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZI4>);
  insert_("Na_Na_zC3", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZC3>);
  insert_("Na_Na_zI3", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZI3>);
  insert_("Na_Na_zC2", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZC2>);
  insert_("Na_Na_zI2", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZI2>);
  insert_("Na_Na_zC1", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZC1>);
  insert_("Na_Na_zI1", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZI1>);
  insert_("Na_Na_zI6", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZI6>);
  insert_("Na_Na_zO", &AKP06::get_y_elem_<AKP06::State_::NA_NA_ZO>);
  insert_("v", &AKP06::get_y_elem_<AKP06::State_::V>);
  insert_(names::V_m, &AKP06::get_y_elem_<AKP06::State_::V>);
}




AKP06::Parameters_::Parameters_ () :
  Narsg_gbar  (16.0),
Na_Na_Ooff  (0.005),
comp47_e0  (1.60217646e-19),
Na_Na_alpha  (150.0),
comp18_ca_depth  (0.1),
Narsg_Na_delta  (40.0),
Narsg_Na_epsilon  (1.75),
Narsg_Na_x6  (-25.0),
Narsg_Na_x5  (1000000000000.0),
Narsg_Na_x4  (-1000000000000.0),
comp47_gbar_Kv3  (5.0),
Narsg_Na_x3  (1000000000000.0),
Narsg_Na_x2  (-20.0),
Narsg_Na_alfac  (3.49963551158058),
Narsg_Na_x1  (20.0),
Narsg_Na_beta  (3.0),
Narsg_Na_Oon  (0.75),
celsius  (24.0),
Na_Na_x6  (-25.0),
comp172_cao  (2.4),
Na_Na_x5  (1000000000000.0),
Na_Na_x4  (-1000000000000.0),
Narsg_Na_Coff  (0.5),
Na_Na_x3  (1000000000000.0),
Na_Na_x2  (-20.0),
Na_Na_x1  (20.0),
comp169_e_Leak  (-61.0),
Na_Na_beta  (3.0),
Narsg_Na_alpha  (150.0),
Na_Na_epsilon  (1e-12),
Na_Na_Coff  (0.5),
Na_Na_btfac  (0.316227766016838),
comp141_gbar_Ih  (0.2),
Narsg_Na_Con  (0.005),
comp47_nc  (312500000000.0),
comp19_gbar_Kv1  (11.0),
Narsg_Na_btfac  (0.316227766016838),
Narsg_Na_zeta  (0.03),
Na_Na_Oon  (2.3),
comp17_C_m  (1.0),
temp_adj  (1.24573093961552),
Narsg_Na_gbar  (16.0),
comp18_F  (96485.0),
Na_Na_zeta  (0.03),
Na_e  (-88.0),
Na_Na_gamma  (150.0),
comp91_e_Kv4  (-85.0),
Na_Na_gbar  (14.0),
Narsg_e  (-88.0),
comp47_zn  (1.9196),
comp141_e_Ih  (-30.0),
comp172_pcabar_CaP  (16.67),
comp193_e_CaBK  (-85.0),
comp18_ca0  (0.0001),
Vrest  (-68.0),
comp47_switch_Kv3  (0.0),
comp47_gunit  (16.0),
Na_Na_Con  (0.005),
comp19_e_Kv1  (-85.0),
comp169_gbar_Leak  (0.09),
Narsg_Na_gamma  (150.0),
comp47_e_Kv3  (-85.0),
Na_gbar  (14.0),
comp91_gbar_Kv4  (3.9),
Na_Na_delta  (40.0),
Narsg_Na_Ooff  (0.005),
Na_Na_alfac  (4.63115650669757),
comp193_CaBK_ztau  (1.0),
comp193_gbar_CaBK  (14.0),
comp18_ca_beta  (1.0)
{}


AKP06::State_::State_ (const Parameters_& p) : r_(0)
{
  double v414, v413, v417, v416, v418, v419, v420, v421, temp_adj, v, CaBK_m_tau, Na_Na_x4, Na_Na_delta, Na_b0O, comp172_cao, comp18_ca, comp18_cac, cai, celsius, comp172_pcabar_CaP, comp172_pca_CaP, Na_Na_Ooff, Na_bin, Na_Na_x6, Na_Na_zeta, Na_bip, Narsg_Na_x2, Narsg_Na_beta, Narsg_b01, Narsg_b02, Narsg_b03, Narsg_b04, Na_b1n, Narsg_Na_Coff, Narsg_bi1, Narsg_Na_btfac, Narsg_bi2, Narsg_bi3, Narsg_bi4, Narsg_bi5, Narsg_b11, Narsg_b12, Narsg_b13, Narsg_b14, Narsg_Na_x4, Narsg_Na_delta, Narsg_b0O, CaBK_m_inf, Na_Na_x1, Na_Na_alpha, Na_f01, Na_f02, Na_f03, Na_f04, Na_Na_Con, Na_fi1, Na_Na_alfac, Na_fi2, Na_fi3, Na_fi4, Na_fi5, CaBK_h_tau, Na_f11, Na_f12, Na_f13, Na_f14, Narsg_Na_Ooff, Narsg_bin, CaP_m_tau, Narsg_Na_x6, Narsg_Na_zeta, Narsg_bip, Ih_m_tau, Narsg_b1n, Na_Na_x3, Na_Na_gamma, Na_f0O, Kv3_m, comp47_zn, comp47_e0, comp47_nc, comp47_switch_Kv3, comp47_i_gate_Kv3, comp193_CaBK_ztau, comp193_CaBK_alpha, Na_Na_Oon, Na_fin, Na_Na_x5, Na_Na_epsilon, Na_fip, Narsg_Na_x1, Narsg_Na_alpha, Narsg_f01, Narsg_f02, Narsg_f03, Narsg_f04, Na_f1n, Narsg_Na_Con, Narsg_fi1, Narsg_Na_alfac, Narsg_fi2, Narsg_fi3, Narsg_fi4, Narsg_fi5, Narsg_f11, Narsg_f12, Narsg_f13, Narsg_f14, CaBK_h_inf, comp193_CaBK_beta, Narsg_Na_x3, Narsg_Na_gamma, Narsg_f0O, CaP_m_inf, Ih_m_inf, Narsg_Na_Oon, Narsg_fin, Narsg_Na_x5, Narsg_Na_epsilon, Narsg_fip, Narsg_f1n, Na_Na_x2, Na_Na_beta, Na_b01, Na_b02, Na_b03, Na_b04, Na_Na_Coff, Na_bi1, Na_Na_btfac, Na_bi2, Na_bi3, Na_bi4, Na_bi5, Na_b11, Na_b12, Na_b13, Na_b14, Kv4_m, Kv4_mO, Kv4_h, Kv4_hO, Kv1_m, Kv1_mO, comp193_CaBK_z, comp193_CaBK_zO, Kv3_mO, CaBK_m, CaBK_h, Ih_m, CaP_m, Narsg_Na_zC5, Narsg_Na_zI5, Narsg_Na_zC4, Narsg_Na_zI4, Narsg_Na_zC3, Narsg_Na_zI3, Narsg_Na_zC2, Narsg_Na_zI2, Narsg_Na_zC1, Narsg_Na_zI1, Narsg_Na_zI6, Narsg_Na_zO, Na_Na_zC5, Na_Na_zI5, Na_Na_zC4, Na_Na_zI4, Na_Na_zC3, Na_Na_zI3, Na_Na_zC2, Na_Na_zI2, Na_Na_zC1, Na_Na_zI1, Na_Na_zI6, Na_Na_zO, i_Kv4, i_Kv3, i_Kv1, i_CaBK, ik, i_CaP, ica, i_comp75, i_Leak, i_Ih, i, i_Narsg, i_Na, ina, Narsg_gbar, comp18_ca_depth, comp47_gbar_Kv3, comp169_e_Leak, comp141_gbar_Ih, comp19_gbar_Kv1, comp17_C_m, Narsg_Na_gbar, comp18_F, Na_e, comp91_e_Kv4, Na_Na_gbar, Narsg_e, comp141_e_Ih, comp193_e_CaBK, comp18_ca0, Vrest, comp47_gunit, comp19_e_Kv1, comp169_gbar_Leak, comp47_e_Kv3, Na_gbar, comp91_gbar_Kv4, comp193_gbar_CaBK, comp18_ca_beta, Narsg_Na_z, Na_Na_z ;
  Narsg_gbar  =  p.Narsg_gbar;
  Na_Na_Ooff  =  p.Na_Na_Ooff;
  comp47_e0  =  p.comp47_e0;
  Na_Na_alpha  =  p.Na_Na_alpha;
  comp18_ca_depth  =  p.comp18_ca_depth;
  Narsg_Na_delta  =  p.Narsg_Na_delta;
  Narsg_Na_epsilon  =  p.Narsg_Na_epsilon;
  Narsg_Na_x6  =  p.Narsg_Na_x6;
  Narsg_Na_x5  =  p.Narsg_Na_x5;
  Narsg_Na_x4  =  p.Narsg_Na_x4;
  comp47_gbar_Kv3  =  p.comp47_gbar_Kv3;
  Narsg_Na_x3  =  p.Narsg_Na_x3;
  Narsg_Na_x2  =  p.Narsg_Na_x2;
  Narsg_Na_alfac  =  p.Narsg_Na_alfac;
  Narsg_Na_x1  =  p.Narsg_Na_x1;
  Narsg_Na_beta  =  p.Narsg_Na_beta;
  Narsg_Na_Oon  =  p.Narsg_Na_Oon;
  celsius  =  p.celsius;
  Na_Na_x6  =  p.Na_Na_x6;
  comp172_cao  =  p.comp172_cao;
  Na_Na_x5  =  p.Na_Na_x5;
  Na_Na_x4  =  p.Na_Na_x4;
  Narsg_Na_Coff  =  p.Narsg_Na_Coff;
  Na_Na_x3  =  p.Na_Na_x3;
  Na_Na_x2  =  p.Na_Na_x2;
  Na_Na_x1  =  p.Na_Na_x1;
  comp169_e_Leak  =  p.comp169_e_Leak;
  Na_Na_beta  =  p.Na_Na_beta;
  Narsg_Na_alpha  =  p.Narsg_Na_alpha;
  Na_Na_epsilon  =  p.Na_Na_epsilon;
  Na_Na_Coff  =  p.Na_Na_Coff;
  Na_Na_btfac  =  p.Na_Na_btfac;
  comp141_gbar_Ih  =  p.comp141_gbar_Ih;
  Narsg_Na_Con  =  p.Narsg_Na_Con;
  comp47_nc  =  p.comp47_nc;
  comp19_gbar_Kv1  =  p.comp19_gbar_Kv1;
  Narsg_Na_btfac  =  p.Narsg_Na_btfac;
  Narsg_Na_zeta  =  p.Narsg_Na_zeta;
  Na_Na_Oon  =  p.Na_Na_Oon;
  comp17_C_m  =  p.comp17_C_m;
  temp_adj  =  p.temp_adj;
  Narsg_Na_gbar  =  p.Narsg_Na_gbar;
  comp18_F  =  p.comp18_F;
  Na_Na_zeta  =  p.Na_Na_zeta;
  Na_e  =  p.Na_e;
  Na_Na_gamma  =  p.Na_Na_gamma;
  comp91_e_Kv4  =  p.comp91_e_Kv4;
  Na_Na_gbar  =  p.Na_Na_gbar;
  Narsg_e  =  p.Narsg_e;
  comp47_zn  =  p.comp47_zn;
  comp141_e_Ih  =  p.comp141_e_Ih;
  comp172_pcabar_CaP  =  p.comp172_pcabar_CaP;
  comp193_e_CaBK  =  p.comp193_e_CaBK;
  comp18_ca0  =  p.comp18_ca0;
  Vrest  =  p.Vrest;
  comp47_switch_Kv3  =  p.comp47_switch_Kv3;
  comp47_gunit  =  p.comp47_gunit;
  Na_Na_Con  =  p.Na_Na_Con;
  comp19_e_Kv1  =  p.comp19_e_Kv1;
  comp169_gbar_Leak  =  p.comp169_gbar_Leak;
  Narsg_Na_gamma  =  p.Narsg_Na_gamma;
  comp47_e_Kv3  =  p.comp47_e_Kv3;
  Na_gbar  =  p.Na_gbar;
  comp91_gbar_Kv4  =  p.comp91_gbar_Kv4;
  Na_Na_delta  =  p.Na_Na_delta;
  Narsg_Na_Ooff  =  p.Narsg_Na_Ooff;
  Na_Na_alfac  =  p.Na_Na_alfac;
  comp193_CaBK_ztau  =  p.comp193_CaBK_ztau;
  comp193_gbar_CaBK  =  p.comp193_gbar_CaBK;
  comp18_ca_beta  =  p.comp18_ca_beta;
  v  =  Vrest;
  CaBK_m_tau  =  comp193_CaBK_mtau(v) / temp_adj;
  Na_b0O  =  Na_Na_delta * exp(v / Na_Na_x4) * temp_adj;
  comp18_ca  =  0.0001;
  if (comp18_ca < 0.0001) {v417  =  0.0001;} else {v417  =  comp18_ca;}; 
v416  =  v417;; comp18_cac  =  v416;
  cai  =  comp18_cac;
  comp172_pca_CaP  =  comp172_pcabar_CaP * ghk(v, celsius, cai, comp172_cao);
  Na_bin  =  Na_Na_Ooff * temp_adj;
  Na_bip  =  Na_Na_zeta * exp(v / Na_Na_x6) * temp_adj;
  Narsg_b01  =  Narsg_Na_beta * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b02  =  2.0 * Narsg_Na_beta * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b03  =  3.0 * Narsg_Na_beta * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b04  =  4.0 * Narsg_Na_beta * exp(v / Narsg_Na_x2) * temp_adj;
  Na_b1n  =  Na_Na_delta * exp(v / Na_Na_x4) * temp_adj;
  Narsg_bi1  =  Narsg_Na_Coff * temp_adj;
  Narsg_bi2  =  Narsg_Na_Coff * Narsg_Na_btfac * temp_adj;
  Narsg_bi3  =  Narsg_Na_Coff * Narsg_Na_btfac * Narsg_Na_btfac * temp_adj;
  Narsg_bi4  =  Narsg_Na_Coff * Narsg_Na_btfac * Narsg_Na_btfac * Narsg_Na_btfac * temp_adj;
  Narsg_bi5  =  Narsg_Na_Coff * Narsg_Na_btfac * Narsg_Na_btfac * Narsg_Na_btfac * Narsg_Na_btfac * temp_adj;
  Narsg_b11  =  Narsg_Na_beta * Narsg_Na_btfac * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b12  =  2.0 * Narsg_Na_beta * Narsg_Na_btfac * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b13  =  3.0 * Narsg_Na_beta * Narsg_Na_btfac * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b14  =  4.0 * Narsg_Na_beta * Narsg_Na_btfac * exp(v / Narsg_Na_x2) * temp_adj;
  Narsg_b0O  =  Narsg_Na_delta * exp(v / Narsg_Na_x4) * temp_adj;
  CaBK_m_inf  =  comp193_CaBK_minf(v) / temp_adj;
  Na_f01  =  4.0 * Na_Na_alpha * exp(v / Na_Na_x1) * temp_adj;
  Na_f02  =  3.0 * Na_Na_alpha * exp(v / Na_Na_x1) * temp_adj;
  Na_f03  =  2.0 * Na_Na_alpha * exp(v / Na_Na_x1) * temp_adj;
  Na_f04  =  Na_Na_alpha * exp(v / Na_Na_x1) * temp_adj;
  Na_fi1  =  Na_Na_Con * temp_adj;
  Na_fi2  =  Na_Na_Con * Na_Na_alfac * temp_adj;
  Na_fi3  =  Na_Na_Con * Na_Na_alfac * Na_Na_alfac * temp_adj;
  Na_fi4  =  Na_Na_Con * Na_Na_alfac * Na_Na_alfac * Na_Na_alfac * temp_adj;
  Na_fi5  =  Na_Na_Con * Na_Na_alfac * Na_Na_alfac * Na_Na_alfac * Na_Na_alfac * temp_adj;
  CaBK_h_tau  =  comp193_CaBK_htau(v) / temp_adj;
  Na_f11  =  4.0 * Na_Na_alpha * Na_Na_alfac * exp(v / Na_Na_x1) * temp_adj;
  Na_f12  =  3.0 * Na_Na_alpha * Na_Na_alfac * exp(v / Na_Na_x1) * temp_adj;
  Na_f13  =  2.0 * Na_Na_alpha * Na_Na_alfac * exp(v / Na_Na_x1) * temp_adj;
  Na_f14  =  Na_Na_alpha * Na_Na_alfac * exp(v / Na_Na_x1) * temp_adj;
  Narsg_bin  =  Narsg_Na_Ooff * temp_adj;
  CaP_m_tau  =  comp172_CaP_tau(v) / temp_adj;
  Narsg_bip  =  Narsg_Na_zeta * exp(v / Narsg_Na_x6) * temp_adj;
  Ih_m_tau  =  comp141_Ih_tau(v) / temp_adj;
  Narsg_b1n  =  Narsg_Na_delta * exp(v / Narsg_Na_x4) * temp_adj;
  Na_f0O  =  Na_Na_gamma * exp(v / Na_Na_x3) * temp_adj;
  Kv3_m  =  0.019368887751814;
  if (comp47_switch_Kv3 > 0.0) 
      {v414  =  comp47_nc * 1000000.0 * comp47_e0 * 4.0 * comp47_zn * comp47_gate_flip_Kv3(v, Kv3_m);} 
      else 
        {v414  =  0.0;}; 
v413  =  v414;; comp47_i_gate_Kv3  =  v413;
  comp193_CaBK_alpha  =  comp193_CaBK_zinf(cai) / comp193_CaBK_ztau;
  Na_fin  =  Na_Na_Oon * temp_adj;
  Na_fip  =  Na_Na_epsilon * exp(v / Na_Na_x5) * temp_adj;
  Narsg_f01  =  4.0 * Narsg_Na_alpha * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f02  =  3.0 * Narsg_Na_alpha * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f03  =  2.0 * Narsg_Na_alpha * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f04  =  Narsg_Na_alpha * exp(v / Narsg_Na_x1) * temp_adj;
  Na_f1n  =  Na_Na_gamma * exp(v / Na_Na_x3) * temp_adj;
  Narsg_fi1  =  Narsg_Na_Con * temp_adj;
  Narsg_fi2  =  Narsg_Na_Con * Narsg_Na_alfac * temp_adj;
  Narsg_fi3  =  Narsg_Na_Con * Narsg_Na_alfac * Narsg_Na_alfac * temp_adj;
  Narsg_fi4  =  Narsg_Na_Con * Narsg_Na_alfac * Narsg_Na_alfac * Narsg_Na_alfac * temp_adj;
  Narsg_fi5  =  Narsg_Na_Con * Narsg_Na_alfac * Narsg_Na_alfac * Narsg_Na_alfac * Narsg_Na_alfac * temp_adj;
  Narsg_f11  =  4.0 * Narsg_Na_alpha * Narsg_Na_alfac * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f12  =  3.0 * Narsg_Na_alpha * Narsg_Na_alfac * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f13  =  2.0 * Narsg_Na_alpha * Narsg_Na_alfac * exp(v / Narsg_Na_x1) * temp_adj;
  Narsg_f14  =  Narsg_Na_alpha * Narsg_Na_alfac * exp(v / Narsg_Na_x1) * temp_adj;
  CaBK_h_inf  =  comp193_CaBK_hinf(v) / temp_adj;
  comp193_CaBK_beta  =  (1.0 + -(comp193_CaBK_zinf(cai))) / comp193_CaBK_ztau;
  Narsg_f0O  =  Narsg_Na_gamma * exp(v / Narsg_Na_x3) * temp_adj;
  CaP_m_inf  =  comp172_CaP_inf(v);
  Ih_m_inf  =  comp141_Ih_inf(v);
  Narsg_fin  =  Narsg_Na_Oon * temp_adj;
  Narsg_fip  =  Narsg_Na_epsilon * exp(v / Narsg_Na_x5) * temp_adj;
  Narsg_f1n  =  Narsg_Na_gamma * exp(v / Narsg_Na_x3) * temp_adj;
  Na_b01  =  Na_Na_beta * exp(v / Na_Na_x2) * temp_adj;
  Na_b02  =  2.0 * Na_Na_beta * exp(v / Na_Na_x2) * temp_adj;
  Na_b03  =  3.0 * Na_Na_beta * exp(v / Na_Na_x2) * temp_adj;
  Na_b04  =  4.0 * Na_Na_beta * exp(v / Na_Na_x2) * temp_adj;
  Na_bi1  =  Na_Na_Coff * temp_adj;
  Na_bi2  =  Na_Na_Coff * Na_Na_btfac * temp_adj;
  Na_bi3  =  Na_Na_Coff * Na_Na_btfac * Na_Na_btfac * temp_adj;
  Na_bi4  =  Na_Na_Coff * Na_Na_btfac * Na_Na_btfac * Na_Na_btfac * temp_adj;
  Na_bi5  =  Na_Na_Coff * Na_Na_btfac * Na_Na_btfac * Na_Na_btfac * Na_Na_btfac * temp_adj;
  Na_b11  =  Na_Na_beta * Na_Na_btfac * exp(v / Na_Na_x2) * temp_adj;
  Na_b12  =  2.0 * Na_Na_beta * Na_Na_btfac * exp(v / Na_Na_x2) * temp_adj;
  Na_b13  =  3.0 * Na_Na_beta * Na_Na_btfac * exp(v / Na_Na_x2) * temp_adj;
  Na_b14  =  4.0 * Na_Na_beta * Na_Na_btfac * exp(v / Na_Na_x2) * temp_adj;
  Kv4_m  =  0.34641264037007;
  Kv4_mO  =  Kv4_m;
  Kv4_h  =  0.493672083654485;
  Kv4_hO  =  Kv4_h;
  Kv1_m  =  0.0737822020422147;
  Kv1_mO  =  Kv1_m;
  comp193_CaBK_z  =  0.0909090909090909;
  comp193_CaBK_zO  =  comp193_CaBK_z;
  Kv3_mO  =  Kv3_m;
  CaBK_m  =  0.00326726870663768;
  CaBK_h  =  0.799252570696669;
  Ih_m  =  0.0968851713304939;
  CaP_m  =  0.000135136381706817;
  y_[29]  =  Kv4_mO;
  y_[30]  =  Kv4_hO;
  y_[31]  =  comp18_ca;
  y_[32]  =  Kv1_mO;
  y_[33]  =  comp193_CaBK_zO;
  y_[34]  =  Kv3_mO;
  y_[25]  =  CaBK_m;
  y_[26]  =  CaBK_h;
  y_[27]  =  Ih_m;
  y_[28]  =  CaP_m;
  Narsg_Na_z  =  Narsg_Na_zO;
  Na_Na_z  =  Na_Na_zO;
  v418  =  Kv4_m;; 
i_Kv4  =  (comp91_gbar_Kv4 * v418 * v418 * v418 * v418 * Kv4_h) * (v - comp91_e_Kv4);
  v419  =  Kv3_m;; 
i_Kv3  =  (comp47_gbar_Kv3 * v419 * v419 * v419 * v419) * (v - comp47_e_Kv3);
  v420  =  Kv1_m;; 
i_Kv1  =  (comp19_gbar_Kv1 * v420 * v420 * v420 * v420) * (v - comp19_e_Kv1);
  v421  =  comp193_CaBK_z;; 
i_CaBK  =  (comp193_gbar_CaBK * v421 * v421 * CaBK_m * CaBK_h) * (v - comp193_e_CaBK);
  ik  =  i_Kv4 + i_Kv3 + i_Kv1 + i_CaBK;
  i_CaP  =  comp172_pca_CaP * CaP_m;
  ica  =  i_CaP;
  i_comp75  =  comp47_i_gate_Kv3;
  i_Leak  =  comp169_gbar_Leak * (v - comp169_e_Leak);
  i_Ih  =  (comp141_gbar_Ih * Ih_m) * (v - comp141_e_Ih);
  i  =  i_comp75 + i_Leak + i_Ih;
  i_Narsg  =  (Narsg_gbar * Narsg_Na_z) * (v - Narsg_e);
  i_Na  =  (Na_gbar * Na_Na_z) * (v - Na_e);
  ina  =  i_Narsg + i_Na;
  y_[0]  =  -(ica + i + ik + ina) / comp17_C_m;
}


AKP06::State_::State_ (const State_& s) : r_(s.r_)
{
  for ( int i = 0 ; i < 35 ; ++i ) y_[i] = s.y_[i];
}


AKP06::State_& AKP06::State_::operator=(const State_& s)
{
     assert(this != &s);  
     for ( size_t i = 0 ; i < 35 ; ++i )
       y_[i] = s.y_[i];
     r_ = s.r_;
     return *this;
}




void AKP06::Parameters_::get (DictionaryDatum &d) const
{
  def<double_t>(d, "Narsg_gbar", Narsg_gbar);
  def<double_t>(d, "Na_Na_Ooff", Na_Na_Ooff);
  def<double_t>(d, "comp47_e0", comp47_e0);
  def<double_t>(d, "Na_Na_alpha", Na_Na_alpha);
  def<double_t>(d, "comp18_ca_depth", comp18_ca_depth);
  def<double_t>(d, "Narsg_Na_delta", Narsg_Na_delta);
  def<double_t>(d, "Narsg_Na_epsilon", Narsg_Na_epsilon);
  def<double_t>(d, "Narsg_Na_x6", Narsg_Na_x6);
  def<double_t>(d, "Narsg_Na_x5", Narsg_Na_x5);
  def<double_t>(d, "Narsg_Na_x4", Narsg_Na_x4);
  def<double_t>(d, "comp47_gbar_Kv3", comp47_gbar_Kv3);
  def<double_t>(d, "Narsg_Na_x3", Narsg_Na_x3);
  def<double_t>(d, "Narsg_Na_x2", Narsg_Na_x2);
  def<double_t>(d, "Narsg_Na_alfac", Narsg_Na_alfac);
  def<double_t>(d, "Narsg_Na_x1", Narsg_Na_x1);
  def<double_t>(d, "Narsg_Na_beta", Narsg_Na_beta);
  def<double_t>(d, "Narsg_Na_Oon", Narsg_Na_Oon);
  def<double_t>(d, "celsius", celsius);
  def<double_t>(d, "Na_Na_x6", Na_Na_x6);
  def<double_t>(d, "comp172_cao", comp172_cao);
  def<double_t>(d, "Na_Na_x5", Na_Na_x5);
  def<double_t>(d, "Na_Na_x4", Na_Na_x4);
  def<double_t>(d, "Narsg_Na_Coff", Narsg_Na_Coff);
  def<double_t>(d, "Na_Na_x3", Na_Na_x3);
  def<double_t>(d, "Na_Na_x2", Na_Na_x2);
  def<double_t>(d, "Na_Na_x1", Na_Na_x1);
  def<double_t>(d, "comp169_e_Leak", comp169_e_Leak);
  def<double_t>(d, "Na_Na_beta", Na_Na_beta);
  def<double_t>(d, "Narsg_Na_alpha", Narsg_Na_alpha);
  def<double_t>(d, "Na_Na_epsilon", Na_Na_epsilon);
  def<double_t>(d, "Na_Na_Coff", Na_Na_Coff);
  def<double_t>(d, "Na_Na_btfac", Na_Na_btfac);
  def<double_t>(d, "comp141_gbar_Ih", comp141_gbar_Ih);
  def<double_t>(d, "Narsg_Na_Con", Narsg_Na_Con);
  def<double_t>(d, "comp47_nc", comp47_nc);
  def<double_t>(d, "comp19_gbar_Kv1", comp19_gbar_Kv1);
  def<double_t>(d, "Narsg_Na_btfac", Narsg_Na_btfac);
  def<double_t>(d, "Narsg_Na_zeta", Narsg_Na_zeta);
  def<double_t>(d, "Na_Na_Oon", Na_Na_Oon);
  def<double_t>(d, "comp17_C_m", comp17_C_m);
  def<double_t>(d, "temp_adj", temp_adj);
  def<double_t>(d, "Narsg_Na_gbar", Narsg_Na_gbar);
  def<double_t>(d, "comp18_F", comp18_F);
  def<double_t>(d, "Na_Na_zeta", Na_Na_zeta);
  def<double_t>(d, "Na_e", Na_e);
  def<double_t>(d, "Na_Na_gamma", Na_Na_gamma);
  def<double_t>(d, "comp91_e_Kv4", comp91_e_Kv4);
  def<double_t>(d, "Na_Na_gbar", Na_Na_gbar);
  def<double_t>(d, "Narsg_e", Narsg_e);
  def<double_t>(d, "comp47_zn", comp47_zn);
  def<double_t>(d, "comp141_e_Ih", comp141_e_Ih);
  def<double_t>(d, "comp172_pcabar_CaP", comp172_pcabar_CaP);
  def<double_t>(d, "comp193_e_CaBK", comp193_e_CaBK);
  def<double_t>(d, "comp18_ca0", comp18_ca0);
  def<double_t>(d, "Vrest", Vrest);
  def<double_t>(d, "comp47_switch_Kv3", comp47_switch_Kv3);
  def<double_t>(d, "comp47_gunit", comp47_gunit);
  def<double_t>(d, "Na_Na_Con", Na_Na_Con);
  def<double_t>(d, "comp19_e_Kv1", comp19_e_Kv1);
  def<double_t>(d, "comp169_gbar_Leak", comp169_gbar_Leak);
  def<double_t>(d, "Narsg_Na_gamma", Narsg_Na_gamma);
  def<double_t>(d, "comp47_e_Kv3", comp47_e_Kv3);
  def<double_t>(d, "Na_gbar", Na_gbar);
  def<double_t>(d, "comp91_gbar_Kv4", comp91_gbar_Kv4);
  def<double_t>(d, "Na_Na_delta", Na_Na_delta);
  def<double_t>(d, "Narsg_Na_Ooff", Narsg_Na_Ooff);
  def<double_t>(d, "Na_Na_alfac", Na_Na_alfac);
  def<double_t>(d, "comp193_CaBK_ztau", comp193_CaBK_ztau);
  def<double_t>(d, "comp193_gbar_CaBK", comp193_gbar_CaBK);
  def<double_t>(d, "comp18_ca_beta", comp18_ca_beta);
}


void AKP06::Parameters_::set (const DictionaryDatum &d)
{
  updateValue<double_t>(d, "Narsg_gbar", Narsg_gbar);
  updateValue<double_t>(d, "Na_Na_Ooff", Na_Na_Ooff);
  updateValue<double_t>(d, "comp47_e0", comp47_e0);
  updateValue<double_t>(d, "Na_Na_alpha", Na_Na_alpha);
  updateValue<double_t>(d, "comp18_ca_depth", comp18_ca_depth);
  updateValue<double_t>(d, "Narsg_Na_delta", Narsg_Na_delta);
  updateValue<double_t>(d, "Narsg_Na_epsilon", Narsg_Na_epsilon);
  updateValue<double_t>(d, "Narsg_Na_x6", Narsg_Na_x6);
  updateValue<double_t>(d, "Narsg_Na_x5", Narsg_Na_x5);
  updateValue<double_t>(d, "Narsg_Na_x4", Narsg_Na_x4);
  updateValue<double_t>(d, "comp47_gbar_Kv3", comp47_gbar_Kv3);
  updateValue<double_t>(d, "Narsg_Na_x3", Narsg_Na_x3);
  updateValue<double_t>(d, "Narsg_Na_x2", Narsg_Na_x2);
  updateValue<double_t>(d, "Narsg_Na_alfac", Narsg_Na_alfac);
  updateValue<double_t>(d, "Narsg_Na_x1", Narsg_Na_x1);
  updateValue<double_t>(d, "Narsg_Na_beta", Narsg_Na_beta);
  updateValue<double_t>(d, "Narsg_Na_Oon", Narsg_Na_Oon);
  updateValue<double_t>(d, "celsius", celsius);
  updateValue<double_t>(d, "Na_Na_x6", Na_Na_x6);
  updateValue<double_t>(d, "comp172_cao", comp172_cao);
  updateValue<double_t>(d, "Na_Na_x5", Na_Na_x5);
  updateValue<double_t>(d, "Na_Na_x4", Na_Na_x4);
  updateValue<double_t>(d, "Narsg_Na_Coff", Narsg_Na_Coff);
  updateValue<double_t>(d, "Na_Na_x3", Na_Na_x3);
  updateValue<double_t>(d, "Na_Na_x2", Na_Na_x2);
  updateValue<double_t>(d, "Na_Na_x1", Na_Na_x1);
  updateValue<double_t>(d, "comp169_e_Leak", comp169_e_Leak);
  updateValue<double_t>(d, "Na_Na_beta", Na_Na_beta);
  updateValue<double_t>(d, "Narsg_Na_alpha", Narsg_Na_alpha);
  updateValue<double_t>(d, "Na_Na_epsilon", Na_Na_epsilon);
  updateValue<double_t>(d, "Na_Na_Coff", Na_Na_Coff);
  updateValue<double_t>(d, "Na_Na_btfac", Na_Na_btfac);
  updateValue<double_t>(d, "comp141_gbar_Ih", comp141_gbar_Ih);
  updateValue<double_t>(d, "Narsg_Na_Con", Narsg_Na_Con);
  updateValue<double_t>(d, "comp47_nc", comp47_nc);
  updateValue<double_t>(d, "comp19_gbar_Kv1", comp19_gbar_Kv1);
  updateValue<double_t>(d, "Narsg_Na_btfac", Narsg_Na_btfac);
  updateValue<double_t>(d, "Narsg_Na_zeta", Narsg_Na_zeta);
  updateValue<double_t>(d, "Na_Na_Oon", Na_Na_Oon);
  updateValue<double_t>(d, "comp17_C_m", comp17_C_m);
  updateValue<double_t>(d, "temp_adj", temp_adj);
  updateValue<double_t>(d, "Narsg_Na_gbar", Narsg_Na_gbar);
  updateValue<double_t>(d, "comp18_F", comp18_F);
  updateValue<double_t>(d, "Na_Na_zeta", Na_Na_zeta);
  updateValue<double_t>(d, "Na_e", Na_e);
  updateValue<double_t>(d, "Na_Na_gamma", Na_Na_gamma);
  updateValue<double_t>(d, "comp91_e_Kv4", comp91_e_Kv4);
  updateValue<double_t>(d, "Na_Na_gbar", Na_Na_gbar);
  updateValue<double_t>(d, "Narsg_e", Narsg_e);
  updateValue<double_t>(d, "comp47_zn", comp47_zn);
  updateValue<double_t>(d, "comp141_e_Ih", comp141_e_Ih);
  updateValue<double_t>(d, "comp172_pcabar_CaP", comp172_pcabar_CaP);
  updateValue<double_t>(d, "comp193_e_CaBK", comp193_e_CaBK);
  updateValue<double_t>(d, "comp18_ca0", comp18_ca0);
  updateValue<double_t>(d, "Vrest", Vrest);
  updateValue<double_t>(d, "comp47_switch_Kv3", comp47_switch_Kv3);
  updateValue<double_t>(d, "comp47_gunit", comp47_gunit);
  updateValue<double_t>(d, "Na_Na_Con", Na_Na_Con);
  updateValue<double_t>(d, "comp19_e_Kv1", comp19_e_Kv1);
  updateValue<double_t>(d, "comp169_gbar_Leak", comp169_gbar_Leak);
  updateValue<double_t>(d, "Narsg_Na_gamma", Narsg_Na_gamma);
  updateValue<double_t>(d, "comp47_e_Kv3", comp47_e_Kv3);
  updateValue<double_t>(d, "Na_gbar", Na_gbar);
  updateValue<double_t>(d, "comp91_gbar_Kv4", comp91_gbar_Kv4);
  updateValue<double_t>(d, "Na_Na_delta", Na_Na_delta);
  updateValue<double_t>(d, "Narsg_Na_Ooff", Narsg_Na_Ooff);
  updateValue<double_t>(d, "Na_Na_alfac", Na_Na_alfac);
  updateValue<double_t>(d, "comp193_CaBK_ztau", comp193_CaBK_ztau);
  updateValue<double_t>(d, "comp193_gbar_CaBK", comp193_gbar_CaBK);
  updateValue<double_t>(d, "comp18_ca_beta", comp18_ca_beta);
}


void AKP06::State_::get (DictionaryDatum &d) const
{
  def<double_t>(d, "Kv3_mO", y_[34]);
  def<double_t>(d, "comp193_CaBK_zO", y_[33]);
  def<double_t>(d, "Kv1_mO", y_[32]);
  def<double_t>(d, "comp18_ca", y_[31]);
  def<double_t>(d, "Kv4_hO", y_[30]);
  def<double_t>(d, "Kv4_mO", y_[29]);
  def<double_t>(d, "CaP_m", y_[28]);
  def<double_t>(d, "Ih_m", y_[27]);
  def<double_t>(d, "CaBK_h", y_[26]);
  def<double_t>(d, "CaBK_m", y_[25]);
  def<double_t>(d, "Narsg_Na_zC5", y_[24]);
  def<double_t>(d, "Narsg_Na_zI5", y_[23]);
  def<double_t>(d, "Narsg_Na_zC4", y_[22]);
  def<double_t>(d, "Narsg_Na_zI4", y_[21]);
  def<double_t>(d, "Narsg_Na_zC3", y_[20]);
  def<double_t>(d, "Narsg_Na_zI3", y_[19]);
  def<double_t>(d, "Narsg_Na_zC2", y_[18]);
  def<double_t>(d, "Narsg_Na_zI2", y_[17]);
  def<double_t>(d, "Narsg_Na_zC1", y_[16]);
  def<double_t>(d, "Narsg_Na_zI1", y_[15]);
  def<double_t>(d, "Narsg_Na_zI6", y_[14]);
  def<double_t>(d, "Narsg_Na_zO", y_[13]);
  def<double_t>(d, "Na_Na_zC5", y_[12]);
  def<double_t>(d, "Na_Na_zI5", y_[11]);
  def<double_t>(d, "Na_Na_zC4", y_[10]);
  def<double_t>(d, "Na_Na_zI4", y_[9]);
  def<double_t>(d, "Na_Na_zC3", y_[8]);
  def<double_t>(d, "Na_Na_zI3", y_[7]);
  def<double_t>(d, "Na_Na_zC2", y_[6]);
  def<double_t>(d, "Na_Na_zI2", y_[5]);
  def<double_t>(d, "Na_Na_zC1", y_[4]);
  def<double_t>(d, "Na_Na_zI1", y_[3]);
  def<double_t>(d, "Na_Na_zI6", y_[2]);
  def<double_t>(d, "Na_Na_zO", y_[1]);
  def<double_t>(d, "v", y_[0]);
}


void AKP06::State_::set (const DictionaryDatum &d, const Parameters_&)
{
  updateValue<double_t>(d, "Kv3_mO", y_[34]);
  updateValue<double_t>(d, "comp193_CaBK_zO", y_[33]);
  updateValue<double_t>(d, "Kv1_mO", y_[32]);
  updateValue<double_t>(d, "comp18_ca", y_[31]);
  updateValue<double_t>(d, "Kv4_hO", y_[30]);
  updateValue<double_t>(d, "Kv4_mO", y_[29]);
  updateValue<double_t>(d, "CaP_m", y_[28]);
  updateValue<double_t>(d, "Ih_m", y_[27]);
  updateValue<double_t>(d, "CaBK_h", y_[26]);
  updateValue<double_t>(d, "CaBK_m", y_[25]);
  updateValue<double_t>(d, "Narsg_Na_zC5", y_[24]);
  updateValue<double_t>(d, "Narsg_Na_zI5", y_[23]);
  updateValue<double_t>(d, "Narsg_Na_zC4", y_[22]);
  updateValue<double_t>(d, "Narsg_Na_zI4", y_[21]);
  updateValue<double_t>(d, "Narsg_Na_zC3", y_[20]);
  updateValue<double_t>(d, "Narsg_Na_zI3", y_[19]);
  updateValue<double_t>(d, "Narsg_Na_zC2", y_[18]);
  updateValue<double_t>(d, "Narsg_Na_zI2", y_[17]);
  updateValue<double_t>(d, "Narsg_Na_zC1", y_[16]);
  updateValue<double_t>(d, "Narsg_Na_zI1", y_[15]);
  updateValue<double_t>(d, "Narsg_Na_zI6", y_[14]);
  updateValue<double_t>(d, "Narsg_Na_zO", y_[13]);
  updateValue<double_t>(d, "Na_Na_zC5", y_[12]);
  updateValue<double_t>(d, "Na_Na_zI5", y_[11]);
  updateValue<double_t>(d, "Na_Na_zC4", y_[10]);
  updateValue<double_t>(d, "Na_Na_zI4", y_[9]);
  updateValue<double_t>(d, "Na_Na_zC3", y_[8]);
  updateValue<double_t>(d, "Na_Na_zI3", y_[7]);
  updateValue<double_t>(d, "Na_Na_zC2", y_[6]);
  updateValue<double_t>(d, "Na_Na_zI2", y_[5]);
  updateValue<double_t>(d, "Na_Na_zC1", y_[4]);
  updateValue<double_t>(d, "Na_Na_zI1", y_[3]);
  updateValue<double_t>(d, "Na_Na_zI6", y_[2]);
  updateValue<double_t>(d, "Na_Na_zO", y_[1]);
  updateValue<double_t>(d, "v", y_[0]);
}




AKP06::Buffers_::Buffers_(AKP06& n)
    : logger_(n),
      s_(0),
      c_(0),
      e_(0)
{
    // Initialization of the remaining members is deferred to
    // init_buffers_().
}


AKP06::Buffers_::Buffers_(const Buffers_&, AKP06& n)
    : logger_(n),
      s_(0),
      c_(0),
      e_(0)
{
    // Initialization of the remaining members is deferred to
    // init_buffers_().
}


AKP06::AKP06()
    : Archiving_Node(), 
      P_(), 
      S_(P_),
      B_(*this)
{
    recordablesMap_.create();
}


AKP06::AKP06(const AKP06& n)
    : Archiving_Node(n), 
      P_(n.P_), 
      S_(n.S_),
      B_(n.B_, *this)
{
}
AKP06::~AKP06()
{
    // GSL structs only allocated by init_nodes_(), so we need to protect destruction
    if ( B_.s_ ) gsl_odeiv_step_free(B_.s_);
    if ( B_.c_ ) gsl_odeiv_control_free(B_.c_);
    if ( B_.e_ ) gsl_odeiv_evolve_free(B_.e_);
}


  void AKP06::init_node_(const Node& proto)
{
    const AKP06& pr = downcast<AKP06>(proto);
    P_ = pr.P_;
    S_ = pr.S_;
}


void AKP06::init_state_(const Node& proto)
{
    const AKP06& pr = downcast<AKP06>(proto);
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
      B_.s_ = gsl_odeiv_step_alloc (T1, 35);
    else 
      gsl_odeiv_step_reset(B_.s_);
    
    if ( B_.c_ == 0 )  
      B_.c_ = gsl_odeiv_control_y_new (1e-3, 0.0);
    else
      gsl_odeiv_control_init(B_.c_, 1e-3, 0.0, 1.0, 0.0);
    
    if ( B_.e_ == 0 )  
      B_.e_ = gsl_odeiv_evolve_alloc(35);
    else 
      gsl_odeiv_evolve_reset(B_.e_);
  
    B_.sys_.function  = AKP06_dynamics; 
    B_.sys_.jacobian  = 0;
    B_.sys_.dimension = 35;
    B_.sys_.params    = reinterpret_cast<void*>(this);
}


void AKP06::calibrate()
{
    B_.logger_.init();  
    V_.RefractoryCounts_ = 20;
    V_.U_old_ = S_.y_[0];
}


void AKP06::update(Time const & origin, const long_t from, const long_t to)
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




void AKP06::handle(SpikeEvent & e)
  {
    int flag;
    assert(e.get_delay() > 0);
    flag = 0;


}




void AKP06::handle(CurrentEvent& e)
  {
    assert(e.get_delay() > 0);

    const double_t c=e.get_current();
    const double_t w=e.get_weight();

    B_.currents_.add_value(e.get_rel_delivery_steps(network()->get_slice_origin()), 
			w *c);
  }

void AKP06::handle(DataLoggingRequest& e)
  {
    B_.logger_.handle(e);
  }


}


