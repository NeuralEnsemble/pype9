NEURON {
	POINT_PROCESS Gap
	POINTER vgap
	RANGE g, i
	NONSPECIFIC_CURRENT i
}
PARAMETER { g = 2e-3 (microsiemens) }
ASSIGNED {
	v 		(millivolt)
	vgap 	(millivolt)
	i 		(nanoamp)
}
BREAKPOINT { i = g*(v - vgap)}