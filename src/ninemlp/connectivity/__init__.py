"""

This package defines methods for producing patterns of connectivity between neuron populations


@author: Tom Close
@date: 23/01/13
"""
import numpy as np

def transform_matrix(scale_z=1.0, scale_y=1.0, scale_x=1.0, az=0.0, el=0.0):
    """
    Produces a linear transformation matrix for a set of 3D point vectors so that they are scaled 
    by an ellipsoid from x, y and z axis scalings and azimuth and elevation angles
    
    @param scale_x [float): Scale of the x-axis of the transformation matrix
    @param scale_y [float): Scale of the y-axis of the transformation matrix
    @param scale_z [float): Scale of the z-axis of the transformation matrix        
    @param az [float): The azimuth angle of the rotation in the X-Y plane (degrees)
    @param el [float): The elevation angle of the rotation from the Z plane (degrees)    
    """
    # Put the axis scales into a diagonal matrix
    scale = np.array(((scale_x, 0.0, 0.0), (0.0, scale_y, 0.0), (0.0, 0.0, scale_z)))
    # Calculate the rotation matrix from the azimuth and elevation angles
    angles = np.array((az, el)) * (np.pi / 180.0)
    sin = np.sin(angles)
    cos = np.cos(angles)
    rotation = np.array((( cos[0] * cos[1],  sin[0], -cos[0] * sin[1]),
                         (-sin[0] * cos [1], cos[0],  sin[0] * sin[1]),
                         ( sin[1],           0,       cos[1])))
    # Combine scale and rotation for final rotation matrix
    transform = np.dot(rotation, scale)
#    transform = scale
    return transform

def prolate_transform(orientation, anistropy=2.0):
    """
    Produces a linear transformation matrix for a set of 3D point vectors so that they are scaled 
    by an ellipsoid from x, y and z axis scalings and azimuth and elevation angles
    
    @param scale_x [float): Scale of the x-axis of the transformation matrix
    @param scale_y [float): Scale of the y-axis of the transformation matrix
    @param scale_z [float): Scale of the z-axis of the transformation matrix        
    @param az [float): The azimuth angle of the rotation in the X-Y plane (degrees)
    @param el [float): The elevation angle of the rotation from the Z plane (degrees)    
    """


if __name__ == "__main__":
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    import numpy.random
    points = np.mgrid[-1:1:10j, -1:1:10j, -1:1:10j]
    points = np.transpose(np.reshape(points, (3, -1))) 
    fig = plt.figure()
    transform_points = np.transpose(np.dot(transform_matrix(2.0, az=0.0, el=80), 
                                           np.transpose(points)))
    ax2 = fig.add_subplot(111, projection='3d')
    ax2.set_aspect('equal')    
    ax2.scatter(transform_points[:,0], transform_points[:,1], transform_points[:,2])
    ax2.set_xlabel('X Label')
    ax2.set_ylabel('Y Label')
    ax2.set_zlabel('Z Label')
    plt.show()
    
