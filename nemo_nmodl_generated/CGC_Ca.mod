

TITLE CGC_Ca


NEURON {
  RANGE comp65_ca
  RANGE ica, cai
  USEION ca READ ica WRITE cai
}


FUNCTION linoid (x, y) {
  LOCAL v4111
  if 
    (fabs(x / y) < 1e-06) 
     {v4111  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4111  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4111
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


PARAMETER {
  comp65_beta  =  1.5
  comp65_cao  =  2.0
  comp65_cai0  =  0.0001
  fix_celsius  =  30.0
  comp65_F  =  96485.0
  comp65_d  =  0.2
}


STATE {
  comp65_ca
}


ASSIGNED {
  comp65_ica
  v
  comp65_cai
  ica
  cai
}


PROCEDURE pools () {
  cai = comp65_ca
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  pools ()
}


DERIVATIVE states {
  comp65_cai  =  cai
  comp65_ica  =  ica
  comp65_ca'  =  
  (-(comp65_ica)) / (2.0 * comp65_F * comp65_d) * 10000.0 + 
    -(comp65_beta * (comp65_cai + -(comp65_cai0)))
}


INITIAL {
  comp65_cai  =  cai
  comp65_ica  =  ica
  comp65_ca  =  0.0001
}


PROCEDURE print_state () {
  printf ("NMODL state: t = %g v = %g comp65_ca = %g\n" , t, v,  comp65_ca)
}
