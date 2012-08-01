

TITLE CGC_Lkg2


NEURON {
  RANGE comp0_egaba, comp0_ggaba
  RANGE i_Lkg2
  RANGE e
  NONSPECIFIC_CURRENT i
}


PARAMETER {
  comp0_ggaba  =  2.17e-05
  Vrest  =  -68.0
  fix_celsius  =  30.0
  comp0_egaba  =  -65.0
}


STATE {
}


ASSIGNED {
  ica
  cai
  v
  i
  e
  i_Lkg2
}


BREAKPOINT {
  i_Lkg2  =  comp0_ggaba * (v - comp0_egaba)
  i  =  i_Lkg2
}


INITIAL {
}


PROCEDURE print_state () {
}
