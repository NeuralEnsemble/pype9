import nineml
from .cells import with_synapses


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
            child_cls = getattr(with_synapses, nineml_type)
        except AttributeError:
            child_cls = nineml.Document._get_class_from_type(nineml_type)
        return child_cls
