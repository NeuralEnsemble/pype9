# This file prints the morphology via the psections and a manual print of the
# the 3d points.
# import os
# model_dir = '/home/tclose/git/purkinje/model/Haroon_active_reduced_model'
# model_dir = '/home/tclose/git/cerebellarnuclei/'
# os.chdir(model_dir)
from neuron import h
# if model_dir == '/home/tclose/git/purkinje/model/Haroon_active_reduced_model':
#     import for_import  # @UnresolvedImport @UnusedImport
# else:
#     h.load_file('DCN_params_axis.hoc')
#     h.load_file('DCN_morph.hoc')
#     h.load_file('DCN_mechs1.hoc')
#     h('DCNmechs()')

# Get list of all NEURON sections
allsecs = h.SectionList()
roots = h.SectionList()
roots.allroots()
for root in roots:
    root.push()
    allsecs.wholetree()

# Plot all names, lengths diameters and 3d points
out = ''
for sec in allsecs:
    sec.push()
    out += '{} {}:'.format(sec.name(), sec.L)
    try:
        for i in xrange(sec.nseg + 1):
            out += '{} {} {} {},'.format(h.x3d(i), h.x3d(i), h.x3d(i),
                                         h.diam3d(i))
    except RuntimeError:
        pass
    if out.endswith(','):
        out = out[:-1]
    out += '\n'
    h.pop_section()
print out
