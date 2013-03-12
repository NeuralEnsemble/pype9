# -*- coding: utf-8 -*-
"""
Created on Mon Feb 18 06:09:37 2013

@author: samsung
"""

import matplotlib.pyplot as plt
from os.path import normpath,join
from ninemlp import SRC_PATH
import morphology
import numpy as np
import matplotlib.pyplot as plt 

set = [1,2,3,4,5,6,7,8,9,10,12,14,16,18,20,24,28,32,36,40,45,50,55,65,75,88,100]

def overlap(forest, i,j,VOX_SIZE, central_frac=(1.0, 1.0)):
        mask = forest.get_volume_mask(VOX_SIZE)
        trimmed_frac = (1.0 - np.array(central_frac)) / 2.0
        start = np.array(np.floor(mask.dim[:2] * trimmed_frac), dtype=int)
        end = np.array(np.ceil(mask.dim[:2] * (1.0 - trimmed_frac)), dtype=int)        
        central_mask = mask._mask_array[start[0]:end[0], start[1]:end[1], 0].squeeze()
        num_voxels =  float(np.prod(central_mask.shape))
        overlap = forest[i].num_overlapping(forest[j],VOX_SIZE)/ float(num_voxels)
        return overlap

if __name__=='__main__':
    print "Loading forest....."    
    forest=morphology.Forest(normpath(join(SRC_PATH,'..','morph','Purkinje','xml','GFP_P60.1_slide7_2ndslice-HN-FINAL.xml')))
    print "Finished loading forest."   
    for i in range(2):
        for j in range(i+1,3):
            overlaps=[]
            T=[]
            forest.offset((0.0, 0.0, -500))                            
            forest.align_to_xyz_axes() 
            print "begin calculating overlap of {}th and {}th trees....".format(i,j)
            for t in set:
                t1 = float(t)/10.0
                overlaps.append(overlap(forest,i,j, (t1,t1,1000)))
                T.append(t1)
                print t
            plt.plot(T,overlaps)
    print "begin to plot overlaps"
    plt.xlabel("resolution")
    plt.ylabel("xy-overlaps")
    plt.title("xy-overlaps of dendrite trees")        
    plt.show()    
    print 'end'