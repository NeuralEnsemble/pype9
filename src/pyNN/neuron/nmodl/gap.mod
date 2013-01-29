NEURON {
  POINT_PROCESS Gap
  NONSPECIFIC_CURRENT i
  RANGE g, i
  POINTER vgap
}

PARAMETER {
  v (millivolt)
  vgap (millivolt)
  g = 1 (nanosiemens)
}

ASSIGNED {
  i (nanoamp)
}

BREAKPOINT {
  i = g * (v - vgap)
}
