import subprocess as sp
import os.path
import shutil
import neuron
neuron.h.load_file('stdrun.hoc')

mod_dir = os.path.join(os.path.dirname(__file__), 'mod')

shutil.rmtree(os.path.join(mod_dir, 'x86_64'), ignore_errors=True)
orig_dir = os.getcwd()
os.chdir(mod_dir)
sp.check_call('nrnivmodl', shell=True)
os.chdir(orig_dir)
neuron.load_mechanisms(mod_dir)


sec = neuron.h.Section()
hoc = neuron.h.NoSectionMWE(0.5, sec=sec)
setattr(hoc, 'cm_int', 1.0)
setattr(hoc, 'R', 1.0)
setattr(hoc, 'tau', 1.0)
setattr(hoc, 'tau2', 1.0)
rec = neuron.h.NetCon(hoc, None, sec=sec)
print("running")
neuron.init()
print("finitializing")
neuron.h.finitialize()
print("running")
# neuron.run(10)
neuron.h.tstop = 10
neuron.h.run()
print("Done testing")
