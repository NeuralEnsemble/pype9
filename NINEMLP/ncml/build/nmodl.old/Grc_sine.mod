TITLE Electrode for sinusoidal current clamping

COMMENT
	Author: A. Fontana
	Last revised: 28.3.99
ENDCOMMENT

NEURON {
	POINT_PROCESS GrC_Sine
	RANGE del, dur, amp, i, freq, phase
	ELECTRODE_CURRENT i
}
UNITS {
	(nA) = (nanoamp)
}

PARAMETER {
	PI = 3.141592
	del (ms)
	dur (ms)	
	amp = 0.006 (nA)
	freq = 4 (1/ms)
	phase = 0
}
ASSIGNED { i (nA) }

INITIAL {
	i = 0
}

BREAKPOINT {
	at_time(del)
	at_time(del+dur)

	if (t < del + dur && t > del) {

		
		i = amp*sin(2*PI*freq*t/1000)


	}else{
		i = 0
	}
}
