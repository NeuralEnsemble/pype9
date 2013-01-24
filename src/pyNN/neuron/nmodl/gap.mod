NEURON {
  POINT_PROCESS gap
  ELECTRODE_CURRENT i
  RANGE g, i, vgap
}

PARAMETER {
  g = 1 (nanosiemens)
}

ASSIGNED {
  v (millivolt)
  vgap (millivolt)
  i (nanoamp)
}

BREAKPOINT {
  i = g * (vgap - v)
}
