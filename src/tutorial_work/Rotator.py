'''
Created on Feb 8, 2013

@author: Lisicovas
'''
#The following script is designed to take in a [3xN] matrix and return a [4xN] matrix, which contains the original matrix as well as
#boolean value that indicates whether they fit in the defined elipsoid.
#Tasks
# 1) Write a function for a rotatable elipsoid.
# 2) Define a checking function.
# 3) Define the array modifying function.

#Create a matrix of random points.




#here I need to have points in different colors. Can I add 

#===============================================================================
# def Three_d_plotter(array_to_plot,ax,c):
# 
# ax.scatter(array_to_plot[0], array_to_plot[1], array_to_plot[2], c)
# 
# return ax
# 
# a=Random_points_array (5, 10)
# b=Random_points_array (5, 10)
# fig = pp.figure()
# ax = fig.add_subplot(111, projection='3d')
# 
# c = Three_d_plotter(a, ax,c='r')
# d = Three_d_plotter(b, c,c='b')
# pp.show()
# #documentation
# #plotting of the points
# 
# #Plotting an ellipsoid
# import numpy as np
# 
# 
# 
# from mpl_toolkits.mplot3d import Axes3D
# import matplotlib.pyplot as plt
# import numpy as np
# 
# fig = plt.figure(figsize=plt.figaspect(1))  # Square figure
# ax = fig.add_subplot(111, projection='3d')
# 
# coefs = (1, 5, 2)  # Coefficients in a0/c x**2 + a1/c y**2 + a2/c z**2 = 1 
# # Radii corresponding to the coefficients:
# rx, ry, rz = [1/np.sqrt(coef) for coef in coefs]
# 
# # Set of all spherical angles:
# u = np.linspace(0, 2 * np.pi, 20)
# v = np.linspace(0, np.pi, 20)
# 
# # Cartesian coordinates that correspond to the spherical angles:
# # (this is the equation of an ellipsoid):
# x = rx * np.outer(np.cos(u), np.sin(v))
# y = ry * np.outer(np.sin(u), np.sin(v))
# z = rz * np.outer(np.ones_like(u), np.cos(v))
# 
# # Plot:
# ax.scatter(x, y, z)
# 
# # Adjustment of the axes, so that they all have the same span:
# max_radius = max(rx, ry, rz)
# for axis in 'xyz':
#  getattr(ax, 'set_{}lim'.format(axis))((-max_radius, max_radius))
# 
# plt.show()
#===============================================================================




import numpy as np
import matplotlib.pyplot as pp
from mpl_toolkits.mplot3d import Axes3D
from ninemlp.connectivity import axially_symmetric_tensor 

def ellipsoid_vertex_matrix (complexity):
    coefs = (1, 1, 1)
    rx, ry, rz = [1/np.sqrt(coef) for coef in coefs]
    u = np.linspace(0, 2 * np.pi, complexity)
    v = np.linspace(0, np.pi, complexity)
    x = rx * np.outer(np.cos(u), np.sin(v))
    y = ry * np.outer(np.sin(u), np.sin(v))
    z = rz * np.outer(np.ones_like(u), np.cos(v))
    ellipsoid_matrix = np.vstack((x.ravel(), y.ravel(), z.ravel()))
    ellipsoid_matrix_transpose = ellipsoid_matrix.transpose()
    return ellipsoid_matrix_transpose


def random_points_array (number_of_points, scale):
    working_array = np.random.random_sample((3, number_of_points))*scale*2-scale
    working_array_transpose = working_array.transpose()
    return working_array_transpose

def transformed_space (input_matrix, scale=1.0, orient=(0.0, 0.0, 1.0), isotropy=1.0):
    working_matrix = axially_symmetric_tensor(scale, orient, isotropy)
    working_matrix_inverse = np.linalg.inv(working_matrix)
    transformed_matrix = np.dot(input_matrix, working_matrix_inverse)
    return transformed_matrix

def ellipsoid_mask_fit(input_matrix, scale=1.0, orient=(0.0, 0.0, 1.0), isotropy=1.0):
    working_matrix = axially_symmetric_tensor(scale, orient, isotropy)
    working_matrix_inverse = numpy.linalg.inv(working_matrix)
    transformed_matrix = numpy.dot(input_matrix, working_matrix_inverse)
    substract_matrix = []
    i=0
    while i < len(transformed_matrix[:,0]):
        distance = numpy.sqrt(transformed_matrix[i,0]**2+transformed_matrix[i,1]**2+transformed_matrix[i,2]**2)
        if distance<=1:
            substract_matrix.append(1)
        else:
            substract_matrix.append(0)
        i=i+1
    return substract_matrix


a = ellipsoid_mask_fit(random_points_array (10000,4), 3.0, (0.5, 0.5, 1.0), 0.5)

print a


fig = pp.figure()
ax = fig.add_subplot(111, projection='3d')
i=0
while i < len(a[:,0]):
    if a[i,3]==1:
        ax.scatter(a[i,0], a[i,1], a[i,2], color='r')
#    else:
#        ax.scatter(a[i,0], a[i,1], a[i,2], color='g')
    i=i+1
ax.scatter(0,0,0,color='r')
ax.set_xbound (-5, 5)
ax.set_ybound (-5, 5)
ax.set_zbound (-5, 5)
pp.show()
