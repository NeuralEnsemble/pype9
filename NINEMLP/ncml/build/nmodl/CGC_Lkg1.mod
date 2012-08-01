

TITLE CGC_Lkg1


NEURON {
  RANGE comp0_e, comp0_gbar
  RANGE i_Lkg1
  RANGE e
  NONSPECIFIC_CURRENT i
}


PARAMETER {
  comp0_gbar  =  5.68e-05
  comp0_e  =  -58.0
  Vrest  =  -68.0
  fix_celsius  =  30.0
}


STATE {
}


ASSIGNED {
  ica
  cai
  v
  i
  e
  i_Lkg1
}


BREAKPOINT {
  i_Lkg1  =  comp0_gbar * (v - comp0_e)
  i  =  i_Lkg1
}


INITIAL {
}


PROCEDURE print_state () {
}
