# -*- coding: utf-8 -*-
"""
Created on Wed Feb 13 10:08:06 2013

@author: samsung
"""

import matplotlib.pyplot as plt
from os.path import normpath,join
from ninemlp import SRC_PATH
import morphology
import numpy as np
import matplotlib.pyplot as plt 


def xy_coverages(forest, VOX_SIZE, central_frac=(1.0, 1.0)):
        xy_coverages=[]        
        mask = forest.get_volume_mask(VOX_SIZE)
        #print mask._mask_array.shape
        trimmed_frac = (1.0 - np.array(central_frac)) / 2.0
        start = np.array(np.floor(mask.dim[:2] * trimmed_frac), dtype=int)
        end = np.array(np.ceil(mask.dim[:2] * (1.0 - trimmed_frac)), dtype=int)        
        for z in range(mask._mask_array.shape[2]):
            central_mask = mask._mask_array[start[0]:end[0], start[1]:end[1], 0:z]
            flat_mask = np.sum(central_mask, axis=2)
            num_voxels =  float(np.prod(flat_mask.shape))
            coverage = float(np.count_nonzero(flat_mask)) / num_voxels
            xy_coverages.append(coverage)    
        return xy_coverages,mask._mask_array.shape[2]


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
        VOX_SIZE=(0.5,0.5,1)
        forest[i].offset((0.0, 0.0, -500))                            
        forest[i].align_to_xyz_axes() 
        print "begin to calculate xy-coverage of {}th forest....".format(i)
        coverages,z=xy_coverages(forest[i], VOX_SIZE) 
        if i== 0 or i == 1:
            plt.plot(np.array(range(z)),coverages,"red")
        elif i==2 or i==3 or i==4:
            plt.plot(np.array(range(z)),coverages,"blue")
        elif i==5 or i==6 or i==7:
            plt.plot(np.array(range(z)),coverages,"green")
        plt.xlabel("z-slices")
        plt.ylabel("xy-coverages")
        plt.title("coverages of dendrite trees on xy plane")
    print "begin to plot coverages"
    plt.legend(("P12","P12","P27","P27","P27","P60","P60","P60"))
    plt.show()    
    print 'end'
        
       
