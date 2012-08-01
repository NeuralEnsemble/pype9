
NEMO ?= nemo

%.mod : %.nemo
	$(NEMO) --nmodl --nmodl-method=derivimplicit $< 

all: CGC_cac.mod CGC_CaHVA.mod CGC_KA.mod CGC_KCa.mod CGC_Kir.mod CGC_KM.mod CGC_KV.mod CGC_Lkg1.mod CGC_Lkg2.mod CGC_Na.mod CGC_Nar.mod CGC_pNa.mod 
