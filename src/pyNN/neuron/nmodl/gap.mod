COMMENT

//%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
//
// NOTICE OF COPYRIGHT AND OWNERSHIP OF SOFTWARE
//
// Copyright 2007, The University Of Pennsylvania
//  School of Engineering & Applied Science.
//   All rights reserved.
//   For research use only; commercial use prohibited.
//   Distribution without permission of Maciej T. Lazarewicz not permitted.
//   mlazarew@seas.upenn.edu
//
//%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

ENDCOMMENT

NEURON {

    POINT_PROCESS Gap
    RANGE g, i, vgap
    NONSPECIFIC_CURRENT i
}

UNITS {

  (nA) = (nanoamp)
  (mV) = (millivolt)
  (nS) = (nanosiemens)
}

PARAMETER { g = 0 (nS) }
    
ASSIGNED {

    v    (mV)
    vgap (mV)
    i    (nA)
}
 
BREAKPOINT { 

  if (g>0) {i = (1e-3) * g * (v-vgap) }

}
