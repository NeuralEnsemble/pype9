import subprocess as sp
import os.path
import shutil
from neuron import h, load_mechanisms

mech_name = 'buff_overrun'

mod_dir = os.path.join(os.path.dirname(__file__), 'mod')

shutil.rmtree(os.path.join(mod_dir, 'x86_64'), ignore_errors=True)
orig_dir = os.getcwd()
os.chdir(mod_dir)
sp.check_call('nrnivmodl', shell=True)
os.chdir(orig_dir)
load_mechanisms(mod_dir)


_sec = h.Section()
HocClass = getattr(h, mech_name)
_hoc = HocClass(0.5, sec=_sec)
setattr(_hoc, 'cm___pype9', 1.0)
rec = h.NetCon(_hoc, None, sec=_sec)
print("Done testing")
