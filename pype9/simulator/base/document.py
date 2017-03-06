import nineml
from nineml.document import read_xml


class Document(nineml.Document):
    """
    Extends the nineml.Document class to allow for WithSynapses objects
    """
    write_order = (['DynamicsWithSynapses', 'MultiDynamicsWithSynapses'] +
                   nineml.Document.write_order)

    @classmethod
    def _get_class_from_type(cls, nineml_type):
        # Note that all `DocumentLevelObjects` need to be imported
        # into the root nineml package
        try:
            child_cls = getattr(pype9.simulator.base.cells.with_synapses, nineml_type)
        except AttributeError:
            child_cls = nineml.Document._get_class_from_type(nineml_type)
        return child_cls


def read(url, relative_to=None, **kwargs):
    """
    Read a NineML (possibly with PyPe9 WithSynapses) file and parse its child
    elements

    If the URL does not have a scheme identifier, it is taken to refer to a
    local file.
    """
    xml, url = read_xml(url, relative_to=relative_to)
    root = xml.getroot()
    doc = Document.load(root, url, **kwargs)
    return doc


def write(document, filename, **kwargs):
    """
    Provided for symmetry with read method, takes a nineml.document.Document
    object and writes it to the specified file
    """
    # Encapsulate the NineML element in a document if it is not already
    if not isinstance(document, Document):
        element = document.clone()
        element._document = None
        document = Document(element)
    document.write(filename, version=2.0, **kwargs)


import pype9.simulator.base.cells  # @IgnorePep8
