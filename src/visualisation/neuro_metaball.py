"""
    This module contains methods and classes to load dendritic tree's from Neurolucida's SWC file format into a containing class
    @file neuro_metaball.py
    @author Tom Close
    @date 5/11/2011
"""
#######################################################################################
#
#        Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
import bpy #@UnresolvedImport @UnusedImport
import bpy_types #@UnresolvedImport @UnusedImport
import bpy.ops #@UnresolvedImport
from mathutils import Vector #@UnresolvedImport
#from neurolucida_tree import NeurolucidaTree
from math import sqrt, acos, isnan #@UnusedImport
#from numpy.linalg import norm
#from numpy import cross, dot, array, zeros, any
#=======================================================================================================================
# Define some basic linear algebra functions (for 3x1 vectors) to avoid having to import numpy
#=======================================================================================================================
def cross(a, b):
    if len(a) != 3 or len(b) != 3:
        raise Exception ("Lengths of 'a' (%d) and 'b' (%d) vectors must be 3" % (len(a), len(b)))
    c = (a[1] * b[2] - a[2] * b[1],
     a[2] * b[0] - a[0] * b[2],
     a[0] * b[1] - a[1] * b[0])
    return c
def dot(a, b):
    if len(a) != 3 or len(b) != 3:
        raise Exception ("Lengths of 'a' (%d) and 'b' (%d) vectors must be 3" % (len(a), len(b)))
    c = a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    return c
def dot4(a, b):
    if len(a) != 4 or len(b) != 4:
        raise Exception ("Lengths of 'a' (%d) and 'b' (%d) vectors must be 3" % (len(a), len(b)))
    c = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
    return c
def norm(a):
    if len(a) != 3:
        raise Exception ("Lengths of vector (%d) must be 3" % len(a))
    c = sqrt(dot(a, a))
    return c
def norm4(a):
    if len(a) != 4:
        raise Exception ("Lengths of vector (%d) must be 3" % len(a))
    c = sqrt(dot4(a, a))
    return c
def add(a, b):
    if len(a) != 3 or len(b) != 3:
        raise Exception ("Lengths of 'a' (%d) and 'b' (%d) vectors must be 3" % (len(a), len(b)))
    c = (a[0] + b[0], a[1] + b[1], a[2] + b[2])
    return c
def subtract(a, b):
    if len(a) != 3 or len(b) != 3:
        raise Exception ("Lengths of 'a' (%d) and 'b' (%d) vectors must be 3" % (len(a), len(b)))
    c = (a[0] - b[0], a[1] - b[1], a[2] - b[2])
    return c
def subtract4(a, b):
    if len(a) != 4 or len(b) != 4:
        raise Exception ("Lengths of 'a' (%d) and 'b' (%d) vectors must be 4" % (len(a), len(b)))
    c = (a[0] - b[0], a[1] - b[1], a[2] - b[2], a[3] - b[3])
    return c
def scale(a, k):
    if len(a) != 3:
        raise Exception ("Lengths of 'a' vector (%d) must be 3" % len(a))
    b = (a[0] * k, a[1] * k, a[2] * k)
    return b
def scale4(a, k):
    if len(a) != 4:
        raise Exception ("Lengths of 'a' vector (%d) must be 3" % len(a))
    b = (a[0] * k, a[1] * k, a[2] * k, a[3] * k)
    return b

class NeurolucidaTree:

    class Section:
        def __init__(self, section_id, coord, radius, parent):
            self.id = section_id
            self.coord = coord
            self.parent = parent
            self.radius = radius
            self.children = list()
            if parent:
                parent.children.append(self)

        def has_child(self):
            return len(self.children)

        def is_branch_start(self):
            return len(self.parent.children) > 1

        def is_branch_end(self):
            return not len(self.children)

        def is_fork(self):
            return len(self.children) > 1

        def endpoints(self):
            if self.is_branch_start():
                start = self.parent.coord
            else:
                start = add(self.parent.coord, self.coord)
                start = scale(start, 1.0 / 2.0)
            if self.is_fork() or self.is_branch_end():
                end = self.coord
            else:
                end = add(self.coord, self.children[0].coord)
                end = scale(end, 1.0 / 2.0)
            return (start, end)

    def __init__(self):
        self.start = None
        ## Stores all the sections of the tree in a dictionary indexed by the SWC ID
        self.sections = dict()

    def load(self, filename):
        f = open(filename, 'r')
        line_count = 0
        soma_sections = dict()
        while True:
            line = f.readline()
            if not line:
                break
            line_count = line_count + 1
            contents = line.split()
            if len(contents) != 7:
                raise Exception ('Incorrect number of values (%d) on line %d' % (len(contents), line_count))
            section_id = int(contents[0])
            section_type = int(contents[1])
            coord = (float(contents[2]), float(contents[3]), float(contents[4]))
            radius = float(contents[5])
            parent_id = int(contents[6])
            if section_type == 1: #If section is part of soma add it to list so that the dendritic sections can 
                # Note that the "radius" of soma sections is not relevant as it does not correspond to the radius of the actual soma
                soma_sections[section_id] = NeurolucidaTree.Section(section_id, coord, float('NaN'), None)
            elif section_type == 3:    #If section is part of dendritic tree (instead of soma)
                if parent_id == -1:
                    self.start = NeurolucidaTree.Section(section_id, coord, float('NaN'), None)
                    parent = self.start
                elif parent_id in soma_sections.keys():
                    self.start = soma_sections[parent_id]
                    parent = self.start
                else:
                    parent = self.sections[parent_id]
                self.sections[section_id] = NeurolucidaTree.Section(section_id, coord, radius, parent)
            else:
                raise Exception('Unrecognised section type (%d)' % section_type)

        #print 'Loaded %d sections (%d) from file: %s' % (line_count, len(self.sections), filename)
def swc_to_metaball(filename, scene_scale=0.001):
    nl_tree = NeurolucidaTree()
    nl_tree.load(filename)
#    mb_set = bpy.types.MetaBall('neurolucida_tree')
    for sec in nl_tree.sections.values():
        (start, end) = sec.endpoints()
        centre = add(end, start)
        centre = scale(centre, 0.5)
        disp = subtract(end, start)
        length = norm(disp)
        orient = scale(disp, 1.0 / length)
        init_orient = (1, 0, 0)
        # Test to see if orient and init_orient are identical, if so set the quarternion to default
        if not any(subtract(orient, init_orient)):
            quart = (0, 1, 0, 0)
        else:
            rot_axis = cross(orient, init_orient)
            rot_angle = acos(dot(orient, init_orient))
            quart = (rot_angle, rot_axis[0], rot_axis[1], rot_axis[2])
            quart = scale4(quart, 1.0 / norm4(quart))
        co = Vector((centre[0] * scene_scale, centre[1] * scene_scale, centre[2] * scene_scale))
#        mb.size_x = length
#        mb.rotation = quart
#
#        mb.radius = sec.radius
#        mb.stiffness = 1
#        mb.type = 'CAPSULE'
        bpy.ops.object.metaball_add(type='CAPSULE', location=co, rotation=orient)
        bpy.ops.transform.resize(value=(length * scene_scale, sec.radius * scene_scale, sec.radius * scene_scale), constraint_axis=(True, True, True))
        #bpy.ops.transform.rotate(value=(quart[0],), axis=(quart[1],quart[2],quart[3]))
        #print('bpy.ops.object.metaball_add(type=''CAPSULE'', location=' + str(co) + ', rotation=' + str(orient) + ')')
#    sce = bpy.types.Scene.GetCurrent()
#    sce.objects.new(mb)
#bpy.types.Window.FileSelector(swc_to_metaball, 'load SWC FILE')
swc_to_metaball('/home/tclose/git/cerebellarcortex/Visualisation/example_data/example_purkinje.swc')
