"""
Imports a model in HOC and/or NMODL into the 9ML format
"""
from argparse import ArgumentParser

parser = ArgumentParser(description=__doc__)


def run():
    import os.path
    from pype9.neuron.importer.hoc import HocImporter

    args = parser.parse_args()
    alex_ocnc_dir = os.path.join(
        os.environ['HOME'], 'git', 'alex_ocnc', 'test')

    importer = HocImporter(alex_ocnc_dir, ['stellate_scaled2.hoc'])

    importer.model
