if __name__ == '__main__':

    class unittest(object):

        class TestCase(object):

            def __init__(self):
                try:
                    self.setUp()
                except AttributeError:
                    pass

            def assertEqual(self, first, second):
                print 'are{} equal'.format(' not' if first != second else '')
else:
    try:
        import unittest2 as unittest
    except ImportError:
        import unittest
from nineline.cells import Model
from itertools import chain
import time
import neo.io
from nineline.importer.neuron import save_model_view
# from lxml import etree
from nineline.cells import DummyNinemlModel, DistributedParameter, BranchAncestry
from nineline.cells.neuron import NineCellMetaClass, simulation_controller
from btmorph.btviz import plot_3D_SWC
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, '/home/tclose/git/neurotune/scripts')
from reduce_morphology import merge_leaves, IrreducibleMorphologyException
sys.path.pop(0)
import numpy

psection_fn = '/home/tclose/git/cerebellarnuclei/extracted_data/psections.txt'
mechs_fn = '/home/tclose/git/cerebellarnuclei/extracted_data/mechanisms.txt'
out_fn = '/home/tclose/Desktop/cerebellarnuclei.9ml'

alpha = 0.2

merge_step_depth = 1


class TestHocConversion(unittest.TestCase):

    def test_hoc_conversion(self):
        model = Model.from_psections(psection_fn, mechs_fn)
        model.categorise_segments_for_SWC()
        for comp in chain(model.components_of_class('CaConc'),
                          model.components_of_class('CalConc')):
            segments = list(model.component_segments(comp))
            if len(segments) == 1:
                assert segments[0].name == 'soma'
                comp.parameters['depth'] = DistributedParameter(
                            lambda seg: alpha - 2 * alpha ** 2 / seg.diam + \
                                        4 * alpha ** 3 / (3 * seg.diam ** 2))
            else:
                comp.parameters['depth'] = DistributedParameter(
                                    lambda seg: alpha - alpha ** 2 / seg.diam)
        md = dict((frozenset(c.name for c in comps), segs)
                  for comps, segs in model.get_segment_categories())
        print len(list(model.segments))
        reduced = model
        for i in xrange(1, 9):
            reduced = merge_leaves(reduced, normalise=True, num_merges=1,
                                   error_if_irreducible=False)
            reduced.categorise_segments_for_SWC()
            print len(list(reduced.segments))
            rd = dict((frozenset(c.name for c in comps), segs)
                      for comps, segs in reduced.get_segment_categories())
            for k in rd:
                print ', '.join(k) + ':'
                print "  {} -> {}".format(numpy.sum(s.surface_area
                                                    for s in rd.get(k, [])),
                                          numpy.sum(s.surface_area
                                                    for s in md.get(k, [])))
#             model.plot(show=False)
#             reduced.plot(show=True)
            print "after {} merges".format(i)
#         nineml_model = DummyNinemlModel('CerebellarNuclei',
#                                         '/home/tclose/git/cerebellarnuclei',
#                                         model)
#         CerebellarNuclei = NineCellMetaClass(nineml_model)
#         cell = CerebellarNuclei()
#         cell.record('v')
#         print time.time()
#         simulation_controller.run(1000)
#         print time.time()
#         recording = cell.get_recording('v')
#         out = neo.io.PickleIO('/home/tclose/Desktop/cerebellar_nuclei.neo.pkl')
#         out.write(recording)
#         save_model_view('/home/tclose/git/cerebellarnuclei/extracted_data/'
#                         'regurgitated_mechanisms.txt')
#         print cell


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', default=False, action='store_true')
    args = parser.parse_args()
    if args.run:
        test = TestHocConversion()
        test.test_hoc_conversion()
        print "done"
