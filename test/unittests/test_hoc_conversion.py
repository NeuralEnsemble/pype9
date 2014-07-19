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
# from lxml import etree
from nineline.cells import DummyNinemlModel
from nineline.cells.neuron import NineCellMetaClass, simulation_controller
from neuron import h

psection_fn = '/home/tclose/git/cerebellarnuclei/extracted_data/psections.txt'
mechs_fn = '/home/tclose/git/cerebellarnuclei/extracted_data/mechanisms.txt'
out_fn = '/home/tclose/Desktop/cerebellarnuclei.9ml'


class TestHocConversion(unittest.TestCase):

    def test_hoc_conversion(self):
        model = Model.from_psections(psection_fn, mechs_fn)
        nineml_model = DummyNinemlModel('CerebellarNuclei',
                                        '/home/tclose/git/cerebellarnuclei',
                                        model)
        CerebellarNuclei = NineCellMetaClass(nineml_model)
        cell = CerebellarNuclei()
#         simulation_controller.run(10)
#         h.load_file('mview.hoc')
#         h("""
#         objref m
#         m = new ModelView(0)
#         m.textp("/home/tclose/git/cerebellarnuclei/extracted_data/regurgitated_mechanisms.txt")
#         m.destroy()
#         objref m
#         """)
        for name, seg in cell.segments.iteritems():
            print "{} {:.6f}".format(name, seg.L)
        print cell
#         model9ml = model.to_9ml()
#         etree.ElementTree(model9ml.to_xml()).write(out_fn, encoding="UTF-8",
#                                                    pretty_print=True,
#                                                    xml_declaration=True)


if __name__ == '__main__':
    test = TestHocConversion()
    test.test_hoc_conversion()
    print "done"
