

TITLE CGC_Ca


NEURON {
  RANGE comp0_ca
  RANGE ica, cai
  USEION ca READ ica WRITE cai
}


PARAMETER {
  comp0_cai0  =  0.0001
  comp0_cao  =  2.0
  comp0_d  =  0.2
  comp0_F  =  96485.0
  comp0_beta  =  1.5
}


STATE {
  comp0_ca
}


ASSIGNED {
  ica
  cai
  v
}


PROCEDURE pools () {
  cai = comp0_ca
}


BREAKPOINT {
  SOLVE states METHOD derivimplicit
  pools ()
}


DERIVATIVE states {
  comp0_ca'  =  
  (-(ica)) / (2.0 * comp0_F * comp0_d) + 
    -(comp0_beta * (cai + -(comp0_cai0)))
}


INITIAL {
  comp0_ca  =  0.0001
}


PROCEDURE print_state () {
  printf ("comp0_ca = %g\n" ,  comp0_ca)
}
