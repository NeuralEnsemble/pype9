from __future__ import absolute_import
import os.path
import re
from copy import deepcopy
import itertools
import numpy
from btmorph.btstructs2 import SNode2, P3D2
import nineline.cells
print nineline.cells.__file__
from nineline.cells import (Model, SegmentModel, AxialResistanceModel,
                            MembraneCapacitanceModel, IonChannelModel,
                            ReversalPotentialModel, CurrentClampModel,
                            SynapseModel)


def import_from_hoc(psection_file, mech_file):
    model = load_morph_from_psections(psection_file)
    add_mechs_to_model(model, mech_file)
    map_segments_to_components(model)
    for n in sorted(model.components.keys()):
        print n
    return model


def load_morph_from_psections(psection_file):
    model = Model('psection_import',
            source=os.path.join(os.path.dirname(psection_file), '..'))
    segments = {}
    in_section = False
    started = False
    with open(psection_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith('points: '):  # Reads pt3 point dumps
                # Load the 3d points in the section
                points = numpy.array([float(p) for p in line[8:].split(' ')]).\
                                                               reshape((-1, 3))
                started = True
            elif not started:  # Avoids any leading output lines
                continue
            # If not in section and there is something printed on the line
            # assume it is the start of a new segment
            elif not in_section and line:
                # Skip if it is just one of the random integers that hoc spits
                # out from time to time
                try:
                    int(line)
                    continue
                except ValueError:
                    pass
                # Split line on white space
                parts = line.split(' ')
                # Get segment name
                name = parts[0]
                # Initialise containers to be populated from subsequent lines
                components = {}
                connections = []
                # Read the attributes of the segment from this line
                attributes = {}
                for key_val in parts[2:]:
                    key_val = key_val.strip()
                    if key_val:
                        key, val = key_val.split('=')
                        attributes[key] = float(val)
                in_section = True
            elif in_section:
                # If the closing trailing brace is found collect all the read
                # data into a SegmentModel object
                if line.startswith('}'):
                    diam = components['morphology']['diam']
                    Ra = attributes['Ra']
                    cm = components['capacitance']['cm']
                    num_segments = attributes['nseg']
                    assert num_segments == 1, "Only implemented for nseg == 1"
                    proximal = points[0, :]
                    distal = points[1, :]
                    if len(connections) == 0:
                        parent_name = None
                        root_point = P3D2(xyz=proximal,
                                          radius=diam / 2.0)
                        root = SNode2('__ROOT__')
                        root.set_content({'p3d': root_point})
                        model.set_root(root)
                    elif len(connections) == 1:
                        parent_name = connections[0]
                    else:
                        raise Exception("Segment '{}' has more than one "
                                        "connection (expected only one "
                                        "'parent' segment)")
                    segment = SegmentModel(name, distal, diam)
                    # At this stage the inserted mechanisms are just stored
                    # in the 'inserted' item in the content dictionary
                    # and are mapped to component objects in the map mechanisms
                    # function
                    inserted = dict((n, dict((strip_comp(k, n), v)
                                             for k, v in d.iteritems()))
                                    for n, d in components.iteritems())
                    del inserted['morphology']
                    inserted['Ra'] = {'Ra': Ra}
                    segment.get_content().update({'parent_name': parent_name,
                                                  'Ra': Ra, 'cm': cm,
                                                  'inserted': inserted})
                    segments[segment.name] = segment
                    if parent_name is None:
                        model.root_segment = segment
                    in_section = False
                # If line starts with 'insert' read the component and what has
                # been inserted
                elif line.startswith('insert'):
                    component_name, parameters = line[6:].strip().split('{')
                    component = {}
                    if parameters != '}':
                        for key_vals in parameters.strip()[:-1].split(' '):
                            key, val = key_vals.strip().split('=')
                            component[key] = float(val)
                    components[component_name.strip()] = component
                # If line starts with 'connect' read the parent connection
                elif line.find('connect') > 0:
                    parts = line.strip().split(' ')
                    connections.append(parts[0])
    # Convert parent references from names to Section objects
    for s in segments.itervalues():
        if s.get_content()['parent_name'] is None:
            model.add_node_with_parent(s, model.get_root())
        else:
            model.add_node_with_parent(
                            s, segments[s.get_content()['parent_name']])
    return model


def strip_comp(param_name, comp_name):
    if param_name.endswith(comp_name):
        param_name = param_name[:-(len(comp_name) + 1)]  # the +1 is for the _
    return param_name


def add_mechs_to_model(model, mech_file):
    inserted_mechs, mechs_list, point_procs = read_mech_dump_file(mech_file)
    for name, params in inserted_mechs.iteritems():
        if name == 'Ra':
            if isinstance(params, dict):
                for key, vals in iterate_param_components(name, params):
                    model.add_component(AxialResistanceModel(key, vals['Ra']))
            else:
                model.add_component(AxialResistanceModel('Ra', float(params)))
        elif name == 'capacitance':
            if isinstance(params, dict):
                for key, vals in iterate_param_components(name, params):
                    model.add_component(MembraneCapacitanceModel(key,
                                                                 vals['cm']))
            else:
                model.add_component(MembraneCapacitanceModel('cm',
                                                             float(params)))
        # Otherwise if params is a dict it should be a general density
        # mechanism with multiple parameter groups
        elif isinstance(params, dict):
            for key, vals in iterate_param_components(name, params):
                model.add_component(IonChannelModel(key, name, vals))
        elif name in mechs_list:
            assert params is None
            model.add_component(IonChannelModel(name, name, {}))
        # If it gets down this far and it starts with e then I think this is
        # a fairly safe assumption
        elif name.startswith('e'):
            model.add_component(ReversalPotentialModel(name[1:],
                                                       float(params)))
        # Else it should be single parameter of a mechanism that has a constant
        # value
        else:
            comp_name = [m for m in mechs_list if name.endswith(m)]
            assert len(comp_name) < 2
            if not comp_name:
                raise Exception("Unrecognised inserted mechanism")
            comp_name = comp_name[0]
            param_name = strip_comp(name, comp_name)
            model.add_component(IonChannelModel(comp_name, comp_name,
                                                {param_name: float(params)}))
    for name, params in point_procs.iteritems():
        if name.startswith('I'):  # FIXME: This is a poor assumption, not sure how to improve though @IgnorePep8
            for key, vals in iterate_param_components(name, params):
                model.add_component(CurrentClampModel(key, name, vals))
        else:
            for key, vals in iterate_param_components(name, params):
                model.add_component(SynapseModel(key, name, vals))


def read_mech_dump_file(mech_file):
    # Load mechanisms model view dump from file into nested dictionaries
    # for convenient access
    with open(mech_file) as f:
        contents = {}
        containers = [contents]
        for line in f:
            strip_line = line.strip()
            if strip_line:
                depth = (len(line) - len(line.lstrip())) // 4
                if strip_line.startswith('* '):
                    strip_line = strip_line[2:]  # remove '* '
                    # remove numbers from the front of item
                    strip_line = re.sub('[0-9]+ ', '', strip_line)
                    for _ in xrange(depth, len(containers) - 1):
                        containers.pop()
                    container = {}
                    containers[-1][strip_line] = container
                    containers.append(container)
                else:
                    key_val = strip_line.split('=')
                    if len(key_val) == 2:
                        key, val = key_val
                        val = key_val[0].strip()
                    else:
                        key = '='.join(key_val)
                        val = None
                    index = key.find(' (')
                    if index == -1:
                        index = len(key)
                    key = key[:index]
                    key = key.strip()
                    for _ in xrange(depth, len(containers) - 1):
                        containers.pop()
                    containers[-1][key] = val
    inserted_mechs = contents['real cells']['root soma']['inserted mechanisms']
    mechs_list = contents['Density Mechanisms']['Mechanisms in use']
    point_procs = contents['point processes (can receive events) of base '
                           'classes']['Point Processes']
    return inserted_mechs, mechs_list, point_procs


def iterate_param_components(name, params):
    # For each of the parameters with a 'dict' value, generate a
    # list of values (zipped with the parameter name for convenience),
    # stripping the component suffix from the parameter name
    varying = [[(strip_comp(k, name), w) for w in v.values()]
               for k, v in params.iteritems() if isinstance(v, dict)]
    # For each of the parameters with a 'str' value (i.e. not a dict), add to
    # constant dictionary, stripping the component suffix from the parameter
    # name and convert the values into floats
    constant = dict((strip_comp(k, name), float(v) if v is not None else None)
                    for k, v in params.iteritems() if not isinstance(v, dict))
    # Loop through all combinations of varying parameters and create a new
    # component for each combination (although some won't end up being used)
    # if that combination isn't present in the cell morphology
    for combination in itertools.product(*varying):
        # Initialise comb_key which is generated by looping through contstants
        comp_name = name
        # Copy constants into vals dictionary
        vals = deepcopy(constant)
        # Loop through param-name/value pairs and set value appending the param
        # index
        for param_name, val in combination:
            # Append the param name and value to the comp_name replacing
            # decimal points and minus signs
            if val is not None:
                comp_name += ('__' + param_name +
                              val.replace('.', '_').replace('-', 'm'))
                vals[param_name] = float(val)
            else:
                vals[param_name] = None
        # Yield the component name and dictionary for the current combination
        yield comp_name, vals


def map_segments_to_components(model):
    for seg in model.segments:
        for mech_name, params in seg.get_content()['inserted'].iteritems():
            comp = [c for c in model.components.itervalues()
                    if c.class_name == mech_name and c.parameters == params]
            assert len(comp) < 2
            if not comp:
                raise Exception("Could not find matching component for '{}' "
                                "mechanisms with params:\n    {}"
                                .format(mech_name, params))
            seg.set_component(comp[0])

if __name__ == '__main__':
    model = import_from_hoc('/home/tclose/git/cerebellarnuclei/'
                             'extracted_data/psections.txt',
                             '/home/tclose/git/cerebellarnuclei/'
                             'extracted_data/mechanisms.txt')
