

TITLE CGC_Lkg1


NEURON {
  RANGE comp2635_gbar, comp2635_e
  RANGE i_Lkg1
  RANGE e
  NONSPECIFIC_CURRENT i
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


FUNCTION linoid (x, y) {
  LOCAL v4146
  if 
    (fabs(x / y) < 1e-06) 
     {v4146  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4146  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4146
}


PARAMETER {
  comp2635_e  =  -16.5
  comp2635_gbar  =  5.68e-05
  fix_celsius  =  30.0
}


STATE {
}


ASSIGNED {
  v
  i
  e
  i_Lkg1
}


BREAKPOINT {
  i_Lkg1  =  comp2635_gbar * (v - comp2635_e)
  i  =  i_Lkg1
}


INITIAL {
  e  =  comp2635_e
}


PROCEDURE print_state () {
}
