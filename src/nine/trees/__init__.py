"""

This package defines methods for producing patterns of connectivity between neuron populations


@author: Tom Close
@date: 23/01/13
"""
from __future__ import absolute_import
import numpy as np

def transform_tensor(scale=(1.0, 1.0, 1.0), rotation=(0.0, 0.0, 0.0)):
    """
    Produces a linear transformation matrix for a set of 3D point vectors so that they are scaled 
    by an ellipsoid from x, y and z axis scalings and azimuth and elevation angles
    
    @param scale [np.array(3)]: Scalars that are applied to the x, y and z axes respectively before the rotation
    @param rotation [np.array(3)]: The rotation (in degrees) about the x, y and z axes respectively
    """
    try:
        scale = np.array(scale, dtype=float).reshape(3)
    except:
        raise Exception("Could not convert first argument ({}) into a three-dimensional vector"
                        .format(scale))
    try:
        rotation = np.array(rotation, dtype=float).reshape(3)
    except:
        raise Exception("Could not convert second argument ({}) into a three-dimensional vector"
                        .format(rotation))            
    # Convert angles from degrees to radians
    angles = np.array(rotation) * (np.pi / 180.0)
    # Calculate the rotation matrix from the azimuth and elevation angles
    sin = np.sin(angles)
    cos = np.cos(angles)
    rotation = np.array(((cos[1] * cos[2], cos[0] * sin[2] + sin[0] * sin[1] * cos[2],
                          sin[0] * sin[2] - cos[0] * sin[1] * cos[2]),
                         (-cos[1] * sin[2], cos[0] * cos[2] - sin[0] * sin[1] * sin[2],
                          sin[0] * cos[2] + cos[0] * sin[1] * sin[2]),
                         (sin[1], -sin[0] * cos[1], cos[0] * cos[1])))
    # Combine scale and rotation for final rotation matrix
    transform = np.dot(rotation, np.diag(scale))
    return transform

def axially_symmetric_tensor(scale=1.0, orient=(0.0, 0.0, 1.0), isotropy=1.0):
    """
    Produces a linear transformation matrix for a set of 3D point vectors so that they are scaled 
    by an ellipsoid from x, y and z axis scalings and azimuth and elevation angles
    
    @param orient [np.array(3)]: A vector along with the tensor will be orientated
    @param para_scale [float]: The scale of the tensor along the orientation of the orientation vector
    @param perp_scale [float]: The scale of the tensor along the orientations perpedicular to the orientation vector
    """
    try:
        orient = np.array(orient, dtype=float).reshape(3)
    except:
        raise Exception("Could not convert first argument ({}) into a three-dimensional vector"
                        .format(orient))
    # Ensure the orientation is normalised
    orient /= np.sqrt(np.sum(orient * orient))
    # Create the eigenvalue matrix
    para_scale = scale * isotropy
    perp_scale = scale / isotropy
    eig_values = np.array(((para_scale, 0, 0), (0, perp_scale, 0), (0, 0, perp_scale)))
    # Create the eigen-vector matrix
    ref_axis = np.zeros(3) # To avoid co-linearity between orientation vector and reference vector 
    #                        pick the axis with the smallest value within the orientation vector 
    #                        to be the reference axis generate the perpendicular vectors
    ref_axis[np.argmin(orient)] = 1.0
    eig_vector2 = np.cross(orient, ref_axis)
    eig_vector2 /= np.sqrt(np.sum(eig_vector2 * eig_vector2))
    eig_vector3 = np.cross(orient, eig_vector2)
    eig_vector3 /= np.sqrt(np.sum(eig_vector3 * eig_vector3))
    eig_vectors = np.vstack((orient, eig_vector2, eig_vector3))
    # Combine eigenvector and eigenvalue matrices to create tensor
    tensor = np.dot(np.dot(eig_vectors, eig_values), np.transpose(eig_vectors))
    return tensor


if __name__ == "__main__":
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    import numpy.random
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_aspect('equal')
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')
    if True:
        points = np.mgrid[-1:1:10j, -1:1:10j, -1:1:10j]
        points = np.transpose(np.reshape(points, (3, -1)))
        transform = transform_tensor((1,1,2), (0, 90, 45))
        transform_points = np.transpose(np.dot(transform,
                                               np.transpose(points)))
        ax.scatter(transform_points[:, 0], transform_points[:, 1], transform_points[:, 2])
    else:
        points = np.mgrid[-1:1:30j, -1:1:30j, -1:1:30j]
        points = np.transpose(np.reshape(points, (3, -1)))        
        tensor = axially_symmetric_tensor((1, 1, 1), 4, 2)
        transformed_points = np.transpose(np.dot(tensor, np.transpose(points)))
        dist = np.sqrt(np.sum(transformed_points * transformed_points, axis=1))
        selected_points = points[(dist < 1.0), :]
        ax.scatter(selected_points[:, 0], selected_points[:, 1], selected_points[:, 2])
    plt.show()
    
    
    
