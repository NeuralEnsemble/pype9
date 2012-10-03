

TITLE CGC_Lkg2


NEURON {
  RANGE comp2726_ggaba, comp2726_egaba
  RANGE i_Lkg2
  RANGE e
  NONSPECIFIC_CURRENT i
}


FUNCTION linoid (x, y) {
  LOCAL v4148
  if 
    (fabs(x / y) < 1e-06) 
     {v4148  =  y * (1.0 + -(x / y / 2.0))} 
    else {v4148  =  x / (exp(x / y) + -1.0)} 
linoid  =  v4148
}


FUNCTION sigm (x, y) {
  sigm  =  1.0 / (exp(x / y) + 1.0)
}


PARAMETER {
  fix_celsius  =  30.0
  comp2726_egaba  =  -65.0
  comp2726_ggaba  =  3e-05
}


STATE {
}


ASSIGNED {
  v
  i
  e
  i_Lkg2
}


BREAKPOINT {
  i_Lkg2  =  comp2726_ggaba * (v - comp2726_egaba)
  i  =  i_Lkg2
}


INITIAL {
  e  =  comp2726_egaba
}


PROCEDURE print_state () {
}
