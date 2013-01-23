"""

This package defines methods for producing patterns of connectivity between neuron populations


@author: Tom Close
@date: 23/01/13
"""
import numpy as np

def transform_tensor(z_scale=1.0, y_scale=1.0, x_scale=1.0, az=0.0, el=0.0):
    """
    Produces a linear transformation matrix for a set of 3D point vectors so that they are scaled 
    by an ellipsoid from x, y and z axis scalings and azimuth and elevation angles
    
    @param scale_x [float]: Scale of the x-axis of the transformation matrix
    @param scale_y [float]: Scale of the y-axis of the transformation matrix
    @param scale_z [float]: Scale of the z-axis of the transformation matrix        
    @param az [float]: The "azimuth angle", the clockwise rotation (in degrees) in the x-y plane starting from the x-axis
    @param el [float]: The "elevation angle", the clockwise rotation (in degrees) in the x-z plane starting from the z axis
    """
    # Put the axis scales into a diagonal matrix
    scale = np.array(((x_scale, 0.0, 0.0), (0.0, y_scale, 0.0), (0.0, 0.0, z_scale)))
    # Calculate the rotation matrix from the azimuth and elevation angles
    angles = np.array((az, el)) * (np.pi / 180.0)
    sin = np.sin(angles)
    cos = np.cos(angles)
    rotation = np.array((( cos[0] * cos[1],  sin[0], -cos[0] * sin[1]),
                         (-sin[0] * cos [1], cos[0],  sin[0] * sin[1]),
                         ( sin[1],           0,       cos[1])))
    # Combine scale and rotation for final rotation matrix
    transform = np.dot(rotation, scale)
    return transform

def symmetric_tensor(orient, para_scale=1.0, perp_scale=1.0):
    """
    Produces a linear transformation matrix for a set of 3D point vectors so that they are scaled 
    by an ellipsoid from x, y and z axis scalings and azimuth and elevation angles
    
    @param scale_x [float]: Scale of the x-axis of the transformation matrix
    @param scale_y [float]: Scale of the y-axis of the transformation matrix
    @param scale_z [float]: Scale of the z-axis of the transformation matrix        
    @param az [float]: The azimuth angle of the rotation in the X-Y plane (degrees)
    @param el [float]: The elevation angle of the rotation from the Z plane (degrees)    
    """
    try:
        orient = np.array(orient, dtype=float).reshape(3)
    except:
        raise Exception("Could not convert first argument ({}) into a three-dimensional vector"
                        .format(orient))
    # Ensure the orientation is normalised
    orient /= np.sqrt(np.sum(orient * orient))
    # Create the eigenvalue matrix
    eig_values = np.array(((para_scale, 0, 0), (0, perp_scale, 0), (0, 0, perp_scale)))
    # Create the eigenvector matrix
    ref_axis = np.zeros(3) # To avoid colinearity between orientation vector and reference vector 
    #                        pick the axis with the smallest value to be the reference axis used to
    #                        get perpendicular vectors
    ref_axis[np.argmin(orient)] = 1.0
    eig_vector2 = np.cross(orient, ref_axis)
    eig_vector2 /= np.sqrt(np.sum(eig_vector2 * eig_vector2))
    eig_vector3 = np.cross(orient, eig_vector2)
    eig_vector3 /= np.sqrt(np.sum(eig_vector3 * eig_vector3))    
    eig_vectors = np.vstack((orient, eig_vector2, eig_vector3))
    # Combine eigenvector and eigenvalue matrices to create tensor
    tensor = np.dot(np.dot(eig_vectors,eig_values), np.transpose(eig_vectors))
    return tensor

if __name__ == "__main__":
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    import numpy.random
    points = np.mgrid[-1:1:30j, -1:1:30j, -1:1:30j]
    points = np.transpose(np.reshape(points, (3, -1)))     
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_aspect('equal')    
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')
    if False:
        transform = transform_tensor(2.0, az=0.0, el=80)
        transform_points = np.transpose(np.dot(transform, 
                                               np.transpose(points)))
        ax.scatter(transform_points[:,0], transform_points[:,1], transform_points[:,2])
    else:
        tensor = symmetric_tensor((1,1,1), 4, 2)
        transformed_points = np.transpose(np.dot(tensor, np.transpose(points)))
        dist = np.sqrt(np.sum(transformed_points * transformed_points, axis=1))
        selected_points = points[(dist < 1.0), :]
        ax.scatter(selected_points[:,0], selected_points[:,1], selected_points[:,2])
    plt.show()
    
