NEURON {
  POINT_PROCESS Gap
  NONSPECIFIC_CURRENT i
  RANGE g, i
  POINTER vgap
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
  i = g * (v - vgap)
}
