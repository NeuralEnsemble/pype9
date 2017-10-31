import subprocess as sp
import os.path
import shutil
from neuron import h, load_mechanisms

mech_name = 'BuffOverflow'

mod_dir = os.path.join(os.path.dirname(__file__), 'mod')

shutil.rmtree(os.path.join(mod_dir, 'x86_64'), ignore_errors=True)
orig_dir = os.getcwd()
os.chdir(mod_dir)
sp.check_call('nrnivmodl', shell=True)
os.chdir(orig_dir)
load_mechanisms(mod_dir)


sec = h.Section()
hoc = h.BuffOverflow(0.5, sec=sec)
setattr(hoc, 'cm_int', 1.0)
setattr(hoc, 'R', 1.0)
rec = h.NetCon(hoc, None, sec=sec)
print("Done testing")
