"""

  This package contains the XML handlers to read the NCML files and related
  functions/classes, the NCML base meta-class (a meta-class is a factory that
  generates classes) to generate a class for each NCML cell description (eg. a
  'Purkinje' class for an NCML containing a declaration of a Purkinje cell),
  and the base class for each of the generated cell classes.

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import collections
import math
from itertools import groupby, chain
from copy import copy, deepcopy
import numpy
from lxml import etree
import quantities as pq
import nineml.extensions.biophysical_cells
from nineml.extensions.morphology import (Morphology as Morphology9ml,
                                          Segment as Segment9ml,
                                          ProximalPoint as ProximalPoint9ml,
                                          DistalPoint as DistalPoint9ml,
                                          ParentSegment as ParentSegment9ml,
                                          Classification as Classification9ml,
                                          SegmentClass as SegmentClass9ml,
                                          Member as Member9ml)
from abc import ABCMeta  # Metaclass for abstract base classes
from btmorph.btstructs2 import STree2, SNode2, P3D2
# DEFAULT_V_INIT = -65


class NineCell(object):

    def __init__(self, model=None):
        """
        `model` -- A "Model" object derived from the same source as the default
                   model used to create the class. This default model can be
                   accessed via the 'copy_of_default_model' method. Providing
                   the model here is provided here to allow the modification of
                   morphology and distribution of ion channels programmatically
        """
        if model:
            if model._source is not self._default_model._source:
                raise Exception("Only models derived from the same source as "
                                "the default model can be used to instantiate "
                                "the cell with.")
            self._model = model
        else:
            self._model = self._default_model

    @classmethod
    def copy_of_default_model(cls):
        return deepcopy(cls._default_model)


class NineCellMetaClass(type):

    def __new__(cls, nineml_model, celltype_name, bases, dct):
        dct['parameter_names'] = [p.name for p in nineml_model.parameters]
        dct['_default_model'] = Model.from_9ml(nineml_model)
        return super(NineCellMetaClass, cls).__new__(cls, celltype_name, bases,
                                                     dct)

    def __init__(cls, nineml_model, celltype_name=None, morph_id=None,
                 build_mode=None, silent=None, solver_name=None,
                 standalone=False):
        """
        This initialiser is empty, but since I have changed the signature of
        the __new__ method in the deriving metaclasses it complains otherwise
        (not sure if there is a more elegant way to do this).
        """
        pass


class Model(STree2):

    @classmethod
    def from_9ml(cls, nineml_model):
        morph9ml = nineml_model.morphology
        bio9ml = nineml_model.biophysics
        model = cls(morph9ml.name, source=nineml_model)
        # Add the proximal point of the root get_segment as the root of the
        # model
        root_point = P3D2(xyz=numpy.array((morph9ml.root_segment.proximal.x,
                                           morph9ml.root_segment.proximal.y,
                                           morph9ml.root_segment.proximal.z)),
                          radius=morph9ml.root_segment.proximal.diameter / 2.0)
        root = SNode2('__ROOT__')
        root.set_content({'p3d': root_point})
        model.set_root(root)
        # Add the root get_segment and link with root node
        model.root_segment = SegmentModel.from_9ml(morph9ml.root_segment)
        model.add_node_with_parent(model.root_segment, model.get_root())
        seg_lookup = {model.root_segment.name: model.root_segment}
        # Initially create all the segments and add them to a lookup dictionary
        for seg_9ml in morph9ml.segments.itervalues():
            if seg_9ml != morph9ml.root_segment:
                seg_lookup[seg_9ml.name] = SegmentModel.from_9ml(seg_9ml)
        # Then link together all the parents and children
        for seg_9ml in morph9ml.segments.itervalues():
            if seg_9ml != morph9ml.root_segment:
                parent = seg_lookup[seg_9ml.parent.segment_name]
                segment = seg_lookup[seg_9ml.name]
                model.add_node_with_parent(segment, parent)
        # Add biophysical components
        model.components = {}
        for name, comp in bio9ml.components.iteritems():
            model.components[name] = DynamicComponentModel.from_9ml(comp,
                                                                   bio9ml.name)
        # TODO: This is a hack until I refactor the xml code
        defaults = model.components.pop('__NO_COMPONENT__')
        cm = MembraneCapacitanceModel('cm_default', defaults.parameters['C_m'])
        Ra = AxialResistanceModel('Ra_default', defaults.parameters['Ra'])
        for seg in seg_lookup.itervalues():
            seg.set_component(cm)
            seg.set_component(Ra)
        model.add_component(cm)
        model.add_component(Ra)
        # Get the spike threshold
        model.spike_threshold = defaults.parameters['V_t'] * pq.mV
        # TODO: Likewise this is temporary until the xml code is refactored
        # Add mappings to biophysical components
        segment_classes = {}
        for classification in morph9ml.classifications.itervalues():
            for class_9ml in classification.classes.itervalues():
                seg_class = segment_classes[class_9ml.name] = []
                for member in class_9ml.members:
                    seg_class.append(seg_lookup[member.segment_name])
        for mapping in nineml_model.mappings:
            for comp in mapping.components:
                for seg_cls_name in mapping.segments:
                    for seg in segment_classes[seg_cls_name]:
                        seg.set_component(model.components[comp])
        return model

    @classmethod
    def from_psections(cls, filename):
        """
        Reads a neuron morphology from the output of a psection() call in hoc
        and generates a model tree

        `filename` -- path to a file containing the psection() output
        """
        segments = {}
        in_section = False
        f = open(filename)
        for line in f:
            line = line.strip()
            if not in_section and line.strip():
                parts = line.split(' ')
                name = parts[0]
                attributes = {}
                components = {}
                connections = []
                for key_val in parts[2:]:
                    key_val = key_val.strip()
                    if key_val:
                        key, val = key_val.split('=')
                        attributes[key] = float(val)
                in_section = True
            elif in_section:
                if line.startswith('}'):
                    if len(connections) == 0:
                        parent = None
                    elif len(connections) == 1:
                        parent = connections[0]
                    else:
                        raise Exception("Segment '{}' has more than one "
                                        "connection (expected on one 'parent' "
                                        "segment)")
                    section = SegmentModel(name, attributes['L'],
                                           attributes['Ra'],
                                           components['morphology']['diam'],
                                           components['capacitance']['cm'],
                                           parent)
                    segments[section.name] = section
                    in_section = False
                elif line.startswith('insert'):
                    component_name, parameters = line[6:].strip().split('{')
                    component = {}
                    for key_vals in parameters.strip()[:-1].split(' '):
                        key, val = key_vals.strip().split('=')
                        component[key] = float(val)
                    components[component_name.strip()] = component
                elif line.find('connect') > 0:
                    parts = line.strip().split(' ')
                    connections.append(parts[0])
        # Convert parent references from names to Section objects

        for s in segments.itervalues():
            if s.parent is not None:
                s.parent = segments[s.parent]
        return segments

    def __init__(self, name, source=None):
        self.name = name
        self._source = source

    def __deepcopy__(self, memo):
        """
        Override the __deepcopy__ method to avoid copying the source, which
        should stay constant so it can be compared between copies using the
        'is' keyword
        """
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == '_source':
                setattr(result, k, copy(v))
            else:
                setattr(result, k, deepcopy(v, memo))
        return result

    def to_9ml(self):
        clsf = Classification9ml('default',
                                 [c.to_9ml()
                                  for c in self.segment_classes.itervalues()])
        return Morphology9ml(self.name,
                             dict([(seg.name, seg.to_9ml())
                                   for seg in self.segments]),
                             {'default': clsf})

    def add_component(self, component):
        self.components[component.name] = component
        return component

    @property
    def segments(self):
        """
        Segments are not stored directly as a flat list to allow branches
        to be edited by altering the children of segments. This iterator is
        then used to flatten the list of segments
        """
        return chain([self.root_segment], self.root_segment.all_children)

    @property
    def branches(self):
        """
        An iterator over all branches in the tree
        """
        return self.root_segment.sub_branches

    def get_segment(self, name):
        match = [seg for seg in self.segments if seg.name == name]
        #TODO: Need to check this on initialisation
        assert len(match) <= 1, "Multiple segments with key '{}'".format(name)
        if not len(match):
            raise KeyError("Segment '{}' was not found".format(name))
        return match[0]

    def merge_leaves(self, only_most_distal=False, normalise_sampling=True):
        """
        Reduces a 9ml morphology, starting at the most distal branches and
        merging them with their siblings.
        """
        # Create a complete copy of the morphology to allow it to be reduced
        if only_most_distal:
            # Get the branches at the maximum depth
            max_branch_depth = max(seg.branch_depth for seg in self.segments)
            candidates = [branch for branch in self.branches
                          if branch[0].branch_depth == max_branch_depth]
        else:
            candidates = [branch for branch in self.branches
                          if not branch[-1].children]
        # Only include branches that have consistent segment_classes
        candidates = [branch for branch in candidates
                      if all(b.classes == branch[0].classes for b in branch)]
        if not candidates:
            raise IrreducibleMorphologyException("Cannot reduce the morphology"
                                                 " further{}. without merging "
                                                 "segment_classes")
        needs_tuning = []
        sibling_seg_classes = groupby(candidates,
                                     key=lambda b: (b[0].parent, b[0].classes))
        for (parent, seg_classes), siblings_iter in sibling_seg_classes:
            siblings = list(siblings_iter)
            if len(siblings) > 1:
                average_length = (numpy.sum(seg.length
                                            for seg in chain(*siblings)) /
                                  len(siblings))
                total_surface_area = numpy.sum(seg.length * seg.diameter
                                               for seg in chain(*siblings))
                axial_cond = 0.0
                for branch in siblings:
                    axial_cond += 1.0 / numpy.sum(seg.Ra for seg in branch)
                axial_resistance = 1.0 / axial_cond
                diameter = total_surface_area / average_length
                sorted_names = sorted([s[0].name for s in siblings])
                name = sorted_names[0]
                if len(branch) > 1:
                    name += '_' + sorted_names[-1]
                # Extend the new get_segment in the same direction as the
                # parent get_segment
                #
                # If the classes are the same between parent and the new
                # segment treat them as one
                disp = parent.disp * (average_length / parent.length)
                segment = SegmentModel(name, parent.distal + disp, diameter,
                                       classes=seg_classes)
                # Remove old branches from list
                for branch in siblings:
                    self.remove_node(branch[0])
                self.add_node_with_parent(segment, parent)
                # Create new Ra comp to hold the varied axial resistance
                Ra_comp = AxialResistanceModel(name + '_Ra', axial_resistance)
                self.add_component(Ra_comp)
                segment.add_component(Ra_comp)
                needs_tuning.append(Ra_comp)
        if normalise_sampling:
            self.normalise_spatial_sampling()
        return needs_tuning

    def normalise_spatial_sampling(self, **d_lambda_kwargs):
        """
        Regrids the spatial sampling of the segments in the tree via NEURON's
        d'lambda rule

        `freq`       -- frequency at which AC length constant will be computed
                        (Hz)
        `d_lambda`   -- fraction of the wavelength
        """
        for branch in list(self.branches):
            parent = branch[0].parent
            if parent:
                branch_length = numpy.sum(seg.length for seg in branch)
                # Get weighted average of diameter Ra and cm by segment length
                diameter = 0.0
                Ra = 0.0 * pq.ohm * pq.cm
                cm = 0.0 * pq.uF / (pq.cm ** 2)
                for seg in branch:
                    diameter += seg.diameter * seg.length
                    Ra += seg.Ra * seg.length
                    cm += seg.cm * seg.length
                diameter /= branch_length
                Ra /= branch_length
                cm /= branch_length
                num_segments = self.d_lambda_rule(branch_length,
                                                  diameter * pq.um,
                                                  Ra, cm, **d_lambda_kwargs)
                base_name = branch[0].name
                if len(branch) > 1:
                    base_name += '_' + branch[-1].name
                # Get the direction of the branch
                seg_classes = branch[0].classes
                direction = branch[-1].distal - branch[0].proximal
                disp = direction * (branch_length /
                                    numpy.sqrt(numpy.sum(direction ** 2)))
                # Temporarily add the parent to the new_branch to allow it to
                # be linked to the new segments
                seg_disp = disp / float(num_segments)
                previous_segment = parent
                for i in xrange(num_segments):
                    name = base_name + '_' + str(i)
                    distal = branch[0].proximal + seg_disp * (i + 1)
                    segment = SegmentModel(name, distal, diameter,
                                      classes=seg_classes)
                    previous_segment.add_child(segment)
                    segment.set_parent_node(previous_segment)
                    previous_segment = segment
                parent.remove_child(branch[0])

    @classmethod
    def d_lambda_rule(cls, length, diameter, Ra, cm,
                      freq=(100.0 * pq.Hz), d_lambda=0.1):
        """
        Calculates the number of segments required for a straight branch
        section so that its segments are no longer than d_lambda x the AC
        length constant at frequency freq in that section.

        See Hines, M.L. and Carnevale, N.T.
           NEURON: a tool for neuroscientists.
           The Neuroscientist 7:123-135, 2001.

        `length`     -- length of the branch section
        `diameter`   -- diameter of the branch section
        `Ra`         -- Axial resistance (Ohm cm)
        `cm`         -- membrane capacitance (uF cm^(-2))
        `freq`       -- frequency at which AC length constant will be computed
                        (Hz)
        `d_lambda`   -- fraction of the wavelength

        Returns:
            The number of segments required for the corresponding fraction of
            the wavelength
        """
        # Calculate the wavelength for the get_segment
        lambda_f = 1e5 * numpy.sqrt(in_units(diameter, 'um') /
                                    (4 * numpy.pi * in_units(freq, 'Hz') *
                                     in_units(Ra, 'ohm.cm') *
                                     in_units(cm, 'uF/cm^2')))
        return int((length / (d_lambda * lambda_f) + 0.9) / 2) * 2 + 1

    def merge_morphology_seg_classes(self, from_class, into_class):
        raise NotImplementedError


class SegmentModel(SNode2):

    @classmethod
    def from_9ml(cls, nineml_model):
        """
        Creates a node from a 9ml description
        """
        seg = cls(nineml_model.name,
                  numpy.array((nineml_model.distal.x, nineml_model.distal.y,
                               nineml_model.distal.z)),
                  nineml_model.distal.diameter)
        if nineml_model.parent and nineml_model.parent.fraction_along != 1.0:
            seg.get_content()['fraction_along'] = nineml_model.parent.\
                                                                 fraction_along
        return seg

    def __init__(self, name, point, diameter):
        super(SegmentModel, self).__init__(name)
        p3d = P3D2(xyz=point, radius=(diameter / 2.0))
        self.set_content({'p3d': p3d,
                          'components': {},
                          'elec_props': {}})

    def __repr__(self):
        return ("Segment: '{}' at point {} with diameter {}"
                .format(self.name, self.distal, self.diameter))

    def to_9ml(self):
        """
        Returns a 9ml version of the node object
        """
        if self.parent:
            proximal = None
            parent = ParentSegment9ml(self.parent.get_index(), 1.0)
        else:
            parent = None
            root = self.get_parent_node().get_content()['p3d']
            proximal = ProximalPoint9ml(root.xyz[0], root.xyz[1], root.xyz[2],
                                        root.radius * 2.0)
        distal = DistalPoint9ml(self.distal[0], self.distal[1], self.distal[2],
                                self.diameter)
        return Segment9ml(self.get_index(), distal, proximal=proximal,
                          parent=parent)

    @property
    def name(self):
        return self._index

#     @property
#     def classes(self):
#         return self.get_content()['classes']

    def set_component(self, comp, overwrite=False):
        """
        Sets a components component to the current segment

        `comp`      -- the component to set
        `overwrite` -- if this flag is set existing components with matching
                       simulator names will be overwritten
        """
        bio_dict = self.get_content()['components']
        # Check for clashing simulator names (the names the simulator refers to
        # the components)
        clash = [c for c in bio_dict.itervalues()
                   if c.simulator_name == comp.simulator_name]
        assert len(clash) < 2, "multi. components with the same simulator_name"
        if clash:
            if overwrite:
                del bio_dict[clash[0]]
            else:
                raise Exception("Clash of import names in setting biophysic "
                                "components between '{}' and '{}' in segment "
                                "'{}".format(comp.name, clash.name, self.name))
        bio_dict[comp.simulator_name] = comp

    @property
    def components(self):
        return self.get_content()['components'].itervalues()

    def _get_comp_by_simulator_name(self, sim_name):
        match = [c for c in self.get_content()['components']
                 if c.simulator_name == sim_name]
        assert len(match) < 2, "multiple '{}' components found ".\
                                                               format(sim_name)
        if not match:
            raise AttributeError("'{}' property not set for segment '{}'"
                                 .format(sim_name, self.name))
        return match[0]

    @property
    def Ra(self):
        return self._get_comp_by_simulator_name('Ra').value

    @property
    def cm(self):
        return self._get_comp_by_simulator_name('cm').value

    @property
    def distal(self):
        return self.get_content()['p3d'].xyz

    @distal.setter
    def distal(self, distal):
        """
        Sets the distal point of the get_segment shifting all child
        segments by the same displacement (to keep their lengths constant)

        `distal`         -- the point to update the distal endpoint of the
                            get_segment to [numpy.array(3)]
        """
        disp = distal - self.distal
        for child in self.all_children:
            child.distal += disp
        self.raw_set_distal(distal)

    def raw_set_distal(self, distal):
        """
        Sets the distal point of the get_segment without shifting child
        segments

        `distal`         -- the point to update the distal endpoint of the
                            get_segment to [numpy.array(3)]
        """
        self.get_content()['p3d'].xyz = distal

    @property
    def diameter(self):
        return self.get_content()['p3d'].radius * 2.0

    @diameter.setter
    def diameter(self, diameter):
        self.get_content()['p3d'].radius = diameter / 2.0

    @property
    def proximal(self):
        parent_distal = self.get_parent_node().get_content()['p3d'].xyz
        if 'fraction_along' in self.get_content():
            return (self.get_parent_node().proximal +
                    self.get_content()['fraction_along'] * parent_distal)
        else:
            return parent_distal

    @property
    def disp(self):
        return self.distal - self.proximal

    @property
    def length(self):
        return numpy.sqrt(numpy.sum(self.disp ** 2))

    @length.setter
    def length(self, length):
        """
        Sets the length of the get_segment, shifting the positions of all child
        nodes so that their lengths stay constant

        `length` -- the new length to set the get_segment to
        """
        seg_disp = self.distal - self.proximal
        orig_length = numpy.sqrt(numpy.sum(seg_disp ** 2))
        seg_disp *= length / orig_length
        self.distal = self.proximal + seg_disp

    @property
    def parent(self):
        parent = self.get_parent_node()
        # Check to see whether the parent of this node is the root node in
        # which case return None or whether it is another get_segment
        return parent if isinstance(parent, SegmentModel) else None

    @parent.setter
    def parent(self, parent):
        if not self.parent:
            raise Exception("Cannot set the parent of the root node")
        self.set_parent_node(parent)

    @property
    def children(self):
        return self.get_child_nodes()

    @property
    def siblings(self):
        try:
            return [c for c in self.parent.children if c is not self]
        except AttributeError:  # No parent
            return []

    @property
    def all_children(self):
        for child in self.children:
            yield child
            for childs_child in child.all_children:
                yield childs_child

    @property
    def branch_depth(self):
        branch_count = 0
        seg = self
        while seg.parent_ref:
            if seg.siblings:
                branch_count += 1
            seg = seg.parent_ref.get_segment
        return branch_count

    @property
    def sub_branches(self):
        """
        Iterates through all sub-branches of the current get_segment, starting
        at the current get_segment
        """
        seg = self
        branch = [self]
        while len(seg.children) == 1:
            seg = seg.children[0]
            branch.append(seg)
        yield branch
        for child in seg.children:
            for sub_branch in child.sub_branches:
                yield sub_branch

    def branch_start(self):
        """
        Gets the start of the branch (a section of tree without any sub
        branches the current get_segment lies on
        """
        seg = self
        while seg.parent and not seg.siblings:
            seg = seg.parent
        return seg


class DynamicComponentModel(object):

    # Declare this class abstract to avoid accidental construction
    __metaclass__ = ABCMeta

    @classmethod
    def from_9ml(cls, nineml_model, container_name):
        parameters = {}
        for key, val in nineml_model.parameters.iteritems():
            conv_unit = val.unit
            if conv_unit is None:
                conv_unit = 'dimensionless'
            elif conv_unit.startswith('/'):
                    conv_unit = '1' + conv_unit
            conv_unit = conv_unit.replace('2', '^2')
            conv_unit = conv_unit.replace('uf', 'uF')
            conv_unit = conv_unit.replace('**', '^')
            parameters[key] = pq.Quantity(val.value, conv_unit)
        if nineml_model.type == 'post-synaptic-conductance':
            Component = SynapseModel
        else:
            Component = IonChannelModel
        component = Component(nineml_model.name, parameters,
                              import_prefix=(container_name + '_'))
        component._source = nineml_model
        return component

    def __deepcopy__(self, memo):
        """
        Override the __deepcopy__ method to avoid copying the source, which
        should stay constant so it can be compared between copies using the
        'is' keyword
        """
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == '_source':
                setattr(result, k, copy(v))
            else:
                setattr(result, k, deepcopy(v, memo))
        return result

    def __init__(self, name, parameters, import_prefix=''):
        """
        `import_prefix -- If a import_prefix is provided, then it is used
                          as a prefix to the component (eg. if
                          biophysics_name='Granule' and component_name='CaHVA',
                          the insert mechanism would be 'Granule_CaHVA'), used
                          for NCML mechanisms
        """
        self.name = name
        self.parameters = parameters
        self.simulator_name = import_prefix + self.name
        self._source = None


class IonChannelModel(DynamicComponentModel):
    pass


class SynapseModel(DynamicComponentModel):
    pass


class StaticComponentModel(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value


class AxialResistanceModel(StaticComponentModel):

    simulator_name = 'Ra'


class MembraneCapacitanceModel(StaticComponentModel):

    simulator_name = 'cm'


def in_units(quantity, units):
    """
    Returns the quantity as a float in the given units

    `quantity` -- the quantity to convert [pq.Quantity]
    `units`    -- the units to convert to [pq.Quantity]
    """
    return numpy.array(pq.Quantity(quantity, units))


class IrreducibleMorphologyException(Exception):
    pass
