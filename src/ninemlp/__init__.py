"""

  This package aims to contain all extensions to the pyNN package required for interpreting 
  networks specified in NINEML+. It is possible that some changes will need to be made in the 
  pyNN package itself (although as of 13/6/2012 this hasn't been necessary).
  
  @file ncml.py
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import os
import xml.sax
import time

__version__ = "0.0.1"

SRC_PATH_ENV_NAME = 'NINEMLP_SRC_PATH'
MPI_NAME = 'NINEMLP_MPI'

BUILD_MODE_OPTIONS = ['lazy', 'force', 'build_only', 'require', 'compile_only']
DEFAULT_BUILD_MODE = 'lazy'
pyNN_build_mode = DEFAULT_BUILD_MODE

if SRC_PATH_ENV_NAME in os.environ: # NINEMLP_SRC_PATH has been set as an environment variable use it
    SRC_PATH = os.environ[SRC_PATH_ENV_NAME]
else: # Otherwise determine from path to this module
    SRC_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

if MPI_NAME in os.environ:
    import mpi4py #@UnresolvedImport
    
if os.environ['HOME'] == '/home/tclose':
    # I apologise for this little hack (this is the path on my machine, 
    # to save me having to set the environment variable in eclipse)
    os.environ['LD_PRELOAD']='/usr/lib/libmpi.so' # This is a work around for my MPI installation    
    os.environ['NEURON_INIT_MPI'] = '1'    
    
def create_seeds(specified_seeds, sim_state=None):
    """
    If sim_state (pyNN.*simulator_name*.simulator.state) is provided the number of processes and the 
    process rank is taken into account so that each process is provided a different seed. If wanting
    to use PyNN's "parallel_safe" option then it shouldn't be provided.
    """
    try:
        num_seeds = len(specified_seeds)
    except TypeError:
        specified_seeds = [specified_seeds]
        num_seeds = 1
    if sim_state:
        process_rank = sim_state.mpi_rank  #@UndefinedVariable
        num_processes = sim_state.num_processes #@UndefinedVariable
        if num_processes != 1:
            transformed_seeds = []
            for seed in specified_seeds:
                transformed_seeds = seed * num_processes + process_rank
            specified_seeds = transformed_seeds
    else:
        process_rank = 0
        num_processes = 1   
    generated_seed = int(time.time() * 256) 
    out_seeds = []
    for seed in specified_seeds:
        if seed is not None:
            out_seeds.append(int(seed))
        else:
            proposed_seed = generated_seed + process_rank
            # Ensure the proposed seed isn't the same as one of the specified seeds (not sure if 
            # this is necessary but it could theoretically be a problem if they were the same)
            while proposed_seed in specified_seeds:
                proposed_seed += num_seeds * num_processes
            out_seeds.append(proposed_seed)
            generated_seed += num_processes
    return out_seeds if num_seeds != 1 else out_seeds[0] 

class XMLHandler(xml.sax.handler.ContentHandler):

    def __init__(self):
        self._open_components = []
        self._required_attrs = []

    def characters(self, data):
        pass

    def endElement(self, name):
        """
        Closes a component, removing its name from the _open_components list. 
        
        WARNING! Will break if there are two tags with the same name, with one inside the other and 
        only the outer tag is opened and the inside tag is differentiated by its parents
        and attributes (this would seem an unlikely scenario though). The solution in this case is 
        to open the inside tag and do nothing. Otherwise opening and closing all components 
        explicitly is an option.
        """
        if self._open_components and name == self._open_components[-1]:
            self._open_components.pop()
            self._required_attrs.pop()

    def _opening(self, tag_name, attr, ref_name, parents=[], required_attrs=[]):
        if tag_name == ref_name and self._parents_match(parents, self._open_components) and \
                all([(attr[key] == val or val == None) for key, val in required_attrs]):
            self._open_components.append(ref_name)
            self._required_attrs.append(required_attrs)
            return True
        else:
            return False

    def _closing(self, tag_name, ref_name, parents=[], required_attrs=[]):
        if tag_name == ref_name and self._parents_match(parents, self._open_components[:-1]) and \
                self._required_attrs[-1] == required_attrs:
            return True
        else:
            return False

    def _parents_match(self, required_parents, open_parents):
        if len(required_parents) > len(open_parents):
            return False
        for required, open in zip(reversed(required_parents), reversed(open_parents)):
            if isinstance(required, str):
                if required != open:
                    return False
            else:
                try:
                    if not any([ open == r for r in required]):
                        return False
                except TypeError:
                    raise Exception("Elements of the 'required_parents' argument need to be " \
                                    "either strings or lists/tuples of strings")
        return True














