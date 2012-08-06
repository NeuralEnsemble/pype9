/******Cerebellar Cortex with Gap Junctions between Golgi cells******/

Developers:    Fabio M Simoes de Souza & E De Schutter

Work Progress: Jan 2010 - Dec 2010

Developed At: Okinawa Institute of Science and Technology
               Computational Neuroscience Unit Okinawa - Japan
	       
Model Published in: 

             Simoes de Souza FM and De Schutter E (2011) Robustness
             effect of gap junctions between Golgi cells on cerebellar
             cortex oscillations.  Neural Systems & Circuits 1:7.

Abstract

Background: Previous one-dimensional network modeling of the
cerebellar granular layer has been successfully linked with a range of
cerebellar cortex oscillations observed in vivo. However, the recent
discovery of gap junctions between Golgi cells (GoCs), which may cause
oscillations by themselves, has raised the question of how
gap-junction coupling affects GoC and granular-layer oscillations. To
investigate this question, we developed a novel two-dimensional
computational model of the GoC-granule cell (GC) circuit with and
without gap junctions between GoCs.Results: Isolated GoCs coupled by
gap junctions had a strong tendency to generate spontaneous
oscillations without affecting their mean firing frequencies in
response to distributed mossy fiber input. Conversely, when GoCs were
synaptically connected in the granular layer, gap junctions increased
the power of the oscillations, but the oscillations were primarily
driven by the synaptic feedback loop between GoCs and GCs, and the gap
junctions did not change oscillation frequency or the mean firing rate
of either GoCs or GCs.Conclusion: Our modeling results suggest that
gap junctions between GoCs increase the robustness of cerebellar
cortex oscillations that are primarily driven by the feedback loop
between GoCs and GCs. The robustness effect of gap junctions on
synaptically driven oscillations observed in our model may be a
general mechanism, also present in other regions of the brain.

Usage instructions:

Auto-launch from ModelDB or download and extract the archive.  Then
under:

----
MSWIN

run mknrndll, cd to the archive and make the nrnmech.dll.  Then double
click on the mosinit.hoc file.

----
MAC OS X

Drag and drop the network folder onto the mknrndll icon.
Drag and drop the mosinit.hoc file onto the nrngui icon.

----
Linux/Unix

Change directory to the network folder. run nrnivmodl. Then type
nrngui mosinit.hoc

----

Uncomment the GJ flag on mosinit.hoc to select a network with or
without GJ between GoCs.
Once the simulation is started it will produce a result similar to
figure 9 from Simoes de Souza and De Schutter 2011.
