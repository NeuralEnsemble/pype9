from __future__ import absolute_import
import nineline.pyNN.common.cells
from pyNN.parameters import ParameterSpace
from collections import defaultdict
import pyNN.standardmodels
import nest
from nineline.cells.nest import NineCell, NineCellMetaClass


class NinePyNNCell(nineline.pyNN.common.cells.NinePyNNCell, pyNN.standardmodels.StandardCellType):

    standard_receptor_type = None

    def __init__(self, **parameters):
        nineline.pyNN.common.cells.NinePyNNCell.__init__(self)
        pyNN.standardmodels.StandardCellType.__init__(self, **parameters)

    def memb_init(self):
        # Initialisation of member states goes here
        print "WARNING, membrane initialization function has not been implemented"
        pass

    def translate(self, parameters):
        """
        Translate standardized model parameters to simulator-specific parameters. Overrides the
        the method in StandardModelType to provide a simpler translation that avoids the evaluation 
        of the 'dots' in the standard name
        """
        native_parameters = {}
        for name in parameters.keys():
            # FIXME: A hack before Ivan implements this as a parameter 
            if name != 'all_segs.Ra':
                try:
                    native_parameters[self.translations[name]['translated_name']] = parameters[name]
                except KeyError:
                    print "Omitting parameter '{}'".format(name)
        return ParameterSpace(native_parameters, schema=None, shape=parameters.shape)

    def get_receptor_type(self, name):
        seg, receptor_name = name.split('.') #@UnusedVariable - at this stage just throw away the segment
        return nest.GetDefaults(self.nest_model)["receptor_types"][receptor_name]


class NinePyNNCellMetaClass(nineline.pyNN.common.cells.NinePyNNCellMetaClass):
    """
    Metaclass for compiling NineMLCellType subclases
    Called by nineml_celltype_from_model
    """
    def __new__(cls, celltype_name, nineml_model, build_mode='lazy', silent=False, solver_name='cvode'): #@NoSelf
        dct = {'model': NineCellMetaClass(celltype_name, nineml_model, build_mode=build_mode, 
                                          silent=silent, solver_name='cvode')}
        dct['nest_name'] = {"on_grid": celltype_name, "off_grid": celltype_name}
        dct['nest_model'] = celltype_name
        dct['translations'] = cls._construct_translations(dct['model'].memb_model,
                                                          dct['model'].component_translations)        
        celltype = super(NinePyNNCellMetaClass, cls).__new__(cls, celltype_name + 'PyNN', 
                                                             (NinePyNNCell,), dct)       
        return celltype

    @classmethod
    def _construct_translations(cls, memb_model, component_translations):
        comp_groups = defaultdict(list)
        for comp in memb_model.mechanisms:
            comp_groups[str(comp.id)].append(NineCell.group_varname(comp.group_id))
        translations = []
        for comp, params in component_translations.iteritems():
            if comp != 'Extracellular':
                for param, native_n_val in params.iteritems():
                    # These are hacks just to get it to work initially, which will be removed once
                    # the neuron version of the cell respects these components at which point they
                    # should be accessed via
                    if comp in ('Geometry', 'Membrane'):
                        if comp == 'Geometry':
                            standard_name = 'soma_group.' + str(param)
                        elif comp == 'Membrane':
                            standard_name = 'all_segs.' + str(param)
                        translations.append((standard_name, native_n_val[0]))
                    else:
                        for seg_group in comp_groups[comp]:
                            standard_name = '{}.{}.{}'.format(seg_group, comp, param)
                            translations.append((standard_name, native_n_val[0]))
        return pyNN.standardmodels.build_translations(*translations)
