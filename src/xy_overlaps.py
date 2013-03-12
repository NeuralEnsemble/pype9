# -*- coding: utf-8 -*-
"""
Created on Mon Feb 18 03:28:56 2013

@author: samsung
"""

import matplotlib.pyplot as plt
from os.path import normpath,join
from ninemlp import SRC_PATH
import morphology
import numpy as np
import matplotlib.pyplot as plt 

def xy_overlaps(forest, VOX_SIZE, central_frac=(1.0, 1.0)):
        xy_overlaps=[]   
        Zs=[]
        mask = forest.get_volume_mask(VOX_SIZE)
        trimmed_frac = (1.0 - np.array(central_frac)) / 2.0
        start = np.array(np.floor(mask.dim[:2] * trimmed_frac), dtype=int)
        end = np.array(np.ceil(mask.dim[:2] * (1.0 - trimmed_frac)), dtype=int)        
        for z in range(mask._mask_array.shape[2]):
            central_mask = mask._mask_array[start[0]:end[0], start[1]:end[1], 0:z]
            temp=np.array(central_mask,dtype = int )
            flat_mask = np.sum(temp, axis=2)
            num_voxels =  float(np.prod(flat_mask.shape))
            #if np.count_nonzero(flat_mask) > 0:
            #    overlap = float(np.count_nonzero(flat_mask)+np.count_nonzero(flat_mask-1) -num_voxels)/ float(np.count_nonzero(flat_mask))
            #    xy_overlaps.append(overlap)  
            #    Zs.append(z)
            overlap = float(np.count_nonzero(flat_mask)+np.count_nonzero(flat_mask-1) -num_voxels)/ float(num_voxels)
            xy_overlaps.append(overlap)
            Zs.append(z)
        return xy_overlaps,Zs


if __name__=='__main__':    
    forest=[]
    print "Loading forest....."    
    forest.append(morphology.Forest(normpath(join(SRC_PATH,'..','morph','Purkinje','xml','GFP_P12.1_slide4_4thslice63x_HN-final.xml'))))
    forest.append(morphology.Forest(normpath(join(SRC_PATH,'..','morph','Purkinje','xml','GFP_P12.3_slidee5_1stslice63x_AP-HN_final.xml'))))
    forest.append(morphology.Forest(normpath(join(SRC_PATH,'..','morph','Purkinje','xml','GFP_P27.1_slide4_3rdslice_edited_HN_final.xml'))))
    forest.append(morphology.Forest(normpath(join(SRC_PATH,'..','morph','Purkinje','xml','GFP_P27.2_slide5_2ndslice_HN-final.xml'))))
    forest.append(morphology.Forest(normpath(join(SRC_PATH,'..','morph','Purkinje','xml','GFP_P27.3_slide4_1stslice-HN-final.xml'))))
    forest.append(morphology.Forest(normpath(join(SRC_PATH,'..','morph','Purkinje','xml','GFP_P60.1_slide7_2ndslice-HN-FINAL.xml'))))
    forest.append(morphology.Forest(normpath(join(SRC_PATH,'..','morph','Purkinje','xml','GFP_P60.2_slide4_2ndslice-HN.xml'))))
    forest.append(morphology.Forest(normpath(join(SRC_PATH,'..','morph','Purkinje','xml','GFP_P60.3_slide7_1stslice.xml'))))
    print "Finished loading forest."   
    for i in range(8):
        VOX_SIZE=(0.5,0.5,0.9)
        forest[i].offset((0.0, 0.0, -500))                            
        forest[i].align_to_xyz_axes() 
        print "begin to calculate overlap of {}th forest....".format(i)
        overlaps,z=xy_overlaps(forest[i], VOX_SIZE)        
        plt.plot(z,overlaps)
        plt.xlabel("z-slices")
        plt.ylabel("xy-overlaps")
        plt.title("xy-overlaps of dendrite trees ")
    print "begin to plot overlaps"
    plt.legend(("P12.1","P12.3","P27.1","P27.2","P27.3","P60.1","P60.2","P60.3"))
    plt.show()    
    print 'end'