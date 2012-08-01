#!BPY

"""
Name: 'SWC Importer'
Blender: 245
Group: 'Import'
Tooltip: 'Import swc file'
"""

#import bpy
#import Blender
#from Blender import *
#from Blender.Mathutils import *
from math import *

def loadswc(file_name):
    swcfile = open(file_name, "r")
    content = swcfile.readlines()
    print content
    swcdata = {}
    for line in content:
        if line[0] != '#':
            linedata = line.split()
            id = int(linedata[0])
            type = int(linedata[1])
            x = float(linedata[2])
            y = float(linedata[3])
            z = float(linedata[4])
            radius = float(linedata[5])
            pre = int(linedata[6])
            swcdata[int(linedata[0])] = {"type": type, "x": x, "y":y, "z":z, "radius":radius, "previous":pre}
    return swcdata

def frange_open(start, end, interval):
    if start == end:
        return [start] * interval
    r_list = []
    step = (end - start) / interval
    curr = start + step
    for i in range(interval):
        r_list.append(curr)
        curr += step
    return r_list

def importswc(file_name):
    data = loadswc(file_name)
    point_list = []
    for point in data.values():
        x = point["x"]
        y = point["y"]
        z = point["z"]
        radius = point["radius"]
        point_list.append([x, y, z, radius])
        if point["previous"] == -1:
            continue
        previous = point["previous"]
        pre_x = data[previous]["x"]
        pre_y = data[previous]["y"]
        pre_z = data[previous]["z"]
        pre_radius = data[previous]["radius"]
        dx = fabs(x - pre_x)
        dy = fabs(y - pre_y)
        dz = fabs(z - pre_z)
        dr = fabs(radius - pre_radius)
        dist = sqrt(pow(dx, 2) + pow(dy, 2) + pow(dz, 2))
        #build from pre to current
        min_radius = min(radius, pre_radius)
        interval = int(ceil(dist / min_radius)) * 4
        x_range = frange_open(x, pre_x, interval)
        y_range = frange_open(y, pre_y, interval)
        z_range = frange_open(z, pre_z, interval)
        r_range = frange_open(radius, pre_radius, interval)
        for i in range(len(x_range)):
            if i == 0:
                continue
            point_list.append([x_range[i], y_range[i], z_range[i], r_range[i]])
    mb = Blender.Metaball.New()
    for p in point_list:
        e = mb.elements.add()
        e.co = Vector(p[0], p[1], p[2])
        e.radius = p[3]
        e.stiffness = 1
    sce = Blender.Scene.GetCurrent()
    sce.objects.new(mb)
    Window.RedrawAll()

#Blender.Window.FileSelector(importswc, 'load SWC FILE')
