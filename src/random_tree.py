# -*- coding: utf-8 -*-
"""
Created on Mon Feb 18 15:13:58 2013

@author: samsung
"""

import matplotlib.pyplot as plt
from os.path import normpath,join
from ninemlp import SRC_PATH
import morphology_random
import numpy as np
#from xy_coverages import xy_coverages
from copy import deepcopy
VOX_SIZE1=(0.65,0.65,6.5)
VOX_SIZE=(0.5,0.5,1.1)

def random_tree(forest):
    num_tree = len(forest)
    forest_random = deepcopy(forest)
    for tree in forest_random.trees:
        tiled_diams = np.transpose(np.tile(tree.diams, (3, 1)))
        tree.min_bounds = np.min(tree.points - tiled_diams, axis=0)
        tree.max_bounds = np.max(tree.points + tiled_diams, axis=0)        
    for tree in forest_random.trees:
        forest_random.min_bounds = np.select([forest_random.min_bounds <= tree.min_bounds, True],[forest_random.min_bounds, tree.min_bounds])
        forest_random.max_bounds = np.select([forest_random.max_bounds >= tree.max_bounds, True],[forest_random.max_bounds, tree.max_bounds])
    bound = (forest_random.max_bounds-forest_random.min_bounds)/2
    #print forest_random.min_bounds,forest_random.max_bounds
    for j in range( num_tree ):
        k = 0
        while k == 0:
            a=np.random.uniform(-bound[0],bound[0],size=1)
            b=np.random.uniform(-bound[1],bound[1],size=1)
            c=np.random.uniform(-bound[1],bound[1],size=1)
            forest_random[j].offset((a[0],b[0],c[0]))
            k = 1
            for point in forest_random[j].points:
                if point[0] > forest_random.max_bounds[0] or point[0] < forest_random.min_bounds[0] or point[1] > forest_random.max_bounds[1] or point[1] < forest_random.min_bounds[1] or point[2] > forest_random.max_bounds[2] or point[2] < forest_random.min_bounds[2]:
                            k = 0
                            forest_random[j].offset((-a[0],-b[0],-c[0]))
                            break 
    return forest_random

def xy_coverages(forest, VOX_SIZE, central_frac=(1.0, 1.0)):
        xy_coverages=[]        
        mask = forest.get_volume_mask(VOX_SIZE)
        trimmed_frac = (1.0 - np.array(central_frac)) / 2.0
        start = np.array(np.floor(mask.dim[:2] * trimmed_frac), dtype=int)
        end = np.array(np.ceil(mask.dim[:2] * (1.0 - trimmed_frac)), dtype=int)        
        for z in range(mask._mask_array.shape[2]):
            central_mask = mask._mask_array[start[0]:end[0], start[1]:end[1], 0:z]
            flat_mask = np.sum(central_mask, axis=2)
            num_voxels =  float(np.prod(flat_mask.shape))
            coverage = float(np.count_nonzero(flat_mask)) / num_voxels
            print coverage
            xy_coverages.append(coverage)    
        return xy_coverages,mask._mask_array.shape[2]


if __name__=='__main__':
    print "loading forest..."
    forest=morphology_random.Forest(normpath(join(SRC_PATH,'..','morph','Purkinje','xml','GFP_P60.1_slide7_2ndslice-HN-FINAL.xml')))
    print "Finished loading forest."
    forest.offset((0.0, 0.0, -500))
    forest.align_to_xyz_axes()
    forest_random = random_tree(forest)    
    print "begin to calculate coverages"
    coverages1,z1=xy_coverages(forest_random, VOX_SIZE1) 
    plt.plot(np.array(range(z1)),coverages1,"red")
    coverages,z=xy_coverages(forest, VOX_SIZE)     
    plt.plot(np.array(range(z)),coverages,"black")   
    print "begin to plot coverages"
    plt.xlabel("z-slices")
    plt.ylabel("xy-coverages")
    plt.title("xy-coverages of  dendrite trees")
    plt.show()    
    print 'end'