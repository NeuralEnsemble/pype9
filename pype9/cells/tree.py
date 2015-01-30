try:
    from btmorph.btstructs2 import STree2, SNode2, P3D2
except ImportError:
    pass  # This is to be refactored out

try:
    from nineml.extensions.morphology import (Morphology as Morphology9ml,
                                              Segment as Segment9ml,
                                              ProximalPoint as ProximalPoint9ml,
                                              DistalPoint as DistalPoint9ml,
                                              ParentSegment as ParentSegment9ml,
                                              Classification as Classification9ml,
                                              SegmentClass as SegmentClass9ml,
                                              Member as Member9ml)
except ImportError:
    pass  # This is dependent on the version of the 9ml library used

try:
    import nineml.extensions.biophysical_cells
except ImportError:
    pass


class Model(STree2):

    @classmethod
    def from_9ml(cls, nineml_model):
        if isinstance(nineml_model, DummyNinemlModel):
            return nineml_model.model  # used in DummyNinemlModel
        morph9ml = nineml_model.morphology
        bio9ml = nineml_model.biophysics
        model = cls(morph9ml.name, source=nineml_model)
        # Add the proximal point of the root get_segment as the root of the
        # model
        model.set_root(numpy.array((morph9ml.root_segment.proximal.x,
                                    morph9ml.root_segment.proximal.y,
                                    morph9ml.root_segment.proximal.z)),
                       morph9ml.root_segment.proximal.diameter)
        # Add the root get_segment and link with root node
        model.root_segment = SegmentModel.from_9ml(morph9ml.root_segment)
        model.root_segment.get_content()['p3d']._type = 1
        # Set the root segments index to be 3 (using a 3 point soma)
        model.root_segment._index = 3
        model.add_node_with_parent(model.root_segment, model.get_root())
        # Create temporary lookup dictionary in order to link segments with
        # their parents by the name specified in the 9ml morphology file
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
        # Clean up fraction_along tags and switch to proximal_offsets
        for seg in seg_lookup.itervalues():
            if 'fraction_along' in seg.get_content():
                offset = -seg.parent.disp * seg.get_content()['fraction_along']
                seg.get_content()['proximal_offset'] = offset
                del seg.get_content()['fraction_along']
        # Add biophysical components
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
    def from_psections(cls, psection_file, mech_file):
        """
        Reads a neuron morphology from the output of a psection() call in hoc
        and generates a model tree

        `filename` -- path to a file containing the psection() output
        """
        # this is imported here to avoid recursive import loop
#         from ..importer.neuron import import_from_hoc
#         return import_from_hoc(psection_file, mech_file)

    def __init__(self, name, source=None):
        self.name = name
        self._source = source
        self.components = {}

    def set_root(self, point, diameter):
        root_point = P3D2(xyz=point, radius=diameter / 2.0, type=1)
        root = SNode2(1)
        root.set_content({'p3d': root_point})
        super(Model, self).set_root(root)

    def set_root_segment(self, segment):
        # TODO: This isn't used yet
        self.set_root(segment.proximal, segment.diameter)
        # Add the root get_segment and link with root node
        self.root_segment = segment
        # Set the SWC type of the root segment to be 1 for soma
        self.root_segment.get_content()['p3d']._type = 1
        # Set the root segments index to be 3 (using a 3 point soma)
        self.root_segment._index = 3
        # Link segment to root_node
        self.add_node_with_parent(self.root_segment, self.get_root())

    def __repr__(self):
        return ("Cell model {} (derived from {}): with {} components and {} "
                "segments"
                .format(self.name, self._source, len(self.components),
                        len(list(self.segments))))

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
                setattr(result, k, v)
            else:
                setattr(result, k, deepcopy(v, memo))
        return result

    def to_9ml(self):
#         clsf = Classification9ml('default',
#                                  [c.to_9ml()
#                                  for c in self.segment_classes.itervalues()])
        return Morphology9ml(self.name,
                             dict([(seg.name, seg.to_9ml())
                                   for seg in self.segments]),
                             {'default': []})

    def write_9ml(self, filename):
        xml = etree.ElementTree(self.to_9ml().to_xml())
        xml.write(filename, encoding="UTF-8", pretty_print=True,
                  xml_declaration=True)

    def _normalise_SWC_indices(self):
        # the self.segments generator will traverse the tree in a depth-first
        # search so the enumerated indices will satisfy SWC's constraint that
        # children have a higher index than their parents. Starts from 4 as the
        # first three points are reserved for the 3-point soma
        for i, seg in enumerate(islice(self.segments, 1, None)):
            seg._index = i + 4

    def write_SWC_tree_to_file(self, filename):
        self._normalise_SWC_indices()
        super(Model, self).write_SWC_tree_to_file(filename)

    def partition_soma_and_other_nodes(self):
        soma, other = super(Model, self).partition_soma_and_other_nodes()
        other.insert(0, soma[2])
        return soma, other

    def _3point_SWC_soma(self, point1, point2, _):
        """
        Because the soma (root_segment) is only represented by two segments
        in this model I need to overwrite this function in order to create the
        third point in between the two endpoints to match the assumptions in
        BTmorph
        """
        point1, point2 = deepcopy((point1, point2))
        mid_point = P3D2((point1.xyz + point2.xyz) / 2.0,
                         (point1.radius + point2.radius) / 2.0)
        avg_offset = (numpy.sum(c.proximal_offset
                                for c in self.root_segment.children) /
                      len(self.root_segment.children))

        for p in (point1, mid_point, point2):
            p.xyz = p.xyz + avg_offset
        return super(Model, self)._3point_SWC_soma(point1, mid_point, point2)

    def add_component(self, component):
        self.components[component.name] = component
        return component

    def clear_current_clamps(self, skip=[]):
        self.components = dict((n, c) for n, c in self.components.iteritems()
                               if not isinstance(c, CurrentClampModel) or
                                  n in skip)
        for seg in self.segments:
            seg.components = [c for c in seg.components
                              if not isinstance(c, CurrentClampModel) or
                                 c.name in skip]

    @property
    def segments(self):
        """
        Segments are not stored directly as a flat list to allow branches
        to be edited by altering the children of segments. This iterator is
        then used to flatten the list of segments
        """
        return chain([self.root_segment], self.root_segment.all_children)

    def component_segments(self, component):
        """
        Returns the segments that use the given component

        `component` -- The component or component name to lookup the
                       related segments for
        """
        if isinstance(component, str):
            component = self.components[component]
        return (seg for seg in self.segments if component in seg.components)

    def components_of_class(self, class_name):
        """
        Returns a generator for the components of class 'class_name'
        """
        return (c for c in self.components.itervalues()
                if c.class_name == class_name)

    def distances_from_soma(self, seg_names=None):
        if seg_names is None:
            segments = self.segments
        else:
            segments = (self.get_segment(n) for n in seg_names)
        for seg in segments:
            dist = numpy.sum(s.length
                             for s in seg.path_to_ancestor(self.root_segment))
            # Offset by half the segment's length and the root_segment's length
            dist += (seg.length - self.root_segment.length) / 2.0
            yield dist, seg

    @property
    def branches(self):
        """
        An iterator over all branches in the tree
        """
        return self.root_segment.sub_branches

    @classmethod
    def branch_sections_w_comps(cls, branch):
        for comps, section in groupby(branch, lambda s: s.id_components):
            yield list(section), comps

    @classmethod
    def branch_sections(cls, branch):
        for section, _ in cls.branch_sections_w_comps(branch):
            yield section

    @property
    def sections(self):
        """
        An iterator over groups of contiguous segments with no branching and
        consistent ionic components
        """
        for branch in self.branches:
            for section in self.branch_sections(branch):
                yield section

    @property
    def sections_w_comps(self):
        """
        An iterator over groups of contiguous segments with no branching and
        consistent ionic components
        """
        for branch in self.branches:
            for section, comps in self.branch_sections_w_comps(branch):
                yield section, comps

    def get_segment(self, name):
        match = [seg for seg in self.segments if seg.name == name]
        # TODO: Need to check this on initialisation
        assert len(match) <= 1, "Multiple segments with key '{}'".format(name)
        if not len(match):
            raise KeyError("Segment '{}' was not found".format(name))
        return match[0]

    def merge_leaves(self, only_most_distal=False, num_merges=1,
                     normalise=True, max_length=False,
                     error_if_irreducible=True, stack_with_parent=True):
        """
        Reduces a 9ml morphology, starting at the most distal branches and
        merging them with their siblings.
        """
        merged_tree = deepcopy(self)
        merged = True
        for merge_index in xrange(num_merges):
            if only_most_distal:
                # Get the branches at the maximum depth
                max_branch_depth = max(seg.branch_depth
                                       for seg in merged_tree.segments)
                candidates = [branch for branch in merged_tree.branches
                              if branch[0].branch_depth == max_branch_depth]
            else:
                candidates = [branch for branch in merged_tree.branches
                              if not branch[-1].children]
            merged = []
            # Group together candidates that are "siblings", i.e. have the same
            # parent and also the same ionic components
            get_parent = lambda b: b[0].parent
            # Potentially this sort is unnecessary as it should already be
            # sorted by parent due to the way the merged_tree is traversed, but
            # it is probably safer this way
            families = groupby(sorted(candidates, key=get_parent),
                               key=get_parent)
            for parent, siblings_iter in families:
                siblings = list(siblings_iter)
                new_segments = []
                unmerged = [zip(*Model.branch_sections_w_comps(b))
                            for b in siblings]
                while len(unmerged) > 1:
                    # Get the "longest" remaining branch, in terms of how many
                    # sections (different sets of component regions) it has
                    # (i.e. not actually length)
                    longest = max(unmerged, key=lambda x: len(x[0]))
                    # Get the branches that can be merged with this branch
                    to_merge = [umg for umg in unmerged
                                if all(u == l for u, l in zip(umg[1],
                                                              longest[1]))]
                    # Find the branches that can be merged with it
                    unmerged = [x for x in unmerged if x not in to_merge]
                    # Skip if this branch cannot be merged with any other
                    # branches (doesn't need to be merged with itself)
                    if len(to_merge) == 1:
                        if stack_with_parent:
                            if len(longest[0]) == 2:
                                if longest[1][0] != parent.id_components:
                                    continue
                                assert all(len(u[0]) == 1 for u in unmerged)
                                to_remove = [u[0][0][0] for u in unmerged]
                                to_merge = unmerged + [((longest[0][1],),
                                                        (longest[1][1],))]
                                unmerged = []
                                if any(m[1][0] != longest[1][1]
                                       for m in to_merge):
                                    continue
                                section_parent = longest[0][0][-1]
                                new_segments.extend(longest[0][0])
                            elif len(longest[0]) == 1:
                                assert len(unmerged) == 1
                                if longest[1][0] == parent.id_components:
                                    near = longest[0][0][0]
                                    far = unmerged[0][0][0][0]
                                else:
                                    near = unmerged[0][0][0][0]
                                    far = longest[0][0][0]
                                new_segments.extend(unmerged[0][0][0])
                                new_segments.extend(longest[0][0])
                                merged_tree.add_node_with_parent(far, near)
                                parent.remove_child(far)
                                unmerged = []
                                continue
                            else:
                                raise NotImplementedError
                        else:
                            continue
                    else:
                        # Initially set the "section_parent" (the parent of the
                        # next newly created section) to the parent of the
                        # branches
                        section_parent = parent
                        to_remove = [b[0][0][0] for b in to_merge]
                    merged.extend(to_merge)
                    for sec_list, distr_comps in zip(izip_longest(
                                                     *(s[0] for s in to_merge),
                                                     fillvalue=None),
                                                     longest[1]):
                        sec_siblings = [s for s in sec_list if s is not None]
                        avg_dir = numpy.sum(seg.disp
                                            for seg in chain(*sec_siblings))
                        avg_dir = avg_dir / numpy.sqrt(numpy.sum(avg_dir ** 2))
                        # Get the combined properties of the segments to be
                        # merged
                        if max_length:
                            # Use the maximum length of the branches to merge
                            new_length = numpy.max([numpy.sum(seg.length
                                                              for seg in sib)
                                                    for sib in sec_siblings])
                        else:
                            # Use the average length of the branches to merge
                            new_length = (numpy.sum(seg.length
                                             for seg in chain(*sec_siblings)) /
                                          len(sec_siblings))
                        surface_area = numpy.sum(seg.surface_area
                                               for seg in chain(*sec_siblings))
                        # Calculate the (in-parallel) axial resistance of the
                        # branches to be merged as a starting point for the
                        # subsequent tuning step (see the returned
                        # 'needs_tuning' list)
                        axial_cond = 0.0
                        for branch in siblings:
                            axial_cond += 1.0 / numpy.array([seg.Ra
                                                      for seg in branch]).sum()
                        axial_resistance = (1.0 / axial_cond)
                        # Get the diameter of the merged segment so as to
                        # conserve total membrane surface area given that the
                        # length of the segment is the average of the
                        # candidates to be merged.
                        diameter = surface_area / (new_length * numpy.pi)
                        # Get a unique name for the generated segments FIXME:
                        # this is not guaranteed to be unique (but should be in
                        # most cases given a sane naming convention)
                        sorted_names = sorted([s[0].name
                                               for s in sec_siblings])
                        name = sorted_names[0] + '_thru_' + sorted_names[-1]
                        # Get the displacement of the new branch, which is in
                        # the same direction as the parent
                        disp = new_length * avg_dir
                        # Create the segment which will form the new branch
                        segment = SegmentModel(name,
                                               section_parent.distal + disp,
                                               diameter)
                        # Add distributed components to segment
                        for comp in distr_comps:
                            segment.set_component(comp)
                        # TODO: Need to add discrete components too Create new
                        # Ra comp to hold the adjusted axial resistance
                        Ra_comp = AxialResistanceModel('Ra_' + name,
                                                       axial_resistance,
                                                       needs_tuning=True)
                        merged_tree.add_component(Ra_comp)
                        segment.set_component(Ra_comp)
                        # Add new segment to merged_tree
                        merged_tree.add_node_with_parent(segment,
                                                         section_parent)
                        section_parent = segment
                        new_segments.append(segment)
    #                 assert ((numpy.sum(s.surface_area for s in to_remove) -
    #                          numpy.sum(s.surface_area for s in new_segments))
    #                         < 1e-10), "mismatch in surface areas"
                    # Remove old branches from merged_tree
                    for seg in to_remove:
                        parent.remove_child(seg)
    #                 for comps, surface_area in merged_tree.category_surface_areas(): @IgnorePep8
    #                     assert inital_surface_areas[comps] - surface_area < 1e-10 @IgnorePep8
            if not merged:
                break
        if normalise:
            merged_tree = merged_tree.normalise_spatial_sampling()
        if not merged:
            if error_if_irreducible:
                raise IrreducibleMorphologyException(
                                "Could not reduce the morphology after {} "
                                "mergers".format(merge_index))
            else:
                print ("Warning: Could not reduce the morphology after {} "
                       "mergers".format(merge_index))
        return merged_tree

    def normalise_spatial_sampling(self, **d_lambda_kwargs):
        """
        Regrids the spatial sampling of the segments in the tree via NEURON's
        d'lambda rule

        `freq`       -- frequency at which AC length constant will be computed
                        (Hz)
        `d_lambda`   -- fraction of the wavelength
        """
        # Make a new copy of the tree, starting from the root segment from
        # which to build the normalised tree from
        normalised_tree = Model(self.name, self._source)
        for comp in self.components.itervalues():
            normalised_tree.add_component(deepcopy(comp))
        # FIXME: this will copy whole tree which while safe is a bit
        # inefficient
        new_root_segment = deepcopy(self.root_segment)
        # Clear the children from the new tree (I don't think this is not
        # strictly necessary but better safe than sorry)
        new_root_segment.remove_children()
        # Set the new root to the new tree
        normalised_tree.set_root_segment(new_root_segment)
        # A temporary dictionary to assist the linking of segments with
        # their parents in the normalised tree
        parent_lookup = {self.root_segment.name: new_root_segment.name}
        # Loop through all branches (chains of segments linked together by
        # siblingless parent-child relationships). A slight warning but this
        # relies on traversal of the branches in order from parents to children
        # (either depth-first or breadth-first should be okay though)
        for section in self.sections:
            parent = section[0].parent
            # FIXME: Should be able to normalise the soma too (maybe make a
            # fake parent in this case)
            if parent:
                # Get the section length
                section_length = numpy.sum(seg.length for seg in section)
                # Get weighted average of diameter Ra and cm by segment length
                diameter = 0.0
                Ra = 0.0 #* pq.ohm * pq.cm
                cm = 0.0 * pq.uF / (pq.cm ** 2)
                for seg in section:
                    diameter += seg.diameter * seg.length
                    Ra += seg.Ra * seg.length
                    cm += seg.cm * seg.length
                # TODO: instead of finding the average, I could fit a spline
                #       to interpolate these values along the newly fitted
                #       section. Same goes for merged sections
                diameter /= section_length
                Ra /= section_length
                cm /= section_length
                # Calculate the number of required segments via NEURON's
                # d'lambda rule
                num_segments = self.d_lambda_rule(section_length,
                                                  diameter * pq.um,
                                                  Ra, cm, **d_lambda_kwargs)
                # Generate the names for the new segments, starting with the
                # name of the first segment and finishing with the name of the
                # last segment (important because it will be looked up when
                # searching for parents of subsequently normalised sections)
                start_name = section[0].name
                if num_segments > 1:
                    if len(section) > 1:
                        end_name = section[-1].name
                    else:
                        end_name = start_name + '_end'
                else:
                    end_name = start_name
                new_seg_names = [start_name]
                for i in xrange(1, num_segments - 1):
                    new_seg_names.append('{}_to_{}_{}'.format(start_name,
                                                              end_name, i))
                if num_segments > 1:
                    new_seg_names.append(end_name)
                # For looking up the end of the section from the name of the
                # parent in the original tree
                parent_lookup[section[-1].name] = end_name
                # Get a list of distributed components to insert into the new
                # tree
                distr_comps = [normalised_tree.components[c.name]
                               for c in section[0].distributed_components]
                # Get the direction of the section
                direction = section[-1].distal - section[0].proximal
                disp = direction * (section_length /
                                    numpy.sqrt(numpy.sum(direction ** 2)))
                # Get the displacement for each segment
                # Get the set of all axial resistance components in the section
                Ra_set = set([seg.get_component_by_type(AxialResistanceModel)
                               for seg in section])
                # Update Ra if required (if it is inconsistent along the
                # section)
                if len(Ra_set) > 1:
                    new_Ra_comp = AxialResistanceModel(
                                        '{}_{}_Ra'.format(section[0].name,
                                                         section[-1].name), Ra,
                                        needs_tuning=any(ra.needs_tuning
                                                         for ra in Ra_set))
                    normalised_tree.add_component(new_Ra_comp)
                else:
                    # There is only one Ra_comp so
                    new_Ra_comp = next(iter(Ra_set))
                # Find the equivalent parent in the new normalised tree
                parent = normalised_tree.get_segment(
                                                    parent_lookup[parent.name])
                self.create_section(new_seg_names, disp, parent, diameter,
                                    distr_comps,
                                    proximal_offset=section[0].proximal_offset)
        return normalised_tree

    @classmethod
    def create_section(cls, segment_names, displacement, parent, diameter,
                       distributed_comps=[], discrete_comps_fracs=[],
                       proximal_offset=numpy.array([0.0, 0.0, 0.0])):
        """
        Creates a linear chain of n segments starting from 'parent', with n
        determined by the number of segment names provided.

        `segment_names`        -- a list of names for the new segments. The
                                  number of names determines the number of
                                  segments created
        `displacement`         -- the direction and length of the created chain
                                  of segments.
        `parent`               -- the parent segment from which to grow the
                                  chain from
        `diameter`             -- the diameter of the segments in the chain
        `distributed_comps`    -- the distributed components to insert into
                                  each segment
        `discrete_comps_fracs` -- a list (or iterable) of tuples containing a
                                  discrete component and the fraction along the
                                  segment it should be inserted
        `proximal_offset`      -- the offset from the distal point of the
                                  parent the first segment should start
        """
        num_segs = len(segment_names)
        # Get the displacement for each segment
        seg_disp = displacement / float(num_segs)
        # Break the discrete components into groups based on which segment they
        # should be inserted into
        grp_by_seg = dict(groupby(sorted(discrete_comps_fracs, itemgetter(1)),
                                  lambda c_f: numpy.floor(c_f[1] * num_segs)))
        discrete_comps_by_seg = [(i, grp_by_seg.get(i, []))
                                 for i in xrange(num_segs)]
        # Loop through and create the segment chain
        previous_segment = parent
        new_section = []
        for seg_name, (seg_i, discrete_comps) in zip(segment_names,
                                                     discrete_comps_by_seg):
            # Calculate its distal point
            distal = parent.distal + proximal_offset + seg_disp * (seg_i + 1)
            segment = SegmentModel(seg_name, distal, diameter)
            # Set distributed components on segment
            for comp in distributed_comps:
                segment.set_component(comp)
            # Set discrete components on segment
            for comp in discrete_comps:
                segment.set_component(comp)
            # Append the segment to the chain
            previous_segment.add_child(segment)
            segment.set_parent_node(previous_segment)
            # Increment the 'previous_segment' reference to the current segment
            previous_segment = segment
            # Add the segment to the list for the new section
            new_section.append(segment)
        # Set the proximal offset if it is present in the section start
        # (typically when the section starts from the soma)
        if proximal_offset.sum():
            new_section[0].proximal_offset = proximal_offset
        return new_section

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

    def passive_model(self, leak_components):
        """
        Returns a copy of the cell with all the non-passive components
        removed

        `leak_components` -- the leak components to retain in the copy of the
                             model
        """
        def is_passive(comp):
            return (comp.class_name in leak_components or
                    (not isinstance(comp, IonChannelModel) and
                     not isinstance(comp, IonConcentrationModel)))
        passive = deepcopy(self)
        passive.components = dict((n, c) for n, c in passive.components.items()
                               if is_passive(c))
        for seg in passive.segments:
            seg.components = [c for c in seg.components if is_passive(c)]
        return passive

    def plot(self, highlight=[], show=True):
        from btmorph.btviz import plot_3D_SWC
        import matplotlib.pyplot as plt
        for b in highlight:
            for seg in b:
                seg.diameter = 10
        self.write_SWC_tree_to_file('/tmp/swc_tree.swc')
        plot_3D_SWC('/tmp/swc_tree.swc', filter=range(10),
                    color_list=['r', 'g', 'b', 'c', 'm', 'y', 'r--', 'b--',
                                'g--'] * 2)
        if show:
            plt.show()

    def categorise_segments_for_SWC(self, offset=3):
        comp_classes = set()
        for section in self.sections:
            comp_classes.add(section[0].id_components)
        type_index_dict = dict((c, i)
                               for i, c in enumerate(sorted(comp_classes,
                                                        key=lambda x: len(x))))
        for section in self.sections:
            type_index = offset + type_index_dict[section[0].id_components]
            for seg in section:
                seg.get_content()['p3d'].type = type_index

    def get_segment_categories(self):
        sortkey = lambda s: sorted(s.id_components)
        for comp, segments in groupby(sorted(self.segments, key=sortkey),
                                      key=sortkey):
            yield frozenset(comp), list(segments)

    def category_surface_areas(self):
        for comp, segs in self.get_segment_categories():
            yield comp, numpy.sum(s.surface_area for s in segs)


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

    def __init__(self, name, point, diameter, swc_type=3):
        super(SegmentModel, self).__init__(None)
        self.name = name
        p3d = P3D2(xyz=point, radius=(diameter / 2.0), type=swc_type)
        self.set_content({'p3d': p3d,
                          'components': []})

    def __repr__(self):
        return ("Segment: '{}' at point {} with diameter {}"
                .format(self.name, self.distal, self.diameter))

    def __str__(self):
        return "Segment: {}".format(self.name)

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

    def set_component(self, comp, overwrite=False):
        """
        Sets a components component to the current segment

        `comp`      -- the component to set
        `overwrite` -- if this flag is set existing components with matching
                       simulator names will be overwritten
        """

        comps_list = self.get_content()['components']
        if isinstance(comp, PointProcessModel):
            # No need to check for point process model as multiple components
            # can be added
            comps_list.append(comp)
        else:
            # Check for clashing simulator names (the names the simulator
            # refers to the components)
            clash = [c for c in comps_list if c.class_name == comp.class_name]
            assert len(clash) < 2, "multi. components with the same class_name"
            if clash:
                if overwrite:
                    comps_list.remove(clash[0])
                else:
                    raise Exception("Clash of import names in setting "
                                    "biophysics components between '{}' and "
                                    "'{}' in segment '{}"
                                    .format(comp.name, clash[0].name,
                                            self.name))
            comps_list.append(comp)

    def remove_component(self, comp):
        self.get_content()['components'].remove(comp)

    @property
    def components(self):
        return self.get_content()['components']

    @components.setter
    def components(self, components):
        self.get_content()['components'] = components

    @property
    def discrete_components(self):
        return (c for c in self.components if isinstance(c, PointProcessModel))

    @property
    def distributed_components(self):
        return (c for c in self.components
                  if not isinstance(c, PointProcessModel))

    @property
    def id_components(self):
        return frozenset((c for c in self.components
                          if isinstance(c, IonChannelModel) or
                             isinstance(c, IonConcentrationModel) or
                             isinstance(c, MembraneCapacitanceModel)))

    def get_component_by_type(self, comp_type):
        match = [c for c in self.components if isinstance(c, comp_type)]
        assert len(match) < 2, "multiple '{}' components found ".\
                                                     format(comp_type.__name__)
        if not match:
            raise AttributeError("'{}' component not present in segment '{}'"
                                 .format(comp_type.__name__, self.name))
        return match[0]

    @property
    def Ra(self):
        return self.get_component_by_type(AxialResistanceModel).value

    @property
    def cm(self):
        return self.get_component_by_type(MembraneCapacitanceModel).value

    @property
    def proximal(self):
        parent = self.get_parent_node()
        if parent is None:
            raise Exception("Proximal not defined as parent is not set")
        p = parent.get_content()['p3d'].xyz + self.proximal_offset
        # This is to protect against attempts to set the contents of the
        # proximal point which won't do anything as it is a copy of the actual
        # point (which is done because it cannot be updated without affecting
        # the parent which may or may not be desired)
        p.setflags(write=False)
        return p

    @property
    def proximal_offset(self):
        try:
            offset = self.get_content()['proximal_offset']
        except KeyError:
            offset = numpy.zeros((3,))
        return offset

    @proximal_offset.setter
    def proximal_offset(self, offset):
        self.get_content()['proximal_offset'] = offset

    @property
    def distal(self):
        """
        Care is taken to prevent unintentional writing of this array,
        you should use the setter instead
        """
        p = deepcopy(self.get_content()['p3d'].xyz)
        # This is to protect against attempts to set the contents of the distal
        # point which won't do anything as it is a copy of the actual point
        # (which is done because when it is set using the following setter the
        # whole sub-tree is shifted accordingly)
        p.setflags(write=False)
        return p

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
            child.distal = child.distal + disp
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
    def surface_area(self):
        return self.diameter * numpy.pi * self.length

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

    def remove_children(self):
        for child in self.children:
            child.set_parent_node(None)
        self._child_nodes = []

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

    def containing_branch(self):
        seg = self.branch_start()
        branch = []
        while len(seg.children) == 1:
            branch.append(seg)
            seg = seg.children[0]
        branch.append(seg)
        return branch

    def is_leaf(self):
        return len(self.children) == 0

    def path_to_ancestor(self, ancestor):
        """
        A generator of the tree path from the current segment up to the
        provided ancestor.

        `ancestor` -- a segment which is an ancestor of this segment
        """
        next_ancestor = self
        while next_ancestor is not ancestor:
            next_ancestor = next_ancestor.parent
            if next_ancestor is None:
                raise Exception("Segment '{}' is not an ancestor of segment "
                                "'{}'".format(ancestor.name, self.name))
            yield next_ancestor


class ComponentModel(object):

    needs_tuning = False

    def __init__(self):
        self.global_parameters = {}


class DynamicComponentModel(ComponentModel):

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
        component = Component(nineml_model.name,
                              (container_name + '_' + nineml_model.name),
                              parameters)
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
                setattr(result, k, v)
            else:
                setattr(result, k, deepcopy(v, memo))
        return result

    def __init__(self, name, class_name, parameters):
        """
        `name`         -- Name used to refer to the componentclass in the model
                          (eg. 'spiny_dendrite_leak')
        `class_name`   -- Name of the class of the componentclass. For example in
                          NEURON, this would be the name used for the imported
                          NMODL mechanism. Therefore this class name has to be
                          unique for any given segment and two components, say
                          for example only one of 'proximal_dendrite_leak' and
                          'spiny_dendrite_leak' can be set on the same segment
                          if they both use the 'Lkg' componentclass class.
        `parameters`   -- The parameters of the model
        """
        super(DynamicComponentModel, self).__init__()
        self.name = name
        self.class_name = class_name
        self.parameters = parameters
        self._source = None  # Used to store the source file (eg. *.9ml)

    def __repr__(self):
        return ("{} Component '{}', with params: {}"
                .format(self.class_name, self.name, self.parameters))

    def iterate_parameters(self, segment):
        """
        Iterates through parameters calculating distributions if necessary
        """
        for param, val in self.parameters.iteritems():
            if isinstance(val, DistributedParameter):
                val = val.value(segment)
            yield param, val


class IonChannelModel(DynamicComponentModel):
    pass


class PointProcessModel(DynamicComponentModel):
    pass


class SynapseModel(PointProcessModel):
    pass


class CurrentClampModel(PointProcessModel):
    pass


class StaticComponentModel(ComponentModel):

    def __init__(self, name, value):
        super(StaticComponentModel, self).__init__()
        self.name = name
        self.value = value

    @property
    def parameters(self):
        """
        Provided for compatibility with processing of parameters
        """
        # FIXME: Probably should make this class have a parameters dict for
        #       consistency
        return {self.param_name: self.value}


class AxialResistanceModel(StaticComponentModel):

    param_name = class_name = 'Ra'

    def __init__(self, name, value, needs_tuning=False):
        super(AxialResistanceModel, self).__init__(name, value)
        self.needs_tuning = needs_tuning


class MembraneCapacitanceModel(StaticComponentModel):

    param_name = class_name = 'cm'


class IonConcentrationModel(StaticComponentModel):

    def __init__(self, ion_name, value):
        super(IonConcentrationModel, self).__init__(ion_name, value)
        self.class_name = ion_name + '_ion'
        self.param_name = 'e' + ion_name


class DistributedParameter(object):

    def __init__(self, expr_str):
        self.cached = {}
        self._expr_str = expr_str
        self._expr = eval(expr_str)

    def __reduce__(self):
        return self.__class__, (self._expr_str,)

    def value(self, segment):
        try:
            val = self.cached[segment.name]
        except KeyError:
            val = self.cached[segment.name] = self._expr(segment)
        return val


def in_units(quantity, units):
    """
    Returns the quantity as a float in the given units

    `quantity` -- the quantity to convert [pq.Quantity]
    `units`    -- the units to convert to [pq.Quantity]
    """
    return numpy.array(pq.Quantity(quantity, units))


class BranchAncestry(object):
    """
    Is used to map merged branches back to their original position in the full
    morphology. This is done by storing a subtree for every merged segment in
    a dictonary
    """

    class SubBranch(object):

        def __init__(self, start_segment, end_segment=None):
            self.start_name = start_segment.name
            self.end_name = end_segment.name if end_segment else None

    def __init__(self, full_tree):
        self.full_tree = full_tree
        self.history = {}
        self.translations = {}

    def record_merger(self, new_segment, merged_branches):
        # Get the start of the branch containing the new segment
        branch_start = new_segment.branch_start()
        # If the branch start is the same as the new_segment, which will occur
        # when the merge has stopped at a component mismatch border
        if branch_start is new_segment:
            self.history[branch_start.name] = [self.SubBranch(b[0])
                                               for b in merged_branches]
        # If the branch start is before the merger than simply add the name
        # of the branch_start to the list of translations
        else:
            self.history[branch_start.name] = [self.SubBranch(branch_start)]

    def record_replacement(self, new_section, old_section):
        if old_section[-1].is_leaf():
            sub_section = self.SubBranch(old_section[0])
        else:
            sub_section = self.SubBranch(old_section[0], old_section[-1])
        self.history[new_section[0].name] = sub_section

    def get_original(self, segment):
        seg_name = segment.name
        while seg_name in self.history:
            seg_name = self.history[seg_name].start_name
        return self.full_tree.get_segment(seg_name)


class IrreducibleMorphologyException(Exception):
    pass