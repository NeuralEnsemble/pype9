NEURON {
	POINT_PROCESS Gap
	POINTER vnb
	RANGE g, i
	NONSPECIFIC_CURRENT i
}
PARAMETER { g = 2e-3 (microsiemens) }
ASSIGNED {
	v 		(millivolt)
	vnb 	        (millivolt)
	i 		(nanoamp)
}
BREAKPOINT { i = g*(v - vnb)}