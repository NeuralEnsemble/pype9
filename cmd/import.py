"""
Imports a model in HOC and/or NMODL into the 9ML format
"""
raise NotImplementedError
import os.path
from pype9.neuron.importer.hoc import HocImporter

alex_ocnc_dir = os.path.join(
    os.environ['HOME'], 'git', 'alex_ocnc', 'test')

importer = HocImporter(alex_ocnc_dir, ['stellate_scaled2.hoc'])

importer.model
